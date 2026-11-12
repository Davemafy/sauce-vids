import { ArrowRight, ArrowUpRight, Check, CirclePlay, Code2, Film, Focus, Github, MousePointer2, Scissors, ShieldCheck, Sparkles, WandSparkles, Zap } from 'lucide-react';

const repo = 'https://github.com/Davemafy/sauce-vids';

function Bottle() {
  return (
    <svg className="bottle-illustration" viewBox="0 0 510 595" aria-label="Illustration of an upside-down red Sauce squeeze bottle with its cap open" role="img">
      <defs>
        <linearGradient id="bottle-body" x1="0" y1=".5" x2="1" y2=".8">
          <stop offset="0%" stopColor="#680d0b" />
          <stop offset="12%" stopColor="#b91510" />
          <stop offset="31%" stopColor="#f74d27" />
          <stop offset="52%" stopColor="#bd120d" />
          <stop offset="76%" stopColor="#940908" />
          <stop offset="95%" stopColor="#e53b21" />
        </linearGradient>
        <linearGradient id="bottle-label" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#fff9e9" />
          <stop offset="70%" stopColor="#f7e8cf" />
          <stop offset="100%" stopColor="#e9d3b4" />
        </linearGradient>
        <linearGradient id="cap" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#e5cfaf"/>
          <stop offset=".27" stopColor="#fff8e9"/>
          <stop offset=".7" stopColor="#efddc2"/>
          <stop offset="1" stopColor="#c8a684"/>
        </linearGradient>
        <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#fff" stopOpacity=".7"/>
          <stop offset="1" stopColor="#fff" stopOpacity="0"/>
        </linearGradient>
        <pattern id="cap-threads" patternUnits="userSpaceOnUse" width="9" height="12">
          <path d="M4 0V12" stroke="#a98a6e" strokeWidth="2" opacity=".28"/>
        </pattern>
        <filter id="bottle-shadow" x="-30%" y="-20%" width="160%" height="150%">
          <feDropShadow dx="-11" dy="17" stdDeviation="12" floodColor="#772b18" floodOpacity=".22" />
        </filter>
      </defs>
      <g transform="rotate(23 275 225)" filter="url(#bottle-shadow)">
        <path d="M143-74C160-102 350-97 373-67C385-42 387 13 376 63L373 235C371 274 334 296 313 322L307 351L212 351L206 325C189 303 148 280 142 239L132 42C127 3 131-47 143-74Z" fill="url(#bottle-body)" stroke="#7f100b" strokeWidth="2"/>
        <path d="M161-53C166-68 179-72 196-71L192 222C192 251 205 275 219 291C189 268 162 260 158 224Z" fill="url(#shine)" opacity=".72"/>
        <path d="M353-60C360-41 357 22 354 65L351 225C351 248 341 273 328 284" fill="none" stroke="#fff0d6" strokeWidth="10" strokeLinecap="round" opacity=".18"/>
        <path d="M285-66C320-61 335-49 337-21" stroke="#ffd9b1" strokeWidth="12" opacity=".18" strokeLinecap="round" fill="none"/>
        <rect x="162" y="36" width="193" height="196" rx="33" fill="url(#bottle-label)" stroke="#ffecd4" strokeWidth="5"/>
        <rect x="170" y="44" width="177" height="180" rx="27" fill="none" stroke="#a52a20" strokeWidth="3"/>
        <text x="257" y="113" textAnchor="middle" fontSize="55" fontWeight="800" fontFamily="Georgia,serif" fontStyle="italic" fill="#a71913">Sauce</text>
        <path d="M203 128Q253 149 315 125" stroke="#ad1b16" strokeWidth="4" fill="none" strokeLinecap="round"/>
        <text x="257" y="163" textAnchor="middle" fontSize="14" fontWeight="800" letterSpacing="1.4" fontFamily="Arial,sans-serif" fill="#4b231a">TURN RECORDINGS</text>
        <text x="257" y="182" textAnchor="middle" fontSize="14" fontWeight="800" letterSpacing="1.4" fontFamily="Arial,sans-serif" fill="#4b231a">INTO DEMOS</text>
        <path d="M245 204C251 191 268 195 268 204C268 214 253 217 245 204Z" fill="#bc2115"/>
        <path d="M250 197L255 193L260 198" stroke="#557c37" strokeWidth="3" fill="none" strokeLinecap="round"/>
        <path d="M210 345C215 359 301 364 311 346L317 369C315 385 207 389 203 369Z" fill="#e4ccb0"/>
        <rect x="188" y="364" width="141" height="62" rx="17" fill="url(#cap)" stroke="#e3d1bc" strokeWidth="2"/>
        <rect x="193" y="370" width="132" height="50" rx="12" fill="url(#cap-threads)"/>
        <path d="M198 370L320 370M200 417L318 417" stroke="#fff9eb" strokeWidth="4" opacity=".85"/>
        <rect x="226" y="419" width="67" height="22" rx="8" fill="#f7ebd8" stroke="#bda48b" strokeWidth="2"/>
        <path d="M236 440Q257 461 282 440L275 467Q254 483 240 467Z" fill="#e6ceb3" stroke="#fdf7ea" strokeWidth="3"/>
        <ellipse cx="256" cy="464" rx="15" ry="8" fill="#9b1510"/>
        <path d="M193 392C169 386 156 386 138 398" fill="none" stroke="#f1dac0" strokeWidth="9" strokeLinecap="round"/>
        <path d="M135 388C109 379 70 394 66 412C65 438 111 460 141 449C159 442 159 402 135 388Z" fill="url(#cap)" stroke="#e1bfa6" strokeWidth="3"/>
        <ellipse cx="111" cy="419" rx="33" ry="20" fill="#ffedda" opacity=".42"/>
        <path d="M83 421Q102 394 136 418" fill="none" stroke="#fff9eb" strokeWidth="5" opacity=".6"/>
      </g>
    </svg>
  );
}

