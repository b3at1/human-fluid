import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from app import main,tutoring
from app.db import Principal,Invite,Grant,Inference,Admin,now
from app.auth import hash_token
from argon2 import PasswordHasher
from conftest import start,mutation
from test_api import private_solution

class Stub:
    def __init__(self):self.calls=0;self.messages=[];self.block=None;self.enter=threading.Event()
    def estimate(self,messages):return len(str(messages).encode())+100
    def generate(self,messages):
        self.calls+=1;self.messages=messages;self.enter.set()
        if self.block:self.block.wait(10)
        return 'Test provider: trace the prerequisite arrows from the prerequisite to the dependent course.',100

def approve(client,database):
    code=secrets.token_urlsafe(32)
    with database.begin() as db:db.add(Invite(code_hash=hash_token(code),label='test invitation',expires=now()+3600,daily_limit=30))
    r=mutation(client,'/ai/redeem',{'code':code});assert r.status_code==200,r.text
    client.headers['X-CSRF-Token']=r.json()['csrf_token']
    return code

def attempt(client,database):
    t=start(client)['current'];return mutation(client,'/instances/'+t['instance_id']+'/submit',{'answer':private_solution(database,t['instance_id'])}).json()['id']

def enable(monkeypatch,stub):
    monkeypatch.setattr(main.settings,'ai_enabled',True);monkeypatch.setattr(main.settings,'ai_provider','local');monkeypatch.setattr(tutoring,'get_provider',lambda:stub)

def test_access_disabled_and_revocation(client,database,monkeypatch):
    aid=attempt(client,database);stub=Stub();enable(monkeypatch,stub)
    assert mutation(client,'/attempts/'+aid+'/discussion',{'message':'explain'}).status_code==403;assert stub.calls==0
    approve(client,database)
    with database.begin() as db:db.scalar(select(Grant)).revoked=True
    assert mutation(client,'/attempts/'+aid+'/discussion',{'message':'explain'}).status_code==403;assert stub.calls==0

def test_expired_grant(client,database,monkeypatch):
    aid=attempt(client,database);stub=Stub();enable(monkeypatch,stub);approve(client,database)
    with database.begin() as db:db.scalar(select(Grant)).expires=now()-1
    assert mutation(client,'/attempts/'+aid+'/discussion',{'message':'why'}).status_code==403;assert stub.calls==0

def test_idempotency_quota_context_and_canary(client,database,monkeypatch):
    aid=attempt(client,database);stub=Stub();enable(monkeypatch,stub);approve(client,database)
    canary='hf-canary-never-in-public-84297';monkeypatch.setattr(main.settings,'ai_api_key',canary)
    r=mutation(client,'/attempts/'+aid+'/discussion',{'message':'Why?'},'same-request');assert r.status_code==200,r.text
    again=mutation(client,'/attempts/'+aid+'/discussion',{'message':'Why?'},'same-request');assert again.json()==r.json();assert stub.calls==1
    assert mutation(client,'/attempts/'+aid+'/discussion',{'message':'Different'},'same-request').status_code==409
    assert canary not in str(stub.messages)
    for path in ['/ai/status','/me','/progress','/attempts','/attempts/'+aid,'/attempts/'+aid+'/discussion']:
        assert canary not in client.get('/api/v1'+path).text
    assert canary not in mutation(client,'/export').text
    monkeypatch.setattr(main.settings,'ai_grant_requests_per_day',1)
    assert mutation(client,'/attempts/'+aid+'/discussion',{'message':'Again'}).status_code==429
    assert stub.calls==1
    with database() as db:assert db.scalar(select(Inference)).tokens==100

def test_unknown_outcome_is_durable(client,database,monkeypatch):
    aid=attempt(client,database);stub=Stub();enable(monkeypatch,stub);approve(client,database)
    def broken(messages):stub.calls+=1;raise tutoring.OutcomeUnknown('SENSITIVE RAW PROVIDER ERROR')
    stub.generate=broken
    r=mutation(client,'/attempts/'+aid+'/discussion',{'message':'Why?'},'timeout-request');assert r.status_code==503;assert 'SENSITIVE' not in r.text
    with database() as db:row=db.scalar(select(Inference));assert row.state=='outcome-unknown';assert row.tokens>100
    assert mutation(client,'/attempts/'+aid+'/discussion',{'message':'Why?'},'timeout-request').status_code==409
    assert mutation(client,'/attempts/'+aid+'/discussion',{'message':'Another?'}).status_code==429
    assert stub.calls==1

def test_concurrent_reservation_one_call(client,database,monkeypatch):
    aid=attempt(client,database);stub=Stub();enable(monkeypatch,stub);approve(client,database);stub.block=threading.Event()
    cookies=dict(client.cookies);csrf=client.headers['X-CSRF-Token']
    def send(key):
        with TestClient(main.app,cookies=cookies) as other:
            other.headers.update({'Origin':main.settings.public_origin,'X-CSRF-Token':csrf})
            return mutation(other,'/attempts/'+aid+'/discussion',{'message':'Why?'},key)
    with ThreadPoolExecutor(2) as pool:
        first=pool.submit(send,'concurrent-first');assert stub.enter.wait(10)
        second=pool.submit(send,'concurrent-second');r=second.result(10);assert r.status_code==429,r.text
        stub.block.set();assert first.result(10).status_code==200
    assert stub.calls==1

