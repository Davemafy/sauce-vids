import React from 'react';
import {
  AbsoluteFill, Audio, Easing, Img, OffthreadVideo, Sequence,
  interpolate, staticFile, useCurrentFrame
} from 'remotion';
import type {StudioProject, Scene, CameraKeyframe, Background} from './types';

type FilmProps = {project: StudioProject};
const ease = Easing.inOut(Easing.cubic);

const clamp = (n: number, lo: number, hi: number) =>
  Math.max(lo, Math.min(hi, n));

const valueBetween = (
  from: number, to: number, progress: number
) => from + (to - from) * ease(clamp(progress, 0, 1));

function cameraAt(frame: number, keys: CameraKeyframe[]): CameraKeyframe {
  const sorted = [...keys].sort((a, b) => a.frame - b.frame);
  if (!sorted.length) return {frame, scale: 1, focus_x: .5, focus_y: .5};
  if (frame <= sorted[0].frame) return sorted[0];
  if (frame >= sorted[sorted.length - 1].frame)
    return sorted[sorted.length - 1];
  for (let i = 1; i < sorted.length; i++) {
    const next = sorted[i], previous = sorted[i - 1];
    if (frame > next.frame) continue;
    const progress = (frame - previous.frame) / (next.frame - previous.frame);
    return {
      frame,
      scale: valueBetween(previous.scale, next.scale, progress),
      focus_x: valueBetween(previous.focus_x, next.focus_x, progress),
      focus_y: valueBetween(previous.focus_y, next.focus_y, progress),
    };
  }
  return sorted[sorted.length - 1];
}

/** An intentionally authored wallpaper treatment, not a generic UI gradient. */
export const Wallpaper: React.FC<{background: Background}> = ({background}) => {
  const frame = useCurrentFrame();
  if (background.kind === 'image') {
    return <AbsoluteFill style={{overflow: 'hidden'}}>
      <Img src={staticFile(background.file)} style={{
        width: '100%', height: '100%', objectFit: 'cover',
        transform: `scale(${1.025 + frame * 0.000009})`,
      }}/>
      <AbsoluteFill style={{background: 'rgba(8,12,22,.055)'}}/>
    </AbsoluteFill>;
  }
  if (background.preset === 'ink') {
    return <AbsoluteFill style={{background:'#15191f'}}>
      <AbsoluteFill style={{
        background:'radial-gradient(ellipse 63% 65% at 58% 116%, #343b4c 0%, transparent 100%)',
      }}/>
    </AbsoluteFill>;
  }
  if (background.preset === 'warm-paper') {
    return <AbsoluteFill style={{background:'#e8e1d3'}}>
      <AbsoluteFill style={{
        background:'radial-gradient(ellipse 45% 76% at 9% 85%, #d8b8a5 0%, transparent 100%), radial-gradient(ellipse 50% 61% at 90% 20%, #f6ecda 0%, transparent 100%)',
        opacity:0.85,
      }}/>
    </AbsoluteFill>;
  }
  // Two large out-of-focus color fields give the frame a deliberate ambient
  // environment, rather than putting a gradient on the product interface.
  const drift = Math.sin(frame / 210) * 17;
  return <AbsoluteFill style={{background:'#d8dbed', overflow:'hidden'}}>
    <AbsoluteFill style={{
      transform: `translate3d(${drift}px,0,0)`,
      background:'radial-gradient(ellipse 48% 50% at 91% 53%, rgba(171,80,231,.78), transparent 89%), radial-gradient(ellipse 62% 62% at 9% 89%, rgba(248,142,113,.9), transparent 81%), radial-gradient(ellipse 56% 34% at 55% 100%, rgba(234,172,126,.54), transparent 90%)',
      filter:'blur(24px)',
    }}/>
    <AbsoluteFill style={{
      background:'linear-gradient(180deg,rgba(255,255,255,.26),transparent 38%)',
    }}/>
  </AbsoluteFill>;
};

