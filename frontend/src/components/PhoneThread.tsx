"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { site } from "@/lib/site";

/* ── the script ─────────────────────────────────────────────────────────────
   one array drives the whole thread. `step` is the only real state; the quote
   card's price / status / paid flags are derived by folding the mutations of
   every item revealed so far, so the loop can restart cleanly from zero.     */

type Kind = "me" | "them" | "quote" | "system" | "file" | "pay";

type Item = {
  kind: Kind;
  text?: string;
  /** ms of dead air before this item lands */
  pause: number;
  /** ms the "…" indicator shows first (them-side only) */
  typing?: number;
  mutate?: { price?: number; status?: "open" | "countered" | "accepted"; paid?: boolean };
  /** scroll back to the quote card instead of the bottom */
  focus?: boolean;
};

const SCRIPT: Item[] = [
  { kind: "me", pause: 700, text: "need a pitch deck for my seed round. fintech, 12 slides, by friday" },
  {
    kind: "them",
    pause: 500,
    typing: 1500,
    text: "seed-stage fintech, 12 slides, friday. before i price it — do you have live metrics i should pull from, or am i building the story from scratch?",
  },
  { kind: "me", pause: 1500, text: "i'll send numbers. what's the damage?" },
  { kind: "them", pause: 400, typing: 1400, text: "here's the job." },
  { kind: "quote", pause: 350 },
  { kind: "me", pause: 1900, text: "can you do 200?" },
  {
    kind: "them",
    pause: 400,
    typing: 1700,
    text: "200 is below 2× my delivery cost. i'd be taking that at a loss. 295 and i start now.",
    mutate: { price: 295, status: "countered" },
    focus: true,
  },
  { kind: "me", pause: 1900, text: "fine. go." },
  { kind: "system", pause: 700, text: "quote accepted · $295", mutate: { status: "accepted" } },
  { kind: "system", pause: 1100, text: "sandbox resumed · building 12 slides" },
  { kind: "system", pause: 1500, text: "terac verifier hired · −$28" },
  { kind: "file", pause: 1500 },
  { kind: "pay", pause: 1000 },
  { kind: "system", pause: 2200, text: "apple pay · $295 settled to stripe", mutate: { paid: true } },
  {
    kind: "them",
    pause: 700,
    typing: 1300,
    text: "paid. pricing memory updated — acceptance is at 71%, so the next quote goes out 15% higher.",
  },
];

const QUOTE_INDEX = SCRIPT.findIndex((i) => i.kind === "quote");
const BASE_PRICE = 340;

