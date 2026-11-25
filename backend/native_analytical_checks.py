"""Batched guarded DOM reads for the native long-story clock."""
from backend.curious_sequence import analytic_name,analytic_option,assert_local

# Each query preserves observed identity and rejects sensitive descendants.
PRELUDE=r"""
 const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility==='visible'&&s.display!=='none'&&+s.opacity>0};
 const safe=e=>!e.disabled&&!e.closest('form,a[href],[data-private],[data-secret],[data-sensitive],[inert]');
 const triggers=()=>[...document.querySelectorAll('button[type=button][aria-label="Date range"][aria-haspopup=dialog]')].filter(e=>visible(e)&&safe(e)&&e.getAttribute('aria-expanded')!=='true');
 const dialogs=()=>[...document.querySelectorAll('[role=dialog]')].filter(visible);
 const norm=e=>(e.innerText||'').trim().replace(/\s+/g,' ');
"""
def batch_panels(page):
    return page.evaluate("()=>{"+PRELUDE+r"""
      const rows=[];
      const read=(e,id)=>{let r=e.getBoundingClientRect();if(id&&e.checkVisibility()&&!e.closest('form,[data-private],[data-secret],[data-sensitive]')&&r.x>=0&&r.y>=0&&r.width>=100&&r.height>=100&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1)rows.push({id,x:r.x,y:r.y,width:r.width,height:r.height});};
      for(const e of document.querySelectorAll('[role=tabpanel]'))read(e,e.id);
      if(triggers().length===1){
        const regions=[...document.querySelectorAll('main section[aria-label],main [role=region][aria-label]')];
        for(const e of regions){
          const label=e.getAttribute('aria-label');
          if(label&&regions.filter(x=>x.getAttribute('aria-label')===label).length===1)read(e,'region:'+label);
        }
      }
      return rows;
    }""")

def apply_preset(page,url,picker,label,click):
    if not analytic_name(picker) or not analytic_option(picker,label):raise ValueError("Unrecognized analytical preset")
    assert_local(page,url)
    trigger=page.evaluate_handle("()=>{"+PRELUDE+"const a=triggers();return !dialogs().length&&a.length===1?a[0]:null;}").as_element()
    if trigger is None:raise ValueError("Observed analytical trigger missing or ambiguous")
    click(trigger,None)
    page.locator('[role=dialog]:visible').first.wait_for(state="visible",timeout=3500)
    assert_local(page,url)
    option=page.evaluate_handle("label=>{"+PRELUDE+r"""
      const d=dialogs();
      if(d.length!==1||d[0].querySelector('form,input,textarea,a[href],[data-private],[data-secret],[data-sensitive]'))return null;
      const options=[...d[0].querySelectorAll('button[type=button][role=option][aria-selected=false]:not([aria-disabled=true])')].filter(e=>visible(e)&&safe(e)&&norm(e)===label);
      return options.length===1?options[0]:null;
    }""",label).as_element()
    if option is None:raise ValueError("Ambiguous, sensitive or missing analytical preset")
    # Pin the exact DOM popup before the click. Re-reading a changing
    # locator count twice races the framework's close animation.
    original=option.evaluate_handle("e=>e.closest('[role=dialog]')").as_element()
    if original is None:raise ValueError("Analytical popup identity missing")
    click(option,label)
    from playwright.sync_api import TimeoutError as BrowserTimeout, Error as BrowserError
    closed="original=>{"+PRELUDE+"""
      const current=dialogs();
      if(current.some(e=>e!==original))throw new Error('Unexpected dialog after analytical action');
      return current.length===0;
    }"""
    try:
        page.wait_for_function(closed,arg=original,timeout=3500,polling=50)
    except BrowserTimeout as exc:
        raise ValueError("Original analytical dialog did not close") from exc
    except BrowserError as exc:
        raise ValueError("Unexpected dialog after analytical action") from exc
    assert_local(page,url)
    predicate="label=>{"+PRELUDE+"const a=triggers();return !dialogs().length&&a.length===1&&norm(a[0])===label;}"
    # Native physical dispatch is asynchronous with the application's state
    # update. Never mistake an old label for a failed or successful action.
    try:page.wait_for_function(predicate,arg=label,timeout=3500,polling=100)
    except BrowserTimeout as exc:raise ValueError("Applied analytical preset does not match observed option") from exc
    assert_local(page,url)
    return picker
