"""Offline single-frame WebGL2 material study using genuine native source."""
import argparse,base64,hashlib,json,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
    a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--sha256',required=True);a.add_argument('--at',type=float,required=True);a.add_argument('--out',type=Path,required=True)
    x=a.parse_args()
    if hashlib.sha256(x.source.read_bytes()).hexdigest()!=x.sha256:raise ValueError('Source hash mismatch')
    x.out.mkdir(parents=True,exist_ok=False)
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(x.at),'-i',str(x.source),'-frames:v','1','-c:v','png','-f','image2pipe','-'])
    if not raw:raise ValueError('Empty source')
    sky=(ROOT/'assets/stages/sauce_sky_halftone_1536x864.webp').read_bytes()
    uri=lambda b,m:'data:image/'+m+';base64,'+base64.b64encode(b).decode()
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True,executable_path='/opt/devmcp-browsers/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader'])
        page=b.new_page();page.set_content((ROOT/'assets/shaders/optical-cover-study.html').read_text())
        renderer=page.evaluate('window.renderer')
        for black,name in ((True,'black'),(False,'cloud')):
            png=page.evaluate('async d=>window.study(d[0],d[1],d[2])',[uri(raw,'png'),uri(sky,'webp'),black])
            (x.out/(name+'.png')).write_bytes(base64.b64decode(png.split(',',1)[1]))
        b.close()
    (x.out/'receipt.json').write_text(json.dumps({'renderer':renderer,'sourceSha256':x.sha256,'at':x.at,'researchOnly':True,'ownerApproved':False},indent=2))
if __name__=='__main__':main()
