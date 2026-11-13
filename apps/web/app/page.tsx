import Image from 'next/image';
import {
  ArrowDownIcon,
  ArrowRightIcon,
  ArrowUpRightIcon,
  GithubLogoIcon,
  PlayIcon,
  VideoCameraIcon,
} from '@phosphor-icons/react/ssr';
import { WaitlistForm } from '../components/waitlist-form';

const github = 'https://github.com/Davemafy/sauce-vids';

function Wordmark({ light = false }: { light?: boolean }) {
  return (
    <a href="#top" aria-label="Sauce home" className={`inline-flex items-start font-script text-[43px] leading-none tracking-[-.045em] md:text-[48px] ${light ? 'text-sauce-cream' : 'text-sauce-red'}`}>
      Sauce<span className="relative top-[7px] ml-[3px] font-body text-[10px] font-extrabold tracking-normal">™</span>
    </a>
  );
}

function TopRibbon() {
  return (
    <div aria-hidden="true" className="overflow-hidden bg-[#f8bf38] text-sauce-red-deep">
      <div className="flex min-w-max items-center justify-around gap-7 px-4 py-[6px] font-display text-[17px] font-black uppercase leading-none tracking-[.035em] sm:gap-11 sm:text-[18px]">
        {['CAPTURE', 'DIRECT', 'PRODUCE', 'SHARE', 'CAPTURE', 'DIRECT', 'PRODUCE', 'SHARE', 'CAPTURE', 'DIRECT'].map((word, i) => (
          <span key={i} className="inline-flex items-center gap-6 sm:gap-10">
            {word} <ArrowRightIcon size={15} weight="bold" />
          </span>
        ))}
      </div>
    </div>
  );
}

function Header() {
  return (
    <header className="relative z-50 bg-sauce-red text-sauce-cream">
      <div className="mx-auto flex h-[74px] max-w-[1650px] items-center justify-between gap-5 px-5 sm:px-10 xl:px-14">
        <Wordmark light />
        <nav aria-label="Main navigation" className="hidden items-center gap-8 font-display text-[24px] font-extrabold uppercase leading-none tracking-[.012em] md:flex lg:gap-14">
          <a className="transition-colors hover:text-[#f8bf38] focus-visible:outline-2 focus-visible:outline-offset-4" href="#about">Product</a>
          <a className="transition-colors hover:text-[#f8bf38] focus-visible:outline-2 focus-visible:outline-offset-4" href="#example">Examples</a>
          <a className="transition-colors hover:text-[#f8bf38] focus-visible:outline-2 focus-visible:outline-offset-4" href="#how">How it works</a>
        </nav>
        <a
          href="#waitlist"
          className="hidden min-h-[45px] items-center justify-center gap-3 rounded-full bg-sauce-cream px-7 font-display text-[22px] font-black uppercase text-sauce-red transition-transform hover:-translate-y-[2px] focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-sauce-cream sm:inline-flex"
        >
          Join waitlist <ArrowRightIcon size={18} weight="bold" aria-hidden="true" />
        </a>
        <details className="group relative sm:hidden">
          <summary className="flex min-h-[44px] cursor-pointer list-none items-center justify-center rounded-full border border-sauce-cream/40 px-4 font-display text-[21px] font-extrabold uppercase marker:hidden focus-visible:outline-3 focus-visible:outline-offset-3 [&::-webkit-details-marker]:hidden">
            Menu
          </summary>
          <nav aria-label="Mobile navigation" className="absolute right-0 top-[57px] flex w-[220px] flex-col gap-1 rounded-[18px] border border-sauce-cream/30 bg-sauce-red p-3 shadow-2xl">
            <a className="rounded-lg px-3 py-2 text-lg font-bold hover:bg-white/10" href="#about">Product</a>
            <a className="rounded-lg px-3 py-2 text-lg font-bold hover:bg-white/10" href="#example">Examples</a>
            <a className="rounded-lg px-3 py-2 text-lg font-bold hover:bg-white/10" href="#how">How it works</a>
            <a className="rounded-lg bg-sauce-cream px-3 py-2 text-lg font-bold text-sauce-red" href="#waitlist">Join waitlist</a>
          </nav>
        </details>
      </div>
    </header>
  );
}

