from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess,os,time,json
P=Path('studio/.tmp/film-05');P.mkdir(parents=True,exist_ok=True)
W,H,FPS=1600,900,60
xv=subprocess.Popen(['Xvfb',os.environ.get('SAUCE_DISPLAY',':98'),'-screen','0','1600x900x24','-nolisten','tcp','-ac'],stdout=(P/'xvfb.log').open('w'),stderr=subprocess.STDOUT)
time.sleep(.7)
if xv.poll() is not None:raise RuntimeError('Display failed')
os.environ['DISPLAY']=os.environ.get('SAUCE_DISPLAY',':98')
events=[];pointer=[]
start=None
def now():return round(time.monotonic()-start,3) if start else 0
def until(t):
 while now()<t:time.sleep(.015)
try:
 with sync_playwright() as pw:
  gui=os.environ.get('SAUCE_CHROME_BIN','studio/.tmp/educational-pilot/browsers/chromium-1254/chrome-linux64/chrome')
  ctx=pw.chromium.launch_persistent_context(str(P/('profile-'+str(int(time.time())))),headless=False,executable_path=str(Path(gui).resolve()),viewport={'width':1600,'height':900},
    args=['--no-sandbox','--window-position=0,0','--window-size=1600,900','--app=https://www.brimble.io/'])
  pg=ctx.pages[0]
  pg.goto('https://www.brimble.io/',wait_until='domcontentloaded',timeout=30000)
  pg.wait_for_timeout(950)
  x,y=1350.,700.
  def m(nx,ny):
   global x,y
   pg.mouse.move(nx,ny);x,y=nx,ny
   pointer.append([now(),round(nx,2),round(ny,2)])
  def glide(nx,ny,seconds):
   sx,sy=x,y;beg=time.monotonic()
   for i in range(1,max(5,int(seconds*60))+1):
    u=i/max(5,int(seconds*60));k=u*u*(3-2*u)
    m(sx+(nx-sx)*k,sy+(ny-sy)*k)
    time.sleep(max(0,beg+seconds*u-time.monotonic()))
  m(x,y)
  record=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','x11grab','-draw_mouse','0','-video_size','1600x900','-framerate','60','-i',os.environ['DISPLAY'],
    '-t','15.5','-c:v','libx264','-preset','veryfast','-crf','15','-pix_fmt','yuv420p','-threads','6',str(P/'capture.mp4')],
    stdin=subprocess.DEVNULL,stderr=(P/'capture.log').open('w'))
  time.sleep(.3);start=time.monotonic()
  until(1.9)
  btn=pg.get_by_role('button',name='Connect your agent')
  btn.evaluate("(e)=>window.scrollTo({top:window.scrollY+e.getBoundingClientRect().top-400,behavior:'smooth'})")
  until(3.75)
  box=btn.bounding_box()
  if not box or not 0<box['y']<800:raise RuntimeError('Connect button not visible: '+str(box))
  glide(box['x']+box['width']/2,box['y']+box['height']/2,.64)
  until(4.9);pg.mouse.down();pg.mouse.up()
  dlg=pg.get_by_role('dialog');dlg.wait_for(state='visible')
  events.append({'t':now(),'action':'connect-modal-visible','rect':dlg.bounding_box()})
  until(6.4)
  option=dlg.get_by_text('Codex',exact=True);option.wait_for(state='visible')
  ob=option.bounding_box()
  glide(ob['x']+25,ob['y']+ob['height']/2,.73)
  until(7.7);pg.mouse.down();pg.mouse.up()
  pg.get_by_text('Copied. Paste it into your terminal',exact=False).wait_for(state='visible')
  events.append({'t':now(),'action':'setup-command-visible'})
  until(9.1)
  cp=dlg.get_by_role('button',name='Copy')
  if cp.count():
   cr=cp.bounding_box();glide(cr['x']+cr['width']/2,cr['y']+cr['height']/2,.73)
   until(10.15);pg.mouse.down();pg.mouse.up()
   events.append({'t':now(),'action':'copy-confirmation'})
  until(14.9)
  record.wait(timeout=35)
  pg.screenshot(path=str(P/'verified-state.png'))
  (P/'capture-events.json').write_text(json.dumps({'url':'https://www.brimble.io/','events':events,'pointer':pointer,'seconds':15.5,
    'verification':'Real public product; copied setup command shown. No authenticated connection or deployment.'},indent=2))
  print('CAPTURE',str(P/'capture.mp4'),'EVENTS',events,'CURSOR_SAMPLES',len(pointer))
  ctx.close()
finally:
 xv.terminate()
