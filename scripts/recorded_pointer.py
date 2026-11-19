"""Project one source-timed cursor onto cursorless recorded footage."""
from functools import lru_cache

import cv2
import numpy as np


def pointer_track(manifest, width, height):
    if manifest.get("cursorless") is not True:
        return None
    try:
        track = np.asarray([(p["t"], p["x"], p["y"])
                            for p in manifest["pointer_samples"]], dtype=np.float64)
    except (KeyError, TypeError, ValueError):
        return None
    if (track.ndim != 2 or len(track) < 2 or not np.isfinite(track).all()
            or np.any(np.diff(track[:, 0]) <= 0)
            or np.any(track[:, 1:] < 0) or np.any(track[:, 1] >= width)
            or np.any(track[:, 2] >= height)):
        return None
    return track


def draw_pointer(stage, tip_x, tip_y, scale=1.):
    height = stage.shape[0]
    glyph = np.float32([[0,0],[4,32],[11,25],[18,43],[25,39],[17,22],[29,22]])
    glyph *= scale * height/1080
    glyph += (tip_x,tip_y)
    polygon = np.int32(np.rint(glyph*16))
    cv2.fillPoly(stage,[polygon],(13,14,15),cv2.LINE_AA,shift=4)
    cv2.polylines(stage,[polygon],True,(249,249,249),max(1,round(scale * height/385)),cv2.LINE_AA,shift=4)


@lru_cache(maxsize=2)
def _loupe_cursor_asset(clean=False):
    # Render a conventional arrow on a transparent, supersampled tile.
    # The forward tip sits at (4, 4); rounded joins keep the stem clean.
    from cairosvg import svg2png
    svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 50">
      <path d="M4 4 L32 29 Q33.5 30.5 31 31 L21 31 L27 43
               Q28 45 26 46 L23 47 Q21 48 20 46 L14 34 L7 40
               Q5 41 5 38 Z" fill="#151618" stroke="#f6f6f6"
        stroke-width="2.05" stroke-linejoin="round"/>
    </svg>'''
    if clean:
        # A straight, constant-width shaft with parallel edges.
        svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 50">
          <path d="M4 4 L4 35 L12.5 27 L20 43 L25.4 40.5 L17.9 24.5 L29 24.5 Z"
                fill="#121316" stroke="#ffffff" stroke-width="1.65" stroke-linejoin="round"/>
        </svg>'''
    png=svg2png(bytestring=svg,output_width=160,output_height=200)
    rgba=cv2.imdecode(np.frombuffer(png,np.uint8),cv2.IMREAD_UNCHANGED).astype(np.float32)/255.
    rgba[:,:,:3] *= rgba[:,:,3:4]
    return rgba


def draw_loupe_pointer(stage, tip_x, tip_y, *, scale=1., clean=False):
    asset = _loupe_cursor_asset(clean)
    size = scale*stage.shape[0]/1080
    left,top = tip_x-4*size,tip_y-4*size
    x0,y0 = max(0,int(np.floor(left))),max(0,int(np.floor(top)))
    x1,y1 = min(stage.shape[1],int(np.ceil(left+40*size))),min(stage.shape[0],int(np.ceil(top+50*size)))
    if x1<=x0 or y1<=y0:
        return
    matrix = np.float32([[size/4,0,left-x0],[0,size/4,top-y0]])
    cursor = cv2.warpAffine(asset,matrix,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR)
    roi = stage[y0:y1,x0:x1]
    roi[:] = np.rint(roi*(1.-cursor[:,:,3:4])+255.*cursor[:,:,:3])


def project_pointer(stage, track, matrix, time, scale=1.):
    x, y = (np.interp(time, track[:, 0], track[:, col]) for col in (1, 2))
    draw_pointer(stage, *(matrix @ [x, y, 1.]), scale=scale)
    return stage
