"""Evidence-first candidate sampling and conservative localized color proof."""
import numpy as np
import cv2

def localized_color_proof(before,after,settled):
    """Require distributed, persistent chromatic changes in a real result panel.

    Does not admit hover-only noise, tiny marks or a one-pixel change, and
    does not replace the independent decoded-source adapter.
    """
    if before.shape!=after.shape or before.shape!=settled.shape or before.size==0:
        return None
    def chroma(im):
        return cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(np.float32)[:,:,1:]
    b,a,s=map(chroma,(before,after,settled))
    mask=np.linalg.norm(a-b,axis=2)>=20
    persistent=mask & (np.linalg.norm(s-b,axis=2)>=20) & (np.linalg.norm(s-a,axis=2)<=8)
    area=mask.size
    if persistent.mean()<.018 or persistent.sum()<.85*mask.sum():return None
    _,_,stats,cent=cv2.connectedComponentsWithStats(persistent.astype(np.uint8),8)
    components=[(row,c) for row,c in zip(stats[1:],cent[1:]) if row[4]>=area*.0005 and row[2]>=12 and row[3]>=8]
    if len(components)<3 or sum(r[4] for r,_ in components)<area*.016:return None
    h,w=mask.shape
    zones={(min(2,int(c[0]*3/w)),min(2,int(c[1]*3/h))) for _,c in components}
    if len(zones)<3:return None
    coarse=float(np.mean(np.max(cv2.absdiff(cv2.resize(before,(128,64)),cv2.resize(after,(128,64))),axis=2)>12))
    if coarse<.02:return None
    return {"persistentChromaFraction":float(persistent.mean()),"components":len(components),"zones":len(zones),"coarseChangedFraction":coarse}

def diverse_candidates(catalog,limit=8):
    """Bounded representative sample, not a hand-authored customer story."""
    groups={}
    for row in catalog:
        key=row.get("group") or row["kind"]
        groups.setdefault(key,[]).append(row)
    # Sample successive group alternatives, spanning the observed option list.
    orders=[]
    for rows in groups.values():
        ix=[]
        for i in (0,len(rows)//2,len(rows)-1,*range(len(rows))):
            if i not in ix:ix.append(i)
        orders.append([rows[i] for i in ix])
    return diverse_candidates_round_robin(dict(enumerate(orders)),limit)

def balance_hypotheses(catalog,requested,limit=8):
    """Retain model preferences within groups; allocate broad probe coverage.

    The compiler chooses a representative experiment, never the final story.
    A large single picker remains unrestricted when no other groups exist.
    """
    def group(a):return a.get("group") or a["kind"]
    groups={}
    for a in catalog:groups.setdefault(group(a),[]).append(a)
    if len(groups)<2:return requested[:limit]
    preferred={}
    for a in requested:preferred.setdefault(group(a),[]).append(a)
    for k,rows in groups.items():
        # Keep model preferences first, then alternatives spread through list.
        seen={r["id"] for r in preferred.get(k,[])}
        ordered=preferred.get(k,[])+[r for r in diverse_candidates(rows,len(rows)) if r["id"] not in seen]
        groups[k]=ordered
    return diverse_candidates_round_robin(groups,limit)

def diverse_candidates_round_robin(groups,limit):
    result=[]
    for i in range(max(map(len,groups.values()),default=0)):
        for rows in groups.values():
            if i<len(rows):result.append(rows[i])
            if len(result)==limit:return result
    return result

def require_provider_reply(raw,conversation):
    if raw is not None:return raw
    attempts=conversation.data.get("attempts",[])
    last=attempts[-1] if attempts else {}
    status=last.get("http_status")
    if status in (429,503,404):
        raise RuntimeError(f"Gemini returned HTTP {status}")
    raise RuntimeError("Gemini did not return evidence-led direction")
