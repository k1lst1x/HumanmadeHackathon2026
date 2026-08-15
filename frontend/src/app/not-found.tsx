import Link from "next/link";
import { site } from "@/lib/site";
import { MsgIcon, SmsAqua } from "@/components/ui";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-desk px-5 py-16">
      <section className="w-full max-w-xl text-center">
        <p className="font-mono text-[13px] font-semibold uppercase tracking-[0.18em] text-mute">
          404
        </p>
        <h1 className="mt-4 text-[clamp(2.6rem,9vw,5rem)] font-medium leading-none tracking-[-0.045em]">
          wrong thread
        </h1>
        <p className="mx-auto mt-5 max-w-md text-[16px] leading-relaxed text-mute">
          This page is not part of the conversation. Text the agent or head back
          to the shop.
        </p>

        <div className="mt-8 flex flex-col justify-center gap-2.5 sm:flex-row">
          <SmsAqua variant="blue" size="lg" className="w-full sm:w-auto">
            <MsgIcon />
            text {site.phone}
          </SmsAqua>
          <Link
            href="/"
            className="aqua px-6 py-3 text-[16px] font-medium tap-target sm:px-7 sm:py-3.5 sm:text-[17px]"
          >
            back home
          </Link>
        </div>
      </section>
    </main>
  );
}