function ConceptFrame({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={`relative overflow-hidden rounded-[17px] border-[5px] border-[#f9ece1] bg-[#241628] shadow-[0_16px_0_#73140d2b,0_24px_35px_#66120b30] ${compact ? 'w-full' : 'w-full max-w-[520px]'}`}
      aria-label="Illustrative concept of a Sauce product-demo frame"
      role="img"
    >
      <div className="flex h-7 items-center justify-between bg-[#fff4ec] px-3">
        <div className="flex gap-[5px]">
          <span className="size-2 rounded-full bg-[#ed5141]" />
          <span className="size-2 rounded-full bg-[#efb73d]" />
          <span className="size-2 rounded-full bg-[#43af78]" />
        </div>
        <span className="text-[10px] font-bold tracking-wide text-[#73433f]">ILLUSTRATIVE FRAME</span>
        <span className="size-2" />
      </div>
      <div className="flex aspect-[2/1] min-h-[140px] bg-[#f7e7e7]">
        <div className="flex w-[28%] shrink-0 flex-col gap-3 border-r border-[#e2cbcb] bg-[#fcecec] p-[5%] text-[9px] text-[#59404c]">
          <span className="mb-2 font-extrabold text-[#402338]">◉ Acme</span>
          <span>⌂ &nbsp;Home</span>
          <span className="rounded bg-[#ebd4dc] p-1 font-bold">▣ &nbsp;Projects</span>
          <span>▤ &nbsp;Team</span>
        </div>
        <div className="w-full min-w-0 p-[5%]">
          <p className="mb-[7%] text-[clamp(13px,2vw,21px)] font-extrabold tracking-tight text-[#2c2026]">Projects</p>
          {['Website redesign', 'Mobile app', 'Release notes'].map((name, i) => (
            <div key={name} className={`mb-[6%] flex items-center gap-3 rounded-md px-2 py-1.5 ${i === 1 ? 'bg-[#f7c7d0]' : ''}`}>
              <div className="grid size-6 shrink-0 place-items-center rounded bg-[#4e89d3] text-xs font-bold text-white">▣</div>
              <div className="min-w-0">
                <p className="truncate text-[clamp(8px,1.2vw,12px)] font-bold text-[#2c2026]">{name}</p>
                <p className="truncate text-[clamp(6px,.8vw,9px)] text-[#8e7884]">Updated recently</p>
              </div>
              {i === 1 && <div className="ml-auto flex size-6 shrink-0 items-center justify-center rounded-full border border-[#b81531]/30 bg-[#d8374d] text-white"><span className="text-[11px]">⌖</span></div>}
            </div>
          ))}
        </div>
      </div>
      <div className="flex h-8 items-center gap-3 bg-[#281e2a] px-3 text-sauce-cream">
        <PlayIcon size={12} weight="fill" aria-hidden="true" />
        <span className="font-body text-[10px] tabular-nums">0:04 / 0:28</span>
        <span className="h-[3px] flex-1 rounded-full bg-white/30"><span className="block h-full w-1/3 rounded-full bg-[#f26a71]" /></span>
        <span className="font-body text-[9px] font-bold">HD</span>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <section className="relative isolate overflow-hidden bg-sauce-orange" aria-labelledby="hero-heading">
      <div className="pointer-events-none absolute -bottom-1 left-0 z-30 w-[39%] max-w-[580px] -translate-x-[34%] sm:w-[33%] sm:-translate-x-[20%] xl:-translate-x-[22%]">
        <Image
          src="/art/record.webp"
          width={677}
          height={900}
          alt="Photorealistic red Sauce RECORD squeeze bottle held in a hand"
          priority
          sizes="(max-width: 640px) 50vw, 33vw"
          className="h-auto w-full"
        />
      </div>
      <div className="pointer-events-none absolute -bottom-5 right-0 z-30 w-[38%] max-w-[520px] translate-x-[29%] sm:w-[29%] sm:translate-x-[13%] xl:translate-x-[18%]">
        <Image
          src="/art/polish.webp"
          width={677}
          height={900}
          alt="Photorealistic orange Sauce POLISH squeeze bottle held in a hand"
          priority
          sizes="(max-width: 640px) 50vw, 30vw"
          className="h-auto w-full"
        />
      </div>
      <div className="relative mx-auto min-h-[690px] max-w-[1650px] px-4 pt-[45px] pb-[160px] sm:min-h-[750px] sm:px-8 md:min-h-[715px] md:pt-12 md:pb-[95px] xl:px-12">
        <div className="relative z-10 md:ml-[24%] lg:ml-[26%]">
          <p className="mb-2 hidden font-display text-[23px] font-black uppercase tracking-[.18em] text-sauce-red-deep md:block">AI-directed demos, without the editing.</p>
          <h1
            id="hero-heading"
            className="max-w-full text-center font-display text-[clamp(4.2rem,18.6vw,7.5rem)] font-black uppercase leading-[.77] tracking-[-.033em] text-sauce-cream sm:text-[clamp(6.5rem,15.5vw,12rem)] md:text-left md:text-[clamp(6.5rem,10.2vw,11.5rem)]"
          >
            <span className="block md:hidden">MAKE</span>
            <span className="hidden md:block">MAKE SOFTWARE</span>
            <span className="block md:hidden">SOFTWARE</span>
            <span className="mt-[.07em] block">WORTH</span>
            <span className="mt-[.07em] block">WATCHING.</span>
          </h1>
        </div>
        <div id="waitlist" className="relative z-40 mx-auto mt-9 flex w-full max-w-[600px] scroll-mt-28 flex-col items-center md:ml-[26%] md:mt-9 md:items-start lg:ml-[29%]">
          <p className="mb-5 max-w-[480px] text-center text-[17px] font-bold leading-[1.3] tracking-[-.025em] text-sauce-red-deep sm:text-[22px] md:text-left">
            Turn real product interactions into polished demos for launches, changelogs and pull requests.
          </p>
          <WaitlistForm />
        </div>
        <p className="absolute right-5 bottom-7 left-5 z-40 mx-auto text-center font-display text-[16px] font-extrabold uppercase tracking-[.1em] text-sauce-red-deep sm:text-[19px] md:left-auto md:right-[32%]">
          Your product. Directed beautifully.
        </p>
      </div>
    </section>
  );
}

