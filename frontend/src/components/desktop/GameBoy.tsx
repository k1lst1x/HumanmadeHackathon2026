"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { blip, sweep } from "@/lib/audio";
import { useDesktop } from "./DesktopContext";
import Draggable from "./Draggable";

/* real DMG resolution and palette */
const W = 160;
const H = 144;
const PAL = ["#9bbc0f", "#8bac0f", "#306230", "#0f380f"] as const;
const CELL = 8;
const COLS = W / CELL; // 20
const ROWS = H / CELL; // 18

type Mode = "snake" | "brick";
type Phase = "title" | "playing" | "over";
type P = { x: number; y: number };

type State = {
  phase: Phase;
  score: number;
  best: number;
  // snake
  snake: P[];
  dir: P;
  queued: P | null;
  food: P;
  stepMs: number;
  acc: number;
  // brick
  paddle: number;
  ball: { x: number; y: number; vx: number; vy: number };
  bricks: boolean[];
  lives: number;
};

const BRICK_COLS = 8;
const BRICK_ROWS = 4;
const BRICK_W = 18;
const BRICK_H = 7;

function freshSnake(): Pick<State, "snake" | "dir" | "queued" | "food" | "stepMs" | "acc"> {
  return {
    snake: [
      { x: 6, y: 9 },
      { x: 5, y: 9 },
      { x: 4, y: 9 },
    ],
    dir: { x: 1, y: 0 },
    queued: null,
    food: { x: 14, y: 9 },
    stepMs: 130,
    acc: 0,
  };
}

function freshBrick(): Pick<State, "paddle" | "ball" | "bricks" | "lives"> {
  return {
    paddle: W / 2 - 14,
    ball: { x: W / 2, y: 96, vx: 52, vy: -62 },
    bricks: new Array(BRICK_COLS * BRICK_ROWS).fill(true),
    lives: 3,
  };
}

