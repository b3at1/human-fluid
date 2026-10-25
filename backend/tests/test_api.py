import json
import secrets
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select,func
from fastapi.testclient import TestClient
from app import main
from app.db import Item,Attempt,Principal,Invite,Grant,Inference,now
from app.auth import hash_token
from conftest import mutation,start

def private_solution(database,id):
    with database() as db:return db.get(Item,id).task['solution']

def complete(client,database,s):
    results=[]
    for pos in range(s['total']):
        t=s['current'];r=mutation(client,'/instances/'+t['instance_id']+'/submit',{'answer':private_solution(database,t['instance_id'])})
        assert r.status_code==200,r.text;results.append(r.json())
        s=mutation(client,'/sessions/'+s['id']+'/next').json()
    return s,results

def test_full_session_resume_immutable(client,database):
    s=start(client,'mixed');t=s['current'];iid=t['instance_id']
    assert 'solution' not in json.dumps(t)
    assert client.patch('/api/v1/instances/'+iid+'/draft',json={'scratchpad':'A note','answer':True}).status_code==200
    assert mutation(client,'/sessions/'+s['id'],{'state':'paused'},method='patch').status_code==200
    assert mutation(client,'/sessions/'+s['id']+'/next').status_code==409
    s=mutation(client,'/sessions/'+s['id'],{'state':'active'},method='patch').json()
    assert s['current']['draft']['scratchpad']=='A note'
    expected=private_solution(database,iid)
    r=mutation(client,'/instances/'+iid+'/submit',{'answer':expected,'confidence':.75});assert r.status_code==200,r.text
    again=mutation(client,'/instances/'+iid+'/submit',{'answer':not expected});assert again.json()['id']==r.json()['id'];assert again.json()['correct']
    s=mutation(client,'/sessions/'+s['id']+'/next').json()
    for _ in range(7):
        t=s['current'];r=mutation(client,'/instances/'+t['instance_id']+'/submit',{'answer':private_solution(database,t['instance_id'])});assert r.status_code==200,r.text
        s=mutation(client,'/sessions/'+s['id']+'/next').json()
    assert s['state']=='completed';assert mutation(client,'/sessions/'+s['id'],{'state':'active'},method='patch').status_code==409
    with database() as db:assert db.scalar(select(func.count()).select_from(Attempt))==8

def test_hints_assistance_and_duplicate(client,database):
    t=start(client)['current'];iid=t['instance_id']
    for _ in range(2): assert mutation(client,'/instances/'+iid+'/hints',{'index':0}).json()['hints_used']==1
    a=mutation(client,'/instances/'+iid+'/submit',{'answer':private_solution(database,iid)}).json();assert a['assisted']
    assert client.get('/api/v1/progress').json()['practice'][0]['independent']==0
    assert mutation(client,'/instances/'+iid+'/hints',{'index':1}).status_code==409

def test_check_embargo_every_route(client,database):
    s=start(client,'check');iid=s['current']['instance_id']
    assert mutation(client,'/instances/'+iid+'/hints',{'index':0}).status_code==403
    a=mutation(client,'/instances/'+iid+'/submit',{'answer':private_solution(database,iid)}).json();assert a['correct'] is None;assert a['sealed'];assert 'explanation' not in a
    assert 'explanation' not in client.get('/api/v1/attempts/'+a['id']).json()
    assert mutation(client,'/attempts/'+a['id']+'/discussion',{'message':'explain'}).status_code==403
    assert client.get('/api/v1/attempts/'+a['id']+'/discussion').status_code==403
    exported=mutation(client,'/export').json();assert exported['history'][0]['correct'] is None;assert 'solution' not in json.dumps(exported)
    assert not client.get('/api/v1/progress').json()['checks']
    assert mutation(client,'/sessions/'+s['id']+'/release',{'confirm':True}).status_code==409
    for _ in range(9):
        s=mutation(client,'/sessions/'+s['id']+'/next').json();iid=s['current']['instance_id']
        r=mutation(client,'/instances/'+iid+'/submit',{'answer':private_solution(database,iid)});assert r.status_code==200,r.text
    s=client.get('/api/v1/sessions/'+s['id']).json();assert s['state']=='completed';assert s['current']['result']['sealed']
    assert client.get('/api/v1/progress').json()['checks'][0]['count']==10
    assert mutation(client,'/sessions/'+s['id']+'/release',{'confirm':True}).status_code==200
    assert client.get('/api/v1/attempts/'+a['id']).json()['explanation']['steps']

def test_ownership_isolation(client,database):
    s=start(client);iid=s['current']['instance_id'];aid=mutation(client,'/instances/'+iid+'/submit',{'answer':True}).json()['id']
    with TestClient(main.app) as other:
        other.headers['Origin']=main.settings.public_origin
        other.headers['X-CSRF-Token']=other.post('/api/v1/guest',json={}).json()['csrf_token']
        for path in ['/sessions/'+s['id'],'/instances/'+iid,'/attempts/'+aid,'/attempts/'+aid+'/discussion']:
            assert other.get('/api/v1'+path).status_code==404
        assert mutation(other,'/instances/'+iid+'/submit',{'answer':False}).status_code==404
        assert other.patch('/api/v1/attempts/'+aid+'/reflection',json={'note':'bad'}).status_code==404
        assert mutation(other,'/export').json()['history']==[]
        assert mutation(other,'/me/data',{'confirm':True},method='delete').status_code==200
    assert client.get('/api/v1/attempts/'+aid).status_code==200

