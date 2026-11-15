/** Studio stage parameters and perspective anchor projection.
 * Film pixels are rendered by Sauce's existing OpenCV homography compositor.
 * This mathematical contract shares the same 1820px focal length and tilt cap.
 */
import {Rect,clamp,finite} from "./types";
export interface StudioStageConfig {
  width:number;height:number;
  window:{x:number;y:number;width:number;height:number};
  focalLength:number;maxTiltDegrees:number;
  reflectionIntensity:number;roughness:number;contactShadowBlur:number;
  ambientShadowBlur:number;
}
export const DEFAULT_STAGE:StudioStageConfig={
  width:1920,height:1080,
  window:{x:220,y:124,width:1480,height:832},
  focalLength:1820,maxTiltDegrees:2.5,
  reflectionIntensity:.25,roughness:.35,
  contactShadowBlur:13,ambientShadowBlur:45,
};
export interface CameraProjection { zoom:number;centerX:number;centerY:number;offsetX:number;offsetY:number;
  sourceScale:number;rotateX:number;rotateY:number }
export function createStudioStage(reflectionIntensity:number):StudioStageConfig {
  if(!finite(reflectionIntensity)||reflectionIntensity<0||reflectionIntensity>.5)
    throw new Error("floorReflectionIntensity must be between 0 and 0.5");
  return {...DEFAULT_STAGE,reflectionIntensity};
}
export function projectAnchor(box:Rect,camera:CameraProjection,stage:StudioStageConfig=DEFAULT_STAGE):{x:number;y:number}{
  if(!finite(box.x)||!finite(box.y)||!finite(box.width)||!finite(box.height)||box.width<0||box.height<0)
    throw new Error("Invalid anchor box");
  const anchorX=box.x+box.width/2;
  const anchorY=box.y;
  const {window:win}=stage;
  const rawX=win.x+camera.offsetX+anchorX*camera.sourceScale;
  const rawY=win.y+camera.offsetY+anchorY*camera.sourceScale;
  const cx=win.x+win.width/2,cy=win.y+win.height/2;
  const ax=clamp(camera.rotateX,-stage.maxTiltDegrees,stage.maxTiltDegrees)*Math.PI/180;
  const ay=clamp(camera.rotateY,-stage.maxTiltDegrees,stage.maxTiltDegrees)*Math.PI/180;
  const X=rawX-cx,Y=rawY-cy;
  const X1=X*Math.cos(ay),Z1=-X*Math.sin(ay);
  const Y2=Y*Math.cos(ax)-Z1*Math.sin(ax);
  const Z2=Y*Math.sin(ax)+Z1*Math.cos(ax);
  const perspective=stage.focalLength/(stage.focalLength-Z2);
  return {x:cx+X1*perspective,y:cy+Y2*perspective};
}
