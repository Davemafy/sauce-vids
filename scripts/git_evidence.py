"""Opt-in, bounded Git commit evidence for recorded feature-reveal events.

Never runs code from a repository or embeds an arbitrary repository file in
published content. The operator selects a commit and an actual source moment.
"""
from __future__ import annotations
import argparse,json,re,subprocess
from pathlib import Path

SHA=re.compile(r'^[a-fA-F0-9]{7,40}$')
PATH=re.compile(r'^[A-Za-z0-9_./-]{1,140}$')
PRIVATE=re.compile(r'password|secret|token|api.?key|private.?key|authorization|[\w.+-]+@[\w.-]+\.[a-z]{2,}',re.I)


def validate_commit(record:dict)->dict:
    if not isinstance(record,dict) or not SHA.fullmatch(str(record.get('sha',''))):
        raise ValueError('Invalid Git revision')
    file=record.get('file');title=record.get('title');lines=record.get('lines')
    if not isinstance(file,str) or not PATH.fullmatch(file) or '..' in file:
        raise ValueError('Unsafe Git file path')
    if not isinstance(title,str) or len(title)>72 or PRIVATE.search(title):
        raise ValueError('Private/invalid commit description')
    if not isinstance(lines,list) or not 1<=len(lines)<=16:
        raise ValueError('A localized diff requires 1–16 lines')
    for line in lines:
        if (not isinstance(line,str) or not 1<=len(line)<=160 or
            line[0] not in ' +-@' or PRIVATE.search(line) or
            any(ord(c)<32 and c!='\t' for c in line)):
            raise ValueError('Unsafe or excessive localized diff')
    return {'sha':record['sha'].lower(),'file':file,'title':title,'lines':list(lines)}


def commit_from_git(repository:Path,revision:str)->dict:
    repository=Path(repository).resolve()
    if not SHA.fullmatch(revision):raise ValueError('Require explicit Git SHA')
    def git(*args):
        return subprocess.run(['git','-C',str(repository),*args],capture_output=True,
          text=True,timeout=12,check=True).stdout
    actual=git('rev-parse','--verify',revision+'^{commit}').strip()
    title=git('show','-s','--format=%s',actual).strip()[:72]
    # `--no-ext-diff` and fixed arguments avoid external diff drivers.
    patch=git('-c','diff.external=','show','--no-ext-diff','--format=',
              '--unified=2','--no-renames',actual)
    current=None;lines=[]
    for line in patch.splitlines():
        if line.startswith('+++ b/'):
            candidate=line[6:]
            if PATH.fullmatch(candidate) and '..' not in candidate:
                current=candidate
        elif current and line.startswith('@@'):
            lines=[line[:160]]
        elif current and lines and line.startswith(('+','-',' ')):
            lines.append(line)
            if len(lines)>=14:
                try:return validate_commit({'sha':actual,'file':current,'title':title,
                                            'lines':lines})
                except ValueError:current=None;lines=[]
        if current and lines and len(lines)>=5:
            try:return validate_commit({'sha':actual,'file':current,'title':title,
                                        'lines':lines})
            except ValueError:current=None;lines=[]
    if current and lines:
        return validate_commit({'sha':actual,'file':current,'title':title,'lines':lines})
    raise ValueError('Commit has no safe localized textual diff (or contains private content)')


def annotate_session(session_path:Path,repo:Path,revision:str,at_ms:float)->dict:
    from session_contract import verify_package
    session_path=Path(session_path).resolve();session=json.loads(session_path.read_text())
    verify_package(session,session_path.parent)
    if not isinstance(at_ms,(int,float)) or not session['states'][0]['at_ms']<=at_ms<=session['states'][-1]['at_ms']:
        raise ValueError('Commit reveal must occur within actual capture')
    commit=commit_from_git(repo,revision)
    session['events'].append({'t':at_ms,'type':'feature-commit','commit':commit})
    session['events'].sort(key=lambda e:e['t'])
    verify_package(session,session_path.parent)
    session_path.write_text(json.dumps(session,indent=2)+'\n')
    return commit

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--commit',required=True);p.add_argument('--at-ms',type=float,required=True)
    a=p.parse_args();print(json.dumps(annotate_session(a.session,a.repo,a.commit,a.at_ms),indent=2))
