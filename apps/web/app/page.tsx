import Image from 'next/image';
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
        <a
          href="#waitlist"
          className="inline-flex min-h-[44px] items-center gap-2 rounded-full border-2 border-sauce-cream bg-sauce-cream px-4 font-display text-[19px] font-black uppercase leading-none text-sauce-red transition-colors hover:bg-[#f7cf6e] focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-sauce-cream sm:px-6 sm:text-[23px]"
        >
          Get early access
          <ArrowRightIcon size={18} weight="bold" aria-hidden="true" />
        </a>
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
            src="/art/record.webp"
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
            src="/art/polish.webp"
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
            className="relative mt-6 w-full font-display text-[clamp(5.2rem,15.5vw,17rem)] font-black uppercase leading-[.74] tracking-[-.042em] text-sauce-cream sm:mt-7 lg:mt-8 lg:text-[clamp(10rem,14vw,19rem)]"
          >
            <span className="block">MAKE</span>
            <span className="mt-[.045em] block sm:hidden">SOFTWARE</span>
            <span className="mt-[.045em] hidden sm:block">SOFTWARE</span>
            <span className="mt-[.045em] block">WORTH</span>
            <span className="mt-[.045em] block">WATCHING.</span>
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
      <Footer />
    </div>
  );
}