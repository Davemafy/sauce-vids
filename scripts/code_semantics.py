"""AST-linked camera targets for trace events with explicit code provenance.

No code is inferred from screenshots. Events must provide a real file,
line, bounding box, and visible line geometry. Source read is confined to
an operator-specified code workspace and never executed.
"""
from __future__ import annotations
import ast, json, subprocess
from pathlib import Path
from dataclasses import dataclass

EXTENSIONS=frozenset({'.py','.js','.jsx','.ts','.tsx','.mjs','.cjs'})
AST_NODE_TYPES=(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)
PARSER=Path(__file__).with_name('code_focus_ast.cjs')


@dataclass(frozen=True)
class CodeFocus:
    file:str
    name:str
    kind:str
    line_start:int
    line_end:int
    active_line:int
    event_ms:float
    box:dict
    visible_start:int
    line_height:float

    def target_rect(self)->dict:
        # Focus active symbol up to 10 lines, keeping its declaration visible;
        # avoid framing a 300-line class with unreadable text.
        first=max(self.visible_start,self.line_start)
        last=min(self.line_end,self.visible_start+35,
                 max(first,self.active_line)+3)
        x=float(self.box['x'])
        y=float(self.box['y'])+(first-self.visible_start)*self.line_height
        height=max(16.,(last-first+1)*self.line_height)
        return {'x':x,'y':y,'width':float(self.box['width']),
                'height':min(height,float(self.box['height']))}


def _python_symbol(source:str,line:int)->dict|None:
    tree=ast.parse(source)
    options=[]
    for node in ast.walk(tree):
        if isinstance(node,AST_NODE_TYPES) and node.lineno<=line<=node.end_lineno:
            options.append(node)
    if not options:return None
    node=min(options,key=lambda n:n.end_lineno-n.lineno)
    return {'type':type(node).__name__,'name':node.name,
            'begin':node.lineno,'end':node.end_lineno}


def _babel_symbol(source:str,line:int)->dict|None:
    request=json.dumps({'source':source,'line':line})
    process=subprocess.run(['node',str(PARSER)],input=request,text=True,
       capture_output=True,check=True,timeout=12)
    return json.loads(process.stdout)


def resolve_code_focus(event:dict,repo_root:Path)->CodeFocus:
    if event.get('type')!='code-focus':
        raise ValueError('Expected code-focus trace event')
    rel=event.get('file')
    if not isinstance(rel,str) or not rel or '\\' in rel:
        raise ValueError('Invalid code path')
    root=repo_root.resolve(strict=True)
    target=(root/rel).resolve(strict=True)
    if not target.is_relative_to(root) or target.suffix.lower() not in EXTENSIONS:
        raise ValueError('Code focus must target a supported file inside workspace')
    if target.stat().st_size>1000000:raise ValueError('Code file exceeds AST parsing limit')
    line=int(event['line'])
    source=target.read_text(encoding='utf-8')
    if not 1<=line<=len(source.splitlines()):
        raise ValueError('Active code line out of bounds')
    symbol=(_python_symbol(source,line) if target.suffix.lower()=='.py'
            else _babel_symbol(source,line))
    if symbol is None:
        symbol={'type':'line','name':f'line {line}','begin':line,'end':line}
    box=event['box']
    if not all(k in box for k in ('x','y','width','height')):
        raise ValueError('Code event requires visible DOM bounding box')
    if float(box['width'])<30 or float(box['height'])<16:
        raise ValueError('Code DOM box too small')
    lh=float(event.get('line_height',20))
    if not 8<=lh<=48:raise ValueError('Invalid visible line height')
    vis=int(event.get('first_visible_line',1))
    if vis<1:raise ValueError('Invalid visible line position')
    return CodeFocus(rel,symbol['name'],symbol['type'],
        int(symbol['begin']),int(symbol['end']),line,float(event['t']),
        box,vis,lh)