def test_invite_atomic_single_use(client,database):
    code=secrets.token_urlsafe(32)
    with database.begin() as db:db.add(Invite(code_hash=hash_token(code),label='atomic',expires=now()+60))
    def redeem():
        with TestClient(main.app) as c:
            c.headers['Origin']=main.settings.public_origin;c.headers['X-CSRF-Token']=c.post('/api/v1/guest',json={}).json()['csrf_token']
            return mutation(c,'/ai/redeem',{'code':code}).status_code
    with ThreadPoolExecutor(2) as pool:assert sorted(pool.map(lambda _:redeem(),range(2)))==[200,403]

def test_admin_no_default_and_owner_controls(client,database):
    assert client.get('/api/v1/admin/status').status_code==403
    with database.begin() as db:db.add(Admin(username='test-owner',password=PasswordHasher().hash('synthetic-password-123')))
    assert mutation(client,'/admin/login',{'username':'test-owner','password':'wrong'}).status_code==403
    assert mutation(client,'/admin/login',{'username':'test-owner','password':'synthetic-password-123'}).status_code==200
    result=mutation(client,'/admin/invites',{'label':'visitor'}).json();assert result['code']
    public=client.get('/api/v1/admin/status').text;assert result['code'] not in public;assert 'code_hash' not in public
    assert mutation(client,'/admin/logout').status_code==200
    assert client.get('/api/v1/admin/status').status_code==403

def test_admin_limit_survives_guest_deletion(client,database):
    for _ in range(10):assert mutation(client,'/admin/login',{'username':'missing','password':'wrong'}).status_code==403
    assert mutation(client,'/me/data',{'confirm':True},method='delete').status_code==200
    token=client.post('/api/v1/guest',json={}).json()['csrf_token'];client.headers['X-CSRF-Token']=token
    assert mutation(client,'/admin/login',{'username':'missing','password':'wrong'}).status_code==429

def test_transport_cap_and_local_host_guards(monkeypatch):
    import httpx,json
    monkeypatch.setattr(main.settings,'ai_provider','local');monkeypatch.setattr(main.settings,'ai_base_url','http://127.0.0.1:11434/v1');monkeypatch.setattr(main.settings,'ai_model','synthetic-test');monkeypatch.setattr(main.settings,'ai_api_key','')
    seen=[]
    def transport(request):
        body=json.loads(request.content);seen.append(body)
        assert str(request.url)=='http://127.0.0.1:11434/v1/chat/completions'
        return httpx.Response(200,json={'choices':[{'message':{'content':'Synthetic adapter transport response'}}],'usage':{'total_tokens':25}})
    original=httpx.Client
    monkeypatch.setattr(tutoring.httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(transport),**kwargs))
    provider=tutoring.CompatibleProvider();reply,usage=provider.generate([{'role':'user','content':'hello'}])
    assert reply.startswith('Synthetic') and usage==25;assert seen[0]['max_tokens']==main.settings.ai_max_output_tokens;assert seen[0]['stream'] is False;assert 'tools' not in seen[0]
    monkeypatch.setattr(main.settings,'ai_base_url','https://paid.example/v1')
    import pytest
    with pytest.raises(tutoring.ProviderFailure):tutoring.CompatibleProvider()

def test_production_and_budget_config_fail_closed():
    from app.config import Settings
    from pydantic import ValidationError
    import pytest
    with pytest.raises(RuntimeError):Settings(app_env='production',cookie_secure=False).validate_runtime()
    with pytest.raises(ValidationError):Settings(app_env='prod')
    with pytest.raises(ValidationError):Settings(ai_max_output_tokens=-1)
    with pytest.raises(RuntimeError):Settings(ai_provider='cloud',ai_enabled=True,ai_cap_verified=False).validate_runtime()

def test_scratchpad_context_opt_in(client,database,monkeypatch):
    t=start(client)['current'];iid=t['instance_id'];client.patch('/api/v1/instances/'+iid+'/draft',json={'scratchpad':'PRIVATE SCRATCHPAD MARKER'})
    aid=mutation(client,'/instances/'+iid+'/submit',{'answer':private_solution(database,iid)}).json()['id']
    stub=Stub();enable(monkeypatch,stub);approve(client,database)
    assert mutation(client,'/attempts/'+aid+'/discussion',{'message':'why?'}).status_code==200
    assert 'PRIVATE SCRATCHPAD MARKER' not in str(stub.messages)
    assert mutation(client,'/attempts/'+aid+'/discussion',{'message':'why?','include_scratchpad':True}).status_code==200
    assert 'PRIVATE SCRATCHPAD MARKER' in str(stub.messages)

def test_production_serves_spa_and_true_api_404(client):
    from pathlib import Path
    from app.config import ROOT
    if not (ROOT/'frontend/dist/index.html').exists():return
    r=client.get('/');assert r.status_code==200;assert 'text/html' in r.headers['content-type']
    r=client.get('/api/v1/unknown');assert r.status_code==404;assert 'application/json' in r.headers['content-type'];assert r.json()['error']['request_id']
