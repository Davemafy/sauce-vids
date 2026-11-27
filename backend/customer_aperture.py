"""Lossless native-source aperture for a fully observed embedded product."""
import copy,hashlib,json,math,subprocess
from pathlib import Path

def sha(path):
    with Path(path).open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def aperture(regions,manifest):
    """One fixed landscape aperture; all real pointer and evidence must fit."""
    if not regions or any(not isinstance(r,dict) for r in regions):return None
    sw,sh=(manifest["capture_rect"][k] for k in ("width","height"))
    if (sw,sh)!=(3840,2160):return None
    fields=("x","y","width","height")
    if any(any(type(r.get(k)) not in (float,int) or not math.isfinite(r[k]) for k in fields) for r in regions):return None
    base=regions[0]
    if any(any(abs(r[k]-base[k])>8 for k in fields) for r in regions):return None
    boxes=list(regions)
    for e in manifest["events"]:
        boxes.extend(e[k] for k in ("targetRect","resultRect","componentRect") if k in e)
    pts=manifest["pointer_samples"]
    if not pts:return None
    left=min([r["x"] for r in boxes]+[p["x"] for p in pts])-32
    top=min([r["y"] for r in boxes]+[p["y"] for p in pts])-32
    right=max([r["x"]+r["width"] for r in boxes]+[p["x"] for p in pts])+32
    bottom=max([r["y"]+r["height"] for r in boxes]+[p["y"] for p in pts])+32
    # Multiples of 32 x 18 preserve exact 16:9 and YUV420 alignment.
    n=max(60,math.ceil((right-left)/32),math.ceil((bottom-top)/18))
    w,h=32*n,18*n
    if w>sw*.84 or h>sh*.84:return None
    def origin(lo,hi,size,total):
        minimum=max(0,math.ceil((hi-size)/2)*2)
        maximum=min(total-size,math.floor(lo/2)*2)
        if minimum>maximum:return None
        return max(minimum,min(maximum,round((lo+hi-size)/4)*2))
    x=origin(left,right,w,sw);y=origin(top,bottom,h,sh)
    if x is None or y is None:return None
    return [x,y,w,h]

def translate(manifest,rect):
    x,y,w,h=rect;d=copy.deepcopy(manifest)
    sw,sh=(d["capture_rect"][k] for k in ("width","height"))
    if any(type(v) is not int or v%2 for v in rect) or not (0<=x<x+w<=sw and 0<=y<y+h<=sh and w>=1920 and h>=1080 and w*9==h*16):
        raise ValueError("Invalid native product aperture")
    for e in d["events"]:
        for k in ("targetRect","resultRect","componentRect"):
            if k not in e:continue
            r=e[k];r["x"]-=x;r["y"]-=y
            if not (0<=r["x"]<r["x"]+r["width"]<=w and 0<=r["y"]<r["y"]+r["height"]<=h):
                raise ValueError("Aperture would remove verified evidence")
    for p in d["pointer_samples"]:
        p["x"]-=x;p["y"]-=y
        if not (0<=p["x"]<w and 0<=p["y"]<h):
            raise ValueError("Aperture would remove real pointer")
    d["capture_rect"]={"width":w,"height":h}
    return d

def frame_hashes(path,filter_=None):
    cmd=["ffmpeg","-v","error","-xerror","-nostdin","-i",str(path),"-map","0:v:0"]
    if filter_:cmd+=["-vf",filter_]
    cmd+=["-an","-pix_fmt","yuv420p","-f","framemd5","-"]
    raw=subprocess.check_output(cmd,text=True,timeout=180)
    return [line.split(",")[-1].strip() for line in raw.splitlines() if line and not line.startswith("#")]

def derive(source,manifest_path,regions):
    """Retain original full native master/manifest. Never interpolate source pixels."""
    source,manifest_path=map(Path,(source,manifest_path))
    original=json.loads(manifest_path.read_text())
    rect=aperture(regions,original)
    if rect is None:return source,manifest_path
    x,y,w,h=rect
    target=source.with_name("product-aperture.mp4")
    output=manifest_path.with_name("product-aperture-manifest.json")
    if target.exists() or output.exists():raise ValueError("Refuse to replace existing aperture")
    d=translate(original,rect)
    filt=f"crop={w}:{h}:{x}:{y}"
    subprocess.run(["ffmpeg","-v","error","-xerror","-nostdin","-n","-i",str(source),
        "-map","0:v:0","-vf",filt,"-an","-c:v","libx264","-preset","ultrafast",
        "-qp","0","-pix_fmt","yuv420p","-threads","4","-movflags","+faststart",str(target)],
        check=True,timeout=180)
    a=frame_hashes(source,filt);b=frame_hashes(target)
    if len(a)!=round(original["duration"]*60) or a!=b:
        raise ValueError("Native aperture did not preserve every decoded source frame")
    d["nativeCrop"]={"schema":"sauce-native-aperture-v1","rect":rect,"regions":regions,
        "originalSourceSha256":sha(source),"originalManifestSha256":sha(manifest_path),
        "derivedSourceSha256":sha(target),"frames":len(a),
        "decodedFrameHashesSha256":hashlib.sha256("\n".join(a).encode()).hexdigest()}
    output.write_text(json.dumps(d,indent=2)+"\n")
    return target,output

def validate_binding(source,manifest_path):
    """Revalidate immutable crop provenance at the actual render entry point."""
    source,manifest_path=map(Path,(source,manifest_path))
    d=json.loads(manifest_path.read_text())
    proof=d.get("nativeCrop")
    if proof is None:return
    if not isinstance(proof,dict):raise ValueError("Malformed aperture proof")
    parent=source.with_name("source.mp4");original=manifest_path.with_name("manifest.json")
    if (proof.get("schema")!="sauce-native-aperture-v1" or source==parent or manifest_path==original
        or not parent.is_file() or not original.is_file()
        or proof.get("originalSourceSha256")!=sha(parent)
        or proof.get("originalManifestSha256")!=sha(original)
        or proof.get("derivedSourceSha256")!=sha(source)):
        raise ValueError("Aperture provenance hash mismatch")
    prior=json.loads(original.read_text());rect=aperture(proof.get("regions"),prior)
    if rect is None or rect!=proof.get("rect") or translate(prior,rect)!={k:v for k,v in d.items() if k!="nativeCrop"}:
        raise ValueError("Aperture geometry differs from original recording")
    if proof.get("frames")!=round(prior["duration"]*60) or not isinstance(proof.get("decodedFrameHashesSha256"),str) or len(proof["decodedFrameHashesSha256"])!=64:
        raise ValueError("Aperture missing decoded frame proof")
