import json
import secrets
import time
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from collections import Counter, defaultdict
from typing import Annotated
from fastapi import FastAPI, APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import select, func, text, delete
from sqlalchemy.orm import Session as DBSession
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from app.config import settings, ROOT
from app.db import DB, Principal, Session, Bank, Item, Attempt, Review, Event, Restored, Admin, LoginAttempt, AdminSession, Invite, Grant, Inference, Setting, now, uid
from app.auth import database, principal, admin, fail, hash_token, set_guest, rotate
from app.schemas import *
from app.tasks.engine import FAMILIES, NAMES, LESSONS, public, grade, hint, explain
from app.tasks.rules import apply
from app.tasks.solvers import digest
from app.tasks.bank import get_task, BANK_VERSION
from app.curriculum import choose, adapt, POLICY_VERSION
from app import tutoring

@asynccontextmanager
async def lifespan(app):
    settings.validate_runtime()
    with DB() as db:
        if db.execute(text('SELECT version_num FROM alembic_version')).scalar()!='0002':
            raise RuntimeError('Database migration required: run python -m app.cli migrate.')
        counts={(f,l,s):c for f,l,s,c in db.execute(select(Bank.family,Bank.level,Bank.split,func.count()).group_by(Bank.family,Bank.level,Bank.split))}
        if any(counts.get((f,l,s),0)<n for f in ('dependencies','logic') for l in range(1,5) for s,n in [('practice',50),('check',15)]):
            raise RuntimeError('Required content is missing. Run python -m app.cli bank before starting.')
    yield

app=FastAPI(title='Human Fluid API',version='0.1.0',lifespan=lifespan)
api=APIRouter(prefix='/api/v1')
D=Annotated[DBSession,Depends(database)]

@app.middleware('http')
async def boundary(request:Request,call_next):
    request_id=uuid.uuid4().hex
    request.state.request_id=request_id
    def error(status,code,message): return JSONResponse({'error':{'code':code,'message':message,'request_id':request_id}},status_code=status)
    if request.url.path.startswith('/api') and request.method in ('POST','PATCH','DELETE','PUT'):
        if request.headers.get('origin') not in settings.allowed_origins or request.headers.get('sec-fetch-site')=='cross-site':
            return error(403,'origin_rejected',f'Open {settings.public_origin} to connect. If you host the app at another address, set PUBLIC_ORIGIN to that address and restart the server.')
        if request.headers.get('content-type','').split(';')[0]!='application/json':
            return error(415,'json_required','Send an application/json request.')
        data=b''
        async for chunk in request.stream():
            data+=chunk
            if len(data)>1048576: return error(413,'body_too_large','Request exceeds the 1 MB limit.')
        request._body=data
        if request.url.path!='/api/v1/guest':
            with DB() as db:
                p=db.scalar(select(Principal).where(Principal.token_hash==hash_token(request.cookies.get('hf_guest','')),Principal.expires>now()))
                if not p: return error(401,'guest_required','Start a guest profile first.')
                if not secrets.compare_digest(request.headers.get('x-csrf-token',''),p.csrf): return error(403,'csrf_rejected','Refresh this page before trying again.')
    try: response=await call_next(request)
    except Exception:
        return error(500,'internal_error','The request could not be completed. Your existing progress is saved.')
    response.headers['X-Request-ID']=request_id
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if request.url.path.startswith('/api'): response.headers['Cache-Control']='no-store'
    return response

@app.exception_handler(StarletteHTTPException)
async def http_error(request,exc):
    detail=exc.detail if isinstance(exc.detail,dict) else {'code':f'http_{exc.status_code}','message':str(exc.detail)}
    return JSONResponse({'error':{**detail,'request_id':request.state.request_id}},status_code=exc.status_code)
@app.exception_handler(RequestValidationError)
async def validation_error(request,exc):
    return JSONResponse({'error':{'code':'invalid_request','message':'Check the requested fields, formats, and size limits.','request_id':request.state.request_id}},status_code=422)

def owned(db,cls,id,p):
    obj=db.get(cls,id)
    if not obj or obj.owner!=p.id: fail(404,'That record is unavailable.','not_found')
    return obj

def event(db,p,kind,data): db.add(Event(owner=p.id,kind=kind,data=data))
def attempt_for(db,item): return db.scalar(select(Attempt).where(Attempt.item_id==item.id))
def visible(db,item):
    s=db.get(Session,item.session_id)
    return s.mode in ('mixed','focus') or (s.state=='completed' and s.released)