function About() {
  return (
    <section id="about" className="scroll-mt-10 bg-sauce-cream px-5 py-20 sm:px-10 sm:py-28">
      <div className="mx-auto grid max-w-[1320px] gap-10 lg:grid-cols-[1fr_.95fr] lg:items-end lg:gap-20">
        <div>
          <p className="mb-4 font-display text-[20px] font-black uppercase tracking-[.16em] text-sauce-red">01 / What Sauce is</p>
          <h2 className="max-w-[800px] font-display text-[clamp(4.5rem,9vw,10rem)] font-black uppercase leading-[.79] tracking-[-.025em] text-sauce-red">
            NOT ANOTHER<br />TIMELINE.
          </h2>
        </div>
        <div className="max-w-[570px] pb-2">
          <p className="text-[clamp(1.25rem,2vw,1.9rem)] font-semibold leading-[1.3] tracking-[-.04em] text-sauce-ink">
            You tell the agent what to show. Sauce captures real software, composes the story and renders the film.
          </p>
          <p className="mt-5 max-w-[470px] text-base leading-[1.6] text-sauce-ink/75">
            No dragging clips around. No pretending generated screens are your product. A working capture-to-film pipeline, built for software that ships.
          </p>
          <a href={github} target="_blank" rel="noopener noreferrer" className="mt-8 inline-flex items-center gap-2 border-b-2 border-sauce-red pb-1 font-bold text-sauce-red hover:gap-3 focus-visible:outline-3 focus-visible:outline-offset-4">
            Explore the Hermes plugin <ArrowUpRightIcon size={20} weight="bold" aria-hidden="true" />
          </a>
        </div>
      </div>
    </section>
  );
}

