"""Fixed Sauce cloud stage: user-provided halftone sky, rounded floating screen.

This paints ONLY the stage. The product screen remains the genuine browser
frame, projected by the already-validated camera into a fixed physical card.
The director cannot choose the background, border radius, shadow, or margins.
"""
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

PRESET = "cloud_shadow_v1"
CLOUD = Path(__file__).resolve().parents[1] / "assets/stages/cloud_shadow_v2_1536x864.jpg"


def window_geometry(source_size, output_size):
    sw, sh = source_size
    ow, oh = output_size
    aspect = sw / sh
    # Larger hero: the stage remains visible, but captured text is no
    # longer reduced to a small distant thumbnail.
    w = min(ow * .875, oh * .875 * aspect)
    h = w / aspect
    if h > oh * .875 + .001:
        raise ValueError("Impossible landscape stage geometry")
    x0 = round((ow - w) / 2)
    y0 = round((oh - h) / 2)
    x1 = round(x0 + w)
    y1 = round(y0 + h)
    radius = max(5, round(min(ow, oh) * .019))
    return x0, y0, x1, y1, radius


@lru_cache(maxsize=3)
def backdrop(ow, oh):
    img = cv2.imread(str(CLOUD), cv2.IMREAD_COLOR)
    if img is None or img.shape[:2] != (864, 1536):
        raise ValueError("Cloud Shadow requires the owner's genuine 1536x864 "
                         "cobalt halftone reference; low-resolution substitutes "
                         "are forbidden")
    # Keep the exact owner-supplied print: no artificial halftone or blur.
    if (ow, oh) == (1536, 864):
        return img
    mode = cv2.INTER_AREA if ow <= 1536 and oh <= 864 else cv2.INTER_CUBIC
    return cv2.resize(img, (ow, oh), interpolation=mode)