def test_query_replay_privacy(client,database):
    s=start(client,'focus','hypothesis');iid=s['current']['instance_id']
    r=mutation(client,'/instances/'+iid+'/queries',{'input':1},'query-replay');assert r.status_code==200,r.text
    assert r.json()==mutation(client,'/instances/'+iid+'/queries',{'input':1},'query-replay').json()
    assert mutation(client,'/instances/'+iid+'/queries',{'input':2},'query-replay').status_code==409
    assert set(r.json())=={'queries'}
    with database() as db:assert r.json()['queries'][0]['output']==main.apply(db.get(Item,iid).task['formal']['rule'],1)
    assert mutation(client,'/instances/'+iid+'/queries',{'input':True}).status_code==422

def test_csrf_origin_limits(client):
    assert client.post('/api/v1/sessions',json={'mode':'mixed'},headers={'Origin':'https://evil.example'}).status_code==403
    assert client.post('/api/v1/sessions',json={'mode':'mixed'},headers={'X-CSRF-Token':'wrong'}).status_code==403
    assert client.post('/api/v1/sessions',json={'mode':'mixed'},headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
    assert client.post('/api/v1/guest',content='x'*1048577,headers={'Content-Type':'application/json'}).status_code==413
    assert client.get('/api/v1/not-a-route').status_code==404

def test_restore_no_privileges_and_unverified(client,database):
    s=start(client);iid=s['current']['instance_id'];mutation(client,'/instances/'+iid+'/submit',{'answer':True})
    backup=mutation(client,'/export').json();assert mutation(client,'/restore',{**backup,'admin':True}).status_code==422
    backup['history'][0]['correct']=True
    assert mutation(client,'/restore',backup).json()['verified'] is False
    assert client.get('/api/v1/progress').json()['restored_unverified']==1
    assert not client.get('/api/v1/ai/status').json()['approved']
    assert client.get('/api/v1/admin/status').status_code==403

def test_invalid_answer_preserves_unsubmitted(client,database):
    t=start(client)['current'];r=mutation(client,'/instances/'+t['instance_id']+'/submit',{'answer':'True'});assert r.status_code==422
    assert not client.get('/api/v1/instances/'+t['instance_id']).json()['submitted']

def test_native_check_pool_can_issue():
    from app.tasks.bank import get_task
    for f in ['ordering','induction','hypothesis']:
        t=get_task(None,f,2,'check',147,set());assert t['split']=='check'

def test_check_forms_structurally_disjoint(client,database):
    first=start(client,'check');second=start(client,'check')
    from app.db import Session
    with database() as db:
        a=db.get(Session,first['id']);b=db.get(Session,second['id'])
        assert a.manifest['form']=='A' and b.manifest['form']=='B'
        assert not {t['fingerprint'] for t in a.manifest['tasks']}&{t['fingerprint'] for t in b.manifest['tasks']}

def test_export_restore_preserves_worked_history(client,database):
    s=start(client);iid=s['current']['instance_id'];a=mutation(client,'/instances/'+iid+'/submit',{'answer':private_solution(database,iid)}).json()
    exported=mutation(client,'/export').json();snapshot=exported['history'][0]['review']
    assert snapshot['render']['kind']=='dependency_graph';assert snapshot['steps']
    assert mutation(client,'/restore',exported).status_code==200
    assert client.get('/api/v1/restored').json()['items'][0]['review']['steps']==snapshot['steps']
    assert mutation(client,'/restore',exported).json()['restored']==0

def test_completed_check_per_item_correctness_remains_sealed(client,database):
    s,results=complete(client,database,start(client,'check'))
    assert s['current']['result']['correct'] is None
    assert all(r['correct'] is None for r in client.get('/api/v1/attempts').json()['items'])
    assert client.get('/api/v1/progress').json()['checks'][0]['correct']==10

def test_delete_removes_grants_and_history(client,database):
    s=start(client);iid=s['current']['instance_id'];mutation(client,'/instances/'+iid+'/submit',{'answer':True})
    from test_tutoring import approve
    approve(client,database)
    assert mutation(client,'/me/data',{'confirm':False},method='delete').status_code==422
    assert mutation(client,'/me/data',{'confirm':True},method='delete').status_code==200
    with database() as db:
        assert db.scalar(select(func.count()).select_from(Grant))==0
        assert db.scalar(select(func.count()).select_from(Attempt))==0

def test_restore_depth_size_enums_and_authority_rejected(client):
    base={'family':'dependencies','difficulty':1,'mode':'focus','correct':True,'assisted':False,'created':1,'reflection':{},'provenance':'synthetic test'}
    for patch in [{'difficulty':99},{'family':'unknown'},{'grant':True},{'reflection':{'note':'x'*3001}}]:
        assert mutation(client,'/restore',{'schema_version':1,'history':[{**base,**patch}]}).status_code==422
    assert mutation(client,'/restore',{'schema_version':1,'history':[base]*2001}).status_code==422
    assert mutation(client,'/ai/redeem',{'code':'unknown-code-which-is-not-valid'}).status_code==403
