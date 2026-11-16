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


def plan_studio_motion(session:dict,duration_s:float,fps:int,
                       config:dict,preset:str|None=None,
                       preset_overrides:dict|None=None,
                       session_dir:Path|None=None)->dict:
    if not BUNDLE.is_file():
        raise RuntimeError('Missing StudioMotion JS bundle. Run: cd scripts/studio-motion && npm ci && npm run build')
    events=_enrich_events(session)
    if preset is not None and session_dir is not None:
        from spatial_parallax import evidence_attention_events
        events.extend(evidence_attention_events(session_dir,session))
        events.sort(key=lambda e:e['t'])
    data={'events':events,
          'startMs':session['states'][0]['at_ms'],
          'durationMs':duration_s*1000.,
          'fps':fps,
          'config':config}
    if preset is not None:
        if preset not in ('clean-studio','3d-launch','hyper-cut'):
            raise ValueError('Unsupported Sauce preset')
        data['preset']=preset
        if preset_overrides is not None:
            if not isinstance(preset_overrides,dict):
                raise ValueError('Preset overrides must be a JSON object')
            data['presetOverrides']=preset_overrides
    elif preset_overrides is not None:
        raise ValueError('Cannot override a missing preset')
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
    if preset is not None:
        engine=report.get('motionEngine')
        if not isinstance(engine,dict) or engine.get('schema')!='sauce-motion-plan-v1':
            raise RuntimeError('Missing versioned Sauce Motion Engine plan')
        settings=engine.get('preset',{})
        if (settings.get('schemaVersion')!=1 or settings.get('id')!=preset
            or settings.get('export',{}).get('fps')!=fps):
            raise RuntimeError('Preset identity, version or fps mismatch')
        fp=engine.get('framePlan',{})
        if fp.get('schema')!='sauce-frame-plan-v1' or fp.get('fps')!=fps:
            raise RuntimeError('Unrecognized FramePlan schema')
        instructions=fp.get('frames')
        if not isinstance(instructions,list) or len(instructions)!=len(frames):
            raise RuntimeError('FramePlan count does not match StudioMotion clock')
        for i,frame in enumerate(instructions):
            pose=frame.get('camera',{})
            if (frame.get('outputFrame')!=i
                or abs(frame['sourceMs']-frames[i]['sourceMs'])>1e-3
                or not 0.8<=pose.get('scale',0)<=2.
                or not 600<=pose.get('perspectivePx',0)<=3000
                or max(abs(pose.get('rotateXDeg',99)),
                       abs(pose.get('rotateYDeg',99)))>6.):
                raise RuntimeError(f'Invalid FramePlan camera/time at {i}')
        foley=engine.get('foleyPlan',{})
        if (foley.get('schema')!='sauce-foley-plan-v1'
            or foley.get('sampleRate')!=48000
            or abs(foley.get('durationMs',0)-fp.get('outputDurationMs',-100))>.1):
            raise RuntimeError('FoleyPlan not aligned to FramePlan')
        max_sample=int((fp['outputDurationMs']+1000/fps)*48)
        for cue in foley.get('cues',[]):
            if (cue.get('sound') not in ('click_crisp','whoosh_soft','pop_glass')
                or not isinstance(cue.get('outputSample'),int)
                or not 0<=cue['outputSample']<max_sample
                or abs(cue.get('outputMs',-1000)-cue['outputSample']/48)>.05):
                raise RuntimeError('Invalid output-synchronized Foley cue')
    return report
