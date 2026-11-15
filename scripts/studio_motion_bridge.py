"""Strict JSON bridge between TypeScript StudioMotion plan and Python video exporter.

Uses a compiled JS planner. The trace stays on stdin and is never uploaded.
New features are opt-in so legacy films and audio pipelines remain untouched.
"""
from __future__ import annotations
import json,subprocess,re
from pathlib import Path

SRC=Path(__file__).resolve().parent
BUNDLE=SRC/'studio-motion'/'dist'/'bridge.js'


def _enrich_events(session:dict)->list[dict]:
    """Build safe action labels from verified workflow selectors on older traces."""
    events=[dict(event) for event in session['events']]
    click_phases=[p for p in session.get('workflow',[]) if p.get('action')=='click']
    actions=[p for p in events if p.get('type')=='pointerdown']
    for event,phase in zip(actions,click_phases):
        selector=str(phase.get('selector',''))
        m=re.search(r'(?::has-text|:text-is)\(([\'"])([^\'"]{1,60})\1\)',selector)
        if not m or any(c in m.group(2).lower() for c in ('password','token','secret','api key')):
            continue
        # The label originates in the already verified Playwright selector.
        if selector.startswith('button'):
            event.setdefault('tag','button')
            event.setdefault('ariaLabel',m.group(2))
    return events


def plan_studio_motion(session:dict,duration_s:float,fps:int,config:dict)->dict:
    if not BUNDLE.is_file():
        raise RuntimeError('Missing StudioMotion JS bundle. Run: cd scripts/studio-motion && npm ci && npm run build')
    data={'events':_enrich_events(session),
          'startMs':session['states'][0]['at_ms'],
          'durationMs':duration_s*1000.,
          'fps':fps,
          'config':config}
    proc=subprocess.run(['node',str(BUNDLE)],input=json.dumps(data),
                        text=True,capture_output=True,timeout=18)
    if proc.returncode:
        raise RuntimeError('StudioMotion planner rejected trace: '+proc.stderr[:1000])
    report=json.loads(proc.stdout)
    if report.get('schema')!='sauce-studio-motion-v1':raise RuntimeError('Studio planner schema mismatch')
    frames=report.get('frameMap')
    if not frames or not isinstance(frames,list) or len(frames)>60000:
        raise RuntimeError('Invalid StudioMotion frame mapping')
    prev=-1
    for frame in frames:
        t=float(frame['sourceMs'])
        if not prev<t<=duration_s*1000+1e-3:raise RuntimeError('Time map not monotonic')
        prev=t
    if any(x.get('sourceStartMs',0)<0 for x in report['callouts']):
        raise RuntimeError('Invalid callout timestamp')
    return report
