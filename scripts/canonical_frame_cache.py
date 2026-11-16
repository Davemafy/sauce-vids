"""Private canonical composited-frame snapshots for deterministic Sauce exports.

The user-approved HAR session and source screenshots are validated by replay
before applying this lock. Snapshots never go in the public proof directory.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np


def identity_for_composition(source_identity:str,frame_plan:dict,
                             seed:int,renderer_paths:list[Path])->str:
    """Digest the exact source, output time/camera map, seed and code files."""
    digest=hashlib.sha256()
    digest.update(b"sauce-canonical-composition-v1\0")
    digest.update(source_identity.encode())
    digest.update(json.dumps(frame_plan,sort_keys=True,
               separators=(",",":"),ensure_ascii=True).encode())
    digest.update(str(seed).encode())
    for path in renderer_paths:
        digest.update(path.name.encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


class CanonicalComposition:
    def __init__(self,root:Path,identity:str,total_frames:int):
        if len(identity)!=64 or total_frames<=0:
            raise ValueError("Invalid canonical composition identity")
        self.directory=root/"composited"/identity
        self.directory.mkdir(parents=True,exist_ok=True)
        self.manifest=self.directory/"manifest.json"
        self.identity=identity
        self.total_frames=total_frames
        self.hashes:list[str]=[]
        self.reused=self.manifest.is_file()
        self.live_diff_frames=0
        if self.reused:
            data=json.loads(self.manifest.read_text())
            if (data.get("identity")!=identity or
                data.get("frames")!=total_frames or
                not isinstance(data.get("hashes"),list) or
                len(data["hashes"])!=total_frames):
                raise RuntimeError("Compositor cache manifest incompatible")
            self.hashes=data["hashes"]

    def use(self,index:int,frame:np.ndarray)->np.ndarray:
        """Return pinned canonical pixels, checking every stored PNG SHA-256."""
        if not 0<=index<self.total_frames or frame.dtype!=np.uint8:
            raise ValueError("Invalid canonical composition frame")
        target=self.directory/f"{index:05d}.png"
        if self.reused:
            if not target.is_file():
                raise FileNotFoundError(target)
            raw=target.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=self.hashes[index]:
                raise RuntimeError("Canonical composition frame hash mismatch")
            pinned=cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_COLOR)
            if pinned is None or pinned.shape!=frame.shape:
                raise RuntimeError("Canonical composition frame dimension mismatch")
            self.live_diff_frames+=int(not np.array_equal(pinned,frame))
            return pinned
        if not cv2.imwrite(str(target),frame,[cv2.IMWRITE_PNG_COMPRESSION,3]):
            raise RuntimeError("Could not write canonical private frame")
        self.hashes.append(hashlib.sha256(target.read_bytes()).hexdigest())
        return frame

    def finish(self)->None:
        if self.reused:return
        if len(self.hashes)!=self.total_frames:
            raise RuntimeError("Incomplete canonical composition frames")
        data={"identity":self.identity,"frames":self.total_frames,
              "hashes":self.hashes,"private":True}
        temp=self.manifest.with_suffix(".tmp")
        temp.write_text(json.dumps(data,indent=2))
        temp.replace(self.manifest)
