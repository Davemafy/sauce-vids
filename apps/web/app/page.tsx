import Image from 'next/image';
import Link from 'next/link';
import {
  ArrowRightIcon, ArrowUpRightIcon, CheckCircleIcon,
  GithubLogoIcon, PlayIcon, FilmStripIcon, GitPullRequestIcon,
} from '@phosphor-icons/react/ssr';
import { WaitlistForm } from '../components/waitlist-form';
import { TryUrlForm } from '../components/try-url-form';
import s from './landing.module.css';

const github = 'https://github.com/Davemafy/sauce-vids';
const film = 'https://devmcp.davemafy.xyz/sauce-motion-phase2/master-1080p60.mp4';
const poster = 'https://devmcp.davemafy.xyz/sauce-motion-phase2/poster.jpg';

function Wordmark({ light = false }: { light?: boolean }) {
  return <Link href="/" className={s.wordmark} data-light={light} aria-label="Sauce home">Sauce<span className={s.wordmarkTM}>™</span></Link>;
}

function Header() {
  return <header className={s.header}>
    <div className={s.headerInner}>
      <Wordmark light />
      <nav className={s.nav} aria-label="Main navigation">
        <a href="#watch">Watch the work</a>
        <a href="#how">How it works</a>
        <a href="#auto-pr">Auto PR</a>
      </nav>
      <Link href="/studio" className={s.navCta}>Open Studio <ArrowUpRightIcon size={17} weight="bold" aria-hidden="true"/></Link>
    </div>
  </header>;
}

function Hero() {
  return <section id="top" className={s.hero} aria-labelledby="main-title">
    <div className={s.heroGrid}>
      <div className={s.heroCopy}>
        <div className={s.eyebrow}><span className={s.eyebrowDot}/> PRODUCT FILMS, FRESHLY MADE <span>001 — SAUCE STUDIO</span></div>
        <h1 id="main-title" className={s.heroTitle}>Make software <em>worth</em> watching.</h1>
        <p className={s.heroDesc}>You built something good. We make sure people actually see it. Sauce turns real product interactions into videos with a little more taste.</p>
        <TryUrlForm/>
        <a href="#watch" className={s.heroSee}>Or watch a real Sauce render <ArrowRightIcon weight="bold" size={17} aria-hidden="true"/></a>
      </div>
      <div className={s.heroVisual} aria-label="Sauce squeeze bottles in a studio campaign">
        <div className={s.heroBadge}><span>100%</span><small>REAL PRODUCT<br/>ON SCREEN</small></div>
        <div className={s.heroStamp} aria-hidden="true">THE GOOD STUFF<br/>IS IN THE DETAILS</div>
        <Image className={s.bottleRecord}
          src={`${process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || ''}/art/record.webp`}
          width={600} height={800} alt="Red Sauce Record squeeze bottle"
          priority sizes="(max-width: 750px) 58vw, 34vw"/>
        <Image className={s.bottlePolish}
          src={`${process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || ''}/art/polish.webp`}
          width={600} height={800} alt="Orange Sauce Polish squeeze bottle"
          priority sizes="(max-width: 750px) 44vw, 27vw"/>
        <p className={s.heroVisualFoot}>01 / RAW INPUT <span>→</span> 02 / FILM WORTH SHARING</p>
      </div>
    </div>
  </section>;
}

function RunningBand() {
  return <div className={s.band} aria-hidden="true">
    <div>REAL INTERACTIONS <span>✳</span> GOOD CAMERA WORK <span>✳</span> SHARP FRAMES <span>✳</span> NOT ANOTHER SCREEN RECORDING <span>✳</span> REAL INTERACTIONS <span>✳</span> GOOD CAMERA WORK <span>✳</span></div>
  </div>;
}

function FilmShowcase() {
  return <section className={s.filmSection} id="watch" aria-labelledby="watch-title">
    <div className={s.sectionTop}>
      <span className={s.lightKicker}>01 / SEE THE DIFFERENCE</span>
      <span className={s.edition}>SAUCE CUTS — VOL. 001</span>
    </div>
    <div className={s.filmIntro}>
      <h2 id="watch-title">Nobody came to watch<br/><em>your cursor.</em></h2>
      <p>They came to see what your software does. We film real interactions, not imaginary results.</p>
    </div>
    <div className={s.filmStage}>
      <div className={s.filmChrome}><span className={s.chromeDots}><i/><i/><i/></span><span>SAUCE STUDIO / PRESENTATION 01</span><span>1080P · 60 FPS</span></div>
      <video src={film} poster={poster} className={s.filmVideo}
        autoPlay loop muted playsInline controls preload="metadata"
        aria-label="Previously rendered Sauce product demonstration video"/>
    </div>
    <div className={s.filmMeta}>
      <div><span className={s.filmTag}>TECHNIQUE STUDY · 3 SEC</span><strong>An early real Sauce capture.</strong><p>This short clip proves a specific camera technique. It is not an approved autonomous product film. Public URL capture remains in private pilot.</p></div>
      <Link className={s.filmLink} href="/studio">Try your own link <ArrowUpRightIcon weight="bold" aria-hidden="true"/></Link>
    </div>
  </section>;
}

