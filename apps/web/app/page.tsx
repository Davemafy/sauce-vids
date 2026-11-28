import Image from 'next/image';
import Link from 'next/link';
import { ArrowRightIcon, ArrowUpRightIcon, GithubLogoIcon } from '@phosphor-icons/react/ssr';
import { WaitlistForm } from '../components/waitlist-form';

const github = 'https://github.com/Davemafy/sauce-vids';

function Wordmark() {
  return (
    <a
      href="#top"
      aria-label="Sauce — back to top"
      className="inline-flex items-start font-script text-[43px] leading-none tracking-[-.055em] text-sauce-cream sm:text-[49px]"
    >
      Sauce
      <sup className="ml-1 pt-[4px] font-body text-[10px] font-bold tracking-normal">TM</sup>
    </a>
  );
}

function Header() {
  return (
    <header className="relative z-50 bg-sauce-red text-sauce-cream">
      <div className="mx-auto flex h-[74px] max-w-[1720px] items-center justify-between gap-6 px-5 sm:h-[82px] sm:px-10 xl:px-16">
        <Wordmark />
        <p className="hidden font-display text-[21px] font-black uppercase tracking-[.075em] text-sauce-cream/90 md:block">
          Product videos, with taste.
        </p>
        <div className="flex items-center gap-4 sm:gap-6">
         <a href="#film" className="hidden text-[13px] font-semibold text-sauce-cream underline-offset-4 hover:underline sm:inline">Watch the film</a>
         <a
          href="#waitlist"
          className="inline-flex min-h-[44px] items-center gap-2 rounded-full border-2 border-sauce-cream bg-sauce-cream px-4 font-display text-[19px] font-black uppercase leading-none text-sauce-red transition-colors hover:bg-[#f7cf6e] focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-sauce-cream sm:px-6 sm:text-[23px]"
        >
          Get early access
          <ArrowRightIcon size={18} weight="bold" aria-hidden="true" />
         </a>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <main id="top">
      <section
        aria-labelledby="hero-heading"
        className="relative isolate min-h-[970px] overflow-hidden bg-sauce-orange sm:min-h-[1000px] lg:min-h-[900px] xl:min-h-[940px]"
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 z-0 h-[7px] bg-[#efbf46]" aria-hidden="true" />

        {/* Product photography is deliberately positioned separately from the typography,
            so the experience remains responsive and accessible. */}
        <div className="pointer-events-none absolute -bottom-[125px] left-1/2 z-[5] w-[min(83vw,520px)] -translate-x-1/2 -rotate-[9deg] sm:-bottom-[145px] sm:w-[min(63vw,600px)] lg:bottom-[-140px] lg:left-[-80px] lg:w-[min(38vw,600px)] lg:translate-x-0 lg:-rotate-[14deg]">
          <Image
            src={`${process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || ""}/art/record.webp`}
            alt="Sauce RECORD — red squeeze bottle product artwork"
            width={600}
            height={800}
            priority
            sizes="(max-width: 640px) 83vw, (max-width: 1024px) 63vw, 38vw"
            className="h-auto w-full"
          />
        </div>
        <div className="pointer-events-none absolute -bottom-[120px] right-[-5%] z-[5] hidden w-[min(35vw,570px)] rotate-[13deg] lg:block">
          <Image
            src={`${process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || ""}/art/polish.webp`}
            alt="Sauce POLISH — orange squeeze bottle product artwork"
            width={600}
            height={800}
            priority
            sizes="35vw"
            className="h-auto w-full"
          />
        </div>

        <div className="relative z-10 mx-auto flex max-w-[1720px] flex-col items-center px-4 pt-[63px] text-center sm:px-8 sm:pt-[80px] lg:pt-[55px] xl:px-12">
          <p className="font-display text-[20px] font-black uppercase tracking-[.15em] text-sauce-red-deep sm:text-[25px]">
            The next chapter of product demos
          </p>

          <h1
            id="hero-heading"
            className="relative mt-6 w-full font-display text-[clamp(5.2rem,15.5vw,17rem)] font-black uppercase leading-[.74] tracking-[-.042em] text-sauce-cream sm:mt-7 lg:mt-8 lg:text-[clamp(9.5rem,13.5vw,16.5rem)]"
          >
            <span className="block lg:hidden">MAKE</span>
            <span className="mt-[.045em] block lg:hidden">SOFTWARE</span>
            <span className="mt-[.045em] block lg:hidden">WORTH</span>
            <span className="mt-[.045em] block lg:hidden">WATCHING.</span>
            <span className="hidden lg:block">MAKE SOFTWARE</span>
            <span className="mt-[.065em] hidden lg:block">WORTH WATCHING.</span>
          </h1>

          <div
            id="waitlist"
            className="relative z-30 mt-8 flex w-full max-w-[600px] scroll-mt-24 flex-col items-center sm:mt-10 lg:mt-9"
          >
            <p className="max-w-[450px] text-center font-body text-[17px] font-bold leading-[1.38] tracking-[-.025em] text-sauce-red-deep sm:text-[21px]">
              Real software. AI-directed storytelling. A finished demo that does your product justice.
            </p>
            <div className="mt-5 w-full">
              <WaitlistForm source="hero" />
            </div>
          </div>
        </div>

        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-[6] h-[24px] bg-sauce-red" aria-hidden="true" />
      </section>
    </main>
  );
}

function FilmShowcase() {
  return (
    <section id="film" aria-labelledby="film-heading" className="bg-[#151519] px-5 py-20 text-[#f4efe5] sm:px-10 sm:py-28 xl:px-16">
      <div className="mx-auto max-w-[1440px]">
        <div className="mb-9 flex flex-col justify-between gap-7 md:mb-12 md:flex-row md:items-end">
          <div className="max-w-[760px]">
            <p className="mb-5 font-body text-[13px] font-semibold text-[#d69c75]">A screen recording is not a demo.</p>
            <h2 id="film-heading" className="font-body text-[clamp(2.35rem,5.6vw,5.8rem)] font-semibold leading-[1.02] tracking-[-.068em]">
              The difference is <span className="font-serif italic font-normal text-[#f0b18a]">in the details.</span>
            </h2>
          </div>
          <p className="max-w-[340px] font-body text-[15px] leading-[1.7] text-[#aaa5a7]">
            Real interface. Deliberate camera movement. A little depth. And tactile sound placed on the exact frame.
          </p>
        </div>
        <div className="rounded-[16px] border border-white/15 bg-[#202127] p-[7px] shadow-[0_40px_90px_-40px_rgba(0,0,0,0.8),0_80px_160px_-60px_rgba(0,0,0,0.5)] sm:p-[11px]">
          <div className="relative aspect-video overflow-hidden rounded-[9px] bg-[#090a0f]">
            <video
              aria-label="AFTER: A demo with Sauce — verified 3D Launch film"
              src="https://devmcp.davemafy.xyz/sauce-motion-phase2/master-1080p60.mp4"
              poster="https://devmcp.davemafy.xyz/sauce-motion-phase2/poster.jpg"
              className="h-full w-full object-contain"
              autoPlay
              muted
              loop
              playsInline
              controls
              preload="metadata"
            />
          </div>
        </div>
        <div className="mt-7 flex flex-col justify-between gap-6 sm:flex-row sm:items-center">
          <div>
            <p className="font-body text-[12px] font-semibold tracking-[.04em] text-[#dca888]">AFTER: A demo with Sauce</p>
            <p className="mt-2 font-body text-[14px] leading-relaxed text-[#a9a5a8]">
              3D Launch preset · 1080p / 60fps · sound on playback. This is a real rendered interaction, not a mockup.
            </p>
          </div>
          <Link href="/studio" className="inline-flex min-h-[46px] flex-none items-center justify-center gap-3 rounded-[8px] bg-[#ecc1a1] px-6 font-body text-[13px] font-bold text-[#2c201d] transition-colors hover:bg-[#ffddc5] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#ecc1a1]">
            Open Sauce Studio <ArrowUpRightIcon size={16} weight="bold" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="bg-sauce-red px-5 py-7 text-sauce-cream sm:px-10 sm:py-9 xl:px-16">
      <div className="mx-auto flex max-w-[1620px] flex-col gap-8 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Wordmark />
          <p className="mt-2 max-w-[330px] font-body text-[13px] font-medium leading-[1.5] text-sauce-cream/85">
            Make software worth watching.
            <span className="block">Built for the people who build software.</span>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-7 gap-y-3 text-[13px] font-semibold">
          <a href="#waitlist" className="underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-3">Early access</a>
          <a href={github} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-3">
            <GithubLogoIcon size={17} weight="fill" aria-hidden="true" /> GitHub <ArrowUpRightIcon size={14} weight="bold" aria-hidden="true" />
          </a>
          <span className="text-sauce-cream/75">© {new Date().getFullYear()} Sauce</span>
        </div>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <div className="min-w-0 overflow-x-clip">
      <Header />
      <Hero />
      <FilmShowcase />
      <Footer />
    </div>
  );
}