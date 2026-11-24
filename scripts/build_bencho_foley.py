"""Render the pinned MIT Bencho recipes with Chromium's OfflineAudioContext.
No network, no Pro assets. Generate all 24 samples and three Sauce aliases.
"""
import argparse,base64,hashlib,json,subprocess,tempfile,wave
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/"assets/foley/bencho"
ALIASES={"click_crisp":"tick","whoosh_soft":"glide","pop_glass":"plop"}
UPSTREAM="84dfcee170171257a28631402d37ff34900bc773"

def build(out,chromium=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    recipes=(BANK/"sounds.js").read_text()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chromium,headless=True,args=["--no-sandbox"])
        try:
            page=browser.new_page()
            page.route("**/*",lambda route:route.abort())
            samples=page.evaluate("""async code=>{
              const exports={};let seed=81217;
              Math.random=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296};
              const lib=new Function('exports',code+';return exports')(exports);
              const out={};
              for(const name of lib.SOUND_NAMES){
                const notes=lib.SOUNDS[name];
                const length=Math.ceil((Math.max(...notes.map(n=>(n.at||0)+n.ms))+25)*48);
                const ctx=new OfflineAudioContext(1,length,48000);
                lib.schedule(ctx,notes,0);
                const buf=await ctx.startRendering();
                const signal=buf.getChannelData(0);
                let raw='';const bytes=new Uint8Array(signal.buffer);
                for(let i=0;i<bytes.length;i+=8192)raw+=String.fromCharCode(...bytes.subarray(i,i+8192));
                out[name]=btoa(raw);
              }
              return out;
            }""",recipes)
        finally:browser.close()
    assert len(samples)==24
    meta={}
    with tempfile.TemporaryDirectory() as tmp:
        for name,value in samples.items():
            signal=np.frombuffer(base64.b64decode(value),dtype="<f4")
            assert np.isfinite(signal).all() and 0<len(signal)<=48000
            peak=float(np.max(np.abs(signal)));assert peak>0
            # Level-match for Sauce's existing gain controls, no timing alteration.
            pcm=(signal/peak*.55*32767).astype("<i2")
            temp=Path(tmp)/"sound.wav"
            with wave.open(str(temp),"wb") as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(pcm.tobytes())
            dest=out/(name+".flac")
            subprocess.run(["ffmpeg","-v","error","-y","-i",str(temp),"-map_metadata","-1",str(dest)],check=True)
            meta[name]={"samples":len(signal),"sha256":hashlib.sha256(dest.read_bytes()).hexdigest()}
    for alias,name in ALIASES.items():
        (out/(alias+".flac")).write_bytes((out/(name+".flac")).read_bytes())
    (out/"catalog.json").write_text(json.dumps({"upstream":UPSTREAM,"license":"MIT","sampleRate":48000,"peak":.55,"aliases":ALIASES,"sounds":meta},indent=2)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--out",required=True);p.add_argument("--chromium");a=p.parse_args()
    build(a.out,a.chromium)
