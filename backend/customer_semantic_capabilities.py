"""Bounded public read-only capabilities discovered from native ARIA contracts.

Models select observed IDs only. No guessed targets or arbitrary button clicks.
"""
import re
from backend.curious_sequence import safe_label,assert_local

SCAN=r'''(pick)=>{
 const blocked='form,a[href],nav,[role=navigation],[role=dialog],[inert],[data-private],[data-secret],[data-sensitive]';
 const text=e=>(e.getAttribute('aria-label')||e.innerText||'').trim().replace(/\s+/g,' ');
 const rect=e=>{let r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
 const visible=e=>{let r=rect(e),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return r.width>=8&&r.height>=8&&r.x>=0&&r.y>=0&&r.x+r.width<=innerWidth&&r.y+r.height<=innerHeight&&h&&e.contains(h)};
 const button=e=>e.matches('button:not([type=submit]):not(:disabled)')&&!e.form&&!e.closest(blocked)&&e.getAttribute('aria-disabled')!=='true'&&visible(e);
 const result=e=>{let r=rect(e);return !e.closest(blocked)&&!e.querySelector('form,input[type=password],[contenteditable=true],[data-private],[data-secret],[data-sensitive]')&&r.x>=0&&r.y>=0&&r.x+r.width<=innerWidth+1&&r.y+r.height<=innerHeight+1&&r.width*r.height>=innerWidth*innerHeight*.18&&visible(e)};
 const rows=[],hits=[];
 const add=(row,e)=>{rows.push(row);if(pick&&row.key===pick)hits.push(e)};
 for(const t of [...document.querySelectorAll('main table, [role=main] table, main [role=table]')].slice(0,20)){
  const name=(t.getAttribute('aria-label')||t.querySelector('caption')?.innerText||'').trim().replace(/\s+/g,' ');
  const body=t.querySelector('tbody,[role=rowgroup]:last-child');if(!name||!body||!result(body))continue;
  const headers=[...t.querySelectorAll('thead th,[role=columnheader]')];if(!headers.some(h=>['none','ascending','descending'].includes(h.getAttribute('aria-sort'))))continue;
  const data=[...body.querySelectorAll('tr,[role=row]')].map(r=>r.innerText.trim().replace(/\s+/g,' ')).filter(Boolean);
  if(data.length<3||data.length>200)continue;
  for(const h of headers){const bs=[...h.querySelectorAll('button')];if(bs.length!==1||!button(bs[0]))continue;
   const b=bs[0],label=text(b),state=h.getAttribute('aria-sort')||'none';
   if(!label||!['none','ascending','descending'].includes(state))continue;
   add({key:JSON.stringify(['sort',name,label]),surface:JSON.stringify(['table',name]),name,label,group:'Sort: '+label,verb:'sort',state,rect:rect(body),data},b);
  }
 }
 for(const b of [...document.querySelectorAll('main button[aria-pressed][aria-controls], [role=main] button[aria-pressed][aria-controls]')].slice(0,60)){
  if(!button(b))continue;const label=text(b),state=b.getAttribute('aria-pressed'),id=b.getAttribute('aria-controls');
  if(!/^(show|hide|toggle|switch|view)\b/i.test(label)||!['true','false'].includes(state)||!id||id.includes(' '))continue;
  const targets=[...document.querySelectorAll('[id]')].filter(x=>x.id===id);if(targets.length!==1)continue;
  const t=targets[0];if(!result(t)||t.contains(b))continue;
  const name=(t.getAttribute('aria-label')||t.querySelector('h1,h2,h3,h4')?.innerText||'').trim().replace(/\s+/g,' ');if(!name)continue;
  add({key:JSON.stringify(['toggle',id,label]),surface:JSON.stringify(['region',id]),label,group:'View: '+label,verb:'toggle',state,rect:rect(t),name},b);
 }
 return pick?(hits.length===1?hits[0]:null):rows;
}'''

def scan(page):
    rows=page.evaluate(SCAN,None)
    return [r for r in rows if safe_label(r['label']) and safe_label(r['group']) and safe_label(r.get('name',r['label'])) and sum(x['key']==r['key'] for x in rows)==1]

def catalog(page):
    return [{'id':f'cap{i}','kind':'option','control':'semantic-capability','key':r['key'],'surface':r['surface'],'group':r['group'],'label':r['label'],'verb':r['verb']} for i,r in enumerate(scan(page)[:24])]

def observed(page,key):
    rows=[r for r in scan(page) if r['key']==key]
    if len(rows)!=1:raise ValueError('Semantic capability identity changed')
    return rows[0]

def locate(page,action):
    r=observed(page,action['key'])
    if any(r[k]!=action[k] for k in ('label','surface','verb','group')):raise ValueError('Semantic capability mismatch')
    h=page.evaluate_handle(SCAN,action['key']).as_element()
    if h is None:raise ValueError('Semantic capability obstructed')
    return h

def result_region(page,key):
    r=observed(page,key)
    return {**r['rect'],'semantic_key':key}

def apply(page,url,action,click):
    before=observed(page,action['key']);click(locate(page,action),action['label']);assert_local(page,url)
    after=observed(page,action['key'])
    if before['state']==after['state']:raise ValueError('Semantic state not changed')
    if before['verb']=='sort':
        if after['state'] not in ('ascending','descending') or before['data']==after['data'] or sorted(before['data'])!=sorted(after['data']):raise ValueError('Not a witnessed row reordering')
