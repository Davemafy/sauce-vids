"""Dependency-free Sauce session trace contract (safe for CI validation)."""
from __future__ import annotations
import hashlib
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit

SCHEMA='sauce.session.v1'
ALLOWED_ACTIONS=frozenset({'click','hover','move','approach','fill','scroll','wait'})


def safe_url(url:str)->str:
    p=urlsplit(url)
    if p.scheme not in ('https','http','file'):
        raise ValueError('Unsupported URL scheme')
    host=p.hostname or ''
    if p.scheme!='file' and not host:
        raise ValueError('HTTP URL missing host')
    return urlunsplit((p.scheme,host+((':'+str(p.port)) if p.port else ''),p.path,'',''))


def validate_actions(actions:list[dict]) -> None:
    if not isinstance(actions,list) or not actions:
        raise ValueError('Workflow must contain at least one action')
    for a in actions:
        if not isinstance(a,dict) or a.get('action') not in ALLOWED_ACTIONS:
            raise ValueError('Unsupported action: '+str(a))
        if a['action'] in ('click','hover','fill','approach') and not a.get('selector'):
            raise ValueError('Missing action selector')
        if a['action']=='fill' and a.get('secret'):
            raise ValueError('Sensitive values require a separate authorized input channel')
        selector=a.get('selector','')
        if not isinstance(selector,str) or len(selector)>300:
            raise ValueError('Invalid selector')
        for expected in ('expect_selector','expect_text'):
            if expected in a and (not isinstance(a[expected],str) or len(a[expected])>500):
                raise ValueError('Invalid expected state')
        if a['action']=='move':
            if 'x' not in a or 'y' not in a:
                raise ValueError('Move action missing coordinates')


def verify_package(session:dict,folder:Path)->dict:
    if session.get('schema')!=SCHEMA:
        raise ValueError('Unsupported Sauce session schema')
    info=session['page']
    width,height=info['viewport']
    if not(320<=width<=2560 and 240<=height<=1440 and 1<=info['dpr']<=3):
        raise ValueError('Invalid source dimensions')
    if safe_url(session['source_url'])!=session['source_url']:
        raise ValueError('Unsafe source URL')
    if not session.get('states') or not session.get('events'):
        raise ValueError('Missing source evidence')
    states=session['states']
    for state in states:
        filename=state['file']
        if not isinstance(filename,str) or Path(filename).name!=filename or not filename.endswith('.png'):
            raise ValueError('Unsafe screenshot path')
        src=(folder/'states'/filename)
        if not src.is_file():raise FileNotFoundError(src)
        if hashlib.sha256(src.read_bytes()).hexdigest()!=state['sha256']:
            raise ValueError('Screenshot hash mismatch: '+state['name'])
    events=session['events']
    if any(events[i+1]['t']<events[i]['t'] for i in range(len(events)-1)):
        raise ValueError('Nonmonotone event timestamps')
    workflow=session['workflow']
    if any('value' in item or 'password' in item or 'secret' in item for item in workflow):
        raise ValueError('Sensitive workflow value leaked into trace')
    validate_actions([{k:v for k,v in item.items() if k in ('action','selector','expect_text','expect_selector','x','y')}
                      for item in workflow])
    return info

def cursor_class(css:str|None)->str:
    """CSS cursor state used by the native glyph compositor."""
    if css=='none':return 'none'
    if css in ('pointer','grab','grabbing'):return 'pointer'
    if css in ('text','vertical-text'):return 'text'
    return 'default'
