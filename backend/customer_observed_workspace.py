"""Observe actual browser-local workspace controls without requiring ARIA widgets.

The director chooses observed IDs. Local-only statements, exact UI identity,
visible preview geometry and the existing public network guard are required.
No text entry, submissions, arbitrary coordinates or external actions.
"""
import re
from backend.curious_sequence import safe_label,assert_local

SCAN=r'''(pick)=>{
 const blocked='form,a[href],nav,[role=navigation],[role=dialog],[inert],[data-private],[data-secret],[data-sensitive]';
 const norm=s=>(s||'').trim().replace(/\s+/g,' ');
 const text=e=>norm(e.getAttribute('aria-label')||e.innerText||e.getAttribute('title'));
 const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
 const inside=r=>r.x>=0&&r.y>=0&&r.x+r.width<=innerWidth+1&&r.y+r.height<=innerHeight+1;
 const hit=e=>{const r=rect(e),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return inside(r)&&h&&(h===e||e.contains(h))};
 const local=/nothing (?:leaves|is uploaded)|(?:runs?|works?|processed|processing|stays?) (?:entirely |fully |locally )?(?:in|on|inside) your browser|(?:client.side|browser.local|local.only)/i;
 const purpose=/^(?:(?:chart|graph|visualization|diagram|plot)\s+(?:type|style|mode)|(?:view|display|layout|palette|theme|appearance|style|orientation|visualization|chart type)(?:\s+(?:mode|type|options))?)$/i;
 const risky=/\b(?:save|apply|run|execute|start|stop|enable|disable|sync|install|import|export|copy|paste|open|close|settings|more|next|back|randomize|generate|create|new|edit|manage|delete|remove|clear|reset|share|send|buy|pay|login|sign|account)\b/i;
 const rows=[],hits=[],seen=new Set();
 const roots=[...document.querySelectorAll('main,[role=main]')];
 for(const root of roots){
  if(!local.test(root.innerText.slice(0,16000)))continue;
  for(const b of [...root.querySelectorAll('button[type=button]:not(:disabled)')].slice(0,150)){
   if(b.closest(blocked)||b.form)continue;
   let g=b.parentElement;
   for(let j=0;g&&j<3;j++,g=g.parentElement){
    const buttons=[...g.querySelectorAll('button[type=button]')];
    if(buttons.length<2||buttons.length>24)continue;
    if(seen.has(g))break;seen.add(g);
    const group=g.parentElement;
    if(!group||group.closest(blocked))break;
    const headings=[...group.children].filter(e=>e!==g&&!e.querySelector('button,input,textarea,select')&&!e.matches('button,input,textarea,select')).map(text).filter(t=>purpose.test(t));
    const title=norm(g.getAttribute('aria-label')||group.getAttribute('aria-label')||headings[0]);
    if(!purpose.test(title))break;
    const all=buttons.map(text);if(all.some(t=>!t)||new Set(all).size!==all.length)break;
    let workspace=group.parentElement,preview=null,graphic=null;
    for(let n=0;workspace&&n<5&&workspace!==root.parentElement;n++,workspace=workspace.parentElement){
     const r=rect(workspace);if(r.width<420||r.width>innerWidth||r.height>innerHeight*.92||r.height<250)continue;
     if(!local.test(workspace.innerText.slice(0,8000)))continue;
     const markers=[...workspace.querySelectorAll('span,h1,h2,h3,h4,label,div,p')].filter(e=>e.children.length===0&&/^(live preview|preview|result|output|visualization)$/i.test(text(e)));
     if(markers.length!==1)continue;
     for(let p=markers[0].parentElement,i=0;p&&i<5&&p!==workspace;i++,p=p.parentElement){
      const pics=[...p.querySelectorAll('svg,canvas,img')].filter(e=>{const q=rect(e);return q.width>=300&&q.height>=180&&!e.closest(blocked)&&e.checkVisibility()});
      if(pics.length!==1||p.contains(g))continue;
      const pr=rect(pics[0]);if(pr.width*pr.height<innerWidth*innerHeight*.09)continue;
      preview=text(markers[0]);graphic=pics[0];break;
     }
     if(graphic)break;
    }
    if(!graphic||!workspace)break;
    const surface=rect(workspace),result=rect(graphic),key=JSON.stringify([title,preview,all]);
    for(const e of buttons){const label=text(e);if(!label||risky.test(label)||e.form||e.closest(blocked)||e.disabled||e.getAttribute('aria-disabled')==='true')continue;
     const row={key:JSON.stringify([key,label]),workspace:key,group:title,label,surface,result,visible:hit(e),resultVisible:inside(result)&&graphic.checkVisibility()};
     rows.push(row);if(pick===row.key&&row.visible&&row.resultVisible)hits.push(e);
    }
    break;
   }
  }
 }
 return pick?(hits.length===1?hits[0]:null):rows;
}'''