def item_view(db,item):
    s=db.get(Session,item.session_id); a=attempt_for(db,item)
    out={**public(item.task),'instance_id':item.id,'session_id':s.id,'mode':s.mode,'hints_used':item.hints,'queries':item.queries,'draft':item.draft,'rationale':item.rationale,'position':item.position+1,'total':s.total,'submitted':bool(a),'state':s.state,'feedback_sealed':not visible(db,item)}
    if a: out['result']=attempt_view(db,a,with_task=False)
    if s.mode in ('mixed','focus'): out['hints']=[hint(item.task,k,item.queries) for k in range(item.hints)]
    return out

def attempt_view(db,a,with_task=True):
    item=db.get(Item,a.item_id); s=db.get(Session,item.session_id); permitted=visible(db,item)
    aggregate=s.mode in ('mixed','focus') or s.state=='completed'
    out={'id':a.id,'family':item.task['family'],'difficulty':item.task['difficulty'],'mode':s.mode,'session_id':s.id,'created':a.created,'assisted':a.assisted,'correct':a.correct if permitted else None,'confidence':a.confidence,'reflection':a.reflection,'sealed':not permitted,'provenance':item.task['source']}
    if permitted:
        out.update(answer=a.answer,explanation=explain(item.task,a.answer,item.queries))
        if with_task: out['task']=item_view(db,item)
    return out

def session_view(db,s):
    items=db.scalars(select(Item).where(Item.session_id==s.id).order_by(Item.position)).all()
    current=items[-1] if items else None
    return {'id':s.id,'mode':s.mode,'family':s.family,'state':s.state,'total':s.total,'completed':sum(attempt_for(db,i) is not None for i in items),'current':item_view(db,current) if current else None,'released':s.released,'manifest':{k:v for k,v in s.manifest.items() if k!='tasks'}}

def idem_key(request):
    key=request.headers.get('idempotency-key','')
    if not 8<=len(key)<=100: fail(422,'A valid idempotency key is required.','idempotency_required')
    return key

def replay(db,p,kind,key,body):
    rows=db.scalars(select(Event).where(Event.owner==p.id,Event.kind==kind)).all()
    old=next((x for x in rows if x.data.get('key')==key),None)
    if old:
        if old.data['hash']!=digest(body): fail(409,'This request key was already used for different content.','idempotency_conflict')
        return old.data['result']

def save_replay(db,p,kind,key,body,result): event(db,p,kind,{'key':key,'hash':digest(body),'result':result})

@api.post('/guest')
def guest(request:Request,response:Response,db:D):
    p=db.scalar(select(Principal).where(Principal.token_hash==hash_token(request.cookies.get('hf_guest','')),Principal.expires>now()))
    if not p:
        token=secrets.token_urlsafe(32)
        p=Principal(token_hash=hash_token(token),csrf=secrets.token_urlsafe(32),expires=now()+settings.session_days*86400)
        db.add(p); db.flush(); set_guest(response,token,settings)
    return {'csrf_token':p.csrf,'guest':True}

@api.get('/me')
def me(request:Request,db:D):
    p=principal(request,db); a=db.get(AdminSession,hash_token(request.cookies.get('hf_admin','')))
    sessions=db.scalars(select(Session).where(Session.owner==p.id,Session.state.in_(['active','paused'])).order_by(Session.created.desc())).all()
    return {'guest':True,'csrf_token':p.csrf,'admin':bool(a and a.expires>now()),'levels':p.levels,'sessions':[{'id':s.id,'mode':s.mode,'state':s.state} for s in sessions]}

@api.get('/families')
def families():
    return [{'id':f,'name':NAMES[f],'lesson':LESSONS[f],'levels':4} for f in FAMILIES]

@api.post('/sessions')
def start(body:Start,request:Request,db:D):
    p=principal(request,db); key=idem_key(request); b=body.model_dump(); old=replay(db,p,'start',key,b)
    if old: return session_view(db,owned(db,Session,old['id'],p))
    if body.mode=='focus' and not body.family: fail(422,'Choose a family for focused practice.')
    total={'mixed':8,'focus':6,'check':10,'probe':6}[body.mode]
    s=Session(owner=p.id,mode=body.mode,family=body.family if body.mode=='focus' else None,total=total)
    db.add(s); db.flush()
    if body.mode in ('check','probe'):
        count=db.scalar(select(func.count()).select_from(Session).where(Session.owner==p.id,Session.mode==body.mode,Session.id!=s.id))
        form=count%2
        excluded=set()
        for candidate_form in range(form+1):
            tasks=[]
            for pos in range(total):
                f=FAMILIES[pos%5] if body.mode=='check' else 'ordering'
                t=get_task(db,f,2,'check' if body.mode=='check' else 'probe',candidate_form*100000+pos*1000+147,excluded)
                tasks.append(t); excluded.add(t['fingerprint'])
        exposure=db.scalar(select(func.count()).select_from(Event).where(Event.owner==p.id,Event.kind=='assessment_release')) or 0
        s.manifest={'version':'balanced-1' if body.mode=='check' else 'schedule-presentation-1','bank_version':BANK_VERSION,'form':chr(65+form),'fixed_level':2,'transfer_type':'presentation generalization; exploratory, related task' if body.mode=='probe' else None,'prior_releases':exposure,'repeated_form':count>=2,'tasks':tasks,'feedback':'sealed until explicit release after completion'}
    save_replay(db,p,'start',key,b,{'id':s.id})
    return session_view(db,s)

