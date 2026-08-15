import { site, tiers } from "@/lib/site";
import { Aqua, Check, MsgIcon, Sticky, TrafficLights } from "./ui";

export default function Pricing() {
  return (
    <section
      id="pricing"
      className="sky relative scroll-mt-12 overflow-hidden px-5 py-24 sm:py-32"
    >
      <div className="relative mx-auto max-w-5xl">
        <header className="text-center text-white">
          <p className="text-[13px] font-medium uppercase tracking-[0.16em] text-white/70">
            pricing
          </p>
          <h2 className="mt-3 text-[clamp(2rem,5vw,3.1rem)] font-medium leading-[1.03] tracking-[-0.035em] drop-shadow-sm">
            it quotes you itself.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[16px] leading-relaxed text-white/85">
            there is no rate card — the price comes out of a memory of every job
            it has closed. these are what people actually pay.
          </p>
        </header>

        <div className="mt-14 grid items-start gap-5 md:grid-cols-3">
          {tiers.map((t) => (
            <div key={t.id} className="relative">
              {t.popular && (
                <span className="absolute -top-3 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded-full border border-black/20 bg-white px-3 py-1 text-[12px] font-medium shadow-sm">
                  most ordered
                </span>
              )}

              <div className="win">
                <div className="win-bar">
                  <TrafficLights />
                </div>

                <div className="bg-white px-6 pb-7 pt-7 text-center">
                  <h3 className="text-[26px] font-medium tracking-tight">
                    {t.name}
                  </h3>
                  <p className="mt-1.5 text-[15px] text-black/70">{t.line}</p>
                  <p className="mt-1 text-[12px] text-mute-2">{t.best}</p>

                  <div className="my-6 border-y border-dashed border-black/12 py-6">
                    <p className="text-[clamp(2.6rem,7vw,3.4rem)] font-medium leading-none tracking-tight">
                      {t.price}
                    </p>
                    <p className="mt-2 text-[12.5px] text-mute">
                      typical · quoted per job
                    </p>
                    <Aqua
                      href={site.phoneHref}
                      variant={t.popular ? "blue" : "plain"}
                      className="mt-5"
                    >
                      text to order
                    </Aqua>
                  </div>

                  <p className="text-left text-[13px] text-mute">includes</p>
                  <ul className="mt-3 space-y-2.5 text-left">
                    {t.includes.map((i) => (
                      <li key={i} className="flex items-start gap-2 text-[14px] leading-snug">
                        <Check className="mt-[2px] text-ink" />
                        <span className="text-black/75">{i}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* the negotiation block — heyclicky's maker-discount terminal, ours */}
        <div className="relative mt-10">
          <Sticky
            tone="pink"
            className="absolute -top-4 right-4 z-10 w-[132px] rotate-[6deg] text-[11.5px]"
          >
            it really will say no
          </Sticky>

          <div className="win win-dark">
            <div className="win-bar">
              <TrafficLights dark />
              <span className="flex-1 pr-[46px] text-center text-[12px] font-medium text-white/55">
                negotiate.sh
              </span>
            </div>
            <div className="grid gap-6 p-6 font-mono sm:grid-cols-[1.2fr_auto] sm:items-center sm:p-8">
              <div>
                <p className="text-[15px] text-white">
                  &lt; think it&apos;s too much? &gt;
                </p>
                <p className="mt-3 max-w-lg text-[13.5px] leading-relaxed text-white/55">
                  counter in the thread. it holds a floor at 2× delivery cost and
                  will decline below it — but between the floor and the quote,
                  it deals. students and first-time founders: say so, it factors
                  that in.
                </p>
              </div>
              <Aqua href={site.phoneHref} variant="plain" className="font-sans">
                <MsgIcon />
                make it an offer
              </Aqua>
            </div>
          </div>
        </div>

        <p className="mt-5 text-center text-[12.5px] text-black/45">
          prices shown are what recent jobs settled at. your quote is generated
          for your job and shown before you commit to anything.
        </p>
      </div>
    </section>
  );
}
