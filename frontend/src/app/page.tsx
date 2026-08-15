import MenuBar from "@/components/MenuBar";
import Hero from "@/components/Hero";
import Steps from "@/components/Steps";
import Pricing from "@/components/Pricing";
import Proof from "@/components/Proof";
import Faq from "@/components/Faq";
import CtaFooter from "@/components/CtaFooter";
import { DesktopProvider } from "@/components/desktop/DesktopContext";
import FloatingApps from "@/components/desktop/FloatingApps";

export default function Home() {
  return (
    <DesktopProvider>
      <main id="main-content">
        <MenuBar />
        <Hero />
        <Steps />
        <Pricing />
        <Proof />
        <Faq />
        <CtaFooter />
      </main>
      <FloatingApps />
    </DesktopProvider>
  );
}
