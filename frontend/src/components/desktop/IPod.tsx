"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Player, blip } from "@/lib/audio";
import { TRACKS } from "@/lib/tracks";
import { useDesktop } from "./DesktopContext";
import Draggable from "./Draggable";

const fmt = (s: number) => {
  if (!Number.isFinite(s) || s < 0) s = 0;
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
};

type View = "list" | "now";

export default function IPod() {
  const { open, close, focused, focus } = useDesktop();
  const hasKeys = focused === "ipod";
  const player = useRef<Player | null>(null);

  const [view, setView] = useState<View>("list");
  const [sel, setSel] = useState(0);
  const [cur, setCur] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [pos, setPos] = useState(0);
  const [dur, setDur] = useState(0);
  const [note, setNote] = useState<string | null>(null);
  const [vol, setVol] = useState(0.6);

  useEffect(() => {
    if (open.ipod) return;
    player.current?.stop();
    player.current = null;
  }, [open.ipod]);

  useEffect(
    () => () => {
      player.current?.stop();
      player.current = null;
    },
    [],
  );

  /* progress ticker — setState only from the interval callback */
  useEffect(() => {
    const id = setInterval(() => {
      const p = player.current;
      if (!p) return;
      setPos(p.position);
      setDur(p.duration);
      setPlaying(p.playing);
    }, 200);
    return () => clearInterval(id);
  }, []);

  /** Play track i. An `optional` track whose file is missing is skipped, with
      a note, so the music never stalls on a slot that isn't filled in yet.
      Written as a loop rather than recursion — a self-referencing useCallback
      is not something the React Compiler will accept. */
  const play = useCallback(
    async (start: number): Promise<void> => {
      if (!player.current) player.current = new Player(vol);
      const p = player.current;
      p.setVolume(vol);

      let msg: string | null = null;
      let i = start;

      const commit = (at: number) => {
        setNote(msg);
        setCur(at);
        setSel(at);
        setView("now");
        setPlaying(true);
      };

      for (let hop = 0; hop < TRACKS.length; hop++) {
        const t = TRACKS[i];
        if (t.src) {
          if (await p.playFile(t.src)) {
            commit(i);
            return;
          }
          if (t.optional) {
            msg = `${t.title}: drop the mp3 in /public/audio to enable`;
            i = (i + 1) % TRACKS.length;
            continue;
          }
          msg = "file not found — playing the built-in loop";
        }
        p.playSynth(t.synth, 0);
        commit(i);
        return;
      }
    },
    [vol],
  );

  const toggle = useCallback(() => {
    const p = player.current;
    if (cur === null || !p) {
      void play(sel);
      return;
    }
    if (p.playing) {
      p.pause();
      setPlaying(false);
    } else {
      p.resume();
      setPlaying(true);
    }
  }, [cur, play, sel]);

  /** previous / next track — wraps, and keeps playing */
  const skip = useCallback(
    (d: number) => {
      blip(d > 0 ? 980 : 720, 0.04, "square", 0.06);
      const from = cur ?? sel;
      const next = (from + d + TRACKS.length) % TRACKS.length;
      void play(next);
    },
    [cur, play, sel],
  );

  /** move the highlight in the list */
  const move = useCallback((d: number) => {
    blip(860 + d * 60, 0.028, "square", 0.05);
    setView("list");
    setSel((s) => (s + d + TRACKS.length) % TRACKS.length);
  }, []);

  /** MENU: back out of now-playing to the list */
  const menu = useCallback(() => {
    blip(620, 0.035, "square", 0.05);
    setView((v) => (v === "now" ? "list" : "now"));
  }, []);

  /* click wheel: spin to scrub the list.
     Capture is taken only when the gesture starts on the wheel itself —
     capturing on a button press swallows its click, which is exactly why the
     arrows felt dead before. */
  const wheelRef = useRef<HTMLDivElement>(null);
  const lastAngle = useRef<number | null>(null);
  const accum = useRef(0);
  const spinning = useRef(false);

  const onWheelDown = useCallback((e: React.PointerEvent) => {
    if ((e.target as HTMLElement).closest("button")) return;
    spinning.current = true;
    lastAngle.current = null;
    accum.current = 0;
    try {
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    } catch {
      /* capture unavailable */
    }
  }, []);

  const onWheelMove = useCallback(
    (e: React.PointerEvent) => {
      if (!spinning.current || e.buttons !== 1) return;
      const el = wheelRef.current;
      if (!el) return;
      const r = el.getBoundingClientRect();
      const a = Math.atan2(
        e.clientY - (r.top + r.height / 2),
        e.clientX - (r.left + r.width / 2),
      );
      if (lastAngle.current !== null) {
        let d = a - lastAngle.current;
        if (d > Math.PI) d -= 2 * Math.PI;
        if (d < -Math.PI) d += 2 * Math.PI;
        accum.current += d;
        const step = Math.PI / 5;
        while (Math.abs(accum.current) >= step) {
          move(accum.current > 0 ? 1 : -1);
          accum.current -= Math.sign(accum.current) * step;
        }
      }
      lastAngle.current = a;
    },
    [move],
  );

  const onWheelUp = useCallback(() => {
    spinning.current = false;
    lastAngle.current = null;
    accum.current = 0;
  }, []);

  /* keyboard — only while this device owns focus, so it can't steal the
     arrows from the handheld when both are open */
  useEffect(() => {
    if (!open.ipod || !hasKeys) return;
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      switch (e.key) {
        case "ArrowUp": e.preventDefault(); move(-1); break;
        case "ArrowDown": e.preventDefault(); move(1); break;
        case "ArrowLeft": e.preventDefault(); skip(-1); break;
        case "ArrowRight": e.preventDefault(); skip(1); break;
        case "Enter": e.preventDefault(); void play(sel); break;
        case " ": e.preventDefault(); toggle(); break;
        case "Escape": menu(); break;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open.ipod, hasKeys, move, skip, play, sel, toggle, menu]);

  if (!open.ipod) return null;

  const track = cur === null ? null : TRACKS[cur];
  const pct = dur > 0 ? Math.min(100, (pos / dur) * 100) : 0;
  const showNow = view === "now" && track;

  return (
    <Draggable
      clamp
      onGrab={() => focus("ipod")}
      title="drag the iPod anywhere"
      className="pointer-events-auto absolute left-[5%] top-[12%] z-40"
    >
      <div
        className={`w-[250px] rounded-[20px] bg-gradient-to-b from-[#f6f6f6] to-[#d8d8db] p-3 transition-shadow ${
          hasKeys
            ? "shadow-[0_28px_60px_-18px_rgba(0,0,0,0.55),0_0_0_2px_rgba(10,124,255,0.75)]"
            : "shadow-[0_28px_60px_-18px_rgba(0,0,0,0.55),0_0_0_1px_rgba(0,0,0,0.16)]"
        }`}
      >
        <div className="mb-2.5 flex items-center justify-between px-0.5">
          <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-black/70">
            iPod
          </span>
          <button
            data-nodrag
            onClick={() => close("ipod")}
            aria-label="close iPod"
            className="flex size-[15px] items-center justify-center rounded-full bg-black/15 text-[10px] leading-none text-black/60 transition-colors hover:bg-red hover:text-white"
          >
            ×
          </button>
        </div>

        {/* screen */}
        <div className="min-h-[128px] rounded-[5px] bg-[#0f1c14] p-2.5 font-mono text-[11px] text-[#c8ffd8] shadow-[inset_0_2px_10px_rgba(0,0,0,0.85)]">
          <div className="mb-1.5 flex items-center justify-between border-b border-[#c8ffd8]/20 pb-1 text-[9.5px] text-[#c8ffd8]/70">
            <span>{playing ? "▶ now playing" : showNow ? "❙❙ paused" : "iPod"}</span>
            <span>{Math.round(vol * 100)}%</span>
          </div>

          {showNow ? (
            <>
              <p className="truncate text-[12px] font-semibold text-white">
                {track.title}
              </p>
              <p className="truncate text-[10px] text-[#c8ffd8]/70">
                {track.artist}
              </p>
              <p className="truncate text-[9.5px] text-[#c8ffd8]/45">
                {track.album}
              </p>
              <div className="mt-2 h-[5px] overflow-hidden rounded-full bg-[#c8ffd8]/20">
                <div
                  className="h-full rounded-full bg-[#7dffa8]"
                  style={{ width: `${pct}%`, transition: "width .2s linear" }}
                />
              </div>
              <div className="mt-1 flex justify-between text-[9px] text-[#c8ffd8]/60">
                <span>{fmt(pos)}</span>
                <span>
                  {cur !== null ? `${cur + 1}/${TRACKS.length}` : ""} · {fmt(dur)}
                </span>
              </div>
            </>
          ) : (
            <ul className="space-y-[3px]">
              {TRACKS.map((t, i) => (
                <li
                  key={t.title}
                  className={`flex items-center justify-between gap-2 truncate rounded-[3px] px-1 py-[2px] ${
                    i === sel ? "bg-[#7dffa8] text-[#0f1c14]" : ""
                  }`}
                >
                  <span className="truncate">{t.title}</span>
                  {i === cur && <span className="shrink-0 text-[9px]">▶</span>}
                  {t.optional && i !== cur && (
                    <span className="shrink-0 text-[8px] opacity-60">mp3</span>
                  )}
                </li>
              ))}
            </ul>
          )}

          {note && (
            <p className="mt-1.5 border-t border-[#c8ffd8]/20 pt-1 text-[8.5px] leading-tight text-[#ffd76a]">
              {note}
            </p>
          )}
        </div>

        {/* click wheel */}
        <div
          ref={wheelRef}
          data-nodrag
          onPointerDown={onWheelDown}
          onPointerMove={onWheelMove}
          onPointerUp={onWheelUp}
          onPointerCancel={onWheelUp}
          className="relative mx-auto mt-4 size-[172px] touch-none select-none rounded-full bg-gradient-to-b from-[#fcfcfc] to-[#e3e3e6] shadow-[inset_0_1px_2px_#fff,0_1px_3px_rgba(0,0,0,0.22)]"
        >
          <WheelBtn className="left-1/2 top-0 h-[38px] w-[74px] -translate-x-1/2 items-start pt-2" onClick={menu}>
            MENU
          </WheelBtn>
          <WheelBtn className="bottom-0 left-1/2 h-[38px] w-[74px] -translate-x-1/2 items-end pb-2" onClick={() => move(1)}>
            ▼
          </WheelBtn>
          <WheelBtn className="left-0 top-1/2 h-[74px] w-[38px] -translate-y-1/2 justify-start pl-2" onClick={() => skip(-1)}>
            ⏮
          </WheelBtn>
          <WheelBtn className="right-0 top-1/2 h-[74px] w-[38px] -translate-y-1/2 justify-end pr-2" onClick={() => skip(1)}>
            ⏭
          </WheelBtn>

          <button
            data-nodrag
            onClick={() => (view === "list" ? void play(sel) : toggle())}
            aria-label={playing ? "pause" : "play"}
            className="absolute left-1/2 top-1/2 flex size-[64px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-gradient-to-b from-white to-[#e8e8ea] text-[13px] text-black/55 shadow-[inset_0_1px_1px_#fff,0_1px_4px_rgba(0,0,0,0.28)] transition-transform active:scale-95"
          >
            {playing ? "❙❙" : "▶"}
          </button>
        </div>

        <div className="mt-3 flex items-center gap-2 px-1" data-nodrag>
          <span className="text-[10px] text-black/65">vol</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={vol}
            aria-label="volume"
            onChange={(e) => {
              const v = Number(e.target.value);
              setVol(v);
              player.current?.setVolume(v);
            }}
            className="h-1 flex-1 cursor-pointer accent-imsg"
          />
        </div>

        <p className="mt-2 text-center text-[9px] leading-tight text-black/65">
          {hasKeys
            ? "spin the wheel · ⏮⏭ change track · menu goes back"
            : "click the iPod to give it the keyboard"}
        </p>
      </div>
    </Draggable>
  );
}

function WheelBtn({
  children,
  className,
  onClick,
}: {
  children: React.ReactNode;
  className: string;
  onClick: () => void;
}) {
  return (
    <button
      data-nodrag
      onClick={onClick}
      className={`absolute flex items-center justify-center rounded-full text-[10px] font-semibold tracking-wide text-black/70 transition-colors hover:text-black active:text-imsg ${className}`}
    >
      {children}
    </button>
  );
}
