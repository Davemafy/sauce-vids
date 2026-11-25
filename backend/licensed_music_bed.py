"""Optional hash-pinned CC0 music bed for customer-source Sauce films.

No automatic unlicensed asset discovery and no generic synthesized clicks.
A human/operator configures one existing track + independent FMA CC0 page
once; every fresh URL job uses the same permitted taste experiment.
Source-hash, license, and artwork claims remain separate from film approval.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,math,os,re,subprocess
from pathlib import Path


@dataclass(frozen=True)
class LicensedMusic:
    path:Path
    id:str
    title:str
    artist:str
    source:str
    license:str
    audio_sha256:str
    evidence_sha256:str
    evidence_source:str

    def public_receipt(self):
        return {"track_id":self.id,"title":self.title,"artist":self.artist,
                "source":self.source,"license":self.license,
                "audio_sha256":self.audio_sha256,
                "license_evidence_sha256":self.evidence_sha256,
                "licensed_customer_use":True,
                "creative_approved":False}


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(2**20),b""):
            h.update(chunk)
    return h.hexdigest()


def licensed_music_from_env():
    track=os.getenv("SAUCE_CC0_TRACK_ID","")
    if not track:
        return None
    if not re.fullmatch(r"[a-z0-9-]{2,35}",track):
        raise ValueError("Invalid CC0 music identifier")
    keys=("SAUCE_CC0_CATALOG_PATH","SAUCE_CC0_PROOF_PATH",
          "SAUCE_CC0_PROOF_SHA256")
    vals=[os.getenv(k,"") for k in keys]
    if not all(vals) or not re.fullmatch(r"[a-f0-9]{64}",vals[-1]):
        raise ValueError("Missing operator-pinned CC0 license evidence")
    catalog=Path(vals[0]).resolve(strict=True)
    evidence=Path(vals[1]).resolve(strict=True)
    if not catalog.is_file() or not evidence.is_file() or sha256(evidence)!=vals[2]:
        raise ValueError("Licensed music proof hash mismatch")
    source=json.loads(catalog.read_text())
    rows=source.get("tracks",[])
    items=[i for i in rows if isinstance(i,dict) and i.get("id")==track]
    if len(items)!=1:
        raise ValueError("Unknown or ambiguous music in verified catalog")
    entry=items[0]
    if (entry.get("license")!="CC0-1.0" or
        entry.get("license_url")!="https://creativecommons.org/publicdomain/zero/1.0/" or
        not re.fullmatch(r"[a-f0-9]{64}",entry.get("sha256","")) or
        entry.get("file")!=f"tracks/{track}.mp3" or
        not isinstance(entry.get("title"),str) or not entry["title"].strip() or
        not isinstance(entry.get("artist"),str) or not entry["artist"].strip() or
        not isinstance(entry.get("source"),str) or
        not entry["source"].startswith("https://freemusicarchive.org/music/")):
        raise ValueError("Music license catalog entry invalid")
    audio=(catalog.parents[2]/entry["file"]).resolve(strict=True)
    if (audio.parent!=(catalog.parents[2]/"tracks").resolve() or
        not audio.is_file() or sha256(audio)!=entry["sha256"]):
        raise ValueError("CC0 audio source file digest mismatch")
    raw=evidence.read_text(errors="replace")
    # Independent downloaded FMA HTML: exact artist, track title, license
    # canonical URL, and source domain must all match at once.
    title=f'<title>{entry["artist"]} - {entry["title"]} - Free Music Archive</title>'
    if (title not in raw or
        'CC0 1.0 Universal License' not in raw or
        'rel="license" href="https://creativecommons.org/publicdomain/zero/1.0/"' not in raw or
        len(raw)>1_500_000):
        raise ValueError("Source license HTML does not prove CC0")
    return LicensedMusic(audio,track,entry["title"],entry["artist"],
                         entry["source"],entry["license"],entry["sha256"],
                         vals[2],entry["source"])


def add_music_to_master(master:Path, track:LicensedMusic, duration:float, *, preserve_foley=False):
    """Mix a quiet, originally licensed track; preserve *exact* H264 picture.

    Silent soundbeds to cheat QA are not allowed. Source audio is actual CC0
    music with a provenance receipt, restrained level and soft fade.
    """
    master=Path(master)
    if (not master.is_file() or not 2<=duration<=75 or
        not math.isfinite(duration) or track is None):
        raise ValueError("Missing original video or licensed music")
    temp=master.with_name("sauce-audio-mux.pending.mp4")
    if temp.exists():
        raise ValueError("Refusing to overwrite an existing music remix")
    ending=max(.3,float(duration)-.45)
    fade=f"volume=0.19,afade=t=in:st=0:d=0.22,afade=t=out:st={ending:.3f}:d=0.43,aresample=48000"
    filters=f"[1:a:0]{fade}[music]"
    output="[music]"
    if preserve_foley:
        # Keep the original event clock. No replacement of verified cues;
        # limiter latency compensation keeps the mix aligned to the picture.
        filters+=";[0:a:0]aresample=48000[fx];[fx][music]amix=inputs=2:duration=first:normalize=0,alimiter=limit=.9:level=0:latency=1[mix]"
        output="[mix]"
    argv=["ffmpeg","-hide_banner","-loglevel","error","-xerror","-nostdin",
          "-i",str(master),"-i",str(track.path),"-filter_complex",
          filters,
          "-map","0:v:0","-map",output,
          "-c:v","copy","-c:a","aac","-ar","48000","-ac","2",
          "-b:a","128k","-t",str(round(duration,5)),
          "-movflags","+faststart",str(temp)]
    try:
        produced=subprocess.run(argv,timeout=45,capture_output=True,text=True)
        if produced.returncode:
            raise RuntimeError("Licensed music mux failed: "+
                               produced.stderr[-600:])
        result=json.loads(subprocess.check_output(
          ["ffprobe","-v","error","-show_entries",
           "stream=codec_type,codec_name,sample_rate,channels,r_frame_rate,nb_frames",
           "-of","json",str(temp)],text=True,timeout=12))
        video=[s for s in result["streams"] if s.get("codec_type")=="video"]
        audio=[s for s in result["streams"] if s.get("codec_type")=="audio"]
        if (len(video)!=1 or len(audio)!=1 or
            video[0].get("r_frame_rate")!="60/1" or
            audio[0].get("codec_name")!="aac" or
            audio[0].get("sample_rate")!="48000" or audio[0].get("channels")!=2):
            raise RuntimeError("Music mux did not preserve the real video/audio contract")
        # FFmpeg stream copy cannot modify a single original encoded video
        # picture; the UI is identical, now with verifiably licensed audio.
        temp.replace(master)
    finally:
        if temp.exists():temp.unlink()