@api.get('/sessions/{id}')
def get_session(id:str,request:Request,db:D): return session_view(db,owned(db,Session,id,principal(request,db)))

@api.patch('/sessions/{id}')
def change_session(id:str,body:SessionChange,request:Request,db:D):
    p=principal(request,db); s=owned(db,Session,id,p)
    if s.state in ('completed','abandoned'): fail(409,'This session is already closed.')
    s.state=body.state
    return session_view(db,s)

@api.post('/sessions/{id}/next')
def next_item(id:str,request:Request,db:D):
    p=principal(request,db); s=owned(db,Session,id,p)
    if s.state in ('abandoned','paused'): fail(409,'Resume this session before continuing.')
    items=db.scalars(select(Item).where(Item.session_id==s.id).order_by(Item.position)).all()
    if items and not attempt_for(db,items[-1]): return session_view(db,s)
    if len(items)>=s.total: return session_view(db,s)
    action=choose(db,p,s,items)
    if s.mode in ('check','probe'): task=s.manifest['tasks'][len(items)]
    else:
        history=db.scalars(select(Item).where(Item.owner==p.id)).all()
        excluded={i.task['fingerprint'] for i in history}
        try: task=get_task(db,action.family,action.level,'practice',secrets.randbelow(10000000),excluded)
        except ValueError as e: fail(409,str(e),'content_exhausted')
    policy={'version':POLICY_VERSION,'eligible_actions':[{'family':f,'level':p.levels.get(f,1)} for f in ([s.family] if s.family else FAMILIES)],'selected':{'family':action.family,'level':action.level},'probability':None,'review_id':action.review_id}
    i=Item(owner=p.id,session_id=s.id,position=len(items),task=task,rationale=action.rationale,policy=policy)
    db.add(i); db.flush(); event(db,p,'teaching_action',{'item_id':i.id,**policy,'rationale':action.rationale})
    return session_view(db,s)

@api.post('/sessions/{id}/release')
def release(id:str,body:Confirm,request:Request,db:D):
    p=principal(request,db); s=owned(db,Session,id,p)
    if not body.confirm or s.state!='completed' or s.mode not in ('check','probe'): fail(409,'Finish the assessment and explicitly confirm exposure of its content.')
    if not s.released: event(db,p,'assessment_release',{'session_id':s.id,'manifest':{k:v for k,v in s.manifest.items() if k!='tasks'}})
    s.released=True
    return session_view(db,s)

@api.get('/instances/{id}')
def instance(id:str,request:Request,db:D): return item_view(db,owned(db,Item,id,principal(request,db)))

def active_item(db,p,id):
    i=owned(db,Item,id,p); s=db.get(Session,i.session_id)
    if attempt_for(db,i) or s.state!='active': fail(409,'This item is no longer accepting changes.')
    return i,s

@api.patch('/instances/{id}/draft')
def draft(id:str,body:Draft,request:Request,db:D):
    p=principal(request,db); i,s=active_item(db,p,id)
    if len(json.dumps(body.answer))>1000: fail(422,'Draft answer is too long.')
    i.draft=body.model_dump(); return {'saved':True}

@api.post('/instances/{id}/hints')
def hints(id:str,body:HintRequest,request:Request,db:D):
    p=principal(request,db); i,s=active_item(db,p,id)
    if s.mode not in ('mixed','focus'): fail(403,'Hints are unavailable during assessments.')
    if body.index>i.hints: fail(409,'Reveal hints in order.')
    value=hint(i.task,body.index,i.queries)
    if body.index==i.hints:
        i.hints+=1; event(db,p,'hint',{'item_id':i.id,'index':body.index})
    return {'hint':value,'hints_used':i.hints}

