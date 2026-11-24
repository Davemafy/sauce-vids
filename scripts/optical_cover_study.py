"""Offline single-frame WebGL2 material study using genuine native source."""
import argparse,base64,hashlib,json,subprocess
import cv2
import numpy as np
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
    a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--sha256',required=True);a.add_argument('--at',type=float,required=True);a.add_argument('--out',type=Path,required=True)
    a.add_argument('--bulge',type=float,default=0.)
    a.add_argument('--polished',action='store_true')
    a.add_argument('--clear-shoulder',action='store_true')
    a.add_argument('--manifest',type=Path)
    a.add_argument('--manifest-sha256')
    x=a.parse_args()
    if x.clear_shoulder and (x.polished or not 0<x.bulge<=.12):raise ValueError('Clear shoulder requires sag in (0,.12] and no legacy polished mode')
    mode=2 if x.clear_shoulder else int(x.polished)
    if not 0<=x.bulge<=.30:raise ValueError('Bulge outside optical study bounds')
    if bool(x.manifest)!=bool(x.manifest_sha256):raise ValueError('Require pinned cursor manifest')
    if hashlib.sha256(x.source.read_bytes()).hexdigest()!=x.sha256:raise ValueError('Source hash mismatch')
    x.out.mkdir(parents=True,exist_ok=False)
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(x.at),'-i',str(x.source),'-frames:v','1','-c:v','png','-f','image2pipe','-'])
    if not raw:raise ValueError('Empty source')
    image=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
    if image is None:raise ValueError('Invalid source frame')
    sh,sw=image.shape[:2]
    pointer=None
    if x.manifest:
        if hashlib.sha256(x.manifest.read_bytes()).hexdigest()!=x.manifest_sha256:raise ValueError('Manifest hash mismatch')
        from recorded_pointer import pointer_track,pointer_role_at
        m=json.loads(x.manifest.read_text())
        track=pointer_track(m,sw,sh)
        if track is None or not x.bulge:raise ValueError('Require convex cursorless source')
        idx=int(np.argmin(abs(track[:,0]-x.at)))
        if abs(track[idx,0]-x.at)>.009:raise ValueError('No observed pointer sample within half a native frame')
        pointer={'source':track[idx,1:].tolist(),'observedAt':float(track[idx,0]),'role':pointer_role_at(m,x.at)}
    sky=(ROOT/'assets/stages/sauce_sky_halftone_1536x864.webp').read_bytes()
    uri=lambda b,m:'data:image/'+m+';base64,'+base64.b64encode(b).decode()
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True,executable_path='/opt/devmcp-browsers/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader'])
        page=b.new_page();page.set_content((ROOT/'assets/shaders/optical-cover-study.html').read_text())
        renderer=page.evaluate('window.renderer')
        if not renderer:raise ValueError('Missing shader renderer')
        if pointer:
            pointer['projection']=page.evaluate('d=>window.projectSource(...d)',[pointer['source'],sw,sh,x.bulge,mode])
            if not pointer['projection']['visible'] or pointer['projection']['residual']>1e-6:raise ValueError('Optical cursor projection failed')
        for black,name in ((True,'black'),(False,'cloud')):
            png=page.evaluate('async d=>window.study(d[0],d[1],d[2],d[3],d[4])',[uri(raw,'png'),uri(sky,'webp'),black,x.bulge,mode])
            data=base64.b64decode(png.split(',',1)[1])
            if pointer:
                from recorded_pointer import draw_reference_pointer
                frame=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
                draw_reference_pointer(frame,*pointer['projection']['pixel'],scale=.73,role=pointer['role'])
                data=cv2.imencode('.png',frame)[1].tobytes()
            (x.out/(name+'.png')).write_bytes(data)
        b.close()
    (x.out/'receipt.json').write_text(json.dumps({'renderer':renderer,'sourceSha256':x.sha256,'at':x.at,'bulge':x.bulge,'pointer':pointer,'polished':x.polished,'clearShoulder':x.clear_shoulder,'researchOnly':True,'ownerApproved':False},indent=2))
if __name__=='__main__':main()