export const BrowserWindow: React.FC<{scene: Scene; showFootage?: boolean; settledFrame?: number}> = ({scene, showFootage=true, settledFrame}) => {
  const frame = useCurrentFrame();
  const {browser} = scene;
  const cam = cameraAt(settledFrame ?? frame, scene.camera);
  const chromeHeight = 86;
  const contentHeight = browser.width / browser.aspect_ratio;
  const height = chromeHeight + contentHeight;
  const scale = cam.scale;
  // Center rotation/scaling around an explicitly chosen focus point.
  const tx = (0.5 - cam.focus_x) * browser.width * (scale - 1) * 1.25;
  const ty = (0.5 - cam.focus_y) * height * (scale - 1) * 1.25;
  const dark = browser.chrome === 'dark';
  const foreground = dark ? '#f3f3f2' : '#252629';
  const chrome = dark ? '#18191d' : '#f6f5f4';

  return <div style={{
    position:'absolute', left:browser.x, top:browser.y, width:browser.width,
    height, transformOrigin:'center center',
    transform:`translate3d(${tx}px,${ty}px,0) scale(${scale})`,
    borderRadius:browser.radius, overflow:'hidden',
    background:'#fff',
    border:dark ? '1px solid rgba(255,255,255,.12)' : '1px solid rgba(18,20,31,.10)',
    boxShadow:'0 47px 105px rgba(19,21,42,.34), 0 14px 40px rgba(19,21,42,.14), 0 2px 3px rgba(19,21,42,.11)',
    willChange:'transform'
  }}>
    <div style={{
      height:chromeHeight, background:chrome, color:foreground,
      fontFamily:'-apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif',
      userSelect:'none', borderBottom:dark ? '1px solid #2b2c31' : '1px solid #d9dadc',
      boxSizing:'border-box',
    }}>
      <div style={{
        height:35,display:'flex',alignItems:'center',gap:8,
        padding:'0 16px',boxSizing:'border-box',
        background: dark ? '#25262b' : '#ebecef'
      }}>
        <div style={{display:'flex',alignItems:'center',gap:8,marginRight:26}}>
          {['#ff5f57','#febc2e','#28c840'].map((color,index)=>
            <div key={index} style={{
              width:12,height:12,borderRadius:'50%',background:color,
              boxShadow:'inset 0 0 0 .6px rgba(0,0,0,.18)'
            }}/>
          )}
        </div>
        <div style={{
          height:31,alignSelf:'end',display:'flex',alignItems:'center',
          background:dark ? '#34363b' : '#f9f9fa',
          borderRadius:'11px 11px 0 0',padding:'0 13px',
          width:245,minWidth:0,boxSizing:'border-box',gap:11
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
               style={{flexShrink:0,opacity:.87}}>
            <circle cx="12" cy="12" r="8.4" stroke="currentColor" strokeWidth="1.7"/>
            <path d="M3.9 12h16.2M12 3.7c5.5 5 5.5 11.6 0 16.6M12 3.7c-5.5 5-5.5 11.6 0 16.6"
              stroke="currentColor" strokeWidth="1.1"/>
          </svg>
          <span style={{fontSize:13,fontWeight:500,whiteSpace:'nowrap',overflow:'hidden',
                        textOverflow:'ellipsis',flex:1,letterSpacing:'-.01em'}}>
            {browser.title}
          </span>
          <span style={{fontSize:15,lineHeight:'14px',opacity:.53,marginLeft:4}}>×</span>
        </div>
        <span style={{fontSize:19,opacity:.57,marginLeft:10}}>+</span>
      </div>
      <div style={{
        height:50,display:'flex',alignItems:'center',gap:19,
        padding:'0 17px',boxSizing:'border-box',
        background:dark ? '#34363b' : '#f9f9fa',
        borderTop: dark ? '1px solid rgba(255,255,255,.03)' : '1px solid #ebebeb'
      }}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
             style={{opacity:.67,flexShrink:0}}>
          <path d="m15 5-7 7 7 7" stroke="currentColor" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
             style={{opacity:.35,flexShrink:0}}>
          <path d="m9 5 7 7-7 7" stroke="currentColor" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
             style={{opacity:.75,flexShrink:0}}>
          <path d="M20.5 8A9 9 0 1 0 21 12M20.5 3v5h-5"
                stroke="currentColor" strokeWidth="1.9"
                strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <div style={{
          height:36,flex:1,minWidth:0,borderRadius:18,display:'flex',alignItems:'center',
          background:dark ? '#24252a' : '#e9eaed',
          border:dark?'1px solid rgba(255,255,255,.055)':'1px solid #dfe0e3',
          padding:'0 15px',boxSizing:'border-box',gap:10
        }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
               style={{opacity:.56,flexShrink:0}}>
            <rect x="5" y="10.5" width="14" height="10" rx="2"
                  stroke="currentColor" strokeWidth="1.8"/>
            <path d="M8 10V7a4 4 0 0 1 8 0v3"
                  stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
          <span style={{
            fontSize:13,opacity:.8,overflow:'hidden',whiteSpace:'nowrap',
            textOverflow:'ellipsis',letterSpacing:'.005em'
          }}>{browser.url}</span>
        </div>
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
             style={{opacity:.68,flexShrink:0}}>
          <path d="M12 17V3m0 0L8 7m4-4 4 4M5 13v7h14v-7"
                stroke="currentColor" strokeWidth="1.7"
                strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <svg width="19" height="19" viewBox="0 0 24 24"
             style={{opacity:.69,flexShrink:0}} fill="currentColor">
          <circle cx="12" cy="5" r="1.65"/>
          <circle cx="12" cy="12" r="1.65"/>
          <circle cx="12" cy="19" r="1.65"/>
        </svg>
      </div>
    </div>
    <div style={{width:browser.width,height:contentHeight,background:'#f4f5f5'}}>
      {showFootage && <OffthreadVideo
        src={staticFile(scene.footage)}
        startFrom={scene.footage_start_frame}
        muted
        style={{width:'100%',height:'100%',objectFit:'fill',display:'block'}}
      />}
    </div>
  </div>;
};

const FilmScene: React.FC<{scene: Scene}> = ({scene}) => (
  <AbsoluteFill>
    <BrowserWindow scene={scene}/>
  </AbsoluteFill>
);

export const StudioFilm: React.FC<FilmProps> = ({project}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill>
    <Wallpaper background={project.background}/>
    {project.scenes.map(scene=>
      <Sequence
        key={scene.id}
        from={scene.start_frame}
        durationInFrames={scene.duration_frames}
      >
        <FilmScene scene={scene}/>
      </Sequence>
    )}
    {project.audio ? <Audio
      src={staticFile(project.audio.file)}
      volume={(f) => {
        const fadeIn = interpolate(f,[0,18],[0,1],{
          extrapolateLeft:'clamp',extrapolateRight:'clamp'
        });
        const fadeOut = interpolate(f,
          [project.canvas.duration_frames-24,project.canvas.duration_frames-1],
          [1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}
        );
        return project.audio!.volume * fadeIn * fadeOut;
      }}
    /> : null}
  </AbsoluteFill>;
};
