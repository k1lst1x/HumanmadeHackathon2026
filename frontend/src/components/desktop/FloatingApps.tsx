"use client";

import IPod from "./IPod";
import GameBoy from "./GameBoy";
import { useDesktop } from "./DesktopContext";

/**
 * Fixed layer that floats above the page. It is click-through by default, so
 * only the devices themselves capture pointer events — the page underneath
 * stays fully usable while an app is open.
 */
export default function FloatingApps() {
  const { open } = useDesktop();
  if (!open.ipod && !open.gameboy) return null;
  return (
    <div className="pointer-events-none fixed inset-0 z-40">
      <IPod />
      <GameBoy />
    </div>
  );
}
