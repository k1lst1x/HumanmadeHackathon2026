import { site, stats } from "@/lib/site";
import { Aqua, Kao, MsgIcon, SmsAqua } from "./ui";

export default function CtaFooter() {
  return (
    <>
      <section className="relative overflow-hidden dots border-t border-black/10 px-5 py-24 text-center sm:py-32">
        <Kao className="absolute left-[12%] top-[22%] hidden -rotate-[8deg] lg:block">
          {"\\(^o^)/"}
        </Kao>
        <Kao className="absolute right-[13%] top-[62%] hidden rotate-[7deg] lg:block">
          {"(•‿•)"}
        </Kao>

        <div className="relative mx-auto max-w-2xl">
          <p className="text-[13px] font-medium uppercase tracking-[0.16em] text-mute">
            the entire signup flow
          </p>
          <h2 className="mt-4 text-[clamp(2.2rem,6.5vw,4rem)] font-medium leading-[1] tracking-[-0.04em]">
            open messages.
            <br />
            say what you need.
          </h2>

          <div className="mt-9 flex flex-col items-center justify-center gap-2.5 sm:flex-row">
            <SmsAqua
              variant="blue"
              size="lg"
              className="w-full sm:w-auto"
            >
              <MsgIcon />
              text {site.phone}
            </SmsAqua>
            <Aqua href="#pricing" size="lg" className="w-full sm:w-auto">
              see prices first
            </Aqua>
          </div>

          <p className="mt-4 text-[13px] text-mute">
            quote back in ninety seconds · median {stats.median} to delivery ·
            you pay after you see it
          </p>
        </div>
      </section>

      <footer className="border-t border-black/10 bg-white/50 px-5 py-8">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <span className="flex size-6 items-center justify-center rounded-[7px] bubble-blue">
              <MsgIcon className="size-3.5" />
            </span>
            <span className="text-[14px] font-semibold">textshop</span>
            <span className="text-[13px] text-mute">
              — pitch decks by text
            </span>
          </div>
          <p className="text-center text-[12.5px] text-mute-2 sm:text-right">
            no employees · no dashboard · no website but this one
          </p>
        </div>
      </footer>
    </>
  );
}
