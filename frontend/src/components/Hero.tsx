import { site, stats, trustBar } from "@/lib/site";
import PhoneThread from "./PhoneThread";
import Draggable from "./desktop/Draggable";
import { Aqua, Kao, MsgIcon, Sticky, Win } from "./ui";

export default function Hero() {
  return (
    <section id="top" className="relative overflow-hidden dots pt-[38px]">
      {/* the pitch and the clutter share one stage, so the scattered pieces
          stay beside the headline instead of drifting down the whole page */}
      <div className="relative flex min-h-[560px] flex-col justify-center lg:min-h-[770px]">
        {/* ── scattered desktop, large screens only ─────────────────────
            every piece is a <Draggable> — pick it up, drop it anywhere.   */}
        <div className="absolute inset-0 hidden lg:block">
          <Draggable className="absolute left-[2%] top-[8%] w-[212px] -rotate-[4deg]">
            <Win title="seed_deck_v3.pdf" caption="delivered 10:14 am">
              <SlideThumb />
            </Win>
          </Draggable>

          <Draggable className="absolute left-[4.5%] top-[53%] w-[262px] rotate-[2deg]">
            <Notification />
          </Draggable>

          <Draggable className="absolute left-[2%] top-[85%] w-[148px] -rotate-[7deg]">
            <Sticky tone="yellow">
              one-pager was {stats.from}.<br />
              it set that price itself
            </Sticky>
          </Draggable>

          <Draggable className="absolute right-[2.5%] top-[9%] w-[152px] rotate-[5deg]">
            <Sticky tone="blue">
              i countered $60.
              <br />
              it said no.
            </Sticky>
          </Draggable>

          <Draggable className="absolute right-[4.5%] top-[46%] w-[208px] rotate-[3deg]">
            <Win title="Receipt" caption="stripe · settled">
              <Receipt />
            </Win>
          </Draggable>

          <Draggable className="absolute right-[1.5%] top-[86%] w-[224px] -rotate-[3deg]">
            <div className="rounded-[20px] rounded-bl-[7px] bg-bubble px-3.5 py-2.5 text-[13px] leading-snug text-ink shadow-sm">
              no login. no call. no invoice. i texted a number and got a deck.
            </div>
          </Draggable>

          <Draggable className="absolute right-[19.5%] top-[19%] w-[168px] rotate-[5deg]">
            <Win title="slide 1">
              <TitleSlide />
            </Win>
          </Draggable>

          <Draggable className="absolute left-[20%] top-[36%] -rotate-[6deg]">
            <AppIcon badge="3" />
          </Draggable>

          <Draggable className="absolute left-[23%] top-[5%] rotate-[6deg]">
            <Kao>{"¯\\_(ツ)_/¯"}</Kao>
          </Draggable>
          <Draggable className="absolute right-[24%] top-[6%] -rotate-[7deg]">
            <Kao>{"(•‿•)"}</Kao>
          </Draggable>
          <Draggable className="absolute left-[45%] top-[94%]">
            <Kao>{"^ω^"}</Kao>
          </Draggable>
          <Draggable className="absolute right-[21%] top-[63%] rotate-[5deg]">
            <Kao>{"\\(^o^)/"}</Kao>
          </Draggable>

          <Draggable className="absolute left-[25%] top-[82%] -rotate-[5deg]">
            <Folder label="drafts" />
          </Draggable>
          <Draggable className="absolute right-[24%] top-[81%] rotate-[6deg]">
            <Folder label="decks" />
          </Draggable>
        </div>

        {/* ── the pitch ───────────────────────────────────────────────── */}
        <div className="relative mx-auto w-full max-w-2xl px-5 py-16 text-center">
        <h1 className="animate-rise text-[clamp(3.1rem,9vw,5.5rem)] font-medium leading-[0.98] tracking-[-0.045em]">
          textshop
        </h1>

        <p className="mt-3 animate-rise text-[clamp(1.15rem,3.2vw,1.6rem)] leading-snug text-black/75 [animation-delay:60ms]">
          pitch decks by text. usually done in an hour.
        </p>

        <p className="mx-auto mt-5 max-w-xl animate-rise text-[15.5px] leading-relaxed text-mute [animation-delay:110ms] sm:text-[16.5px]">
          you text what you need. a price comes back in ninety seconds. the deck
          lands in the same thread, checked by a real human before it&apos;s
          sent.{" "}
          <span className="font-medium text-ink">
            you pay after you&apos;ve seen it.
          </span>
        </p>

        <div className="mt-8 flex animate-rise flex-col items-center justify-center gap-2.5 [animation-delay:160ms] sm:flex-row">
          <Aqua
            href={site.phoneHref}
            variant="blue"
            size="lg"
            className="w-full sm:w-auto"
          >
            <MsgIcon />
            text {site.phone}
          </Aqua>
          <Aqua href="#proof" size="lg" className="w-full sm:w-auto">
            see a real deck
          </Aqua>
        </div>

          <p className="mt-3.5 animate-rise text-[13px] text-mute [animation-delay:200ms]">
            free quote · no account · {stats.delivered} decks delivered so far
          </p>
        </div>
      </div>

      {/* ── the product, front and centre ─────────────────────────────── */}
      <div className="relative mx-auto max-w-3xl px-5 pb-4 pt-4">
        <div className="mx-auto w-full max-w-[360px]">
          <PhoneThread />
        </div>
        <p className="mt-4 text-center text-[12.5px] text-mute-2">
          a real job, start to finish — quote, counter, build, human check,
          delivery, payment
        </p>
      </div>

      {/* ── trust strip ───────────────────────────────────────────────── */}
      <div className="relative mt-10 border-y border-black/10 bg-white/60 backdrop-blur">
        <ul className="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-x-7 gap-y-2 px-5 py-3.5">
          {trustBar.map((t) => (
            <li
              key={t}
              className="flex items-center gap-2 text-[13px] text-black/65"
            >
              <span className="size-1.5 rounded-full bg-money" />
              {t}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

/* ── desktop props ─────────────────────────────────────────────────────── */

function SlideThumb() {
  return (
    <div className="aspect-[4/3] bg-white p-3">
      <div className="h-1.5 w-8 rounded-full bg-imsg" />
      <p className="mt-2 text-[10px] font-semibold leading-tight">
        why now: rails finally got cheap
      </p>
      <div className="mt-2 space-y-1">
        {[100, 82, 91, 64].map((w, i) => (
          <div key={i} className="h-[3px] rounded-full bg-black/12" style={{ width: `${w}%` }} />
        ))}
      </div>
      <div className="mt-2.5 flex h-9 items-end gap-1">
        {[28, 40, 34, 62, 78, 100].map((h, i) => (
          <div
            key={i}
            className="flex-1 rounded-[2px] bg-imsg/75"
            style={{ height: `${h}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function Notification() {
  return (
    <div className="flex items-start gap-2.5 rounded-[18px] bg-white/85 p-3 shadow-[0_10px_28px_-10px_rgba(0,0,0,0.4)] ring-1 ring-black/[0.07] backdrop-blur-xl">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-[9px] bubble-green">
        <MsgIcon className="size-4" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <p className="text-[12.5px] font-semibold">Messages</p>
          <p className="text-[10.5px] text-black/40">now</p>
        </div>
        <p className="text-[12.5px] leading-snug text-black/70">
          textshop: your deck is ready — 12 slides, verified.
        </p>
      </div>
    </div>
  );
}

function Receipt() {
  return (
    <div className="relative bg-white px-3.5 py-3">
      <span className="absolute right-2.5 top-2.5 -rotate-[14deg] rounded border-2 border-money-2 px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase tracking-[0.12em] text-money-2">
        paid
      </span>
      <p className="font-mono text-[9.5px] uppercase tracking-[0.14em] text-black/45">
        apple pay
      </p>
      <p className="mt-1 text-[30px] font-semibold leading-none tracking-tight text-ink">
        $95.00
      </p>
      <dl className="mt-2.5 space-y-1 border-t border-black/10 pt-2 text-[10.5px]">
        {[
          ["seed deck", "12 slides"],
          ["human review", "$28"],
          ["settled", "stripe"],
        ].map(([k, v]) => (
          <div key={k} className="flex justify-between gap-2">
            <dt className="text-black/45">{k}</dt>
            <dd className="font-medium text-black/80">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/* a colourful title slide — the collage needs saturation, not more white cards */
function TitleSlide() {
  return (
    <div className="flex aspect-[4/3] flex-col bg-gradient-to-br from-[#0a7cff] via-[#4aa8ff] to-[#7c5cff] p-3.5 text-white">
      <p className="font-mono text-[8.5px] uppercase tracking-[0.18em] text-white/70">
        confidential
      </p>
      <p className="mt-auto text-[17px] font-semibold leading-tight tracking-tight">
        ledger
      </p>
      <p className="text-[10px] leading-snug text-white/80">
        instant settlement for freight brokers
      </p>
      <p className="mt-2.5 text-[8.5px] text-white/60">seed round · 2026</p>
    </div>
  );
}

function AppIcon({ badge, className = "" }: { badge?: string; className?: string }) {
  return (
    <div className={`relative w-[58px] ${className}`}>
      <div className="flex size-[58px] items-center justify-center rounded-[14px] bubble-green shadow-[0_6px_14px_-4px_rgba(0,0,0,0.4)]">
        <MsgIcon className="size-8" />
      </div>
      {badge && (
        <span className="absolute -right-1.5 -top-1.5 flex size-[21px] items-center justify-center rounded-full bg-red text-[11px] font-semibold text-white shadow-sm">
          {badge}
        </span>
      )}
      <p className="mt-1 text-center text-[10.5px] text-black/65">Messages</p>
    </div>
  );
}

function Folder({ label, className = "" }: { label: string; className?: string }) {
  return (
    <div className={`flex w-[74px] flex-col items-center gap-1 ${className}`}>
      <svg viewBox="0 0 64 50" className="w-[52px] drop-shadow-sm">
        <path d="M2 10a4 4 0 0 1 4-4h18l6 6h28a4 4 0 0 1 4 4v30a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4z" fill="#7cc0f0" />
        <path d="M2 16h60v28a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4z" fill="#9ad2f7" />
      </svg>
      <span className="text-[11px] text-black/60">{label}</span>
    </div>
  );
}