const prefersReduced = () =>
  typeof window !== "undefined" &&
  !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export default function PhoneThread() {
  const [step, setStep] = useState(0);
  const [typing, setTyping] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const quoteRef = useRef<HTMLDivElement>(null);

  /* the reprice item flags itself; the flash lasts exactly as long as the step
     that follows it, so it needs no state of its own */
  const flash = step > 0 && SCRIPT[step - 1]?.focus === true;

  /* fold every mutation revealed so far → current card state */
  const card = useMemo(() => {
    let price = BASE_PRICE;
    let status: "open" | "countered" | "accepted" = "open";
    let paid = false;
    for (const it of SCRIPT.slice(0, step)) {
      if (it.mutate?.price !== undefined) price = it.mutate.price;
      if (it.mutate?.status) status = it.mutate.status;
      if (it.mutate?.paid) paid = true;
    }
    return { price, status, paid };
  }, [step]);

  /* the clock. reduced-motion collapses every delay to ~0 so the thread lands
     fully rendered instead of animating — same code path, no setState in body */
  useEffect(() => {
    const reduced = prefersReduced();
    if (step >= SCRIPT.length) {
      if (reduced) return;
      const t = setTimeout(() => setStep(0), 7000);
      return () => clearTimeout(t);
    }
    const item = SCRIPT[step];
    const pause = reduced ? 0 : item.pause;
    const type = reduced ? 0 : (item.typing ?? 0);
    const timers: ReturnType<typeof setTimeout>[] = [];
    if (type) {
      timers.push(setTimeout(() => setTyping(true), pause));
      timers.push(
        setTimeout(() => {
          setTyping(false);
          setStep((s) => s + 1);
        }, pause + type),
      );
    } else {
      timers.push(setTimeout(() => setStep((s) => s + 1), pause));
    }
    return () => timers.forEach(clearTimeout);
  }, [step]);

  /* Keep the thread pinned to the newest thing — except when a reprice lands,
     where we jump back up to watch the card mutate in place, then return.
     Drives scrollTop on the container directly: scrollIntoView would also
     scroll every ancestor, which drags the whole page down to the phone. */
  useEffect(() => {
    if (step === 0 || prefersReduced()) return;
    const box = scrollRef.current;
    if (!box) return;

    const toBottom = () =>
      box.scrollTo({ top: box.scrollHeight, behavior: "smooth" });

    if (SCRIPT[step - 1]?.focus) {
      const q = quoteRef.current;
      if (q) {
        box.scrollTo({
          top: Math.max(0, q.offsetTop - (box.clientHeight - q.offsetHeight) / 2),
          behavior: "smooth",
        });
      }
      const t = setTimeout(toBottom, 1500);
      return () => clearTimeout(t);
    }
    toBottom();
  }, [step, typing]);

  const visible = SCRIPT.slice(0, step);

  return (
    <div className="relative mx-auto w-full max-w-[360px]">
      {/* glow behind the device */}
      <div
        aria-hidden
        className="absolute -inset-10 -z-10 rounded-full bg-imsg/20 blur-3xl"
      />

      {/* device */}
      <div className="relative rounded-[3.2rem] bg-ink p-[10px] shadow-[0_50px_90px_-20px_rgba(10,10,12,0.55),0_0_0_1px_rgba(255,255,255,0.08)_inset]">
        <div className="relative overflow-hidden rounded-[2.7rem] bg-white">
          {/* dynamic island */}
          <div className="pointer-events-none absolute left-1/2 top-2.5 z-30 h-[26px] w-[92px] -translate-x-1/2 rounded-full bg-ink" />

          {/* status bar */}
          <div className="relative z-20 flex items-center justify-between px-7 pb-1 pt-3.5 text-[13px] font-semibold text-ink">
            <span className="tabular-nums">9:41</span>
            <span className="flex items-center gap-1.5">
              <Signal />
              <Wifi />
              <Battery />
            </span>
          </div>

          {/* messages header */}
          <div className="relative z-20 border-b border-black/10 bg-white/85 px-4 pb-2.5 pt-1 backdrop-blur-xl">
            <div className="flex items-center gap-2">
              <Chevron />
              <div className="flex flex-1 flex-col items-center">
                <div className="relative flex size-9 items-center justify-center rounded-full bubble-blue text-[13px] font-bold tracking-tight">
                  ts
                  <span className="absolute -bottom-0 -right-0 size-2.5 rounded-full bg-money-2 ring-2 ring-white" />
                </div>
                <span className="mt-0.5 text-[11px] font-medium text-ink/80">
                  {site.phone}
                </span>
              </div>
              <div className="w-4" />
            </div>
          </div>

          {/* thread */}
          <div
            ref={scrollRef}
            className="phone-thread-scroll hide-scrollbar relative flex h-[430px] flex-col overflow-y-auto px-3.5 py-4"
          >
            {/* mt-auto pins a short thread to the bottom the way Messages does,
                without the flex-justify-end overflow trap */}
            <div className="mt-auto space-y-2">
              <p className="pb-1 text-center text-[10px] font-medium uppercase tracking-[0.14em] text-black/65">
                imessage · today 9:41
              </p>

              {visible.map((item, i) => (
                <Row
                  key={i}
                  item={item}
                  card={card}
                  quoteRef={i === QUOTE_INDEX ? quoteRef : undefined}
                  flash={i === QUOTE_INDEX && flash}
                />
              ))}

              {typing && <TypingBubble />}
            </div>
          </div>

          {/* input bar */}
          <div className="flex items-center gap-2 border-t border-black/10 bg-white px-3 pb-5 pt-2.5">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-black/[0.06] text-lg leading-none text-black/65">
              +
            </div>
            <div className="flex h-9 flex-1 items-center rounded-full border border-black/15 px-3.5 text-[13px] text-black/65">
              iMessage
              <span className="ml-0.5 inline-block h-[15px] w-px animate-blink bg-imsg" />
            </div>
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bubble-blue">
              <ArrowUp />
            </div>
          </div>

          {/* home indicator */}
          <div className="pointer-events-none absolute bottom-1.5 left-1/2 h-[5px] w-[120px] -translate-x-1/2 rounded-full bg-ink/85" />
        </div>
      </div>
    </div>
  );
}

