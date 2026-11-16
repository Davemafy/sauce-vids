"""Explicitly capture a real, standalone public Brimble homepage insert.

This is a verified static insert. It does not become a fabricated trace event,
and the decorative bee remains visible in this brand/establishing frame.
"""
from __future__ import annotations
import argparse,hashlib,json,datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

URL='https://www.brimble.io/'
TARGET_HEADING='The cloud for AI agents'


def capture(out:Path,browser_binary:str|None=None)->dict:
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        binary=browser_binary or '/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell'
        browser=pw.chromium.launch(headless=True,executable_path=binary,
            args=['--no-sandbox','--disable-dev-shm-usage'])
        context=browser.new_context(viewport={'width':1280,'height':720},device_scale_factor=2,
            service_workers='block')
        page=context.new_page()
        response=page.goto(URL,wait_until='domcontentloaded',timeout=35000)
        if not response or response.status!=200:raise RuntimeError('Homepage not healthy')
        page.wait_for_timeout(1200)
        heading=page.locator('h1').first.inner_text().strip()
        if heading!=TARGET_HEADING:raise RuntimeError('Homepage did not match verified headline')
        page.evaluate('window.scrollTo({top:120,behavior:"instant"})')
        page.wait_for_timeout(500)
        image=out/'verified-hero.png'
        page.screenshot(path=str(image),scale='device',caret='hide',animations='disabled')
        if page.evaluate('window.scrollY')!=120:raise RuntimeError('Homepage scroll mismatch')
        image_bytes=image.read_bytes()
        report={'schema':'sauce-public-homepage-insert-v1',
                'url':URL,'heading':heading,'scroll_y_css':120,
                'viewport_css':[1280,720],'dpr':2,
                'source_sha256':hashlib.sha256(image_bytes).hexdigest(),
                'size_bytes':len(image_bytes),
                'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'notes':'Static source screenshot. Intentionally contains the real Brimble bee, not a cursor. Does not imply an interaction.'}
        (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        context.close();browser.close();return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(capture(args.out),indent=2))