export default function GameBoy() {
  const { open, close, focused, focus } = useDesktop();
  const hasKeys = focused === "gameboy";
  const canvas = useRef<HTMLCanvasElement>(null);
  const st = useRef<State>({
    phase: "title",
    score: 0,
    best: 0,
    ...freshSnake(),
    ...freshBrick(),
  });
  const held = useRef<Record<string, boolean>>({});
  const [mode, setMode] = useState<Mode>("snake");
  const modeRef = useRef<Mode>("snake");
  const [hud, setHud] = useState({ score: 0, best: 0, phase: "title" as Phase });

  const reset = useCallback((m: Mode) => {
    st.current = {
      phase: "playing",
      score: 0,
      best: st.current.best,
      ...freshSnake(),
      ...freshBrick(),
    };
    modeRef.current = m;
    blip(660, 0.06);
    blip(880, 0.06);
  }, []);

  const turn = useCallback((x: number, y: number) => {
    const s = st.current;
    if (modeRef.current === "snake") {
      // no instant reversal
      if (s.dir.x === -x && s.dir.y === -y) return;
      s.queued = { x, y };
    }
  }, []);

  const press = useCallback(
    (k: string, down: boolean) => {
      held.current[k] = down;
      if (!down) return;
      const s = st.current;
      if (k === "start") {
        if (s.phase !== "playing") reset(modeRef.current);
        return;
      }
      if (k === "select") {
        const next: Mode = modeRef.current === "snake" ? "brick" : "snake";
        setMode(next);
        modeRef.current = next;
        st.current = {
          phase: "title",
          score: 0,
          // carry the high score across a game swap instead of wiping it
          best: st.current.best,
          ...freshSnake(),
          ...freshBrick(),
        };
        blip(440, 0.05);
        return;
      }
      if (k === "a" || k === "b") {
        if (s.phase !== "playing") reset(modeRef.current);
        return;
      }
      if (k === "up") turn(0, -1);
      if (k === "down") turn(0, 1);
      if (k === "left") turn(-1, 0);
      if (k === "right") turn(1, 0);
    },
    [reset, turn],
  );

  /* keyboard — gated on focus so the iPod can't swallow the D-pad */
  useEffect(() => {
    if (!open.gameboy || !hasKeys) return;
    const map: Record<string, string> = {
      ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right",
      w: "up", s: "down", a: "left", d: "right",
      Enter: "start", Shift: "select", " ": "a", z: "a", x: "b",
    };
    const down = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      const k = map[e.key];
      if (!k) return;
      e.preventDefault();
      press(k, true);
    };
    const up = (e: KeyboardEvent) => {
      const k = map[e.key];
      if (k) press(k, false);
    };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, [open.gameboy, hasKeys, press]);

  /* the loop */
  useEffect(() => {
    if (!open.gameboy) return;
    const cv = canvas.current;
    if (!cv) return;
    const g = cv.getContext("2d");
    if (!g) return;
    g.imageSmoothingEnabled = false;

    let raf = 0;
    let prev = performance.now();

    const loop = (now: number) => {
      const dt = Math.min(64, now - prev);
      prev = now;
      const s = st.current;

      if (s.phase === "playing") {
        if (modeRef.current === "snake") stepSnake(s, dt);
        else stepBrick(s, dt, held.current);
      }

      draw(g, s, modeRef.current);

      setHud((h) =>
        h.score === s.score && h.best === s.best && h.phase === s.phase
          ? h
          : { score: s.score, best: s.best, phase: s.phase },
      );

      raf = requestAnimationFrame(loop);
    };

    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [open.gameboy]);

  if (!open.gameboy) return null;

  return (
    <Draggable
      clamp
      onGrab={() => focus("gameboy")}
      title="drag the handheld anywhere"
      className="pointer-events-auto absolute right-[6%] top-[15%] z-40"
    >
      <div
        className={`w-[236px] rounded-b-[34px] rounded-t-[12px] bg-gradient-to-b from-[#d5d2ca] to-[#bfbcb4] p-3 transition-shadow ${
          hasKeys
            ? "shadow-[0_28px_60px_-18px_rgba(0,0,0,0.55),0_0_0_2px_rgba(10,124,255,0.75)]"
            : "shadow-[0_28px_60px_-18px_rgba(0,0,0,0.55),0_0_0_1px_rgba(0,0,0,0.18)]"
        }`}
      >
        <div className="mb-2 flex items-center justify-between px-0.5">
          <span className="text-[9px] font-bold uppercase tracking-[0.14em] text-black/70">
            handheld
          </span>
          <button
            data-nodrag
            onClick={() => close("gameboy")}
            aria-label="close handheld"
            className="flex size-[15px] items-center justify-center rounded-full bg-black/15 text-[10px] leading-none text-black/60 transition-colors hover:bg-red hover:text-white"
          >
            ×
          </button>
        </div>

        {/* screen housing */}
        <div className="rounded-[8px] rounded-b-[22px] bg-[#4a4a52] p-3 pb-5">
          <div className="mb-1.5 flex items-center justify-between text-[7px] font-semibold uppercase tracking-[0.18em] text-white/70">
            <span>dot matrix w/ stereo</span>
            <span className="flex items-center gap-1">
              <span className="size-1.5 rounded-full bg-red" />
              batt
            </span>
          </div>
          <canvas
            ref={canvas}
            width={W}
            height={H}
            data-nodrag
            className="block w-full rounded-[2px]"
            style={{ imageRendering: "pixelated", aspectRatio: `${W}/${H}` }}
          />
          <div className="mt-1.5 flex justify-between font-mono text-[8px] text-white/75">
            <span>score {hud.score}</span>
            <span>best {hud.best}</span>
          </div>
        </div>

        {/* controls */}
        <div className="mt-4 flex items-start justify-between px-1">
          <DPad onPress={press} />
          <div className="mt-2 flex rotate-[-18deg] gap-2.5">
            <Ab label="B" onPress={(d) => press("b", d)} />
            <Ab label="A" onPress={(d) => press("a", d)} />
          </div>
        </div>

        <div className="mt-4 flex items-center justify-center gap-4">
          <Pill label="SELECT" onPress={() => press("select", true)} />
          <Pill label="START" onPress={() => press("start", true)} />
        </div>

        <p className="mt-3 text-center text-[8.5px] leading-tight text-black/65">
          {mode === "snake" ? "SNAKE" : "BRICKS"} · select swaps game ·{" "}
          {hasKeys ? "arrows + enter" : "click it for keyboard"}
        </p>
      </div>
    </Draggable>
  );
}

/* ── game logic ────────────────────────────────────────────────────────── */

function placeFood(s: State) {
  for (let i = 0; i < 200; i++) {
    const f = {
      x: Math.floor(Math.random() * COLS),
      y: Math.floor(Math.random() * (ROWS - 2)) + 2,
    };
    if (!s.snake.some((p) => p.x === f.x && p.y === f.y)) {
      s.food = f;
      return;
    }
  }
}

function stepSnake(s: State, dt: number) {
  s.acc += dt;
  if (s.acc < s.stepMs) return;
  s.acc = 0;

  if (s.queued) {
    s.dir = s.queued;
    s.queued = null;
  }

  const head = { x: s.snake[0].x + s.dir.x, y: s.snake[0].y + s.dir.y };

  if (
    head.x < 0 || head.x >= COLS ||
    head.y < 2 || head.y >= ROWS ||
    s.snake.some((p) => p.x === head.x && p.y === head.y)
  ) {
    s.phase = "over";
    s.best = Math.max(s.best, s.score);
    sweep(400, 60, 0.4);
    return;
  }

  s.snake.unshift(head);
  if (head.x === s.food.x && head.y === s.food.y) {
    s.score += 1;
    s.stepMs = Math.max(60, s.stepMs - 4);
    blip(1100, 0.05);
    placeFood(s);
  } else {
    s.snake.pop();
  }
}

function stepBrick(s: State, dt: number, held: Record<string, boolean>) {
  const t = dt / 1000;
  const speed = 96;
  if (held.left) s.paddle -= speed * t;
  if (held.right) s.paddle += speed * t;
  s.paddle = Math.max(0, Math.min(W - 28, s.paddle));

  const b = s.ball;
  b.x += b.vx * t;
  b.y += b.vy * t;

  if (b.x < 1) { b.x = 1; b.vx *= -1; blip(520, 0.03); }
  if (b.x > W - 4) { b.x = W - 4; b.vx *= -1; blip(520, 0.03); }
  if (b.y < 18) { b.y = 18; b.vy *= -1; blip(520, 0.03); }

  // paddle
  if (b.y > 130 && b.y < 138 && b.x > s.paddle - 3 && b.x < s.paddle + 28) {
    b.y = 130;
    b.vy = -Math.abs(b.vy);
    const hit = (b.x - s.paddle) / 28 - 0.5;
    b.vx = hit * 110;
    blip(760, 0.04);
  }

  // bricks
  for (let i = 0; i < s.bricks.length; i++) {
    if (!s.bricks[i]) continue;
    const bx = (i % BRICK_COLS) * (BRICK_W + 2) + 2;
    const by = Math.floor(i / BRICK_COLS) * (BRICK_H + 2) + 20;
    if (b.x + 3 > bx && b.x < bx + BRICK_W && b.y + 3 > by && b.y < by + BRICK_H) {
      s.bricks[i] = false;
      b.vy *= -1;
      s.score += 1;
      blip(980, 0.04);
      break;
    }
  }

  if (s.bricks.every((x) => !x)) {
    s.phase = "over";
    s.best = Math.max(s.best, s.score);
    blip(880, 0.08);
    blip(1320, 0.12);
    return;
  }

  if (b.y > H) {
    s.lives -= 1;
    sweep(300, 80, 0.3);
    if (s.lives <= 0) {
      s.phase = "over";
      s.best = Math.max(s.best, s.score);
      return;
    }
    b.x = W / 2;
    b.y = 96;
    b.vx = 52;
    b.vy = -62;
  }
}

/* ── rendering ─────────────────────────────────────────────────────────── */

function draw(g: CanvasRenderingContext2D, s: State, mode: Mode) {
  g.fillStyle = PAL[0];
  g.fillRect(0, 0, W, H);

  // status bar
  g.fillStyle = PAL[2];
  g.fillRect(0, 0, W, 14);
  g.fillStyle = PAL[0];
  g.font = "8px ui-monospace, monospace";
  g.fillText(mode === "snake" ? "SNAKE" : "BRICKS", 4, 10);
  g.fillText(
    mode === "brick" ? `LIVES ${Math.max(0, s.lives)}` : `LEN ${s.snake.length}`,
    100,
    10,
  );

  if (s.phase === "title" || s.phase === "over") {
    g.fillStyle = PAL[3];
    g.font = "12px ui-monospace, monospace";
    const title = s.phase === "title" ? "PRESS START" : "GAME OVER";
    g.fillText(title, W / 2 - title.length * 3.4, H / 2 - 6);
    g.font = "8px ui-monospace, monospace";
    const sub = s.phase === "title" ? "select = swap game" : `score ${s.score}`;
    g.fillText(sub, W / 2 - sub.length * 2.3, H / 2 + 10);
    return;
  }

  if (mode === "snake") {
    g.fillStyle = PAL[3];
    g.fillRect(s.food.x * CELL + 2, s.food.y * CELL + 2, CELL - 4, CELL - 4);
    s.snake.forEach((p, i) => {
      g.fillStyle = i === 0 ? PAL[3] : PAL[2];
      g.fillRect(p.x * CELL, p.y * CELL, CELL - 1, CELL - 1);
    });
    return;
  }

  g.fillStyle = PAL[2];
  for (let i = 0; i < s.bricks.length; i++) {
    if (!s.bricks[i]) continue;
    const bx = (i % BRICK_COLS) * (BRICK_W + 2) + 2;
    const by = Math.floor(i / BRICK_COLS) * (BRICK_H + 2) + 20;
    g.fillRect(bx, by, BRICK_W, BRICK_H);
  }
  g.fillStyle = PAL[3];
  g.fillRect(Math.round(s.paddle), 134, 28, 4);
  g.fillRect(Math.round(s.ball.x), Math.round(s.ball.y), 3, 3);
}

/* ── control widgets ───────────────────────────────────────────────────── */

function DPad({ onPress }: { onPress: (k: string, d: boolean) => void }) {
  const btn = (k: string, cls: string, glyph: string) => (
    <button
      data-nodrag
      aria-label={k}
      onPointerDown={(e) => { e.preventDefault(); onPress(k, true); }}
      onPointerUp={() => onPress(k, false)}
      onPointerLeave={() => onPress(k, false)}
      className={`absolute flex items-center justify-center bg-[#2f2f36] text-[8px] text-white/70 transition-colors active:bg-[#4a4a52] ${cls}`}
    >
      {glyph}
    </button>
  );
  return (
    <div className="relative size-[74px]">
      {btn("up", "left-[25px] top-0 h-[25px] w-[24px] rounded-t-[4px]", "▲")}
      {btn("left", "left-0 top-[25px] h-[24px] w-[25px] rounded-l-[4px]", "◀")}
      {btn("right", "right-0 top-[25px] h-[24px] w-[25px] rounded-r-[4px]", "▶")}
      {btn("down", "bottom-0 left-[25px] h-[25px] w-[24px] rounded-b-[4px]", "▼")}
      <span className="pointer-events-none absolute left-[25px] top-[25px] size-[24px] bg-[#2f2f36]" />
    </div>
  );
}

function Ab({ label, onPress }: { label: string; onPress: (d: boolean) => void }) {
  return (
    <button
      data-nodrag
      aria-label={`button ${label}`}
      onPointerDown={(e) => { e.preventDefault(); onPress(true); }}
      onPointerUp={() => onPress(false)}
      className="flex size-[34px] items-center justify-center rounded-full bg-gradient-to-b from-[#a03a68] to-[#7d2a4e] text-[11px] font-bold text-white/80 shadow-[0_2px_4px_rgba(0,0,0,0.35),inset_0_1px_0_rgba(255,255,255,0.3)] transition-transform active:scale-95"
    >
      {label}
    </button>
  );
}

function Pill({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <button
      data-nodrag
      onClick={onPress}
      className="flex flex-col items-center gap-1"
    >
      <span className="h-[9px] w-[34px] rotate-[-18deg] rounded-full bg-[#6a6a72] shadow-[inset_0_1px_0_rgba(255,255,255,0.2)] transition-colors active:bg-[#4a4a52]" />
      <span className="text-[7px] font-bold tracking-[0.1em] text-black/70">
        {label}
      </span>
    </button>
  );
}
