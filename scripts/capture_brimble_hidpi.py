#!/usr/bin/env python3
"""Capture real Brimble states as device-pixel PNG keyframes; no login or fake UI.

Three verified states at the same CSS viewport and 2x device pixel ratio.
Screenshot capture happens off the video clock, so layout and font fidelity
are independent of recording/encoding throughput.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,os,hashlib
P=Path(__file__).resolve().parents[1]/"studio"/".tmp"/"landscape-hidpi"
P.mkdir(parents=True,exist_ok=True)
CHROME=os.environ.get("SAUCE_CHROME_BIN","/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell")
manifest={"source":"https://www.brimble.io/","cssViewport":{"width":1600,"height":900},
 "deviceScaleFactor":2,"states":{}}
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,executable_path=CHROME,args=["--no-sandbox","--disable-dev-shm-usage"])
 c=b.new_context(viewport={"width":1600,"height":900},device_scale_factor=2,
                 color_scheme="light",reduced_motion="reduce",
                 permissions=["clipboard-read","clipboard-write"])
 page=c.new_page()
 response=page.goto("https://www.brimble.io/",wait_until="domcontentloaded",timeout=35000)
 if response is None or response.status>=400:raise RuntimeError("Bad response from real website")
 page.wait_for_timeout(2000)
 btn=page.get_by_role("button",name="Connect your agent",exact=True)
 btn.wait_for(state="visible",timeout=15000)
 def snap(name,proof):
  file=P/(name+".png")
  page.screenshot(path=str(file),scale="device",animations="disabled",timeout=20000)
  from PIL import Image
  im=Image.open(file)
  if im.size!=(3200,1800):raise RuntimeError("Unexpected screenshot dimensions "+str(im.size))
  digest=hashlib.sha256(file.read_bytes()).hexdigest()
  manifest["states"][name]={"file":str(file),"proof":proof,
   "sha256":digest,"bytes":file.stat().st_size,"size":list(im.size)}
  print("STATE",name,im.size,file.stat().st_size,proof,flush=True)
 # Match the real capture's scroll geometry rather than rebuilding HTML.
 btn.evaluate("(e)=>{const y=e.getBoundingClientRect().top+window.scrollY-400;window.scrollTo({top:y,behavior:'instant'})}")
 page.wait_for_timeout(500)
 print("SCROLL",page.evaluate("window.scrollY"),"BUTTON",btn.bounding_box(),flush=True)
 snap("01-agent-section",{"url":page.url,"buttonBox":btn.bounding_box(),
                           "title":page.title(),"scrollY":page.evaluate("window.scrollY")})
 btn.click()
 dlg=page.get_by_role("dialog")
 dlg.wait_for(state="visible",timeout=8000)
 page.wait_for_timeout(400)
 choices=dlg.inner_text()
 if "Claude Code" not in choices or "Codex" not in choices:raise RuntimeError("Actual agent choice dialog missing")
 snap("02-agent-picker",{"dialogBox":dlg.bounding_box(),"containsCodex":True})
 dlg.get_by_text("Codex",exact=True).click()
 page.get_by_text("Copied. Paste it into your terminal",exact=False).wait_for(state="visible",timeout=6000)
 page.wait_for_timeout(350)
 command=page.evaluate("navigator.clipboard.readText()")
 expected="codex mcp add brimble --url https://mcp.brimble.io && codex mcp login brimble"
 if command!=expected:raise RuntimeError("Clipboard verification mismatch")
 snap("03-command-copied",{"dialogBox":dlg.bounding_box(),
      "copyConfirmed":True,"clipboard":command})
 manifest["verified"]=True
 (P/"manifest.json").write_text(json.dumps(manifest,indent=2))
 print("DONE",P/"manifest.json")
 b.close()
