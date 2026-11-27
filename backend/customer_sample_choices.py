"""Public, explicitly sample-data comparisons with separate result pixels."""
from backend.curious_sequence import safe_label,assert_local

SCAN=r'''(pick)=>{
 const blocked='form,a[href],nav,[role=navigation],[inert],[data-private],[data-secret],[data-sensitive],[role=dialog]';
 const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
 const txt=e=>(e.getAttribute('aria-label')||e.innerText||'').trim().replace(/\s+/g,' ');
 const sample=/\b(sample|synthetic|fictional|simulated|invented|mock)\s+(data|numbers|dataset|records)\b/i;
 const visible=e=>{const r=rect(e),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return r.x>=0&&r.y>=0&&r.x+r.width<=innerWidth&&r.y+r.height<=innerHeight&&r.width>=8&&r.height>=8&&h&&e.contains(h)};
 const rows=[],hits=[],seen=new Set();
 for(const b of [...document.querySelectorAll('main button[aria-pressed]')].slice(0,100)){
  if(b.closest(blocked))continue;
  const g=b.parentElement;if(seen.has(g))continue;seen.add(g);
  const nodes=[...g.querySelectorAll('button[aria-pressed]')];
  if(nodes.length<3||nodes.length>12||nodes.some(n=>!n.checkVisibility()||n.closest(blocked)||n.form||n.disabled||n.getAttribute('type')==='submit'||n.getAttribute('aria-disabled')==='true'||!['true','false'].includes(n.getAttribute('aria-pressed'))))continue;
  const labels=nodes.map(txt);if(new Set(labels).size!==labels.length||nodes.filter(n=>n.getAttribute('aria-pressed')==='true').length!==1)continue;
  const section=g.closest('section,[role=region],main');if(!section||!sample.test(section.innerText.slice(0,16000)))continue;
  const name=(section.getAttribute('aria-label')||section.querySelector('h1,h2,h3,h4')?.innerText||'').trim().replace(/\s+/g,' ');if(!name||name.length>100)continue;
  const key=JSON.stringify([name,labels]),bounds=rect(g);let result=null,surface=null;
  for(let p=g.parentElement,j=0;p&&j<3&&p!==section.parentElement;p=p.parentElement,j++){
   if(p.closest(blocked)||p.querySelector('input,textarea,select,[contenteditable=true],form,[data-private],[data-secret],[data-sensitive]'))continue;
   const r=rect(p);if(r.width>innerWidth||r.height>innerHeight*.92||r.width<innerWidth*.25||r.height<innerHeight*.25||p.querySelectorAll('button[aria-pressed]').length!==nodes.length)continue;
   const x=r.x+8,y=r.y+8,right=r.x+r.width-8,bottom=r.y+r.height-8;
   const choices=[[x,bounds.y+bounds.height+8,right,bottom],[bounds.x+bounds.width+8,y,right,bottom],[x,y,bounds.x-8,bottom],[x,y,right,bounds.y-8]];
   const sorted=choices.filter(q=>q[2]>q[0]&&q[3]>q[1]).sort((a,b)=>(b[2]-b[0])*(b[3]-b[1])-(a[2]-a[0])*(a[3]-a[1]));
   if(!sorted.length)continue;const q=sorted[0];if((q[2]-q[0])*(q[3]-q[1])<innerWidth*innerHeight*.07)continue;
   result={x:q[0],y:q[1],width:q[2]-q[0],height:q[3]-q[1]};surface=r;break;
  }
  if(!result)continue;
  rows.push({key,name,surface,result,options:nodes.map(n=>({label:txt(n),selected:n.getAttribute('aria-pressed')==='true',visible:!!visible(n)}))});
  if(pick&&pick.key===key)hits.push(...nodes.filter(n=>txt(n)===pick.label&&n.getAttribute('aria-pressed')==='false'&&visible(n)));
 }
 return pick?(hits.length===1?hits[0]:null):rows;
}'''

def scan(page):
    rows=page.evaluate(SCAN,None)
    return [r for r in rows if safe_label(r['name']) and sum(x['key']==r['key'] for x in rows)==1 and sum(safe_label(x['label']) and not x['selected'] for x in r['options'])>=2]

def find(page,key):
    rows=[r for r in page.evaluate(SCAN,None) if r['key']==key and safe_label(r['name'])]
    return rows[0] if len(rows)==1 else None

def result_region(page,key):
    r=find(page,key);v=page.viewport_size
    if not r or not v:return None
    b=r['result'];s=r['surface']
    if not (0<=s['x'] and 0<=s['y'] and s['x']+s['width']<=v['width']+1 and s['y']+s['height']<=v['height']+1):return None
    return {**b,'sample_choice_key':key}

def prepare(page,url,setup=None):
    rows=scan(page)
    if setup:rows=[r for r in rows if r['key']==setup.get('key')]
    if not rows:return None
    r=max(rows,key=lambda a:a['result']['width']*a['result']['height']);s=r['surface'];v=page.viewport_size
    shift=round(s['y']-(v['height']-s['height'])/2)
    if abs(shift)>6000:return None
    old=page.evaluate('()=>scrollY')
    page.evaluate('(dy)=>window.scrollBy({top:dy,behavior:"instant"})',shift);page.wait_for_timeout(450);assert_local(page,url)
    if not result_region(page,r['key']):
        page.evaluate('(y)=>window.scrollTo({top:y,behavior:"instant"})',old);assert_local(page,url);return None
    return {'kind':'sample-choices','key':r['key']}

def catalog(page,setup):
    r=find(page,setup['key'])
    if not r or not result_region(page,r['key']):return []
    return [{'id':f'sc{i}','kind':'option','control':'sample-choice','group':r['name'],'label':o['label'],'key':r['key'],'source_context':'explicit sample-data comparison'} for i,o in enumerate(r['options']) if not o['selected'] and o['visible'] and safe_label(o['label'])]

def locate(page,action):
    if not safe_label(action['label']) or not result_region(page,action['key']):raise ValueError('Sample choice unavailable')
    h=page.evaluate_handle(SCAN,{'key':action['key'],'label':action['label']}).as_element()
    if h is None:raise ValueError('Sample choice not uniquely visible and inactive')
    return h

def apply(page,url,action,click):
    click(locate(page,action),action['label']);assert_local(page,url)
    r=find(page,action['key'])
    if not r or not any(x['label']==action['label'] and x['selected'] for x in r['options']):raise ValueError('Sample choice state not observed')
