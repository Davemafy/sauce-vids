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
def glass_shell_mask(source_size, output_size):
    """Thick rounded acrylic silhouette OUTSIDE the genuine browser window.

    The shell surrounds, rather than shrinks or paints over, the real source.
    Its generous radius and 2.5%-height rim follow the supplied sky-glass
    object, while the existing card stays 87.5% of the output height.
    """
    ow, oh = output_size
    x0, y0, x1, y1, inner_radius = window_geometry(source_size, output_size)
    pad = max(4, round(oh * .024))
    radius = min(round(oh * .065), inner_radius + pad * 2,
                 (x1-x0+2*pad)//4, (y1-y0+2*pad)//4)
    left, top, right, bottom = x0-pad, y0-pad, x1+pad, y1+pad
    if left < 2 or top < 2 or right >= ow-2 or bottom >= oh-2:
        raise ValueError("Cloud-glass shell would clip the landscape stage")
    mask = np.zeros((oh, ow), dtype=np.uint8)
    cv2.rectangle(mask, (left+radius, top), (right-radius, bottom), 255, -1)
    cv2.rectangle(mask, (left, top+radius), (right, bottom-radius), 255, -1)
    for x,y in ((left+radius, top+radius), (right-radius, top+radius),
                (left+radius, bottom-radius), (right-radius, bottom-radius)):
        cv2.circle(mask, (x,y), radius, 255, -1, cv2.LINE_AA)
    return mask


@lru_cache(maxsize=6)
def stage_plate(source_size, output_size):
    """Cloud-sky acrylic, refraction, softbox highlights, shadow and inset lip.

    All glass is authored once in the fixed physical stage. The video
    compositor masks the original browser on TOP after this material pass;
    therefore the UI never inherits cloudy tint, blur, refraction, or
    invented decorative windows/cursors from the user's material reference.
    """
    ow, oh = output_size
    base = backdrop(ow, oh).astype(np.float32)
    card = card_mask(source_size, output_size)
    shell = glass_shell_mask(source_size, output_size)
    x0,y0,x1,y1,_ = window_geometry(source_size, output_size)
    pad = max(4, round(oh*.024))
    left, top, right, bottom = x0-pad, y0-pad, x1+pad, y1+pad

    # Soft shell-elevation shadow, distinct from the sharp source viewport.
    low = cv2.resize(shell, (max(2,ow//4),max(2,oh//4)),
                     interpolation=cv2.INTER_AREA)
    for sigma, dx, dy, strength in ((21.,0,22,.38),
                                   (6.8,0,7,.24)):
        field=cv2.GaussianBlur(low,(0,0),sigma)
        shifted=np.zeros_like(field)
        ox,oy=round(dx/4),round(dy/4)
        shifted[max(0,oy):,max(0,ox):] = field[:field.shape[0]-max(0,oy),
                                              :field.shape[1]-max(0,ox)]
        opacity=cv2.resize(shifted,(ow,oh),interpolation=cv2.INTER_LINEAR)
        # Keep the backdrop exactly unchanged outside the shadow/shell.
        base *= (1.-strength*opacity.astype(np.float32)[:,:,None]/255.)

    # Real background cloud imagery appears *inside* the thick blue acrylic.
    # Refraction bends cloud contours only at the object edge. This is cached
    # and never remaps the source browser's text or interface pixels.
    dist=cv2.distanceTransform(shell,cv2.DIST_L2,3)
    gy,gx=np.gradient(dist)
    magnitude=np.maximum(np.sqrt(gx*gx+gy*gy),1e-4)
    strength=np.exp(-dist/max(3.,pad*.70))*(shell.astype(np.float32)/255.)
    rows,cols=np.indices((oh,ow),dtype=np.float32)
    dx=(gx/magnitude)*strength*min(7.,pad*.28)
    dy=(gy/magnitude)*strength*min(7.,pad*.28)
    glass=cv2.remap(backdrop(ow,oh),cols+dx,rows+dy,
                    cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
    glass=cv2.GaussianBlur(glass,(0,0),1.25).astype(np.float32)

    # Cloud blue is richer at the lower corners; milky daylight comes from
    # upper-left softbox lighting, NOT from a generic gradient background.
    y=np.clip((rows-top)/max(1.,bottom-top),0.,1.)
    x=np.clip((cols-left)/max(1.,right-left),0.,1.)
    blue=np.empty_like(glass)
    blue[:,:,0]=240.-34.*y
    blue[:,:,1]=165.-83.*y
    blue[:,:,2]=76.-52.*y
    tint=.12+.13*y
    glass=glass*(1.-tint[:,:,None])+blue*tint[:,:,None]

    milk=np.exp(-((x-.09)/.45)**2-((y-.04)/.35)**2)
    lift=(.040+.17*milk)[:,:,None]
    glass=glass*(1.-lift)+np.float32([251,253,255])*lift

    # Thick perimeter bevel: white on the lit upper/left edges, deep cool
    # blue toward the bottom; not a flat 1px line around a generic card.
    bevel=np.clip((max(3.,pad*.60)-dist)/max(3.,pad*.60),0.,1.)
    bevel *= shell.astype(np.float32)/255.
    upper=np.clip((.86-y)/.82,0.,1.)
    left_light=np.clip((.24-x)/.24,0.,1.)
    rim_gain=bevel*(.17+.39*upper+.15*left_light)
    glass=glass*(1.-rim_gain[:,:,None]) + np.float32(
        [250.,253.,255.])*rim_gain[:,:,None]

    # The reference's long white studio reflection lives exclusively in
    # the top glass band. The real webpage covers it wherever they overlap.
    highlight=np.zeros((oh,ow),np.float32)
    cv2.line(highlight,(left+round(.085*(right-left)),top+round(pad*.51)),
             (left+round(.43*(right-left)),top+round(pad*.51)),
             1.,max(2,round(pad*.31)),cv2.LINE_AA)
    highlight=cv2.GaussianBlur(highlight,(0,0),max(2.,pad*.35))
    cv2.ellipse(highlight,(left+round(.18*(right-left)),top+round(pad*.65)),
                (round(.25*(right-left)),max(2,round(pad*.28))),
                0,190,344,.20,max(2,round(pad*.24)),cv2.LINE_AA)
    shine=np.clip(highlight*.62,0.,.66)*(shell.astype(np.float32)/255.)
    glass=glass*(1.-shine[:,:,None])+np.float32([255,255,255])*shine[:,:,None]

    # Broad, dim curved floor-softbox reflection on the lower acrylic rim.
    floor_reflection=np.exp(-((x-.27)/.43)**2-
                            ((y-.97)/.115)**2)*.10
    glass=glass*(1.-floor_reflection[:,:,None]) + np.float32(
        [246.,248.,252.])*floor_reflection[:,:,None]

    shell_alpha=(shell.astype(np.float32)/255.)[:,:,None]
    base=base*(1.-shell_alpha)+glass*shell_alpha

    # Fine inner aperture reflection immediately OUTSIDE the real viewport.
    # A separate matte means browser/source pixels can remain bit-for-bit
    # identical at all fully opaque card-mask positions.
    outer=cv2.dilate(card,np.ones((5,5),np.uint8))
    lip=(outer.astype(np.float32)-card.astype(np.float32))/255.
    lip=np.clip(lip,0.,1.)
    lip*=.40
    base=base*(1.-lip[:,:,None])+np.float32([241.,249.,255.])*lip[:,:,None]
    return np.uint8(np.clip(base,0,255))


def render_cloud_stage(stage, source, t):
    sw, sh = stage.source_size
    ow, oh = stage.output_size
    if source.shape[:2] != (sh, sw):
        raise ValueError("Cloud stage cannot use a fabricated source dimension")
    if stage.stage_preset=="cloud_glass_v1":
        from cloud_glass_object_stage import stage_plate as physical_plate
        from cloud_glass_object_stage import card_mask as aperture_mask
    else:
        physical_plate=stage_plate
        aperture_mask=card_mask
    board = physical_plate(stage.source_size, stage.output_size).copy()
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
    # Both approved cloud materials stay behind the exact original
    # browser aperture, even when its physical camera moves.
    m = aperture_mask(stage.source_size,stage.output_size)
    if stage.immersive:
        m=cv2.warpAffine(m,stage.view_transform(t),(ow,oh),
                         flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    alpha = m.astype(np.float32)[:, :, None] / 255
    return np.uint8(np.clip(board.astype(np.float32)*(1-alpha)
                            + rendered.astype(np.float32)*alpha, 0, 255))


def render_cloud_overview(source, output_size=(1920,1080)):
    """Passive scroll-only stage; no action or invented camera target."""
    if source.ndim!=3 or source.shape[2]!=3 or source.dtype!=np.uint8:
        raise ValueError("Expected genuine decoded BGR browser frame")
    size=(source.shape[1],source.shape[0])
    x0,y0,x1,y1,_=window_geometry(size,output_size)
    board=stage_plate(size,output_size).copy()
    screen=cv2.resize(source,(x1-x0,y1-y0),interpolation=cv2.INTER_AREA
                      if x1-x0<=size[0] else cv2.INTER_CUBIC)
    mask=card_mask(size,output_size)[y0:y1,x0:x1,None].astype(np.uint16)
    dst=board[y0:y1,x0:x1]
    dst[:]=((screen.astype(np.uint16)*mask+
             dst.astype(np.uint16)*(255-mask)+127)//255).astype(np.uint8)
    return board
