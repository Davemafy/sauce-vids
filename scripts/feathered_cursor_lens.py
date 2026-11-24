"""Original persistent cursor lens with a narrow soft perimeter, research only."""
import cv2
import numpy as np
from cursor_lens import CursorLens

FEATHER_PX=20.

def feather_mask(alpha,width):
    """C2 inward fade; no blur or change to the interior source sampling."""
    d=cv2.distanceTransform((alpha>.5).astype(np.uint8),cv2.DIST_L2,5)
    u=np.clip(d/width,0.,1.)
    return alpha*(u*u*u*(10+u*(-15+6*u)))

class FeatheredCursorLens(CursorLens):
    def prepare_material(self):
        super().prepare_material()
        width=FEATHER_PX*self.stage.output_size[1]/1080
        self.alpha=feather_mask(self.alpha,width).astype(np.float32)
        # Existing shoulder light is naturally attenuated by the new alpha.
        # No independent bright outline, extra shadow, or central blur.

    def receipt(self):
        return {**super().receipt(),'profile':'feathered-cursor-lens-v1',
                'inwardFeatherPxAt1080':FEATHER_PX,'cameraUnchanged':True,
                'sourceProjectionUnchanged':True}