def plan_code_foci(events:list[dict],repo_root:Path|None)->list[CodeFocus]:
    if repo_root is None:return []
    return [resolve_code_focus(event,repo_root)
            for event in events if event.get('type')=='code-focus']

@dataclass(frozen=True)
class TerminalFocus:
    event_ms:float
    box:dict
    name:str='terminal'
    kind:str='terminal'
    file:str=''
    line_start:int=0
    line_end:int=0

    def target_rect(self)->dict:
        # Terminal output has no AST: frame the real DOM terminal bounds,
        # never pretend a shell command is a function declaration.
        return {k:float(self.box[k])
                for k in ('x','y','width','height')}


def plan_focus_cues(events:list[dict],
                    repo_root:Path|None)->list[CodeFocus|TerminalFocus]:
    cues:list[CodeFocus|TerminalFocus]=plan_code_foci(events,repo_root)
    for event in events:
        if event.get('type')!='terminal-focus':continue
        box=event.get('box')
        if not box or not all(k in box for k in ('x','y','width','height')):
            raise ValueError('Terminal focus requires actual DOM geometry')
        cues.append(TerminalFocus(float(event['t']),box))
    return sorted(cues,key=lambda f:f.event_ms)


def semantic_camera_track(
    original:list[tuple[float,float,float]],foci:list[CodeFocus|TerminalFocus],
    start_ms:float,fps:int,viewport:tuple[int,int]
)->list[tuple[float,float,float]]:
    """Camera locks onto AST region when a verified code-focus event occurs."""
    if not foci:return original
    from spring_motion import Spring1D,Spring2D
    w,h=viewport
    z_s=Spring1D(original[0][0],stiffness=98,damping=20)
    pan=Spring2D(original[0][1],original[0][2],stiffness=118,damping=21)
    output=[]
    for i,default in enumerate(original):
        t=start_ms+i*1000./fps
        active=next((a for a in reversed(foci)
            if a.event_ms<=t<a.event_ms+2300.),None)
        if active:
            rect=active.target_rect()
            safe_zoom=min(1.75,(w-155)/rect['width'],
                          (h-145)/max(20.,rect['height']))
            # Avoid zooming OUT for a small code block.
            target=(max(1.08,safe_zoom),
                    rect['x']+rect['width']/2,
                    rect['y']+rect['height']/2)
        else:target=default
        if i:
            z_s.step(target[0],1/fps)
            pan.step(target[1],target[2],1/fps)
        output.append((z_s.position,pan.x.position,pan.y.position))
    return output


def active_code_focus(foci:list[CodeFocus|TerminalFocus],t_ms:float)->CodeFocus|TerminalFocus|None:
    return next((a for a in reversed(foci)
                 if a.event_ms<=t_ms<a.event_ms+2300.),None)


def highlight_code_region(frame,focus:CodeFocus|None,
                          zoom:float,dx:float,dy:float,
                          dpr:int,source_factor:float):
    """Emphasize AST-identified block while preserving original syntax colors.

    Works on the warped source DOM *before* the final stage and cursor.
    """
    if focus is None or isinstance(focus,TerminalFocus):return frame
    import cv2
    rect=focus.target_rect()
    x=max(0,round(dx+rect['x']*dpr*source_factor))
    y=max(0,round(dy+rect['y']*dpr*source_factor))
    right=min(frame.shape[1],round(dx+(rect['x']+rect['width'])*dpr*source_factor))
    bottom=min(frame.shape[0],round(dy+(rect['y']+rect['height'])*dpr*source_factor))
    if right<=x or bottom<=y:return frame
    patch=frame[y:bottom,x:right]
    overlay=patch.copy()
    overlay[:]=cv2.addWeighted(patch,.88,
                        __import__('numpy').full_like(patch,(105,86,51)),.12,0)
    frame[y:bottom,x:right]=overlay
    cv2.rectangle(frame,(x,y),(right-1,bottom-1),(174,145,100),1,cv2.LINE_AA)
    return frame