const steps = [
 {number:'01',eyebrow:'YOU',title:'Drop the link.',desc:'Start with a public product URL. Tell Sauce what matters—or let the director explore.',foot:'NO RECORDING SOFTWARE TO INSTALL'},
 {number:'02',eyebrow:'THE DIRECTOR',title:'Find the good bit.',desc:'Sauce explores visible product behavior and checks for a real interaction worth showing.',foot:'REAL BROWSER. REAL EVIDENCE.'},
 {number:'03',eyebrow:'THE EDIT',title:'Make it a film.',desc:'Camera, cursor, timing, composition and export belong to the production system—not your to-do list.',foot:'REVIEW BEFORE YOU SHARE'},
];
function How() {
  return <section className={s.how} id="how" aria-labelledby="how-title">
    <div className={s.howHeading}>
      <span className={s.darkKicker}>02 / THE METHOD</span>
      <h2 id="how-title">You make the product.<br/><em>We'll handle the close-up.</em></h2>
    </div>
    <div className={s.processGrid}>
      {steps.map((step,i)=><article key={step.number} className={s.processCard}>
        <div className={s.processTop}><span>{step.number}</span><span>{step.eyebrow}</span></div>
        <div className={s.processGraphic} data-step={i} aria-hidden="true">
          {i===0?<><span className={s.webBar}/><span className={s.webLines}/><span className={s.webArrow}>↗</span></>:
          i===1?<><span className={s.focusFrame}/><span className={s.focusDot}/><span className={s.focusCaption}>FOCUS / 01</span></>:
          <><span className={s.filmFrame}/><span className={s.filmPlay}><PlayIcon weight="fill" size={22}/></span><span className={s.filmRuler}/></>}
        </div>
        <h3>{step.title}</h3><p>{step.desc}</p><span className={s.processFoot}>{step.foot}</span>
      </article>)}
    </div>
  </section>;
}

function AutoPr() {
  return <section className={s.prSection} id="auto-pr" aria-labelledby="pr-title">
    <div className={s.prCopy}>
      <span className={s.darkKicker}>03 / THE NEXT COURSE <span className={s.inDevelopment}>IN DEVELOPMENT</span></span>
      <h2 id="pr-title">Nobody wants to check out <em>your branch.</em></h2>
      <p>A pull request should show what changed. We're developing a way for Sauce to turn verified UI changes into short, watchable demos that live alongside your code.</p>
      <a href="#waitlist" className={s.prLink}>Get on the early list <ArrowUpRightIcon size={19} weight="bold" aria-hidden="true"/></a>
    </div>
    <div className={s.prArtwork}>
      <div className={s.prWindow} aria-label="Illustration of the planned Auto PR review experience">
        <div className={s.prWindowTop}><GitPullRequestIcon size={22} weight="bold" aria-hidden="true"/><span>Pull request #124</span><span className={s.prReviewTag}>PREVIEW CONCEPT</span></div>
        <div className={s.prWindowBody}>
          <p>New workspace invitations</p>
          <div className={s.prCode}><span>− Manual walkthrough for reviewers</span><span>+ A verified video of the actual change</span></div>
          <div className={s.prFilmBlock}><FilmStripIcon size={32} weight="thin" aria-hidden="true"/><div><strong>Feature walkthrough</strong><span>Illustrative Auto PR flow</span></div><PlayIcon size={22} weight="fill" aria-hidden="true"/></div>
          <div className={s.prChecks}><CheckCircleIcon weight="fill" size={15} aria-hidden="true"/> Tied to the reviewed commit, not a stale recording</div>
        </div>
      </div>
      <div className={s.prSideNote}>FUTURE FEATURE — NOT AVAILABLE IN THE PRIVATE PILOT</div>
    </div>
  </section>;
}

function Waitlist() {
  return <section id="waitlist" className={s.waitlist} aria-labelledby="wait-title">
    <div className={s.waitText}>
      <span>04 / GET FIRST DIBS</span>
      <h2 id="wait-title">Something good<br/>is <em>cooking.</em></h2>
      <p>We're opening Sauce to a small group of builders first. Leave your email and we'll let you know when there's room.</p>
    </div>
    <div className={s.waitBox}>
      <div className={s.waitBoxTitle}>YOUR SEAT AT THE TABLE</div>
      <WaitlistForm source="footer"/>
      <div className={s.waitSmall}>No fabricated demos. No spam. Just the real thing when it's ready.</div>
    </div>
  </section>;
}

function Footer(){
  return <footer className={s.footer}>
    <div className={s.footerTop}><Wordmark light/><p>For the things you've worked too hard on<br/>to show in a bad screen recording.</p></div>
    <div className={s.footerBottom}>
      <span>© {new Date().getFullYear()} Sauce. Product films, with taste.</span>
      <div><Link href="/studio">Studio <ArrowUpRightIcon size={14}/></Link><a href={github} target="_blank" rel="noopener noreferrer"><GithubLogoIcon weight="fill" size={17}/> GitHub</a><a href="#top">Back to top ↑</a></div>
    </div>
  </footer>;
}

export default function Home() {
 return <div className={s.site}><Header/><main><Hero/><RunningBand/><FilmShowcase/><How/><AutoPr/><Waitlist/></main><Footer/></div>;
}