function SauceFrame() {
  return (
    <svg className="sauce-frame" viewBox="0 0 630 365" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="sauce-red" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ff7041" />
          <stop offset=".14" stopColor="#d72312" />
          <stop offset=".55" stopColor="#9e0c08" />
          <stop offset=".82" stopColor="#ce1c0c" />
          <stop offset="1" stopColor="#87110b" />
        </linearGradient>
      </defs>
      <path d="M47 39Q72 14 111 28Q162 10 206 24Q255 2 309 27Q349 4 399 27Q466 8 515 29Q567 15 586 43Q608 65 601 103L599 298Q596 335 563 340Q334 363 88 339Q40 342 31 302L27 100Q20 65 47 39Z"
        fill="none" stroke="#730a06" strokeOpacity=".45" strokeWidth="33" strokeLinejoin="round"/>
      <path d="M47 39Q72 14 111 28Q162 10 206 24Q255 2 309 27Q349 4 399 27Q466 8 515 29Q567 15 586 43Q608 65 601 103L599 298Q596 335 563 340Q334 363 88 339Q40 342 31 302L27 100Q20 65 47 39Z"
        fill="none" stroke="url(#sauce-red)" strokeWidth="27" strokeLinejoin="round"/>
      <path d="M45 33Q66 19 107 26Q169 9 207 21Q255 8 308 22Q360 5 405 23Q468 9 524 26Q556 17 584 42"
        fill="none" stroke="#ff8b52" strokeWidth="8" strokeLinecap="round" opacity=".77"/>
      <path d="M31 101Q33 66 43 52M599 109L597 289M74 336Q283 358 561 337"
        fill="none" stroke="#ffb080" strokeWidth="5" strokeLinecap="round" opacity=".36"/>
      <path d="M17 325Q46 349 77 344Q253 365 419 353Q532 362 600 341Q620 351 623 362L11 365Z" fill="#b71a0d" opacity=".73"/>
    </svg>
  );
}

function SauceStream() {
  return (
    <svg className="sauce-stream" viewBox="0 0 180 240" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="stream-color" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#930e08" />
          <stop offset=".36" stopColor="#ed3b1c" />
          <stop offset=".66" stopColor="#bf1009" />
          <stop offset="1" stopColor="#800d06"/>
        </linearGradient>
      </defs>
      <path d="M91-10C116 15 111 46 86 79C53 120 78 163 90 196C97 216 130 222 162 220"
            stroke="#790600" strokeWidth="41" fill="none" strokeLinecap="round"/>
      <path d="M91-10C116 15 111 46 86 79C53 120 78 163 90 196C97 216 130 222 162 220"
            stroke="url(#stream-color)" strokeWidth="34" fill="none" strokeLinecap="round"/>
      <path d="M97 1C113 43 67 80 72 119C72 140 78 157 84 174" stroke="#ff9874" strokeWidth="8" strokeLinecap="round" fill="none" opacity=".78"/>
      <circle cx="35" cy="170" r="7" fill="#cd1d10"/>
      <circle cx="11" cy="142" r="3.5" fill="#e23c23"/>
      <circle cx="156" cy="194" r="5" fill="#b71108"/>
    </svg>
  );
}

