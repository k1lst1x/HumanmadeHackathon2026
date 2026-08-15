"use client";

import { useEffect, useRef, useState } from "react";
import { site } from "@/lib/site";
import { Wifi, Battery, MsgIcon } from "./ui";
import { useDesktop } from "./desktop/DesktopContext";

const LINKS = [
  ["how it works", "#how"],
  ["pricing", "#pricing"],
  ["see a real deck", "#proof"],
  ["faq", "#faq"],
] as const;

const fmt = (d: Date) =>
  d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
const fmtDate = (d: Date) =>
  d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });

type Menu = "music" | "wifi" | "battery" | "clock" | null;

export default function MenuBar() {
  const { open: apps, toggle } = useDesktop();
  const [now, setNow] = useState("9:41 AM");
  const [date, setDate] = useState("");
  const [menu, setMenu] = useState<Menu>(null);
  const bar = useRef<HTMLElement>(null);

  useEffect(() => {
    const id = setInterval(() => {
      const d = new Date();
      setNow(fmt(d));
      setDate(fmtDate(d));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  /* dismiss any open menu on outside click or escape */
  useEffect(() => {
    if (!menu) return;
    const onDown = (e: PointerEvent) => {
      if (!bar.current?.contains(e.target as Node)) setMenu(null);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setMenu(null);
    window.addEventListener("pointerdown", onDown);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("pointerdown", onDown);
      window.removeEventListener("keydown", onKey);
    };
  }, [menu]);

  return (
    <header
      ref={bar}
      className="fixed inset-x-0 top-0 z-50 border-b border-black/10 bg-desk/85 backdrop-blur-xl"
    >
      <div className="flex h-[38px] items-center gap-1 px-3 sm:gap-4 sm:px-5">
        <a href="#top" className="shrink-0 text-[14px] font-semibold tap-target">
          textshop
        </a>

        <nav className="hidden items-center gap-4 md:flex">
          {LINKS.map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="text-[14px] text-black/70 transition-colors hover:text-black"
            >
              {label}
            </a>
          ))}
        </nav>

        <span
          aria-hidden
          className="pointer-events-none absolute left-1/2 hidden -translate-x-1/2 items-center gap-1.5 lg:flex"
        >
          <span className="flex size-[19px] items-center justify-center rounded-[6px] bubble-blue">
            <MsgIcon className="size-[11px]" />
          </span>
          <span className="font-mono text-[11px] text-black/45">
            {site.phoneCompact}
          </span>
        </span>

        <div className="ml-auto flex items-center gap-1 sm:gap-1.5">
          {/* Apple Music — opens the iPod */}
          <MenuItem
            label="Music"
            active={apps.ipod}
            onClick={() => toggle("ipod")}
          >
            <MusicMark on={apps.ipod} />
          </MenuItem>

          {/* the handheld */}
          <MenuItem
            label="Games"
            active={apps.gameboy}
            onClick={() => toggle("gameboy")}
          >
            <GamepadMark on={apps.gameboy} />
          </MenuItem>

          <MenuItem
            label="Wi-Fi"
            active={menu === "wifi"}
            onClick={() => setMenu((m) => (m === "wifi" ? null : "wifi"))}
            className="hidden sm:flex"
          >
            <Wifi />
          </MenuItem>

          <MenuItem
            label="Battery"
            active={menu === "battery"}
            onClick={() => setMenu((m) => (m === "battery" ? null : "battery"))}
            className="hidden sm:flex"
          >
            <Battery />
          </MenuItem>

          <button
            onClick={() => setMenu((m) => (m === "clock" ? null : "clock"))}
            className={`hidden rounded px-1.5 py-1 text-[13px] font-medium tabular-nums text-black/75 transition-colors hover:bg-black/[0.07] sm:inline ${
              menu === "clock" ? "bg-black/[0.09]" : ""
            }`}
          >
            {now}
          </button>

          <a
            href={site.phoneHref}
            aria-label={site.smsAccessibleName}
            className="ml-1 flex items-center gap-1.5 text-[13.5px] font-medium text-imsg tap-target hover:underline"
          >
            <MsgIcon className="size-[13px]" />
            text us
          </a>
        </div>
      </div>

      {/* drop-downs */}
      {menu === "wifi" && (
        <Sheet>
          <SheetRow k="Wi-Fi" v="on" accent />
          <SheetRow k="Network" v="textshop-5G" />
          <SheetRow k="Signal" v="excellent" />
          <p className="mt-2 border-t border-black/10 pt-2 text-[11.5px] leading-snug text-mute">
            you don&apos;t need any of this to buy a deck. it works over sms too.
          </p>
        </Sheet>
      )}
      {menu === "battery" && (
        <Sheet>
          <SheetRow k="Battery" v="87%" accent />
          <SheetRow k="Source" v="agent float" />
          <SheetRow k="Remaining" v="$1,204" />
          <p className="mt-2 border-t border-black/10 pt-2 text-[11.5px] leading-snug text-mute">
            the float is real — it pays the human reviewers out of this.
          </p>
        </Sheet>
      )}
      {menu === "clock" && (
        <Sheet>
          <p className="text-[15px] font-medium">{now}</p>
          <p className="text-[12.5px] text-mute">{date || "—"}</p>
          <p className="mt-2 border-t border-black/10 pt-2 text-[11.5px] leading-snug text-mute">
            median job takes 34 minutes. text now and it&apos;s done before you
            finish your coffee.
          </p>
        </Sheet>
      )}
    </header>
  );
}

/* ── bits ──────────────────────────────────────────────────────────────── */

function MenuItem({
  children,
  label,
  active,
  onClick,
  className = "",
}: {
  children: React.ReactNode;
  label: string;
  active?: boolean;
  onClick: () => void;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      aria-pressed={active}
      title={label}
      className={`flex items-center justify-center rounded px-1.5 py-1 text-black/70 transition-colors hover:bg-black/[0.07] ${
        active ? "bg-black/[0.09] text-black" : ""
      } ${className}`}
    >
      {children}
    </button>
  );
}

function Sheet({ children }: { children: React.ReactNode }) {
  return (
    <div className="absolute right-3 top-[40px] w-[236px] animate-pop rounded-xl border border-black/10 bg-white/95 p-3 shadow-[0_20px_44px_-14px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:right-5">
      {children}
    </div>
  );
}

function SheetRow({ k, v, accent }: { k: string; v: string; accent?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-[3px]">
      <span className="text-[13px] text-black/60">{k}</span>
      <span
        className={`text-[13px] font-medium ${accent ? "text-money-2" : "text-ink"}`}
      >
        {v}
      </span>
    </div>
  );
}

/** Apple Music-style mark: a rounded gradient tile with a beamed note. */
function MusicMark({ on }: { on: boolean }) {
  return (
    <span className="relative flex size-[19px] items-center justify-center overflow-hidden rounded-[5px] bg-gradient-to-b from-[#fb5c74] to-[#fa2f55] shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]">
      <svg viewBox="0 0 24 24" className="size-[13px]" fill="#fff">
        <path d="M20 3.2 9.4 5.5a1 1 0 0 0-.8 1v9.05a3.1 3.1 0 1 0 1.6 2.7V9.06l9-1.95v6.14a3.1 3.1 0 1 0 1.6 2.7V4.18a1 1 0 0 0-1.2-.98z" />
      </svg>
      {on && (
        <span className="absolute inset-x-0 bottom-0 h-[2px] bg-white/90" />
      )}
    </span>
  );
}

function GamepadMark({ on }: { on: boolean }) {
  return (
    <span className="relative flex size-[19px] items-center justify-center overflow-hidden rounded-[5px] bg-gradient-to-b from-[#7d7d86] to-[#4a4a52] shadow-[inset_0_1px_0_rgba(255,255,255,0.32)]">
      <svg viewBox="0 0 24 24" className="size-[12px]" fill="#fff">
        <path d="M7 9h2v2h2v2H9v2H7v-2H5v-2h2V9zm9.5 0a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3zm-2.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z" />
        <path
          d="M4 6h16a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z"
          fill="none"
          stroke="#fff"
          strokeWidth="1.6"
        />
      </svg>
      {on && <span className="absolute inset-x-0 bottom-0 h-[2px] bg-white/90" />}
    </span>
  );
}