@api.post('/instances/{id}/queries')
def query(id:str,body:Query,request:Request,db:D):
    p=principal(request,db); i=owned(db,Item,id,p); key=idem_key(request); b=body.model_dump()
    old=replay(db,p,'query:'+id,key,b)
    if old: return old
    i,s=active_item(db,p,id)
    if i.task['family']!='hypothesis': fail(422,'This task has no experiment action.')
    x=body.input; scalar=i.task['render']['input_kind']=='number'
    valid=(type(x) is int and abs(x)<=10) if scalar else (isinstance(x,list) and len(x)<=8 and all(type(v) is int and abs(v)<=10 for v in x))
    if not valid: fail(422,'Use integers from −10 to 10; lists may have at most eight values.')
    if len(i.queries)>=12: fail(409,'The twelve-query limit has been reached. Identify a rule or finish this attempt.')
    q={'input':x,'output':apply(i.task['formal']['rule'],x)}; i.queries=i.queries+[q]
    result={'queries':i.queries}; save_replay(db,p,'query:'+id,key,b,result)
    return result

@api.post('/instances/{id}/submit')
def submit(id:str,body:Submission,request:Request,db:D):
    p=principal(request,db); i=owned(db,Item,id,p); a=attempt_for(db,i)
    if a: return attempt_view(db,a)
    i,s=active_item(db,p,id)
    try: correct=grade(i.task,body.answer)
    except ValueError as e: fail(422,str(e),'invalid_answer')
    a=Attempt(owner=p.id,item_id=i.id,answer=body.answer,correct=correct,assisted=i.hints>0,confidence=body.confidence)
    db.add(a); db.flush()
    event(db,p,'first_submit',{'attempt_id':a.id,'policy_version':POLICY_VERSION,'correct':correct,'assisted':a.assisted})
    if s.mode in ('mixed','focus'):
        adapt(db,p,i.task)
        review=db.get(Review,i.policy.get('review_id')) if i.policy.get('review_id') else None
        if review:
            review.completed=True
            interval=min(2,review.interval+1) if correct and not a.assisted else 0
            if correct and not a.assisted:
                db.add(Review(owner=p.id,family=i.task['family'],level=i.task['difficulty'],attempt_id=a.id,due=now()+[86400,259200,604800][interval],interval=interval))
        if not correct or i.hints>=2 or (review and a.assisted):
            db.add(Review(owner=p.id,family=i.task['family'],level=i.task['difficulty'],attempt_id=a.id,due=now()+86400,interval=0))
    if i.position+1>=s.total: s.state='completed'
    return attempt_view(db,a)

@api.get('/attempts')
def journal(request:Request,db:D,family:str | None=None,filter:str='all',offset:int=0,limit:int=30):
    p=principal(request,db)
    if offset<0 or not 1<=limit<=100: fail(422,'Invalid pagination.')
    rows=db.scalars(select(Attempt).where(Attempt.owner==p.id).order_by(Attempt.created.desc())).all()
    if family: rows=[a for a in rows if db.get(Item,a.item_id).task['family']==family]
    if filter=='mistakes': rows=[a for a in rows if not a.correct and not a.assisted and visible(db,db.get(Item,a.item_id))]
    if filter=='assisted': rows=[a for a in rows if a.assisted]
    return {'total':len(rows),'items':[attempt_view(db,a,with_task=False) for a in rows[offset:offset+limit]]}

@api.get('/attempts/{id}')
def get_attempt(id:str,request:Request,db:D): return attempt_view(db,owned(db,Attempt,id,principal(request,db)))
@api.patch('/attempts/{id}/reflection')
def reflection(id:str,body:Reflection,request:Request,db:D):
    p=principal(request,db); a=owned(db,Attempt,id,p)
    if not visible(db,db.get(Item,a.item_id)): fail(403,'Release the assessment before reviewing its items.')
    a.reflection=body.model_dump(); return {'saved':True}
@api.post('/instances/{id}/report')
def report(id:str,body:Report,request:Request,db:D):
    p=principal(request,db); i=owned(db,Item,id,p)
    event(db,p,'item_report',{'item_id':i.id,'source':i.task['source'],'fingerprint':i.task['fingerprint'],**body.model_dump()})
    return {'saved':True}
@api.post('/families/{family}/level')
def level(family:str,body:LevelChange,request:Request,db:D):
    p=principal(request,db)
    if family not in FAMILIES: fail(404,'Unknown family.')
    p.levels={**p.levels,family:body.level}; event(db,p,'manual_level',{'family':family,'level':body.level})
    return {'levels':p.levels}

@api.get('/reviews/due')
def due(request:Request,db:D):
    p=principal(request,db); rows=db.scalars(select(Review).where(Review.owner==p.id,Review.completed==False)).all()
    # An error becomes eligible next session, even before its calendar due date.
    return {'due':sum(r.due<=now() for r in rows),'next_session':len(rows),'families':dict(Counter(r.family for r in rows))}

