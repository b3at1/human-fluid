from sqlalchemy import select
from app.curriculum import RulePolicy,adapt
from app.db import Principal,Session,Item,Attempt,Review,now
from app.tasks.engine import generate
from app.tasks.bank import get_task
from app.tasks.solvers import digest
from conftest import start,mutation
from test_api import private_solution

def test_policy_broad_coverage_and_focus():
    policy=RulePolicy()
    a=policy.select_next({'counts':{'logic':3,'ordering':1},'levels':{'ordering':2}},['logic','ordering'])
    assert (a.family,a.level)==('ordering',2)
    assert policy.select_next({'counts':{},'levels':{}},['logic']).family=='logic'

def test_advancement_requires_six_independent_structures(database):
    with database.begin() as db:
        p=Principal(token_hash='synthetic',csrf='test',expires=now()+3600,levels={});db.add(p);db.flush()
        session=Session(owner=p.id,mode='focus',family='ordering',total=20);db.add(session);db.flush()
        for n in range(6):
            task=generate('ordering',1,n*57+1);i=Item(owner=p.id,session_id=session.id,position=n,task=task,rationale='synthetic test');db.add(i);db.flush()
            db.add(Attempt(owner=p.id,item_id=i.id,answer=task['solution'],correct=True,assisted=False));db.flush()
            adapt(db,p,task)
            assert p.levels.get('ordering',1)==(2 if n==5 else 1)

def test_assisted_success_cannot_advance(database):
    with database.begin() as db:
        p=Principal(token_hash='synthetic',csrf='test',expires=now()+3600,levels={});db.add(p);db.flush()
        s=Session(owner=p.id,mode='focus',family='ordering',total=8);db.add(s);db.flush()
        for n in range(8):
            t=generate('ordering',1,n);i=Item(owner=p.id,session_id=s.id,position=n,task=t,rationale='synthetic');db.add(i);db.flush()
            db.add(Attempt(owner=p.id,item_id=i.id,answer=t['solution'],correct=True,assisted=True));db.flush();adapt(db,p,t)
        assert p.levels.get('ordering',1)==1

def test_due_review_fresh_and_original_preserved(client,database):
    s=start(client);iid=s['current']['instance_id'];a=mutation(client,'/instances/'+iid+'/submit',{'answer':not private_solution(database,iid)}).json()
    assert not a['correct'];assert client.get('/api/v1/reviews/due').json()['next_session']==1
    fresh=start(client,'mixed')['current'];assert fresh['rationale'].startswith('Due review')
    with database() as db:assert db.get(Item,iid).task['fingerprint']!=db.get(Item,fresh['instance_id']).task['fingerprint']
    assert client.get('/api/v1/attempts/'+a['id']).json()['correct'] is False

def test_focus_hypothesis_six_fresh_items(client,database):
    s=start(client,'focus','hypothesis');seen=set()
    for _ in range(6):
        i=s['current'];seen.add(i['instance_id']);r=mutation(client,'/instances/'+i['instance_id']+'/submit',{'answer':private_solution(database,i['instance_id'])});assert r.status_code==200,r.text
        r=mutation(client,'/sessions/'+s['id']+'/next');assert r.status_code==200,r.text;s=r.json()
    assert len(seen)==6 and s['state']=='completed'
