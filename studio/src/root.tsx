import React from 'react';
import {Composition} from 'remotion';
import {StudioFilm, Wallpaper, BrowserWindow} from './studio-film';
import {AbsoluteFill} from 'remotion';
import type {StudioProject} from './types';

const example: StudioProject = {
  schema_version: 1,
  canvas: {width: 1920, height: 1080, fps: 30, duration_frames: 590},
  background: {kind: 'preset', preset: 'lilac-sunset'},
  scenes: [{
    id: 'brimble-overview',
    start_frame: 0,
    duration_frames: 590,
    footage: 'footage/recording.mp4',
    footage_start_frame: 0,
    browser: {
      title: 'Brimble Agent',
      url: 'brimble.io/agent',
      chrome: 'dark',
      width: 1410,
      x: 255,
      y: 72,
      radius: 18,
      aspect_ratio: 16 / 9
    },
    camera: [{frame: 0, scale: 1, focus_x: 0.5, focus_y: 0.5}]
  }]
};

const StudioStage: React.FC<{project:StudioProject}> = ({project}) => (
  <AbsoluteFill>
    <Wallpaper background={project.background}/>
    <BrowserWindow scene={project.scenes[0]} showFootage={false} settledFrame={90}/>
  </AbsoluteFill>
);

export const Root: React.FC = () => (
  <>
  <Composition
    id="SauceStudio"
    component={StudioFilm}
    width={1920}
    height={1080}
    fps={30}
    durationInFrames={590}
    defaultProps={{project: example}}
    calculateMetadata={({props}) => ({
      width: props.project.canvas.width,
      height: props.project.canvas.height,
      fps: props.project.canvas.fps,
      durationInFrames: props.project.canvas.duration_frames
    })}
  />
  <Composition
    id="SauceStage"
    component={StudioStage}
    width={1920}
    height={1080}
    fps={30}
    durationInFrames={1}
    defaultProps={{project:example}}
    calculateMetadata={({props}) => ({
      width:props.project.canvas.width,
      height:props.project.canvas.height,
      fps:props.project.canvas.fps,
      durationInFrames:1
    })}
  />
  </>
);
