import type { SynthTrack } from "./audio";

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * THE PLAYLIST
 *
 * All four tracks below are original compositions written for this page and
 * played live by the synth in audio.ts — they need no files and work offline.
 *
 * TO PLAY A REAL SONG (e.g. "Sunflower"):
 *   1. put the file you own or have licensed at  public/audio/<name>.mp3
 *   2. add `src: "/audio/<name>.mp3"` to a track below (or a new entry)
 *
 * A track with `src` plays the file and uses its `synth` only as a fallback.
 * Mark it `optional: true` and the iPod will skip past it, with a note on
 * screen, when the file isn't there — so the music never stalls.
 *
 * Nothing copyrighted ships in this repo, and none of these are transcriptions
 * of existing songs.
 * ─────────────────────────────────────────────────────────────────────────────
 */

export type Track = {
  title: string;
  artist: string;
  album: string;
  src?: string;
  /** skip instead of falling back when `src` is missing */
  optional?: boolean;
  synth: SynthTrack;
};

export const TRACKS: Track[] = [
  {
    title: "Blue Bubble",
    artist: "textshop",
    album: "hold music for a quote",
    synth: {
      bpm: 84,
      leadWave: "square",
      padWave: "triangle",
      pad:
        "A3,C4,E4/4 F3,A3,C4/4 C4,E4,G4/4 G3,B3,D4/4 " +
        "A3,C4,E4/4 F3,A3,C4/4 C4,E4,G4/2 G3,B3,D4/2 E3,G3,B3/4",
      lead:
        "E4/1 A4/1 C5/2 C5/1 A4/1 F4/2 " +
        "G4/1 C5/1 E5/2 D5/1 B4/1 G4/2 " +
        "A4/2 C5/1 B4/1 A4/2 G4/1 F4/1 " +
        "E4/1 G4/1 C5/2 B4/2 -/2",
      bass:
        "A2/2 E3/2 F2/2 C3/2 C3/2 G3/2 G2/2 D3/2 " +
        "A2/2 E3/2 F2/2 C3/2 C3/2 G3/2 E2/4",
      drums: "k.h.s.h.k.h.s.h.k.h.s.h.k.hks.ho",
    },
  },
  {
    title: "Ninety Seconds",
    artist: "textshop",
    album: "quote to pdf",
    synth: {
      bpm: 118,
      leadWave: "square",
      padWave: "triangle",
      pad:
        "C4,E4,G4/4 A3,C4,E4/4 F3,A3,C4/4 G3,B3,D4/4 " +
        "C4,E4,G4/4 A3,C4,E4/4 F3,A3,C4/4 G3,B3,D4/4",
      lead:
        "G4/1 C5/1 E5/1 G5/1 E5/2 C5/2 " +
        "A4/1 C5/1 E5/1 A5/1 G5/2 E5/2 " +
        "F4/1 A4/1 C5/1 F5/1 E5/2 C5/2 " +
        "D5/1 B4/1 G4/1 B4/1 C5/4 " +
        "G4/1 C5/1 E5/1 G5/1 E5/2 C5/2 " +
        "A4/1 C5/1 E5/1 A5/1 G5/2 E5/2 " +
        "F4/2 E5/2 D5/2 C5/2 " +
        "G4/1 B4/1 D5/1 F5/1 E5/4",
      bass:
        "C2/1 C2/1 G2/1 C3/1 A1/1 A1/1 E2/1 A2/1 " +
        "F1/1 F1/1 C2/1 F2/1 G1/1 G1/1 D2/1 G2/1 " +
        "C2/1 C2/1 G2/1 C3/1 A1/1 A1/1 E2/1 A2/1 " +
        "F1/1 F1/1 C2/1 F2/1 G1/2 G2/2",
      drums: "k.h.s.h.k.hks.h.k.h.s.h.k.hks.ho",
    },
  },
  {
    title: "Pricing Memory",
    artist: "textshop",
    album: "acceptance 71%",
    synth: {
      bpm: 126,
      leadWave: "sawtooth",
      padWave: "triangle",
      pad:
        "D4,F4,A4/4 D4,F4,A4/4 Bb3,D4,F4/4 Bb3,D4,F4/4 " +
        "F3,A3,C4/4 F3,A3,C4/4 C4,E4,G4/4 C4,E4,G4/4",
      lead:
        "D5/1 A4/1 F4/1 A4/1 D5/1 A4/1 F4/1 A4/1 " +
        "Bb4/1 F4/1 D4/1 F4/1 Bb4/1 F4/1 D4/1 F4/1 " +
        "C5/1 A4/1 F4/1 A4/1 C5/1 A4/1 F4/1 A4/1 " +
        "E5/1 C5/1 G4/1 C5/1 E5/2 D5/2",
      bass: "D2/2 D2/1 A2/1 Bb1/2 Bb1/1 F2/1 F1/2 F1/1 C2/1 C2/2 C2/1 G2/1",
      drums: "k.h.s.h.k.h.s.hkk.h.s.h.k.hks.h.",
    },
  },
  {
    title: "Terminal Green",
    artist: "textshop",
    album: "job #4471",
    synth: {
      bpm: 92,
      leadWave: "triangle",
      padWave: "sine",
      pad:
        "A3,C4,E4/8 G3,B3,D4/8 F3,A3,C4/8 E3,G3,B3/8",
      lead:
        "A4/2 -/1 C5/1 E5/2 -/2 " +
        "D5/2 B4/1 G4/1 A4/4 " +
        "C5/2 -/1 A4/1 F4/2 G4/2 " +
        "E4/2 G4/2 A4/4",
      bass: "A1/4 A1/4 G1/4 G1/4 F1/4 F1/4 E1/4 E1/4",
      drums: "k...h...s...h...k...h.k.s...h.o.",
    },
  },
  {
    // The slot for a real, licensed file. Skipped with a note until it exists.
    title: "Sunflower",
    artist: "add public/audio/sunflower.mp3",
    album: "your file · not shipped with this repo",
    src: "/audio/sunflower.mp3",
    optional: true,
    synth: { bpm: 90, lead: "A4/4", bass: "A2/4" },
  },
];
