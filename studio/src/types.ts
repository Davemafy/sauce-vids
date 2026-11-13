export type Background =
  | {kind: 'preset'; preset: 'lilac-sunset' | 'warm-paper' | 'ink' | 'sauce'}
  | {kind: 'image'; file: string};

export type CameraKeyframe = {
  frame: number;
  scale: number;
  focus_x: number;
  focus_y: number;
};

export interface Scene {
  id: string;
  start_frame: number;
  duration_frames: number;
  footage: string;
  footage_start_frame: number;
  browser: {
    title: string;
    url: string;
    chrome: 'dark' | 'light';
    width: number;
    x: number;
    y: number;
    radius: number;
    aspect_ratio: number;
  };
  camera: CameraKeyframe[];
}

export interface StudioProject {
  schema_version: 1;
  canvas: {
    width: number;
    height: number;
    fps: number;
    duration_frames: number;
  };
  background: Background;
  scenes: Scene[];
  audio?: {file: string; volume: number};
  provenance?: {run_id: string; source_url: string};
}
