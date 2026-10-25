import hashlib
import secrets
from fastapi import Request, HTTPException
from sqlalchemy import select, text
from app.db import DB, Principal, AdminSession, now

def hash_token(token): return hashlib.sha256(token.encode()).hexdigest()
def fail(status,message,code=None): raise HTTPException(status,detail={'code':code or f'http_{status}','message':message})
def database():
    with DB() as db:
        # Serialize read-modify-write, including all quota and single-use operations.
        db.execute(text('BEGIN IMMEDIATE'))
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback(); raise

def principal(request:Request,db):
    token=request.cookies.get('hf_guest','')
    p=db.scalar(select(Principal).where(Principal.token_hash==hash_token(token),Principal.expires>now()))
    if not p: fail(401,'Your guest session has expired. Start a new guest profile.','guest_required')
    return p

def admin(request,db):
    principal(request,db)
    token=request.cookies.get('hf_admin','')
    a=db.get(AdminSession,hash_token(token))
    if not a or a.expires<=now(): fail(403,'Owner sign-in required.','admin_required')
    return a

def set_guest(response,token,settings):
    response.set_cookie('hf_guest',token,max_age=settings.session_days*86400,httponly=True,secure=settings.cookie_secure,samesite='lax',path='/')

def rotate(p,response,settings):
    token=secrets.token_urlsafe(32); p.token_hash=hash_token(token); p.csrf=secrets.token_urlsafe(32)
    set_guest(response,token,settings)