function ProductScreen({ enhanced = false }: { enhanced?: boolean }) {
  return (
    <div className={enhanced ? 'product-screen enhanced' : 'product-screen'}>
      <div className="browser-bar">
        <div className="traffic-lights"><i/><i/><i/></div>
        <span className="address-pill">acme.app / projects</span>
        <div className="browser-dots"><span/> <span/></div>
      </div>
      <div className="app-shell">
        <aside className="app-sidebar">
          <div className="app-mark"><span className="app-glyph">✳</span> acme</div>
          <div className="side-item">⌂ <span>Home</span></div>
          <div className="side-item selected">▣ <span>Projects</span></div>
          <div className="side-item">♧ <span>Team</span></div>
          <div className="side-item">⚙ <span>Settings</span></div>
        </aside>
        <div className="project-content">
          <div className="project-title">Projects</div>
          <div className="project-entry"><span className="entry-icon">▣</span><div><strong>Website redesign</strong><small>Updated 2 hours ago</small></div><b>···</b></div>
          <div className={enhanced ? 'project-entry focused' : 'project-entry'}><span className="entry-icon">▣</span><div><strong>Mobile app</strong><small>Updated yesterday</small></div><b>···</b></div>
          <div className="project-entry"><span className="entry-icon">▣</span><div><strong>Marketing site</strong><small>Updated 3 days ago</small></div><b>···</b></div>
        </div>
      </div>
      {enhanced && <div className="fake-cursor" aria-hidden="true"><MousePointer2 size={26} fill="#fff" strokeWidth={2}/><span/></div>}
      <div className="player-bar">
        <span className="play-symbol">{enhanced ? 'Ⅱ' : '▶'}</span>
        <span>{enhanced ? '0:04' : '0:00'} / 0:28</span>
        <div className="timeline"><span style={{ width: enhanced ? '33%' : '8%' }}/></div>
        <span className="speaker">◖))</span>
        <span>⛶</span>
      </div>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <span className="section-kicker">{children}</span>;
}

const features = [
  { icon: <Focus size={25} />, title: 'Show the moment', body: 'Focus on the interaction that matters.' },
  { icon: <MousePointer2 size={25} />, title: 'Lose the jitter', body: 'Give the cursor a little composure.' },
  { icon: <Film size={25} />, title: 'Mind the pacing', body: 'Get to the point. Hold the good bits.' },
  { icon: <WandSparkles size={25} />, title: 'Make it yours', body: 'Brand the film, not the software.' },
];

