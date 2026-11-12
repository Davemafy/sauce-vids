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
  const chromeHeight = 54;
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
      fontFamily:'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      display:'flex', alignItems:'center', position:'relative',
      borderBottom:dark ? '1px solid #2a2b31' : '1px solid #dedede',
      boxSizing:'border-box',padding:'0 18px',fontSize:13,
    }}>
      <div style={{display:'flex',gap:8,alignItems:'center',flex:'0 0 125px'}}>
        {['#ed6a62','#f0c453','#64c76d'].map((color,index)=>
          <div key={index} style={{
            width:12,height:12,borderRadius:'50%',
            background:color,opacity:.94
          }}/>
        )}
      </div>
      <div style={{
        display:'flex',alignItems:'center',gap:9,
        maxWidth:250,minWidth:170,
        background:dark ? '#28292e' : '#eae9e8',
        borderRadius:'9px 9px 0 0', height:38,
        alignSelf:'end', padding:'0 17px',
        boxSizing:'border-box', letterSpacing:'-.01em'
      }}>
        <span style={{opacity:.76,fontSize:11}}>◈</span>
        <span style={{textOverflow:'ellipsis',whiteSpace:'nowrap',overflow:'hidden'}}>
          {browser.title}
        </span>
      </div>
      <div style={{
        position:'absolute',left:'54%',top:'50%',
        transform:'translate(-50%,-50%)',
        opacity:.55,fontSize:12,letterSpacing:'.005em',
        whiteSpace:'nowrap'
      }}>
        {browser.url}
      </div>
      <div style={{marginLeft:'auto',opacity:.65,fontSize:17,paddingRight:8}}>＋</div>
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
