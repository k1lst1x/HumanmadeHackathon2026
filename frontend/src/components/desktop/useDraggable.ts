"use client";

import { useCallback, useRef, useState } from "react";

export type Pos = { x: number; y: number };

/**
 * Pointer-driven dragging.
 *
 * Returns a translate offset rather than absolute coordinates, so an element
 * keeps whatever CSS position it already had (percentages, flow layout, …) and
 * dragging just moves it from there. That keeps the responsive layout intact
 * and stays SSR-safe — nothing is measured on first render.
 */
export function useDraggable(opts: { clampToViewport?: boolean } = {}) {
  const [offset, setOffset] = useState<Pos>({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const start = useRef<{ px: number; py: number; ox: number; oy: number } | null>(null);
  const node = useRef<HTMLElement | null>(null);
  const moved = useRef(false);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      // let real controls (buttons, links, inputs) keep the gesture
      if ((e.target as HTMLElement).closest("[data-nodrag]")) return;
      const el = e.currentTarget as HTMLElement;
      node.current = el;
      try {
        el.setPointerCapture(e.pointerId);
      } catch {
        /* capture unavailable — dragging still works via bubbling */
      }
      start.current = { px: e.clientX, py: e.clientY, ox: offset.x, oy: offset.y };
      moved.current = false;
      setDragging(true);
    },
    [offset.x, offset.y],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      const s = start.current;
      if (!s) return;
      let nx = s.ox + (e.clientX - s.px);
      let ny = s.oy + (e.clientY - s.py);

      if (Math.abs(e.clientX - s.px) + Math.abs(e.clientY - s.py) > 3) {
        moved.current = true;
      }

      if (opts.clampToViewport && node.current) {
        const r = node.current.getBoundingClientRect();
        // where the element would land if the raw delta were applied
        const left = r.left - offset.x + nx;
        const top = r.top - offset.y + ny;
        const maxL = window.innerWidth - 60;
        const maxT = window.innerHeight - 60;
        if (left < -r.width + 60) nx += -r.width + 60 - left;
        if (left > maxL) nx -= left - maxL;
        if (top < 42) ny += 42 - top;
        if (top > maxT) ny -= top - maxT;
      }

      setOffset({ x: nx, y: ny });
    },
    [opts.clampToViewport, offset.x, offset.y],
  );

  const end = useCallback((e: React.PointerEvent) => {
    start.current = null;
    setDragging(false);
    try {
      (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      /* pointer already released */
    }
  }, []);

  const reset = useCallback(() => setOffset({ x: 0, y: 0 }), []);

  return {
    offset,
    dragging,
    /** true when the last gesture actually moved — use it to suppress a click */
    didMove: () => moved.current,
    reset,
    handlers: {
      onPointerDown,
      onPointerMove,
      onPointerUp: end,
      onPointerCancel: end,
    },
    style: {
      transform: `translate3d(${offset.x}px, ${offset.y}px, 0)`,
      touchAction: "none" as const,
    },
  };
}
