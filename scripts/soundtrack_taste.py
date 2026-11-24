"""Owner-calibrated research-only soundtrack selection; no approval of new songs."""
import math

# Actual owner feedback after hearing the three equal-picture Resend mixes.
# Preference applies to music in the given editorial context, not film approval.
OWNER_ANCHORS = {
    'transformation': 'pantheon',
    'showcase': 'electron',
    'interaction': 'slipshod',
}
ROLE_TERMS = {
    'transformation': ('phonk', 'dark hip hop'),
    'showcase': ('ambient', 'atmospheric', 'chillstep', 'trip hop'),
    'interaction': ('house', 'electronic dance'),
}

def rank_candidates(rows, role, recent=(), explore=False):
    if role not in OWNER_ANCHORS:
        raise ValueError('Unknown editorial soundtrack role')
    if not isinstance(recent,(list,tuple)) or any(not isinstance(x,str) for x in recent):
        raise ValueError('Invalid track history')
    anchor=OWNER_ANCHORS[role]
    used=set(recent[-3:])
    ranked=[]
    for r in rows:
        if r.get('license')!='CC0-1.0' or r.get('status')!='candidate':
            continue
        ident=r['id']
        mood=r.get('mood','').lower()
        if ident!=anchor and not any(term in mood for term in ROLE_TERMS[role]):
            continue
        if ident in used:
            continue
        if explore and ident in OWNER_ANCHORS.values():
            continue
        excerpts=r.get('pictureExcerptCandidates',[])
        if not excerpts:
            continue
        score=float(excerpts[0]['rhythmScore'])
        if not math.isfinite(score):
            continue
        # User preference anchors, not a proxy for unobserved music quality.
        # Exploration intentionally searches beyond known anchors.
        score=min(max(score,0),2.5)+(1.0 if ident==anchor else 0)
        if role=='showcase' and any(x in mood for x in ('ambient','atmospheric')):
            score+=.35
        if role=='interaction' and 'minimal house' in mood:
            score+=.25
        ranked.append((score,ident))
    return [{'id':ident,'selectionScore':round(score,4),
             'ownerTasteAnchor':anchor,'role':role,'exploration':explore}
            for score,ident in sorted(ranked,key=lambda x:(-x[0],x[1]))]
