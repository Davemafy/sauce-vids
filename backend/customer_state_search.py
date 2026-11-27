"""Bounded newly visible local capability chains; no guessed actions."""
MAX_BRANCHES=4
MAX_DEPTH=3

def chain(action,witnessed):
    by_id={a['id']:a for a in witnessed};seen={action['id']};parents=[]
    while action.get('requires'):
        parent=action['requires']
        if parent in seen or parent not in by_id or len(parents)>=MAX_DEPTH-1:
            raise ValueError('Invalid observed prerequisite chain')
        seen.add(parent);action=by_id[parent];parents.insert(0,action)
    return parents

def enqueue(queue,initial,witnessed,page,metadata,parent,*,catalog_fn=None):
    if metadata.get('setup',{}).get('kind')!='local-demo-views':return
    depth=1+len(chain(parent,witnessed))
    if depth>=MAX_DEPTH:return
    # Reserve half the branch budget for deeper opportunities.
    cap=2 if depth==1 else MAX_BRANCHES
    if len(queue)>=cap:return
    if catalog_fn is None:
        from backend.customer_local_views import catalog as catalog_fn
    known={(a['group'],a['label']) for a in initial+queue+witnessed}
    for row in catalog_fn(page,metadata['setup']):
        identity=(row['group'],row['label'])
        if identity in known or row['group']==parent.get('group'):continue
        queue.append({**row,'id':f'state{len(queue)}','requires':parent['id']})
        known.add(identity)
        if len(queue)>=cap:break
