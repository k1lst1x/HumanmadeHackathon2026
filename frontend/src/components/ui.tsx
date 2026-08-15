import type { ReactNode } from "react";
import { site } from "@/lib/site";

/* ── window chrome ─────────────────────────────────────────────────────── */

export function TrafficLights({ dark = false }: { dark?: boolean }) {
  return (
    <span className="flex items-center gap-[6px]">
      {["#ff5f57", "#febc2e", "#28c840"].map((c) => (
        <span
          key={c}
          className="size-[11px] rounded-full"
          style={{
            background: c,
            boxShadow: dark ? "none" : "inset 0 0 0 0.5px rgba(0,0,0,0.14)",
          }}
        />
      ))}
    </span>
  );
}

export function Win({
  title,
  children,
  dark = false,
  caption,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  dark?: boolean;
  caption?: string;
  className?: string;
}) {
  return (
    <figure className={className}>
      <div className={`win ${dark ? "win-dark" : ""}`}>
        <div className="win-bar">
          <TrafficLights dark={dark} />
          {title && (
            <span
              className={`flex-1 pr-[46px] text-center text-[12px] font-medium ${
                dark ? "text-white/55" : "text-black/55"
              }`}
            >
              {title}
            </span>
          )}
        </div>
        {children}
      </div>
      {caption && (
        <figcaption className="mt-1.5 text-center text-[12px] text-mute-2">
          {caption}
        </figcaption>
      )}
    </figure>
  );
}

/* ── aqua pills ────────────────────────────────────────────────────────── */

type BtnProps = {
  href: string;
  children: ReactNode;
  variant?: "blue" | "plain" | "dark";
  size?: "sm" | "md" | "lg";
  className?: string;
  ariaLabel?: string;
};

const SIZES = {
  sm: "px-3.5 py-1.5 text-[13px]",
  md: "px-5 py-2.5 text-[15px]",
  lg: "px-6 py-3 text-[16px] sm:px-7 sm:py-3.5 sm:text-[17px]",
};

export function Aqua({
  href,
  children,
  variant = "plain",
  size = "md",
  className = "",
  ariaLabel,
}: BtnProps) {
  const v =
    variant === "blue" ? "aqua-blue" : variant === "dark" ? "aqua-dark" : "";
  return (
    <a
      href={href}
      aria-label={ariaLabel}
      className={`aqua ${v} ${SIZES[size]} inline-flex items-center justify-center gap-2 font-medium tap-target ${className}`}
    >
      {children}
    </a>
  );
}

export function SmsAqua(props: Omit<BtnProps, "href" | "ariaLabel">) {
  return <Aqua {...props} href={site.phoneHref} ariaLabel={site.smsAccessibleName} />;
}

/* ── desktop furniture ─────────────────────────────────────────────────── */

export function Sticky({
  children,
  className = "",
  tone = "yellow",
}: {
  children: ReactNode;
  className?: string;
  tone?: "yellow" | "blue" | "pink";
}) {
  const tones = {
    yellow: "bg-[#fff6a8] shadow-[0_8px_18px_-8px_rgba(0,0,0,0.35)]",
    blue: "bg-[#cfe8ff] shadow-[0_8px_18px_-8px_rgba(0,0,0,0.32)]",
    pink: "bg-[#ffd6e2] shadow-[0_8px_18px_-8px_rgba(0,0,0,0.32)]",
  };
  return (
    <div
      className={`px-3 py-2.5 text-[12.5px] leading-snug text-black/80 ${tones[tone]} ${className}`}
    >
      {children}
    </div>
  );
}

export function Kao({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      className={`select-none font-mono text-[17px] text-black/55 ${className}`}
    >
      {children}
    </span>
  );
}

/* an oversized iMessage bubble used as a pull quote */
export function Quote({
  children,
  side = "them",
  className = "",
}: {
  children: ReactNode;
  side?: "me" | "them";
  className?: string;
}) {
  const me = side === "me";
  return (
    <div
      className={`relative max-w-[26rem] rounded-[22px] px-4 py-3 text-[16px] leading-snug ${
        me ? "bubble-blue tail-r" : "bg-bubble text-ink tail-l"
      } ${className}`}
    >
      {children}
    </div>
  );
}

/* ── icons ─────────────────────────────────────────────────────────────── */

export const MsgIcon = ({ className = "" }: { className?: string }) => (
  <svg viewBox="0 0 16 16" fill="currentColor" className={`size-4 ${className}`}>
    <path d="M8 1.4c-3.9 0-7 2.6-7 5.9 0 1.9 1 3.6 2.7 4.7-.1.9-.5 1.8-1.2 2.4 1.3-.1 2.6-.6 3.6-1.4.6.1 1.2.2 1.9.2 3.9 0 7-2.6 7-5.9S11.9 1.4 8 1.4z" />
  </svg>
);

export const Check = ({ className = "" }: { className?: string }) => (
  <svg viewBox="0 0 16 16" className={`size-[15px] shrink-0 ${className}`}>
    <circle cx="8" cy="8" r="8" fill="currentColor" />
    <path
      d="M4.4 8.3 6.9 10.8 11.7 5.6"
      fill="none"
      stroke="#fff"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const Signal = () => (
  <svg width="17" height="11" viewBox="0 0 17 11" fill="currentColor">
    {[0, 1, 2, 3].map((i) => (
      <rect key={i} x={i * 4.4} y={8 - i * 2.5} width="3" height={3 + i * 2.5} rx="1" />
    ))}
  </svg>
);

export const Wifi = () => (
  <svg width="16" height="11" viewBox="0 0 16 12" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
    <path d="M1 4.2a10 10 0 0 1 14 0M3.7 7a6.2 6.2 0 0 1 8.6 0" />
    <circle cx="8" cy="10" r="1.1" fill="currentColor" stroke="none" />
  </svg>
);

export const Battery = () => (
  <svg width="25" height="12" viewBox="0 0 25 12" fill="none">
    <rect x="0.5" y="0.5" width="21" height="11" rx="3.2" stroke="currentColor" strokeOpacity="0.4" />
    <rect x="2" y="2" width="16" height="8" rx="2" fill="currentColor" />
    <path d="M23 4v4a2 2 0 0 0 0-4z" fill="currentColor" fillOpacity="0.4" />
  </svg>
);
