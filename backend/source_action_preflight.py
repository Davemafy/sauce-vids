"""Opt-in source-outcome probe for a safe public-site Sauce action.

Existing selector preflight checks whether a control exists. This probe checks
whether a *real* interaction visibly changes the actual page, before spending
resources on motion capture and final video encoding. Never confuses visible
change with premium-film approval; human direction remains mandatory.

Requires a selected control from product_explorer.inspect(). No raw DOM
contents or screenshots appear in public release receipts.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from scripts.capture_safety import validate_public_url, guard_route

WIDTH, HEIGHT = 320, 180
MASK_THRESHOLD = 25
MIN_DOM_VISIBLE_DELTA = .006
MIN_GRAPHIC_DELTA = .065


def image_change(before: np.ndarray, after: np.ndarray) -> float:
    if (before is None or after is None or
        before.shape != after.shape or before.ndim != 3 or
        before.shape[2] != 3 or before.dtype != np.uint8 or
        after.dtype != np.uint8):
        raise ValueError("Need paired decoded images from the same real browser viewport")
    a = cv2.GaussianBlur(cv2.resize(before, (WIDTH,HEIGHT)),(3,3),0)
    b = cv2.GaussianBlur(cv2.resize(after,(WIDTH,HEIGHT)),(3,3),0)
    return float(np.mean(np.max(cv2.absdiff(a,b),axis=2)>MASK_THRESHOLD))


def classify_visible_outcome(before: np.ndarray, stable: np.ndarray,
                             after: np.ndarray, before_dom: dict,
                             after_dom: dict) -> dict:
    """Movement is evidence, not a cinematic score or semantic outcome guarantee."""
    baseline=image_change(before,stable)
    changed=image_change(stable,after)
    change_above_baseline=max(0.,changed-1.3*baseline)
    # Fingerprints must be of *visible, nonprivate* text/UI states.
    dom=bool(
      before_dom.get('visible_content_hash') != after_dom.get('visible_content_hash')
      or before_dom.get('dialog_count') != after_dom.get('dialog_count')
      or before_dom.get('aria_controls_hash') != after_dom.get('aria_controls_hash')
      or before_dom.get('url_path') != after_dom.get('url_path'))
    verified=(change_above_baseline >= (MIN_DOM_VISIBLE_DELTA if dom else MIN_GRAPHIC_DELTA))
    return {
      'schema':'sauce-source-action-preflight-v1',
      'decision':'visible_outcome_candidate' if verified else 'no_proven_visible_outcome',
      'baseline_change_fraction':round(baseline,5),
      'post_action_change_fraction':round(changed,5),
      'change_above_baseline':round(change_above_baseline,5),
      'observable_dom_change':dom,
      'human_film_approval':False,
      'first_three_seconds_review_required':True,
      'scope':'Actual public UI change only; not a product-value or artistic score'
    }


FINGERPRINT_JS="""() => {
 const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);
   return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'};
 const text=[...document.querySelectorAll('main,[role=dialog],[role=tabpanel]')]
     .filter(visible).map(e=>(e.innerText||'').slice(0,8000)).join(' ').slice(0,9000)
     ||document.body.innerText.slice(0,9000);
 const attr=[...document.querySelectorAll('[aria-expanded],[aria-selected],[aria-checked]')]
     .filter(visible).map(e=>[e.getAttribute('aria-expanded'),e.getAttribute('aria-selected'),
                             e.getAttribute('aria-checked')].join(':')).join('|').slice(0,10000);
 const url=location.pathname;
 return {text,attr,dialog_count:[...document.querySelectorAll('[role=dialog]')].filter(visible).length,url_path:url};
}"""


def _fingerprint(state: dict) -> dict:
    """Return hashed UI state only; do not write page text into receipts."""
    return {
        'visible_content_hash':hashlib.sha256(state['text'].encode('utf-8')).hexdigest(),
        'aria_controls_hash':hashlib.sha256(state['attr'].encode('utf-8')).hexdigest(),
        'dialog_count':int(state['dialog_count']),
        'url_path':str(state['url_path'])[:256],
    }


def viewport_shift_px(before_scroll:dict,after_scroll:dict,
                      before_box:dict,after_box:dict)->float:
    """Fail closed if the camera moved, rather than scoring page travel as payoff.

    Supports window scrolling and a selected control in a nested scroller.
    A disappearing target may be legitimate (e.g. after state change), but
    cannot serve as independent proof of an unchanged viewport.
    """
    if any(not isinstance(x,dict) for x in
           (before_scroll,after_scroll,before_box,after_box)):
        raise ValueError('Cannot prove stable action viewport')
    try:
        diffs=[abs(float(before_scroll[a])-float(after_scroll[a]))
               for a in ('x','y')]
        diffs.extend(abs(float(before_box[a])-float(after_box[a]))
                     for a in ('x','y'))
    except (KeyError,ValueError,TypeError) as exc:
        raise ValueError('Missing measured source viewport geometry') from exc
    if not all(np.isfinite(d) for d in diffs):
        raise ValueError('Nonfinite measured viewport shift')
    return max(diffs)


def measured_result_region(before:np.ndarray,after:np.ndarray,
                           box:dict|None)->dict:
    """Measure actual new DOM-owned result, not full-screen modal backdrop.

    The supplied rectangle must be obtained from a visible real browser node
    AFTER the action. The metric alone is not an aesthetic endorsement.
    """
    if not isinstance(box,dict):
        return {'result_area_fraction':0.0,'changed_result_fraction':0.0,
                'result_rect':None}
    if before.shape!=after.shape or before.ndim!=3:
        raise ValueError('Result region source frame shapes do not match')
    H,W=before.shape[:2]
    try:
        x,y,w,h=[float(box[k]) for k in ('x','y','width','height')]
    except (KeyError,ValueError,TypeError) as exc:
        raise ValueError('Invalid browser result rectangle') from exc
    if (not np.isfinite([x,y,w,h]).all()
        or min(w,h)<8 or x<0 or y<0 or x+w>W+1 or y+h>H+1):
        raise ValueError('Result box was not fully visible in browser source')
    a=max(0,int(np.floor(x)));b=max(a+1,min(W,int(np.ceil(x+w))))
    c=max(0,int(np.floor(y)));d=max(c+1,min(H,int(np.ceil(y+h))))
    changed=image_change(before[c:d,a:b,:],after[c:d,a:b,:])
    return {'result_area_fraction':round(float((w*h)/(W*H)),5),
            'changed_result_fraction':round(changed,5),
            'result_rect':{k:round(float(box[k]),2) for k in
                           ('x','y','width','height')}}


def visible_result_box(page,control):
    """Read a genuine visible result container, never guess a pretty crop."""
    selectors=['[role="dialog"]','dialog[open]','[role="tabpanel"]']
    aria=page.locator(control['selector']).get_attribute('aria-controls')
    if aria and all(v.isalnum() or v in ('-','_') for v in aria):
        selectors.append('[id="'+aria+'"]')
    for css in selectors:
        matches=page.locator(css)
        for i in range(min(8,matches.count())):
            node=matches.nth(i)
            if node.is_visible():
                box=node.bounding_box()
                if box and box['width']>=48 and box['height']>=36:
                    return box
    return None


def probe_public_action(url: str, report: dict, control_id: str,
                        private_dir: Path, *, browser_executable: str | None = None) -> dict:
    """Trigger one preapproved, non-submitting action in a disposable browser.

    Sensitive forms, cross-origin links, login and paid actions are excluded
    by product_explorer.allowed() plus per-control rechecks.
    """
    from playwright.sync_api import sync_playwright
    from backend.product_explorer import CHROME, allowed, known_dialog_opener
    validate_public_url(url)
    if not isinstance(control_id,str) or not control_id:
        raise ValueError('Missing selected public control')
    controls=[c for c in report.get('controls',[])
              if isinstance(c,dict) and c.get('id')==control_id]
    if len(controls)!=1:
        raise ValueError('Unobserved public action')
    c=controls[0]
    if not allowed(c,report.get('url',url)):
        raise ValueError('Disallowed or sensitive public action')
    if c.get('kind') not in ('tab','button','link'):
        return {'schema':'sauce-source-action-preflight-v1',
                'decision':'unsupported_action_requires_separate_verification',
                'reason':'Non-click gestures require their own real drag/canvas evidence',
                'human_film_approval':False}
    if c.get('in_form') is not False and c.get('kind')!='link':
        raise ValueError('Will not click controls from forms')
    if (c.get('kind')=='button' and
        not known_dialog_opener(c,report.get('url',url)) and
        (c.get('button_type')=='submit' or
         (c.get('controlled_panel') is not True and
          not c.get('text','').strip()))):
        raise ValueError('No verified safe button behavior')
    private_dir=Path(private_dir)
    private_dir.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True,
             executable_path=browser_executable or CHROME,
             args=['--no-sandbox','--disable-dev-shm-usage'])
        try:
            context=b.new_context(viewport={'width':1280,'height':720},
                                  service_workers='block')
            context.route('**/*',guard_route)
            page=context.new_page()
            response=page.goto(url,wait_until='domcontentloaded',timeout=28000)
            if response and response.status>=400:
                raise RuntimeError('Original public site was not accessible')
            validate_public_url(page.url)
            page.wait_for_timeout(550)
            locator=page.locator(c['selector'])
            if locator.count()!=1 or not locator.is_visible():
                raise ValueError('Originally selected public control no longer exists')
            # FIRST bring the actual source control into the recorded
            # viewport. Otherwise playwright.click() scrolls to it and the
            # pixel-delta score wrongly calls that travel a product payoff.
            locator.scroll_into_view_if_needed(timeout=4200)
            page.wait_for_timeout(450)
            before_box=locator.bounding_box()
            before_scroll=page.evaluate('({x:scrollX,y:scrollY})')
            before_state=_fingerprint(page.evaluate(FINGERPRINT_JS))
            before=page.screenshot(type='png',animations='disabled')
            page.wait_for_timeout(360)
            stable=page.screenshot(type='png',animations='disabled')
            locator.click(timeout=4200)
            page.wait_for_timeout(750)
            validate_public_url(page.url)
            after_state=_fingerprint(page.evaluate(FINGERPRINT_JS))
            after_box=locator.bounding_box()
            after_scroll=page.evaluate('({x:scrollX,y:scrollY})')
            after=page.screenshot(type='png',animations='disabled')
            (private_dir/'before.png').write_bytes(before)
            (private_dir/'steady.png').write_bytes(stable)
            (private_dir/'after.png').write_bytes(after)
            arr=lambda blob:cv2.imdecode(np.frombuffer(blob,np.uint8),cv2.IMREAD_COLOR)
            proof=classify_visible_outcome(
                arr(before),arr(stable),arr(after),before_state,after_state)
            # If clicking changes the viewport geometry, these pixels are
            # ambiguous. Never launder scroll or large layout motion into an
            # independently proven UI-value claim.
            try:
                shift=viewport_shift_px(before_scroll,after_scroll,
                                        before_box,after_box)
            except ValueError:
                shift=float('inf')
            if shift>4:
                proof['decision']='viewport_shift_ambiguous'
                proof['reason']='Scroll/layout shift confounded visible product change'
            proof['viewport_shift_px']=round(shift,3) if np.isfinite(shift) else None
            # A full-screen gray modal backdrop is not 80% more useful
            # product content. Score only a browser-observed result container.
            proof.update(measured_result_region(arr(before),arr(after),
                                                 visible_result_box(page,c)))
            proof.update({
                'source_url':str(report.get('url',url)),
                'source_control_id':control_id,
                'control_kind':c['kind'],
                'before_sha256':hashlib.sha256(before).hexdigest(),
                'steady_sha256':hashlib.sha256(stable).hexdigest(),
                'after_sha256':hashlib.sha256(after).hexdigest(),
            })
            (private_dir/'outcome.json').write_text(json.dumps(proof,indent=2))
            return proof
        finally:
            b.close()
