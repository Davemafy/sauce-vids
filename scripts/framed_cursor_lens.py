"""Full-source convex display with a directional optical cover.

Opt-in research. The internal camera is deliberately replaced by a complete
source fit. The local lens remains persistent and shares the cursor transform.
The original source's own clipping cannot be reconstructed.
"""
import cv2
import numpy as np
from cursor_lens import CursorLens
from luminous_display_stage import LINEAR,to_srgb

class FramedCursorLens(CursorLens):
    def camera_quad(self,t):
        x0,y0,x1,y1,_=self.geometry
        return np.float32([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])

    def prepare_material(self):
        super().prepare_material()
        mx,my,qx,qy=self.base_maps
        # Keep one continuous cover. Reduce the corner cutout (not the
        # global bulge), to protect source toolbar / sidebar corners.
        from cloud_window_sky_stage import _rounded_mask
        x0,y0,x1,y1,_=self.geometry
        self.mask=_rounded_mask(self.stage.output_size,(x0,y0,x1,y1),16)
        self.alpha=cv2.remap(self.mask,mx,my,cv2.INTER_LINEAR).astype(np.float32)/255
        d=cv2.distanceTransform((self.alpha>.5).astype(np.uint8),cv2.DIST_L2,5)
        outside=cv2.distanceTransform((self.alpha<=.5).astype(np.uint8),cv2.DIST_L2,5)
        self.d=d
        # Smooth analytic shoulder normals avoid the diagonal discontinuity
        # of a nearest-edge distance-gradient normal.
        dx=np.maximum(1-np.abs(qx),0);dy=np.maximum(1-np.abs(qy),0)
        nx=.23*qx+np.sign(qx)*2.4*np.exp(-dx/.035)
        ny=.23*qy+np.sign(qy)*2.4*np.exp(-dy/.045)
        z=1/np.sqrt(1+nx*nx+ny*ny)
        self.rx=(2*nx*z*z).astype(np.float32)
        self.ry=(2*ny*z*z).astype(np.float32)
        fresnel=.04+.96*(1-z)**5
        self.grazing=(fresnel+.07)*np.exp(-d/49)
        self.grazing=self.grazing.astype(np.float32)
        gy,gx=np.gradient(d-outside)
        n=np.maximum(np.hypot(gx,gy),1e-5)
        split=(gx/n*2.4+gy/n*.9).astype(np.float32)
        directional=np.clip(.64-.24*gy/n+.14*gx/n,.26,.98)
        ridge=lambda off: np.exp(-((d-2.4-off)/1.25)**2)
        spectrum=np.stack([ridge(-split),ridge(0.),ridge(split)],axis=-1)
        crest=np.exp(-((d-2.)/1.3)**2)*directional
        # Narrow spectral meniscus, modest internal scatter; no colored housing.
        scatter=np.exp(-d/27)*(.018+.055*np.clip((qy+.2)/1.2,0,1))
        self.light=(spectrum*.39+crest[:,:,None]*.57+
                    scatter[:,:,None]*np.float32([.64,.25,.36]))*self.alpha[:,:,None]
        self.light=self.light.astype(np.float32)
        self.transmission=(1-.065*np.exp(-d/12)).astype(np.float32)
        low=cv2.resize(self.alpha,(480,270),interpolation=cv2.INTER_AREA)
        shadow=cv2.GaussianBlur(low,(0,0),9)
        shifted=np.zeros_like(shadow);shifted[4:]=shadow[:-4]
        shadow=cv2.resize(shifted,self.stage.output_size)
        self.board=LINEAR[self.sky]*(1-.38*shadow[:,:,None])
        # Static low-frequency optical bloom from actual shoulder light.
        small=cv2.resize(self.light,(480,270),interpolation=cv2.INTER_AREA)
        self.halo=cv2.resize(cv2.GaussianBlur(small,(0,0),1.6),self.stage.output_size)*.15
        self.halo=self.halo.astype(np.float32)

    def finish(self,screen,mx,my,qx,qy,energy,t):
        c,r,s=self.state(t)
        # Reflected studio softboxes shift subtly with the smoothed lens,
        # and are concentrated on the physical shoulder, not the page center.
        shift=float(np.clip((c[0]-960)/960,-1,1))*.12
        top=np.exp(-((self.rx+.22-shift)/.52)**6-((self.ry+.79)/.13)**4)*np.clip(-qy,0,1)**3
        right=np.exp(-((self.rx-.78)/.13)**4-((self.ry+.20)/.48)**6)*np.clip(qx,0,1)**3
        spec=np.clip((top*1.8+right*1.35)*self.grazing,0,.32)
        ui=LINEAR[screen]
        lum=ui@np.float32([.0722,.7152,.2126])
        # Keep contrast: avoid lighting up bright typography even further.
        spec*=1-.66*np.clip(lum,0,1)
        face=ui*self.transmission[:,:,None]+self.light+spec[:,:,None]*np.float32([.92,.96,1.])
        return to_srgb(self.board*(1-self.alpha[:,:,None])+face*self.alpha[:,:,None]+self.halo)

    def receipt(self):
        return {**super().receipt(),'profile':'framed-cursor-lens-v2',
                'fullSourceFit':True,'internalCameraZoomDisabled':True,
                'sourceRoundedCornerRadiusPx':16,'directionalGlassReflection':True,
                'stageCameraMetricsDescribeInputPlanNotRenderedCamera':True}
