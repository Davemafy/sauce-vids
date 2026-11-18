"""Project one source-timed cursor onto cursorless recorded footage."""
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


def project_pointer(stage, track, matrix, time, scale=1.):
    x, y = (np.interp(time, track[:, 0], track[:, col]) for col in (1, 2))
    draw_pointer(stage, *(matrix @ [x, y, 1.]), scale=scale)
    return stage