/* ── rows ────────────────────────────────────────────────────────────────── */

type Card = { price: number; status: "open" | "countered" | "accepted"; paid: boolean };

function Row({
  item,
  card,
  quoteRef,
  flash,
}: {
  item: Item;
  card: Card;
  quoteRef?: React.Ref<HTMLDivElement>;
  flash?: boolean;
}) {
  if (item.kind === "me" || item.kind === "them") {
    const mine = item.kind === "me";
    return (
      <div className={`flex animate-pop ${mine ? "justify-end" : "justify-start"}`}>
        <div
          className={`max-w-[80%] rounded-[20px] px-3.5 py-2 text-[14px] leading-snug ${
            mine
              ? "bubble-blue rounded-br-[7px]"
              : "rounded-bl-[7px] bg-bubble text-ink"
          }`}
        >
          {item.text}
        </div>
      </div>
    );
  }

  if (item.kind === "system") {
    return (
      <div className="animate-pop py-1 text-center">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-black/[0.05] px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-black/70">
          <span className="size-1.5 rounded-full bg-money-2" />
          {item.text}
        </span>
      </div>
    );
  }

  if (item.kind === "file") {
    return (
      <div className="flex animate-pop justify-start">
        <div className="flex w-[80%] items-center gap-3 rounded-[20px] rounded-bl-[7px] bg-bubble p-2.5">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-white shadow-sm">
            <span className="font-mono text-[9px] font-bold text-red-500">PDF</span>
          </div>
          <div className="min-w-0">
            <p className="truncate text-[13px] font-semibold">seed_deck_v3.pdf</p>
            <p className="text-[11px] text-black/70">12 slides · 4.2 mb · verified</p>
          </div>
        </div>
      </div>
    );
  }

  if (item.kind === "pay") {
    return (
      <div className="flex animate-pop justify-start">
        <div className="w-[80%] overflow-hidden rounded-[20px] rounded-bl-[7px] bg-bubble p-2.5">
          <p className="px-1 pb-2 text-[11px] uppercase tracking-wider text-black/70">
            agent pay
          </p>
          <div
            className={`flex h-10 items-center justify-center gap-1.5 rounded-lg text-[13px] font-semibold text-white transition-colors duration-500 ${
              card.paid ? "bg-money" : "bg-ink"
            }`}
          >
            {card.paid ? (
              <>
                <Check /> paid ${card.price}
              </>
            ) : (
              <>
                <Apple /> Pay ${card.price}
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  /* the quote card — mounted once, mutated in place */
  return (
    <div ref={quoteRef} className="flex animate-pop justify-start">
      <div
        className={`w-[86%] overflow-hidden rounded-[20px] rounded-bl-[7px] bg-white shadow-[0_1px_3px_rgba(0,0,0,0.12)] ring-1 transition-all duration-500 ${
          flash ? "scale-[1.03] ring-2 ring-warn" : "ring-black/10"
        }`}
      >
        <div className="flex items-center justify-between bg-bubble/70 px-3 py-1.5">
          <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-black/50">
            quote · seed deck
          </span>
          <StatusChip status={card.status} />
        </div>

        <div className="px-3 pb-3 pt-2.5">
          <div className="flex items-end gap-1.5">
            <span
              key={card.price}
              className="animate-pop text-[34px] font-medium leading-none tracking-tight"
            >
              ${card.price}
            </span>
            {card.price !== BASE_PRICE && (
              <span className="pb-1 font-mono text-[11px] text-black/65 line-through">
                ${BASE_PRICE}
              </span>
            )}
          </div>

          <dl className="mt-2.5 space-y-1 border-t border-black/[0.07] pt-2 text-[11.5px]">
            {[
              ["scope", "12 slides · seed · fintech"],
              ["delivery", "friday, 6:00 pm"],
              ["verification", "1 human expert"],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-3">
                <dt className="text-black/65">{k}</dt>
                <dd className="text-right font-medium text-ink/80">{v}</dd>
              </div>
            ))}
          </dl>

          <div className="mt-3 flex gap-2">
            <button
              disabled
              className={`h-8 flex-1 rounded-lg text-[12.5px] font-semibold text-white transition-colors duration-500 ${
                card.status === "accepted" ? "bg-money" : "bg-imsg"
              }`}
            >
              {card.status === "accepted" ? "accepted ✓" : "accept"}
            </button>
            <button
              disabled
              className="h-8 flex-1 rounded-lg bg-black/[0.06] text-[12.5px] font-semibold text-ink/70"
            >
              counter
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusChip({ status }: { status: Card["status"] }) {
  const map = {
    open: ["open", "bg-imsg/10 text-imsg"],
    countered: ["repriced", "bg-warn/20 text-[#a86000]"],
    accepted: ["accepted", "bg-money/10 text-money"],
  } as const;
  const [label, cls] = map[status];
  return (
    <span
      key={status}
      className={`animate-pop rounded-full px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider ${cls}`}
    >
      {label}
    </span>
  );
}

function TypingBubble() {
  return (
    <div className="flex animate-pop justify-start">
      <div className="flex items-center gap-1 rounded-[20px] rounded-bl-[7px] bg-bubble px-3.5 py-3">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="size-[7px] animate-bounce rounded-full bg-black/35"
            style={{ animationDelay: `${i * 140}ms`, animationDuration: "1s" }}
          />
        ))}
      </div>
    </div>
  );
}

/* ── tiny icons ──────────────────────────────────────────────────────────── */

const Signal = () => (
  <svg width="17" height="11" viewBox="0 0 17 11" fill="currentColor">
    {[0, 1, 2, 3].map((i) => (
      <rect key={i} x={i * 4.4} y={8 - i * 2.5} width="3" height={3 + i * 2.5} rx="1" />
    ))}
  </svg>
);

const Wifi = () => (
  <svg width="16" height="11" viewBox="0 0 16 12" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
    <path d="M1 4.2a10 10 0 0 1 14 0M3.7 7a6.2 6.2 0 0 1 8.6 0" />
    <circle cx="8" cy="10" r="1.1" fill="currentColor" stroke="none" />
  </svg>
);

const Battery = () => (
  <svg width="25" height="12" viewBox="0 0 25 12" fill="none">
    <rect x="0.5" y="0.5" width="21" height="11" rx="3.2" stroke="currentColor" strokeOpacity="0.4" />
    <rect x="2" y="2" width="16" height="8" rx="2" fill="currentColor" />
    <path d="M23 4v4a2 2 0 0 0 0-4z" fill="currentColor" fillOpacity="0.4" />
  </svg>
);

const Chevron = () => (
  <svg width="11" height="18" viewBox="0 0 11 18" fill="none" stroke="#0057d8" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 1 2 9l7 8" />
  </svg>
);

const ArrowUp = () => (
  <svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="M7 12V2M2.5 6.5 7 2l4.5 4.5" />
  </svg>
);

const Check = () => (
  <svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 7.5 5.5 11 12 3.5" />
  </svg>
);

const Apple = () => (
  <svg width="13" height="15" viewBox="0 0 14 16" fill="currentColor">
    <path d="M11.2 8.5c0-1.8 1.4-2.6 1.5-2.7-.8-1.2-2.1-1.4-2.6-1.4-1.1-.1-2.1.6-2.7.6s-1.4-.6-2.3-.6c-1.2 0-2.3.7-2.9 1.7-1.2 2.1-.3 5.3.9 7 .6.9 1.3 1.8 2.2 1.8s1.2-.5 2.3-.5 1.4.5 2.3.5 1.5-.8 2.1-1.7c.7-1 .9-1.9.9-2-.1 0-1.8-.7-1.8-2.7zM9.4 3c.5-.6.8-1.4.7-2.3-.7 0-1.6.5-2.1 1.1-.4.5-.8 1.4-.7 2.2.8.1 1.6-.4 2.1-1z" />
  </svg>
);
