import { agentLog, endorsements } from "@/lib/site";
import DeckViewer from "./DeckViewer";
import { Kao, MsgIcon, SmsAqua, TrafficLights } from "./ui";

const TONE = {
  b: "text-[#5ac8fa]",
  g: "text-[#32d74b]",
  w: "text-[#ffd60a]",
  r: "text-[#ff6961]",
  d: "text-white/45",
} as const;

export default function Proof() {
  return (
    <section id="proof" className="relative scroll-mt-12 px-5 py-20 sm:py-28">
      <div className="mx-auto max-w-5xl">
        <header className="text-center">
          <p className="text-[13px] font-medium uppercase tracking-[0.16em] text-mute">
            real work
          </p>
          <h2 className="mt-3 text-[clamp(2rem,5vw,3.1rem)] font-medium leading-[1.03] tracking-[-0.035em]">
            see exactly what you get.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[16px] leading-relaxed text-mute">
            three decks it built, at three prices. click through every slide
            before you spend anything.
          </p>
        </header>

        <div className="mt-12">
          <DeckViewer />
        </div>

        <div className="mt-10 flex flex-col items-center gap-3">
          <SmsAqua variant="blue" size="lg">
            <MsgIcon />
            get one like this
          </SmsAqua>
          <p className="text-[12.5px] text-mute">
            quote back in ninety seconds · you pay after you&apos;ve seen it
          </p>
        </div>

        {/* only renders once real, permitted quotes exist in site.ts */}
        {endorsements.length > 0 && (
          <div className="mt-16 grid gap-4 sm:grid-cols-2">
            {endorsements.map((t, i) => (
              <figure key={t.q} className={`flex ${i % 2 ? "sm:justify-end" : ""}`}>
                <div className="max-w-[27rem]">
                  <blockquote className="rounded-[22px] rounded-bl-[7px] bg-bubble px-4 py-3 text-[15.5px] leading-snug text-ink">
                    {t.q}
                  </blockquote>
                  <figcaption className="mt-1.5 pl-1 text-[11.5px] text-mute-2">
                    {t.by}
                  </figcaption>
                </div>
              </figure>
            ))}
          </div>
        )}

        {/* the agent's own log — the closest thing we have to a dashboard */}
        <div className="relative mt-16">
          <Kao className="absolute -top-7 left-2 hidden sm:block">{"(•_•)"}</Kao>

          <div className="win win-dark">
            <div className="win-bar">
              <TrafficLights dark />
              <span className="flex-1 pr-[46px] text-center text-[12px] font-medium text-white/55">
                textshop — job #4471 — live
              </span>
            </div>
            <div className="hide-scrollbar overflow-x-auto p-5 sm:p-6">
              <ol className="min-w-[520px] space-y-[7px] font-mono text-[12.5px] leading-relaxed">
                {agentLog.map((l) => (
                  <li key={l.t} className="flex gap-3">
                    <span className="shrink-0 text-white/30">{l.t}</span>
                    <span className={TONE[l.c as keyof typeof TONE]}>{l.m}</span>
                  </li>
                ))}
                <li className="flex gap-3">
                  <span className="shrink-0 text-white/30">10:15:46</span>
                  <span className="text-white/45">
                    idle · waiting for next inbound
                    <span className="ml-1 inline-block h-[13px] w-[7px] translate-y-[2px] animate-blink bg-white/60" />
                  </span>
                </li>
              </ol>
            </div>
          </div>

          <p className="mt-3 text-center text-[12.5px] text-mute-2">
            one job, unedited. this is the whole back office.
          </p>
        </div>
      </div>
    </section>
  );
}
