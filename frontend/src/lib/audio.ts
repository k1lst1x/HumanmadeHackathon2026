/**
 * A small four-voice synth: chord pad, lead, bass and a drum kit, through a
 * shared delay send. It is a real audio engine, not a beeper — tracks are
 * written as note strings in tracks.ts and scheduled onto the Web Audio clock.
 *
 * A track can also point at a real file (`src`); when it does, the file plays
 * instead and the synth is the fallback. Everything is created lazily on the
 * first user gesture, which is what autoplay policy requires.
 */

let ctx: AudioContext | null = null;

export function audioCtx(): AudioContext {
  if (!ctx) {
    const AC =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext;
    ctx = new AC();
  }
  if (ctx.state === "suspended") void ctx.resume();
  return ctx;
}

/* ── notes ─────────────────────────────────────────────────────────────── */

const SEMI: Record<string, number> = {
  C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5,
  "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11,
};

export function hz(name: string): number {
  const m = /^([A-G](?:#|b)?)(-?\d)$/.exec(name.trim());
  if (!m) return 0;
  const midi = (Number(m[2]) + 1) * 12 + SEMI[m[1]];
  return 440 * Math.pow(2, (midi - 69) / 12);
}

export type Step = { freqs: number[]; beats: number };

/**
 * "A3,C4,E4/4 F3/2 -/1" → chord for 4 beats, single note for 2, rest for 1.
 * No suffix means one beat.
 */
export function parseSeq(src: string): Step[] {
  return src
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((tok) => {
      const [names, b] = tok.split("/");
      const beats = b ? Number(b) : 1;
      if (names === "-") return { freqs: [], beats };
      return { freqs: names.split(",").map(hz).filter((f) => f > 0), beats };
    });
}

export type SynthTrack = {
  bpm: number;
  /** melody */
  lead?: string;
  /** sustained chords */
  pad?: string;
  bass?: string;
  /** k kick · s snare · h hat · o open hat · "." rest — one char per 1/2 beat,
   *  looped to fill the bar length */
  drums?: string;
  leadWave?: OscillatorType;
  padWave?: OscillatorType;
};

/* ── player ────────────────────────────────────────────────────────────── */

type Node2 = { osc: OscillatorNode; gain: GainNode };

export class Player {
  private master: GainNode;
  private dry: GainNode;
  private delay: DelayNode;
  private fb: GainNode;
  private wet: GainNode;

  private voices: Node2[] = [];
  private sources: AudioBufferSourceNode[] = [];
  private el: HTMLAudioElement | null = null;
  private elSrc: MediaElementAudioSourceNode | null = null;

  private startedAt = 0;
  private offset = 0;
  private loopLen = 0;
  private track: SynthTrack | null = null;
  private rearmTimer: ReturnType<typeof setTimeout> | null = null;

  playing = false;
  missingFile = false;

  constructor(volume = 0.6) {
    const c = audioCtx();
    this.master = c.createGain();
    this.master.gain.value = volume;
    this.master.connect(c.destination);

    this.dry = c.createGain();
    this.dry.gain.value = 1;
    this.dry.connect(this.master);

    // simple ping-pong-ish delay gives the loops some air
    this.delay = c.createDelay(1.2);
    this.delay.delayTime.value = 0.28;
    this.fb = c.createGain();
    this.fb.gain.value = 0.32;
    this.wet = c.createGain();
    this.wet.gain.value = 0.24;
    this.delay.connect(this.fb);
    this.fb.connect(this.delay);
    this.delay.connect(this.wet);
    this.wet.connect(this.master);
  }

  setVolume(v: number) {
    this.master.gain.setTargetAtTime(v, audioCtx().currentTime, 0.02);
  }

  get position(): number {
    if (this.el) return this.el.currentTime;
    if (!this.playing) return this.offset;
    const t = audioCtx().currentTime - this.startedAt + this.offset;
    return this.loopLen ? t % this.loopLen : t;
  }

  get duration(): number {
    if (this.el) return Number.isFinite(this.el.duration) ? this.el.duration : 0;
    return this.loopLen;
  }

  async playFile(src: string): Promise<boolean> {
    this.stop();
    const el = new Audio();
    el.crossOrigin = "anonymous";
    el.loop = true;
    el.preload = "auto";
    el.src = src;
    try {
      await new Promise<void>((res, rej) => {
        const ok = () => res();
        el.addEventListener("canplay", ok, { once: true });
        el.addEventListener("error", () => rej(new Error("load")), { once: true });
        el.load();
      });
      const node = audioCtx().createMediaElementSource(el);
      node.connect(this.master);
      await el.play();
      this.el = el;
      this.elSrc = node;
      this.playing = true;
      this.missingFile = false;
      return true;
    } catch {
      el.src = "";
      this.missingFile = true;
      return false;
    }
  }

  playSynth(track: SynthTrack, from = 0) {
    this.stop();
    this.track = track;
    this.offset = from;
    this.missingFile = false;

    const c = audioCtx();
    const beat = 60 / track.bpm;
    const t0 = c.currentTime + 0.08;
    this.startedAt = t0;

    const lead = track.lead ? parseSeq(track.lead) : [];
    const pad = track.pad ? parseSeq(track.pad) : [];
    const bass = track.bass ? parseSeq(track.bass) : [];
    const len = (s: Step[]) => s.reduce((a, x) => a + x.beats, 0) * beat;
    this.loopLen = Math.max(len(lead), len(pad), len(bass), beat * 4);

    /* two loops scheduled up front, then a timer re-arms — the tracks are
       short enough that this beats a rolling lookahead scheduler */
    for (let rep = 0; rep < 2; rep++) {
      const base = t0 + rep * this.loopLen - from;
      if (base + this.loopLen < c.currentTime) continue;
      if (pad.length) this.voice(pad, base, beat, track.padWave ?? "triangle", 0.055, 0.5, 0.85);
      if (lead.length) this.voice(lead, base, beat, track.leadWave ?? "square", 0.1, 0.008, 0.5);
      if (bass.length) this.voice(bass, base, beat, "sine", 0.26, 0.01, 0.7);
      if (track.drums) this.drums(track.drums, base, beat);
    }

    this.playing = true;
    this.rearm();
  }

  private rearm() {
    if (this.rearmTimer) clearTimeout(this.rearmTimer);
    if (!this.track || this.loopLen <= 0) return;
    this.rearmTimer = setTimeout(
      () => {
        if (this.playing && this.track) this.playSynth(this.track, 0);
      },
      this.loopLen * 2 * 1000 - 220,
    );
  }

  /** one melodic voice; `attack` and `hold` shape it from pluck to pad */
  private voice(
    steps: Step[],
    base: number,
    beat: number,
    wave: OscillatorType,
    vol: number,
    attack: number,
    hold: number,
  ) {
    const c = audioCtx();
    let t = base;
    for (const { freqs, beats } of steps) {
      const dur = beats * beat;
      if (t + dur > c.currentTime) {
        for (const f of freqs) {
          // two slightly detuned oscillators per note = width
          for (const det of [-5, 5]) {
            const osc = c.createOscillator();
            const g = c.createGain();
            osc.type = wave;
            osc.frequency.value = f;
            osc.detune.value = det;
            const on = Math.max(t, c.currentTime);
            const peak = vol / freqs.length;
            g.gain.setValueAtTime(0, on);
            g.gain.linearRampToValueAtTime(peak, on + attack + 0.004);
            g.gain.setTargetAtTime(0.0001, on + dur * hold, dur * 0.22 + 0.05);
            osc.connect(g);
            g.connect(this.dry);
            g.connect(this.delay);
            osc.start(on);
            osc.stop(t + dur + 0.4);
            this.voices.push({ osc, gain: g });
          }
        }
      }
      t += dur;
    }
  }

  private noiseBuf: AudioBuffer | null = null;
  private noise(): AudioBuffer {
    if (this.noiseBuf) return this.noiseBuf;
    const c = audioCtx();
    const b = c.createBuffer(1, c.sampleRate * 0.4, c.sampleRate);
    const d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    this.noiseBuf = b;
    return b;
  }

  private drums(pattern: string, base: number, beat: number) {
    const c = audioCtx();
    const half = beat / 2;
    const total = Math.round(this.loopLen / half);
    for (let i = 0; i < total; i++) {
      const ch = pattern[i % pattern.length];
      if (!ch || ch === ".") continue;
      const t = base + i * half;
      if (t < c.currentTime) continue;
      if (ch === "k") this.kick(t);
      else if (ch === "s") this.snare(t);
      else if (ch === "h") this.hat(t, 0.045, 0.05);
      else if (ch === "o") this.hat(t, 0.16, 0.04);
    }
  }

  private kick(t: number) {
    const c = audioCtx();
    const osc = c.createOscillator();
    const g = c.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(132, t);
    osc.frequency.exponentialRampToValueAtTime(44, t + 0.11);
    g.gain.setValueAtTime(0.5, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.3);
    osc.connect(g);
    g.connect(this.dry);
    osc.start(t);
    osc.stop(t + 0.34);
    this.voices.push({ osc, gain: g });
  }

  private snare(t: number) {
    const c = audioCtx();
    const src = c.createBufferSource();
    const hp = c.createBiquadFilter();
    const g = c.createGain();
    src.buffer = this.noise();
    hp.type = "highpass";
    hp.frequency.value = 1400;
    g.gain.setValueAtTime(0.22, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.16);
    src.connect(hp);
    hp.connect(g);
    g.connect(this.dry);
    g.connect(this.delay);
    src.start(t);
    src.stop(t + 0.2);
    this.sources.push(src);
  }

  private hat(t: number, dur: number, vol: number) {
    const c = audioCtx();
    const src = c.createBufferSource();
    const hp = c.createBiquadFilter();
    const g = c.createGain();
    src.buffer = this.noise();
    hp.type = "highpass";
    hp.frequency.value = 7000;
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(hp);
    hp.connect(g);
    g.connect(this.dry);
    src.start(t);
    src.stop(t + dur + 0.05);
    this.sources.push(src);
  }

  stop() {
    if (this.rearmTimer) clearTimeout(this.rearmTimer);
    this.rearmTimer = null;
    const now = audioCtx().currentTime;
    for (const { osc, gain } of this.voices) {
      try {
        gain.gain.cancelScheduledValues(now);
        gain.gain.setTargetAtTime(0.0001, now, 0.012);
        osc.stop(now + 0.06);
      } catch {
        /* already stopped */
      }
    }
    this.voices = [];
    for (const s of this.sources) {
      try {
        s.stop();
      } catch {
        /* already stopped */
      }
    }
    this.sources = [];
    if (this.el) {
      this.el.pause();
      try {
        this.elSrc?.disconnect();
      } catch {
        /* not connected */
      }
      this.el.src = "";
      this.el = null;
      this.elSrc = null;
    }
    this.playing = false;
  }

  pause() {
    if (this.el) {
      this.el.pause();
      this.playing = false;
      return;
    }
    const at = this.position;
    this.stop();
    this.offset = at;
  }

  resume() {
    if (this.el) {
      void this.el.play();
      this.playing = true;
      return;
    }
    if (this.track) this.playSynth(this.track, this.offset);
  }
}

/* ── one-shot blips for the handheld ───────────────────────────────────── */

export function blip(freq: number, dur = 0.07, type: OscillatorType = "square", vol = 0.11) {
  try {
    const c = audioCtx();
    const osc = c.createOscillator();
    const g = c.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, c.currentTime);
    g.gain.setValueAtTime(vol, c.currentTime);
    g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + dur);
    osc.connect(g);
    g.connect(c.destination);
    osc.start();
    osc.stop(c.currentTime + dur + 0.02);
  } catch {
    /* audio unavailable — games stay playable without sound */
  }
}

export function sweep(from: number, to: number, dur = 0.35) {
  try {
    const c = audioCtx();
    const osc = c.createOscillator();
    const g = c.createGain();
    osc.type = "square";
    osc.frequency.setValueAtTime(from, c.currentTime);
    osc.frequency.exponentialRampToValueAtTime(Math.max(20, to), c.currentTime + dur);
    g.gain.setValueAtTime(0.12, c.currentTime);
    g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + dur);
    osc.connect(g);
    g.connect(c.destination);
    osc.start();
    osc.stop(c.currentTime + dur + 0.02);
  } catch {
    /* no audio */
  }
}