export default function Home() {
  return (
    <>
      <div className="page-shell">
        <header className="site-header">
          <a className="brand" href="#" aria-label="Sauce home">Sauce<sup>®</sup></a>
          <nav className="desktop-nav" aria-label="Primary navigation">
            <a href="#product">Product</a>
            <a href="#examples">Examples</a>
            <a href="#how-it-works">How it works</a>
            <a href="#getting-started">Get Sauce</a>
          </nav>
          <a className="header-button" href={repo} target="_blank" rel="noopener noreferrer">GitHub <ArrowUpRight size={17}/></a>
          <details className="mobile-menu">
            <summary aria-label="Open navigation">Menu <span>☰</span></summary>
            <nav aria-label="Mobile navigation">
              <a href="#product">Product</a>
              <a href="#examples">Examples</a>
              <a href="#how-it-works">How it works</a>
              <a href="#getting-started">Get Sauce</a>
            </nav>
          </details>
        </header>

        <main>
          <section className="hero" aria-labelledby="hero-title">
            <div className="hero-inner">
              <div className="intro">
                <div className="eyebrow"><span className="tiny-camera">▣</span> THE PRODUCT DEMO ENGINE</div>
                <h1 id="hero-title">A screen recording<br/>is not a demo<span className="period">.</span></h1>
                <div className="hand-underline" aria-hidden="true"/>
                <p>Turn real browser interactions into product videos people actually want to watch.</p>
                <div className="hero-actions">
                  <a className="button-primary" href="#getting-started">Make a demo <ArrowRight size={19}/></a>
                  <a className="button-secondary" href="#examples"><CirclePlay size={19} fill="#ac1713" stroke="#ac1713" color="#ffecdd"/> See the concept</a>
                </div>
                <p className="audience-line">For the people who make software, not slides.</p>
              </div>

              <div className="scene" id="examples" aria-label="Conceptual before and after comparison">
                <div className="bottle-wrap"><Bottle/></div>
                <div className="stream-wrap"><SauceStream/></div>
                <div className="before-wrap">
                  <div className="example-label"><span className="label-badge before-badge">BEFORE</span> Raw recording</div>
                  <ProductScreen/>
                </div>
                <div className="hand-arrow" aria-hidden="true"><svg viewBox="0 0 90 55"><path d="M5 39Q43 8 78 27M62 11L80 27L61 44" fill="none" stroke="#a8180f" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"/></svg></div>
                <div className="after-wrap">
                  <SauceFrame />
                  <div className="after-player">
                    <div className="example-label"><span className="label-badge after-badge">AFTER</span> A demo with Sauce</div>
                    <ProductScreen enhanced/>
                  </div>
                </div>
                <div className="art-disclaimer">Illustrative comparison. Real output footage coming soon.</div>
              </div>
            </div>
            <div className="countertop" aria-hidden="true"/>
          </section>

          <section className="features" id="product" aria-labelledby="features-title">
            <h2 className="visually-hidden" id="features-title">What Sauce does</h2>
            {features.map(feature => <div className="feature" key={feature.title}>
              <div className="feature-icon">{feature.icon}</div>
              <div><h3>{feature.title}</h3><p>{feature.body}</p></div>
            </div>)}
          </section>

          <section className="how-section" id="how-it-works">
            <div className="how-heading">
              <div>
                <SectionLabel>FROM CLICK TO CUT</SectionLabel>
                <h2>Good software.<br/><em>Better showmanship.</em></h2>
              </div>
              <p>Sauce records real interactions, then gives you the tools to direct how they&apos;re seen. No invented screens, no mystery footage.</p>
            </div>
            <div className="process-grid">
              <article className="process-card"><span className="process-index">01</span><div className="process-icon"><Code2 size={33}/></div><h3>Point it at your product.</h3><p>Capture a genuine browser journey with Playwright.</p></article>
              <article className="process-card"><span className="process-index">02</span><div className="process-icon"><Scissors size={33}/></div><h3>Cut the boring bits.</h3><p>Make a focused edit plan around meaningful moments.</p></article>
              <article className="process-card"><span className="process-index">03</span><div className="process-icon"><Sparkles size={33}/></div><h3>Add a little Sauce.</h3><p>Compose a polished presentation from real footage.</p></article>
              <article className="process-card"><span className="process-index">04</span><div className="process-icon"><Zap size={33}/></div><h3>Ship the film.</h3><p>Export an MP4 that shows exactly what your software does.</p></article>
            </div>
          </section>

          <section className="truth-section">
            <div className="truth-label"><ShieldCheck size={20}/> No made-up product demos.</div>
            <p>Real app. Real interactions. Sauce takes care of the presentation.</p>
          </section>

          <section className="getting-started" id="getting-started">
            <div className="getting-copy">
              <SectionLabel>STRAIGHT FROM THE SOURCE</SectionLabel>
              <h2>Ready for a taste?</h2>
              <p>Get the open-source Hermes plugin and try it on a site you&apos;re authorized to record.</p>
              <a className="button-cream" href={repo} target="_blank" rel="noopener noreferrer"><Github size={19}/> Get Sauce on GitHub <ArrowUpRight size={18}/></a>
              <div className="release-note"><Check size={16}/> Open source · MIT licensed</div>
            </div>
            <div className="code-card">
              <span className="code-caption">START HERE</span>
              <code>git clone https://github.com/Davemafy/sauce-vids.git</code>
              <span className="code-tip">The hosted editor and automatic PR demos are on our roadmap.</span>
            </div>
          </section>
        </main>
        <footer className="footer"><span className="footer-logo">Sauce<sup>®</sup></span><span>Made for software worth showing.</span><a href={repo} target="_blank" rel="noopener noreferrer">Source on GitHub ↗</a></footer>
      </div>
    </>
  );
}