@api.get('/progress')
def progress(request:Request,db:D):
    p=principal(request,db); groups=defaultdict(lambda:{'independent':0,'correct':0,'assisted':0,'hint_total':0})
    brier=[]; delayed=[]; hint_trend=defaultdict(lambda:{'attempts':0,'assisted':0,'hints':0})
    rows=db.execute(select(Attempt,Item,Session).join(Item,Attempt.item_id==Item.id).join(Session,Item.session_id==Session.id).where(Attempt.owner==p.id)).all()
    for a,i,s in rows:
        if s.mode not in ('mixed','focus'): continue
        g=groups[(i.task['family'],i.task['difficulty'])]
        if a.assisted: g['assisted']+=1
        else: g['independent']+=1; g['correct']+=int(a.correct)
        g['hint_total']+=i.hints
        week=int(a.created//604800)*604800
        trend=hint_trend[(week,i.task['family'],i.task['difficulty'])]; trend['attempts']+=1; trend['assisted']+=int(a.assisted); trend['hints']+=i.hints
        if a.confidence is not None: brier.append((a.confidence-int(a.correct))**2)
        if i.policy.get('review_id') and not a.assisted:
            review=db.get(Review,i.policy['review_id']); original=db.get(Attempt,review.attempt_id)
            if a.created-original.created>=86400: delayed.append(a.correct)
    checks=[]
    for s in db.scalars(select(Session).where(Session.owner==p.id,Session.mode.in_(['check','probe']),Session.state=='completed').order_by(Session.created)):
        outcomes=[a.correct for a,i,se in rows if se.id==s.id]
        checks.append({'session_id':s.id,'mode':s.mode,'manifest':{k:v for k,v in s.manifest.items() if k!='tasks'},'correct':sum(outcomes),'count':len(outcomes),'released':s.released,'created':s.created})
    return {'completed_sessions':db.scalar(select(func.count()).select_from(Session).where(Session.owner==p.id,Session.state=='completed')),'practice':[{'family':f,'difficulty':l,**v} for (f,l),v in sorted(groups.items())],'checks':checks,'calibration':{'brier':sum(brier)/len(brier) if brier else None,'count':len(brier)},'delayed_review':{'count':len(delayed),'correct':sum(delayed)},'hint_trend':[{'week':w,'family':f,'difficulty':l,**v} for (w,f,l),v in sorted(hint_trend.items())],'restored_unverified':db.scalar(select(func.count()).select_from(Restored).where(Restored.owner==p.id)),'levels':p.levels}

@api.post('/export')
def export(request:Request,db:D):
    p=principal(request,db); history=[]
    for a in db.scalars(select(Attempt).where(Attempt.owner==p.id).order_by(Attempt.created)):
        v=attempt_view(db,a,False)
        record={k:v[k] for k in ('family','difficulty','mode','correct','assisted','created','reflection','provenance')}
        if visible(db,db.get(Item,a.item_id)):
            i=db.get(Item,a.item_id)
            messages=db.scalars(select(Inference).where(Inference.owner==p.id,Inference.attempt_id==a.id,Inference.state=='completed',Inference.reply.is_not(None)).order_by(Inference.created)).all()
            record['review']={'instructions':i.task['instructions'],'render':i.task['render'],'answer':a.answer,'steps':v['explanation']['steps'],'queries':i.queries,'scratchpad':i.draft.get('scratchpad',''),'discussion':[{'message':m.user_message,'reply':m.reply} for m in messages]}
        history.append(record)
    for r in db.scalars(select(Restored).where(Restored.owner==p.id)): history.append(r.data)
    return {'schema_version':1,'history':history}

@api.get('/restored')
def restored_history(request:Request,db:D,offset:int=0):
    p=principal(request,db)
    if offset<0: fail(422,'Invalid offset.')
    return {'total':db.scalar(select(func.count()).select_from(Restored).where(Restored.owner==p.id)),'items':[{'id':r.id,**r.data} for r in db.scalars(select(Restored).where(Restored.owner==p.id).offset(offset).limit(30))]}
@api.post('/restore')
def restore(body:Restore,request:Request,db:D):
    p=principal(request,db); key=idem_key(request); b=body.model_dump(); old=replay(db,p,'restore',key,b)
    if old: return old
    count=db.scalar(select(func.count()).select_from(Restored).where(Restored.owner==p.id))
    if count+len(body.history)>2000: fail(422,'A profile can contain at most 2,000 restored records.')
    existing={digest(r.data) for r in db.scalars(select(Restored).where(Restored.owner==p.id))}
    inserted=0
    for row in body.history:
        data=row.model_dump(exclude_none=True)
        fingerprint=digest(data)
        if fingerprint not in existing:
            db.add(Restored(owner=p.id,data=data)); existing.add(fingerprint); inserted+=1
    result={'restored':inserted,'verified':False}; save_replay(db,p,'restore',key,b,result)
    return result
@api.delete('/me/data')
def delete_data(body:Confirm,request:Request,response:Response,db:D):
    p=principal(request,db)
    if not body.confirm: fail(422,'Explicitly confirm deletion of this guest profile.')
    db.execute(delete(AdminSession).where(AdminSession.id==hash_token(request.cookies.get('hf_admin',''))))
    db.execute(delete(Principal).where(Principal.id==p.id)); response.delete_cookie('hf_guest'); response.delete_cookie('hf_admin')
    return {'deleted':True}

def inference_enabled(db):
    flag=db.get(Setting,'ai_enabled')
    return settings.ai_enabled and (flag.value if flag else True) and settings.ai_provider!='disabled'

def active_grant(db,p):
    grants=db.scalars(select(Grant).where(Grant.owner==p.id,Grant.revoked==False,Grant.expires>now())).all()
    return next((g for g in grants if not db.get(Invite,g.invite_id).revoked),None)

def ai_status(db,p):
    g=active_grant(db,p); enabled=inference_enabled(db); configuration='disabled'
    if enabled:
        try: tutoring.get_provider(); configuration='configured'
        except tutoring.ProviderFailure: configuration='unreachable'
    day=now()//86400*86400
    used=db.scalar(select(func.count()).select_from(Inference).where(Inference.grant_id==g.id,Inference.created>=day)) if g else 0
    reserved=db.scalar(select(func.coalesce(func.sum(Inference.tokens),0)).where(Inference.grant_id==g.id,Inference.created>=day)) if g else 0
    return {'remaining_tokens_today':max(0,settings.ai_grant_tokens_per_day-reserved) if g else 0,'approved':bool(g),'provider_status':configuration,'remaining_today':max(0,min(g.daily_limit,settings.ai_grant_requests_per_day)-used) if g else 0,'message':'Discussion sends the rendered problem, your answer, the worked explanation, and recent thread messages. Scratchpad is sent only if you opt in. Core practice never requires AI.'}

@api.get('/ai/status')
def status(request:Request,db:D): return ai_status(db,principal(request,db))
@api.post('/ai/redeem')
def redeem(body:Redeem,request:Request,response:Response,db:D):
    p=principal(request,db)
    invite=db.scalar(select(Invite).where(Invite.code_hash==hash_token(body.code),Invite.expires>now(),Invite.revoked==False,Invite.redeemed==False))
    if not invite: fail(403,'This invitation is invalid, expired, revoked, or already used.','invite_unavailable')
    invite.redeemed=True
    db.add(Grant(owner=p.id,invite_id=invite.id,expires=invite.expires,daily_limit=invite.daily_limit))
    rotate(p,response,settings); db.flush()
    return {**ai_status(db,p),'csrf_token':p.csrf}

@api.get('/attempts/{id}/discussion')
def thread(id:str,request:Request,db:D):
    p=principal(request,db); a=owned(db,Attempt,id,p)
    if not visible(db,db.get(Item,a.item_id)): fail(403,'Assessment discussion stays sealed until explicit release.')
    messages=db.scalars(select(Inference).where(Inference.owner==p.id,Inference.attempt_id==a.id,Inference.state=='completed',Inference.reply.is_not(None)).order_by(Inference.created)).all()
    return {'messages':[{'message':m.user_message,'reply':m.reply,'created':m.created} for m in messages],**ai_status(db,p)}

@api.delete('/attempts/{id}/discussion')
def clear_thread(id:str,body:Confirm,request:Request,db:D):
    p=principal(request,db); a=owned(db,Attempt,id,p)
    if not body.confirm: fail(422,'Confirm clearing this discussion.')
    rows=db.scalars(select(Inference).where(Inference.owner==p.id,Inference.attempt_id==a.id)).all()
    for row in rows:
        if row.state in ('reserved','outcome-unknown'): fail(409,'A provider request is unresolved. Try later or contact the owner.')
        row.user_message=''; row.reply=None
    return {'cleared':True}

@api.post('/attempts/{id}/discussion')
def discuss(id:str,body:Chat,request:Request,db:D):
    p=principal(request,db); a=owned(db,Attempt,id,p); i=db.get(Item,a.item_id)
    if not visible(db,i): fail(403,'Release assessment content before discussion.')
    g=active_grant(db,p)
    if not g: fail(403,'An active owner-issued AI invitation is required.','approval_required')
    if not inference_enabled(db): fail(503,'AI discussion is disabled. The worked explanation remains available.','provider_disabled')
    key=idem_key(request); body_hash=digest({'attempt_id':id,**body.model_dump()})
    old=db.scalar(select(Inference).where(Inference.owner==p.id,Inference.key==key))
    if old:
        if old.body_hash!=body_hash: fail(409,'This request key was already used for different content.','idempotency_conflict')
        if old.state=='completed': return {'reply':old.reply,'request_id':old.id,'state':old.state}
        fail(409,'This request was already reserved. Its state is '+old.state+'. It will not be sent again.','request_already_reserved')
    try: provider=tutoring.get_provider()
    except tutoring.ProviderFailure: fail(503,'Provider configuration is unavailable. Contact the owner.','provider_unavailable')
    history=db.scalars(select(Inference).where(Inference.owner==p.id,Inference.attempt_id==a.id,Inference.state=='completed',Inference.reply.is_not(None)).order_by(Inference.created)).all()
    if len(history)>=30: fail(429,'This thread has reached its message limit. Clear the discussion to begin a fresh context.')
    messages=tutoring.context(i.task,a,explain(i.task,a.answer,i.queries),i.draft,history,body)
    estimate=provider.estimate(messages)
    if estimate>settings.ai_max_input_tokens: fail(422,'This discussion context is too long. Clear the thread or shorten your message.')
    reservation=estimate+settings.ai_max_output_tokens
    day=now()//86400*86400
    all_today=db.scalars(select(Inference).where(Inference.created>=day)).all()
    mine=[r for r in all_today if r.grant_id==g.id]
    if any(r.state in ('reserved','outcome-unknown') for r in db.scalars(select(Inference).where(Inference.grant_id==g.id))): fail(429,'One request is already pending or unresolved for this grant.')
    if len([r for r in mine if r.created>now()-60])>=settings.ai_grant_requests_per_minute or len(mine)>=min(g.daily_limit,settings.ai_grant_requests_per_day) or len(all_today)>=settings.ai_global_requests_per_day:
        fail(429,'The request allowance has been reached. Try after the limit resets.','quota_reached')
    if sum(r.tokens for r in mine)+reservation>settings.ai_grant_tokens_per_day or sum(r.tokens for r in all_today)+reservation>settings.ai_global_tokens_per_day:
        fail(429,'The daily token reservation allowance has been reached.','token_quota_reached')
    row=Inference(owner=p.id,grant_id=g.id,attempt_id=a.id,key=key,body_hash=body_hash,state='reserved',tokens=reservation,user_message=body.message)
    db.add(row); db.flush(); row_id=row.id
    db.commit()
    try:
        reply,usage=provider.generate(messages)
        if not isinstance(reply,str) or len(reply.encode('utf-8'))>12000: raise tutoring.ProviderFailure('Provider output exceeded limits.')
        if settings.ai_api_key and settings.ai_api_key in reply: raise tutoring.ProviderFailure('Provider output was rejected.')
    except tutoring.ProviderFailure as e:
        db.execute(text('BEGIN IMMEDIATE')); row=db.get(Inference,row_id,populate_existing=True)
        if row: row.state='outcome-unknown' if isinstance(e,tutoring.OutcomeUnknown) else 'failed'; db.commit()
        fail(503,'Provider response unavailable. No automatic retry was made; the conservative reservation remains.','provider_error')
    except Exception:
        db.execute(text('BEGIN IMMEDIATE')); row=db.get(Inference,row_id,populate_existing=True)
        if row: row.state='outcome-unknown'; db.commit()
        fail(503,'Provider outcome is unknown. The reservation is retained.','provider_error')
    db.execute(text('BEGIN IMMEDIATE')); row=db.get(Inference,row_id,populate_existing=True)
    current_grant=db.get(Grant,g.id,populate_existing=True); current_invite=db.get(Invite,g.invite_id,populate_existing=True)
    if not row or not current_grant or current_grant.revoked or current_grant.expires<=now() or current_invite.revoked or not inference_enabled(db):
        if row: row.state='failed'; db.commit()
        fail(403,'Discussion access changed while the request was running.')
    row.reply=reply; row.state='completed'
    if type(usage) is int and 0<=usage<=reservation: row.tokens=usage
    return {'reply':reply,'request_id':row.id,'state':'completed'}

@api.post('/admin/login')
def admin_login(body:Login,request:Request,response:Response,db:D):
    p=principal(request,db); ip_hash=hash_token(request.client.host if request.client else 'local')
    db.execute(delete(LoginAttempt).where(LoginAttempt.created<now()-86400))
    recent=db.scalar(select(func.count()).select_from(LoginAttempt).where(LoginAttempt.ip_hash==ip_hash,LoginAttempt.created>now()-900))
    if recent>=10: fail(429,'Owner sign-in temporarily rate limited.')
    db.add(LoginAttempt(ip_hash=ip_hash)); db.commit(); db.execute(text('BEGIN IMMEDIATE'))
    a=db.scalar(select(Admin).where(Admin.username==body.username))
    ph=PasswordHasher(); encoded=ph.hash(secrets.token_urlsafe(24)) if not a else a.password
    try: valid=ph.verify(encoded,body.password) and a is not None
    except VerificationError: valid=False
    if not valid: fail(403,'Sign-in details are invalid.','login_failed')
    token=secrets.token_urlsafe(32); db.add(AdminSession(id=hash_token(token),admin_id=a.id,expires=now()+3600))
    response.set_cookie('hf_admin',token,max_age=3600,httponly=True,secure=settings.cookie_secure,samesite='strict',path='/')
    return {'admin':True}
@api.post('/admin/logout')
def admin_logout(request:Request,response:Response,db:D):
    a=admin(request,db); db.delete(a); response.delete_cookie('hf_admin'); return {'logged_out':True}
@api.get('/admin/status')
def admin_status(request:Request,db:D):
    admin(request,db)
    return {'enabled':inference_enabled(db),'provider':settings.ai_provider,'configured':bool(settings.ai_base_url and settings.ai_model),'requests_today':db.scalar(select(func.count()).select_from(Inference).where(Inference.created>=now()//86400*86400)),'grants':[{'id':g.id,'label':db.get(Invite,g.invite_id).label,'expires':g.expires,'revoked':g.revoked,'daily_limit':g.daily_limit,'requests':db.scalar(select(func.count()).select_from(Inference).where(Inference.grant_id==g.id))} for g in db.scalars(select(Grant))], 'invites':[{'id':v.id,'label':v.label,'expires':v.expires,'redeemed':v.redeemed,'revoked':v.revoked} for v in db.scalars(select(Invite))]}
@api.post('/admin/inference')
def toggle_inference(body:Toggle,request:Request,db:D):
    admin(request,db)
    if body.enabled and (not settings.ai_enabled or settings.ai_provider=='disabled'): fail(409,'Enable and configure a provider in server settings first.')
    flag=db.get(Setting,'ai_enabled')
    if flag: flag.value=body.enabled
    else: db.add(Setting(key='ai_enabled',value=body.enabled))
    return {'enabled':body.enabled}
@api.post('/admin/invites')
def new_invite(body:NewInvite,request:Request,db:D):
    admin(request,db); code=secrets.token_urlsafe(32)
    invite=Invite(code_hash=hash_token(code),label=body.label,expires=now()+body.days*86400,daily_limit=body.daily_limit)
    db.add(invite); db.flush()
    return {'id':invite.id,'code':code,'expires':invite.expires,'message':'Displayed once. Deliver this invitation out of band; possession authorizes redemption.'}
@api.post('/admin/grants/{id}/revoke')
def revoke(id:str,request:Request,db:D):
    admin(request,db); g=db.get(Grant,id)
    if not g: fail(404,'Grant unavailable.')
    g.revoked=True; return {'revoked':True}
@api.post('/admin/invites/{id}/revoke')
def revoke_invite(id:str,request:Request,db:D):
    admin(request,db); i=db.get(Invite,id)
    if not i: fail(404,'Invitation unavailable.')
    i.revoked=True; return {'revoked':True}

@app.get('/healthz')
def health(): return {'status':'ok'}
@app.get('/readyz')
def ready(db:D):
    db.execute(text('SELECT 1'))
    if (db.scalar(select(func.count()).select_from(Bank)) or 0)<520: fail(503,'Required content is unavailable.')
    return {'status':'ready'}
app.include_router(api)
@app.api_route('/api/{path:path}',methods=['GET','POST','PATCH','DELETE','PUT'],include_in_schema=False)
def missing_api(path:str): fail(404,'API route not found.','not_found')
static=ROOT/'frontend/dist'
if (static/'assets').exists(): app.mount('/assets',StaticFiles(directory=static/'assets'),name='assets')
@app.get('/{path:path}')
def spa(path:str):
    index=static/'index.html'
    if not index.exists(): fail(404,'Build the frontend or use the Vite development server.')
    return FileResponse(index)