def scan(page):
    rows=page.evaluate(SCAN,None)
    return [r for r in rows if safe_label(r['label']) and safe_label(r['group']) and sum(x['key']==r['key'] for x in rows)==1]

def prepare(page,url,setup=None):
    rows=scan(page)
    groups={r['workspace'] for r in rows}
    if setup:groups&={setup['workspace']}
    eligible=[k for k in groups if sum(r['workspace']==k for r in rows)>=2]
    if not eligible:return None
    key=max(sorted(eligible),key=lambda k:next(r['result']['width']*r['result']['height'] for r in rows if r['workspace']==k))
    row=next(r for r in rows if r['workspace']==key);box=row['surface'];v=page.viewport_size
    shift=round(box['y']-(v['height']-box['height'])/2)
    if abs(shift)>6000:return None
    old=page.evaluate('()=>scrollY')
    page.evaluate('(dy)=>window.scrollBy({top:dy,behavior:"instant"})',shift);page.wait_for_timeout(500);assert_local(page,url)
    state={'kind':'observed-workspace','workspace':key}
    if len(catalog(page,state))<2:
        page.evaluate('(y)=>window.scrollTo({top:y,behavior:"instant"})',old);assert_local(page,url);return None
    return state

def catalog(page,setup):
    return [{'id':f'ow{i}','kind':'option','control':'observed-workspace','group':r['group'],'label':r['label'],'key':r['key'],'workspace':r['workspace'],'source_context':'browser-local preview comparison'} for i,r in enumerate(scan(page)) if r['workspace']==setup['workspace'] and r['visible'] and r['resultVisible']]

def observed(page,key):
    rows=[r for r in scan(page) if r['key']==key and r['visible'] and r['resultVisible']]
    if len(rows)!=1:raise ValueError('Observed local control or preview unavailable')
    return rows[0]

def locate(page,action):
    r=observed(page,action['key'])
    if any(r[k]!=action[k] for k in ('label','group','workspace')):raise ValueError('Observed local control identity changed')
    h=page.evaluate_handle(SCAN,action['key']).as_element()
    if h is None:raise ValueError('Observed local control obstructed')
    return h

def result_region(page,key):
    r=observed(page,key);b=r['result']
    return {'x':round(b['x']),'y':round(b['y']),'width':round(b['width']),'height':round(b['height']),'workspace_key':key}

def apply(page,url,action,click):
    click(locate(page,action),action['label']);assert_local(page,url)


def aperture_region(page,setup):
    """Full observed workspace, not the preview graphic alone."""
    rows=[r for r in scan(page) if r['workspace']==setup['workspace'] and r['visible'] and r['resultVisible']]
    if not rows:return None
    base=rows[0]['surface'];v=page.viewport_size
    if any(r['surface']!=base for r in rows) or not v:return None
    if not (0<=base['x']<base['x']+base['width']<=v['width']+1 and 0<=base['y']<base['y']+base['height']<=v['height']+1):return None
    return base
