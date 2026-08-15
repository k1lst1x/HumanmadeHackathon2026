import { faqs } from "@/lib/site";

export default function Faq() {
  return (
    <section id="faq" className="relative scroll-mt-12 px-5 py-20 sm:py-28">
      <div className="mx-auto max-w-3xl">
        <header className="text-center">
          <p className="text-[13px] font-medium uppercase tracking-[0.16em] text-mute">
            faq
          </p>
          <h2 className="mt-3 text-[clamp(2rem,5vw,3.1rem)] font-medium leading-[1.03] tracking-[-0.035em]">
            what people ask before they text.
          </h2>
        </header>

        <div className="mt-12 overflow-hidden rounded-2xl bg-white shadow-[0_1px_2px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.06)]">
          {faqs.map((f, i) => (
            <details
              key={f.q}
              className={`group px-5 sm:px-7 ${i ? "border-t border-black/[0.08]" : ""}`}
            >
              <summary className="flex cursor-pointer items-center gap-4 py-5 tap-target">
                <h3 className="flex-1 text-[16.5px] font-medium tracking-tight transition-colors group-hover:text-imsg sm:text-[18px]">
                  {f.q}
                </h3>
                <span className="relative flex size-6 shrink-0 items-center justify-center rounded-full bg-black/[0.06] transition-colors group-open:bg-imsg">
                  <span className="absolute h-[1.5px] w-[11px] rounded bg-black/70 transition-colors group-open:bg-white" />
                  <span className="absolute h-[11px] w-[1.5px] rounded bg-black/70 transition-all duration-300 group-open:rotate-90 group-open:bg-white" />
                </span>
              </summary>
              <p className="pb-5 pr-8 text-[15px] leading-relaxed text-mute">
                {f.a}
              </p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
