"use client";

import { useState } from "react";
import { samples } from "@/lib/site";
import { TrafficLights } from "./ui";

type Sample = (typeof samples)[number];
type Slide = Sample["slides"][number];

export default function DeckViewer() {
  const [deck, setDeck] = useState(0);
  const [slide, setSlide] = useState(0);
  const s = samples[deck];
  const total = s.slides.length;

  const pick = (i: number) => {
    setDeck(i);
    setSlide(0);
  };
  const go = (d: number) => setSlide((n) => (n + d + total) % total);

  return (
    <div>
      {/* which deck */}
      <div className="flex flex-wrap items-center justify-center gap-2">
        {samples.map((x, i) => (
          <button
            key={x.id}
            onClick={() => pick(i)}
            className={`rounded-full border px-3.5 py-1.5 text-[13px] font-medium transition-colors ${
              i === deck
                ? "border-transparent bg-ink text-white"
                : "border-line bg-white text-black/70 hover:bg-black/[0.04]"
            }`}
          >
            {x.company}
            <span className={i === deck ? "text-white/70" : "text-mute-2"}>
              {" "}
              · {x.tier.split(" · ")[1]}
            </span>
          </button>
        ))}
      </div>

      <div className="mx-auto mt-7 max-w-3xl">
        <div className="win">
          <div className="win-bar">
            <TrafficLights />
            <span className="flex-1 pr-[46px] text-center text-[12px] font-medium text-black/55">
              {s.company.toLowerCase()}_deck.pdf — slide {slide + 1} of {total}
            </span>
          </div>

          <div className="bg-[#f3f3f3] p-3 sm:p-5">
            <SlideView slide={s.slides[slide]} accent={s.accent} />
          </div>

          {/* filmstrip */}
          <div className="flex items-center gap-2 border-t border-black/10 bg-white px-3 py-2.5">
            <button
              onClick={() => go(-1)}
              aria-label="previous slide"
              className="flex size-7 shrink-0 items-center justify-center rounded-full bg-black/[0.06] text-[12px] transition-colors hover:bg-black/10"
            >
              ‹
            </button>
            <div className="hide-scrollbar flex flex-1 gap-1.5 overflow-x-auto">
              {s.slides.map((sl, i) => (
                <button
                  key={i}
                  onClick={() => setSlide(i)}
                  aria-label={`slide ${i + 1}`}
                  className={`h-[7px] flex-1 min-w-[18px] rounded-full transition-colors ${
                    i === slide ? "bg-ink" : "bg-black/15 hover:bg-black/30"
                  }`}
                />
              ))}
            </div>
            <button
              onClick={() => go(1)}
              aria-label="next slide"
              className="flex size-7 shrink-0 items-center justify-center rounded-full bg-black/[0.06] text-[12px] transition-colors hover:bg-black/10"
            >
              ›
            </button>
          </div>
        </div>

        <p className="mt-3 text-center text-[12.5px] text-mute">
          <span className="font-medium text-ink">{s.tier}</span> · first text to
          delivered pdf in {s.turnaround} · {s.line}
        </p>
      </div>
    </div>
  );
}

/* ── slide renderer ────────────────────────────────────────────────────── */

function SlideView({ slide, accent }: { slide: Slide; accent: string }) {
  return (
    <div className="aspect-[16/9] w-full overflow-hidden rounded-[3px] bg-white shadow-[0_2px_10px_rgba(0,0,0,0.14)]">
      <div className="flex h-full flex-col p-[4.5%]">
        {slide.kind === "title" && (
          <div className="flex h-full flex-col justify-center">
            <p
              className="font-mono text-[clamp(7px,1vw,11px)] uppercase tracking-[0.22em]"
              style={{ color: accent }}
            >
              {slide.eyebrow}
            </p>
            <p className="mt-[2%] text-[clamp(22px,5.2vw,58px)] font-semibold leading-none tracking-tight">
              {slide.title}
            </p>
            <p className="mt-[1.5%] text-[clamp(9px,1.7vw,19px)] text-black/60">
              {slide.sub}
            </p>
            <span
              className="mt-[3%] h-[3px] w-[14%] rounded-full"
              style={{ background: accent }}
            />
          </div>
        )}

        {slide.kind === "problem" && (
          <>
            <SlideTitle accent={accent}>{slide.title}</SlideTitle>
            <ul className="mt-[3%] space-y-[2.2%]">
              {slide.bullets.map((b) => (
                <li
                  key={b}
                  className="flex items-start gap-[2%] text-[clamp(8px,1.5vw,17px)] leading-snug text-black/72"
                >
                  <span
                    className="mt-[0.55em] size-[0.42em] shrink-0 rounded-full"
                    style={{ background: accent }}
                  />
                  {b}
                </li>
              ))}
            </ul>
          </>
        )}

        {slide.kind === "chart" && (
          <>
            <SlideTitle accent={accent}>{slide.title}</SlideTitle>
            {/* each column is a definite-height flex box, so the bar's
                percentage height actually resolves */}
            <div className="mt-auto flex h-[58%] gap-[1.6%]">
              {slide.bars.map((h, i) => (
                <div key={i} className="flex flex-1 flex-col">
                  <div className="flex flex-1 items-end">
                    <div
                      className="w-full rounded-t-[2px]"
                      style={{
                        height: `${(h / Math.max(...slide.bars)) * 100}%`,
                        background: accent,
                        opacity: 0.35 + (i / slide.bars.length) * 0.65,
                      }}
                    />
                  </div>
                  <span className="mt-[8%] text-center text-[clamp(6px,0.95vw,11px)] text-black/70">
                    {slide.labels[i]}
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-[2%] font-mono text-[clamp(6px,0.9vw,10px)] uppercase tracking-[0.14em] text-black/65">
              {slide.caption}
            </p>
          </>
        )}

        {slide.kind === "metrics" && (
          <>
            <SlideTitle accent={accent}>{slide.title}</SlideTitle>
            <div className="mt-auto grid h-[62%] grid-cols-2 gap-[3%]">
              {slide.stats.map(([v, k]) => (
                <div
                  key={k}
                  className="flex flex-col justify-center rounded-[3px] bg-black/[0.035] px-[5%]"
                >
                  <span
                    className="text-[clamp(14px,3.1vw,34px)] font-semibold leading-none tracking-tight"
                    style={{ color: accent }}
                  >
                    {v}
                  </span>
                  <span className="mt-[4%] text-[clamp(6.5px,1.05vw,12px)] text-black/50">
                    {k}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}

        {slide.kind === "ask" && (
          <div className="flex h-full flex-col justify-center">
            <p
              className="text-[clamp(18px,4.2vw,46px)] font-semibold leading-none tracking-tight"
              style={{ color: accent }}
            >
              {slide.title}
            </p>
            <ul className="mt-[3.5%] space-y-[2%]">
              {slide.bullets.map((b) => (
                <li
                  key={b}
                  className="text-[clamp(8px,1.5vw,17px)] leading-snug text-black/72"
                >
                  — {b}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function SlideTitle({
  children,
  accent,
}: {
  children: React.ReactNode;
  accent: string;
}) {
  /* rendered slide artwork, not document structure — a heading here would
     skip from the section's h2 straight to h4 */
  return (
    <div>
      <p className="text-[clamp(12px,2.6vw,29px)] font-semibold leading-tight tracking-tight">
        {children}
      </p>
      <span
        className="mt-[1.4%] block h-[2px] w-[9%] rounded-full"
        style={{ background: accent }}
      />
    </div>
  );
}