@lru_cache(maxsize=6)
def card_mask(source_size, output_size):
    ow, oh = output_size
    x0, y0, x1, y1, radius = window_geometry(source_size, output_size)
    r = min(radius, (x1-x0)//4, (y1-y0)//4)
    m = np.zeros((oh, ow), np.uint8)
    cv2.rectangle(m, (x0+r, y0), (x1-r, y1), 255, -1)
    cv2.rectangle(m, (x0, y0+r), (x1, y1-r), 255, -1)
    for x, y in ((x0+r, y0+r), (x1-r, y0+r),
                 (x0+r, y1-r), (x1-r, y1-r)):
        cv2.circle(m, (x, y), r, 255, -1, cv2.LINE_AA)
    return m


@lru_cache(maxsize=6)
def stage_plate(source_size, output_size):
    ow, oh = output_size
    base = backdrop(ow, oh).astype(np.float32)
    m = card_mask(source_size, output_size)
    # Two soft shadows: large atmospheric elevation and close contact.
    # The browser silhouette is rounded, not a hard rectangular shadow.
    small = cv2.resize(m, (ow//4, oh//4), interpolation=cv2.INTER_AREA)
    soft = cv2.GaussianBlur(small, (0, 0), 22)
    close = cv2.GaussianBlur(small, (0, 0), 7)
    for field, dx, dy, alpha in ((soft, 0, 25, .45),
                                 (close, 0, 8, .23)):
        moved = np.zeros_like(field)
        sx = round(dx / 4); sy = round(dy / 4)
        moved[max(0, sy):, max(0, sx):] = field[:len(field)-max(0,sy),
                                                :field.shape[1]-max(0,sx)]
        lifted = cv2.resize(moved, (ow, oh), interpolation=cv2.INTER_LINEAR)
        shadow = np.clip(lifted.astype(np.float32) / 255., 0, 1)
        base *= (1 - alpha * shadow)[:, :, None]
    # No fake browser address bar or synthetic product chrome.
    return np.uint8(np.clip(base, 0, 255))


def render_cloud_stage(stage, source, t):
    sw, sh = stage.source_size
    ow, oh = stage.output_size
    if source.shape[:2] != (sh, sw):
        raise ValueError("Cloud stage cannot use a fabricated source dimension")
    board = stage_plate(stage.source_size, stage.output_size).copy()
    if stage.immersive:
        # Camera approaches the physical object, not a scaled already-low-res
        # screenshot. Background and original soft shadows move together;
        # source UI is separately reprojected from ORIGINAL native DPR2.
        view=stage.view_transform(t)
        board=cv2.warpAffine(board,view,(ow,oh),flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REFLECT_101)
    sq = np.float32([[0, 0], [sw-1, 0], [sw-1, sh-1], [0, sh-1]])
    q = stage.quad(t)
    H = cv2.getPerspectiveTransform(sq, q)
    # Native source is usually DPR2 2880x1800. Perspective-resampling it
    # straight to ~1500px throws away fine lettering without antialiasing.
    # Pre-filter at the displayed screen resolution using INTER_AREA, then
    # warp at <=1:1 scale. Keep original pixels, colors and frame clock.
    q_w = float(np.linalg.norm(q[1] - q[0]))
    q_h = float(np.linalg.norm(q[3] - q[0]))
    scale = min(1., max(q_w/sw, q_h/sh)*1.10)
    if scale < .85:
        dw, dh = max(2, round(sw*scale)), max(2, round(sh*scale))
        frame_for_warp = cv2.resize(source, (dw, dh),
                                   interpolation=cv2.INTER_AREA)
        points = np.float32([[0,0],[dw-1,0],[dw-1,dh-1],[0,dh-1]])
        H = cv2.getPerspectiveTransform(points, q)
    else:
        frame_for_warp = source
    rendered = cv2.warpPerspective(frame_for_warp, H, (ow, oh),
                                   flags=cv2.INTER_CUBIC,
                                   borderMode=cv2.BORDER_CONSTANT)
    exposure = stage.shutter_times(t)
    if exposure is not None:
        early, late = exposure
        a = cv2.warpPerspective(source, cv2.getPerspectiveTransform(sq, stage.quad(early)),
                                 (ow, oh), flags=cv2.INTER_LINEAR)
        b = cv2.warpPerspective(source, cv2.getPerspectiveTransform(sq, stage.quad(late)),
                                 (ow, oh), flags=cv2.INTER_LINEAR)
        rendered = ((a.astype(np.uint16) + 4*rendered.astype(np.uint16)
                     + b.astype(np.uint16) + 3) // 6).astype(np.uint8)
    m = card_mask(stage.source_size, stage.output_size)
    if stage.immersive:
        m=cv2.warpAffine(m,stage.view_transform(t),(ow,oh),
                         flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    # Pixel mask respects rounded corners on every frame and on camera zooms.
    # The second reference specifies material only: an exterior highlight
    # and gentle glazed rim, no invented titlebar, product content or cursor.
    outer=cv2.dilate(m,np.ones((5,5),np.uint8))
    edge=np.clip(outer.astype(np.int16)-m.astype(np.int16),0,255)
    _, top, _, _, radius=window_geometry(stage.source_size,stage.output_size)
    if stage.immersive:
        transform=stage.view_transform(t)
        top=float(transform[1,1]*top+transform[1,2])
        radius=float(radius*transform[1,1])
    ys=np.arange(oh,dtype=np.float32)[:,None]
    upper=np.clip((top+radius*2.5-ys)/max(1.,radius*3.),0.,1.)
    strength=(.20+.35*upper)*edge.astype(np.float32)/255.
    board_f=board.astype(np.float32)
    tint=np.array([239.,244.,252.],dtype=np.float32)
    board=np.uint8(np.clip(board_f*(1.-strength[:,:,None])
                           +tint*strength[:,:,None],0,255))
    alpha = m.astype(np.float32)[:, :, None] / 255
    return np.uint8(np.clip(board.astype(np.float32)*(1-alpha)
                            + rendered.astype(np.float32)*alpha, 0, 255))