function Example() {
  return (
    <section id="example" className="scroll-mt-4 bg-[#64227b] px-5 py-20 text-sauce-cream sm:px-10 sm:py-24">
      <div className="mx-auto grid max-w-[1320px] items-center gap-12 lg:grid-cols-[.65fr_1fr] lg:gap-20">
        <div>
          <p className="font-display text-[20px] font-black uppercase tracking-[.18em] text-[#f6c052]">02 / The result</p>
          <h2 className="mt-5 font-display text-[clamp(5rem,10vw,10rem)] font-black uppercase leading-[.78] tracking-[-.025em]">
            SHOW.<br />DON'T<br />TELL.
          </h2>
          <p className="mt-8 max-w-[420px] text-[18px] leading-[1.5] text-sauce-cream/90">
            One clear product story instead of another screen recording nobody finishes.
          </p>
          <p className="mt-5 text-[13px] font-semibold uppercase tracking-[.07em] text-sauce-cream/65">
            Product preview is illustrative. Verified sample footage is being prepared.
          </p>
        </div>
        <div className="w-full">
          <ConceptFrame compact />
          <div className="mt-5 flex items-center justify-between gap-5">
            <span className="font-display text-[22px] font-extrabold uppercase">Illustrative demo frame</span>
            <a href={github} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 text-sm font-bold underline decoration-2 underline-offset-4">
              Source on GitHub <ArrowUpRightIcon weight="bold" size={16} aria-hidden="true" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function How() {
  return (
    <section id="how" className="scroll-mt-4 bg-[#f7c549] px-5 py-20 sm:px-10 sm:py-28">
      <div className="mx-auto max-w-[1320px]">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="font-display text-[20px] font-black uppercase tracking-[.16em] text-sauce-red">03 / How it works</p>
            <h2 className="mt-3 font-display text-[clamp(4.7rem,10.5vw,11rem)] font-black uppercase leading-[.78] tracking-[-.025em] text-sauce-red">THREE STEPS.<br />ONE FILM.</h2>
          </div>
          <VideoCameraIcon size={64} weight="fill" className="mb-3 text-sauce-red" aria-hidden="true" />
        </div>
        <div className="mt-14 grid border-t-2 border-sauce-red/60 md:grid-cols-3">
          {[
            ['01', 'DIRECT', 'Tell your agent what the product demo should communicate.'],
            ['02', 'CAPTURE', 'Sauce records real browser interactions and stores evidence.'],
            ['03', 'PRODUCE', 'The composition pipeline renders a shareable video.'],
          ].map(([number, label, text]) => (
            <div key={number} className="border-b-2 border-sauce-red/60 px-1 py-8 md:border-r-2 md:px-7 md:last:border-r-0">
              <span className="font-body text-sm font-bold text-sauce-red">{number}</span>
              <h3 className="mt-4 font-display text-[clamp(3.6rem,6vw,6.2rem)] font-black uppercase leading-[.8] text-sauce-red">{label}</h3>
              <p className="mt-5 max-w-[310px] text-[17px] font-medium leading-[1.45] text-sauce-ink">{text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="bg-sauce-red px-5 pt-20 pb-9 text-sauce-cream sm:px-10 sm:pt-24">
      <div className="mx-auto max-w-[1320px]">
        <p className="font-display text-[20px] font-black uppercase tracking-[.15em] text-[#ffd15d]">Get early access</p>
        <h2 className="mt-4 font-display text-[clamp(5rem,10.5vw,11rem)] font-black uppercase leading-[.76] tracking-[-.027em]">GOOD DEMOS.<br />NO FUSS.</h2>
        <p className="mt-6 max-w-[570px] text-[20px] font-medium leading-[1.45] text-sauce-cream/90">
          Sauce is being built in public. Join the list and get the first look.
        </p>
        <div className="mt-8">
          <WaitlistForm source="footer" theme="dark" />
        </div>
        <div className="mt-24 flex flex-wrap items-end justify-between gap-8 border-t border-sauce-cream/40 pt-6">
          <Wordmark light />
          <div className="flex flex-wrap items-center gap-7 text-[13px] font-semibold">
            <a className="underline-offset-4 hover:underline" href="#top">Back to top</a>
            <a className="inline-flex items-center gap-2 underline-offset-4 hover:underline" href={github} target="_blank" rel="noopener noreferrer">
              <GithubLogoIcon size={18} weight="fill" aria-hidden="true" /> GitHub
            </a>
            <span>© {new Date().getFullYear()} Sauce</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <div id="top" className="min-w-0 overflow-x-clip">
      <TopRibbon />
      <Header />
      <main>
        <Hero />
        <About />
        <Example />
        <How />
      </main>
      <Footer />
    </div>
  );
}
