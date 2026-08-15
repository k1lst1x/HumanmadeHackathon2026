import { included, promise, site, steps } from "@/lib/site";
import { Aqua, Check, Kao, MsgIcon, Quote } from "./ui";

export default function Steps() {
  return (
    <section id="how" className="relative scroll-mt-12 px-5 py-20 sm:py-28">
      <div className="mx-auto max-w-5xl">
        <header className="text-center">
          <p className="text-[13px] font-medium uppercase tracking-[0.16em] text-mute">
            how it works
          </p>
          <h2 className="mt-3 text-[clamp(2rem,5vw,3.1rem)] font-medium leading-[1.03] tracking-[-0.035em]">
            three texts and you have a deck.
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-[16px] leading-relaxed text-mute">
            there is no dashboard to learn and no call to book. the whole
            business happens in one thread.
          </p>
        </header>

        <ol className="mt-14 grid gap-5 md:grid-cols-3">
          {steps.map((s) => (
            <li
              key={s.n}
              className="relative rounded-2xl bg-white p-6 shadow-[0_1px_2px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.06)]"
            >
              <div className="flex items-center justify-between">
                <span className="flex size-8 items-center justify-center rounded-full bubble-blue text-[13px] font-semibold">
                  {s.n}
                </span>
                <span className="rounded-full bg-black/[0.05] px-2.5 py-1 text-[11px] font-medium text-black/55">
                  {s.tag}
                </span>
              </div>
              <h3 className="mt-4 text-[20px] font-medium tracking-tight">
                {s.t}
              </h3>
              <p className="mt-2 text-[14.5px] leading-relaxed text-mute">
                {s.d}
              </p>
            </li>
          ))}
        </ol>

        {/* what you get + the guarantee, side by side */}
        <div className="mt-16 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-2xl bg-white p-7 shadow-[0_1px_2px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.06)] sm:p-8">
            <h3 className="text-[22px] font-medium tracking-tight">
              what actually lands in your thread
            </h3>
            <ul className="mt-5 space-y-3">
              {included.map((i) => (
                <li key={i} className="flex items-start gap-2.5 text-[15px] leading-snug">
                  <Check className="mt-[3px] text-money-2" />
                  <span className="text-black/75">{i}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="relative overflow-hidden rounded-2xl bg-ink p-7 text-white shadow-[0_1px_2px_rgba(0,0,0,0.06)] sm:p-8">
            <Kao className="absolute right-5 top-5 text-white/25">{"(•_•)"}</Kao>
            <p className="text-[12px] font-medium uppercase tracking-[0.16em] text-white/45">
              the only guarantee that matters
            </p>
            <h3 className="mt-3 text-[clamp(1.5rem,3.4vw,2rem)] font-medium leading-tight tracking-tight">
              {promise.title}
            </h3>
            <p className="mt-4 text-[15px] leading-relaxed text-white/65">
              {promise.body}
            </p>
            <Aqua
              href={site.phoneHref}
              variant="blue"
              className="mt-7 w-full sm:w-auto"
            >
              <MsgIcon />
              get a free quote
            </Aqua>
          </div>
        </div>

        {/* one honest objection, answered in the medium itself */}
        <div className="mt-16 flex flex-col items-center gap-3">
          <Quote side="me" className="self-end sm:self-auto sm:mr-[8%]">
            wait, so nobody there reads my messages?
          </Quote>
          <Quote className="self-start sm:self-auto sm:ml-[8%]">
            nobody. the agent qualifies you, prices the job, hires the human
            reviewer and collects. we find out you were a customer when the
            money lands.
          </Quote>
        </div>
      </div>
    </section>
  );
}
