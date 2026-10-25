import time
import uuid
from pathlib import Path
from sqlalchemy import create_engine, event, Column, String, Integer, Float, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

def uid(): return uuid.uuid4().hex
def now(): return time.time()
class Base(DeclarativeBase): pass
class Principal(Base):
    __tablename__ = 'principals'
    id = Column(String, primary_key=True, default=uid)
    token_hash = Column(String, unique=True, nullable=False)
    csrf = Column(String, nullable=False)
    expires = Column(Float, nullable=False)
    created = Column(Float, default=now)
    levels = Column(JSON, default=dict)
class Session(Base):
    __tablename__ = 'sessions'
    id = Column(String, primary_key=True, default=uid)
    owner = Column(String, ForeignKey('principals.id', ondelete='CASCADE'), nullable=False, index=True)
    mode = Column(String, nullable=False)
    family = Column(String)
    state = Column(String, default='active')
    total = Column(Integer, nullable=False)
    created = Column(Float, default=now)
    released = Column(Boolean, default=False)
    manifest = Column(JSON, default=dict)
class Bank(Base):
    __tablename__ = 'task_bank'
    id = Column(String, primary_key=True, default=uid)
    family = Column(String, nullable=False, index=True)
    level = Column(Integer, nullable=False)
    split = Column(String, nullable=False)
    fingerprint = Column(String, nullable=False)
    task = Column(JSON, nullable=False)
    __table_args__ = (UniqueConstraint('family','level','split','fingerprint'),)
class Item(Base):
    __tablename__ = 'issued_items'
    id = Column(String, primary_key=True, default=uid)
    owner = Column(String, ForeignKey('principals.id', ondelete='CASCADE'), nullable=False, index=True)
    session_id = Column(String, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    position = Column(Integer, nullable=False)
    task = Column(JSON, nullable=False)
    hints = Column(Integer, default=0)
    queries = Column(JSON, default=list)
    draft = Column(JSON, default=dict)
    rationale = Column(String, nullable=False)
    policy = Column(JSON, default=dict)
    created = Column(Float, default=now)
    __table_args__ = (UniqueConstraint('session_id','position'),)
class Attempt(Base):
    __tablename__ = 'attempts'
    id = Column(String, primary_key=True, default=uid)
    item_id = Column(String, ForeignKey('issued_items.id', ondelete='CASCADE'), unique=True, nullable=False)
    owner = Column(String, ForeignKey('principals.id', ondelete='CASCADE'), nullable=False, index=True)
    answer = Column(JSON, nullable=False)
    correct = Column(Boolean, nullable=False)
    assisted = Column(Boolean, nullable=False)
    confidence = Column(Float)
    created = Column(Float, default=now)
    reflection = Column(JSON, default=dict)
class Review(Base):
    __tablename__ = 'review_queue'
    id = Column(String, primary_key=True, default=uid)
    owner = Column(String, ForeignKey('principals.id', ondelete='CASCADE'), nullable=False)
    family = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    attempt_id = Column(String, ForeignKey('attempts.id', ondelete='CASCADE'), nullable=False)
    due = Column(Float, nullable=False)
    interval = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
class Event(Base):
    __tablename__ = 'events'
    id = Column(String, primary_key=True, default=uid)
    owner = Column(String, ForeignKey('principals.id', ondelete='CASCADE'), nullable=False)
    kind = Column(String, nullable=False)
    data = Column(JSON, default=dict)
    created = Column(Float, default=now)
class Restored(Base):
    __tablename__ = 'restored_history'
    id = Column(String, primary_key=True, default=uid)
    owner = Column(String, ForeignKey('principals.id', ondelete='CASCADE'), nullable=False)
    data = Column(JSON, nullable=False)
class LoginAttempt(Base):
    __tablename__ = 'admin_login_attempts'
    id = Column(String, primary_key=True, default=uid)
    ip_hash = Column(String, nullable=False, index=True)
    created = Column(Float, default=now)
class Admin(Base):
    __tablename__ = 'admin_users'
    id = Column(String, primary_key=True, default=uid)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
class AdminSession(Base):
    __tablename__ = 'admin_sessions'
    id = Column(String, primary_key=True)
    admin_id = Column(String, ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    expires = Column(Float, nullable=False)
class Invite(Base):
    __tablename__ = 'ai_invites'
    id = Column(String, primary_key=True, default=uid)
    code_hash = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False)
    expires = Column(Float, nullable=False)
    redeemed = Column(Boolean, default=False)
    revoked = Column(Boolean, default=False)
    daily_limit = Column(Integer, default=30)
class Grant(Base):
    __tablename__ = 'ai_grants'
    id = Column(String, primary_key=True, default=uid)
    owner = Column(String, ForeignKey('principals.id', ondelete='CASCADE'), nullable=False)
    invite_id = Column(String, ForeignKey('ai_invites.id'), nullable=False, unique=True)
    expires = Column(Float, nullable=False)
    revoked = Column(Boolean, default=False)
    daily_limit = Column(Integer, default=30)
class Inference(Base):
    __tablename__ = 'inference_requests'
    id = Column(String, primary_key=True, default=uid)
    owner = Column(String, ForeignKey('principals.id', ondelete='CASCADE'), nullable=False)
    grant_id = Column(String, ForeignKey('ai_grants.id', ondelete='CASCADE'), nullable=False)
    attempt_id = Column(String, ForeignKey('attempts.id', ondelete='CASCADE'), nullable=False)
    key = Column(String, nullable=False)
    body_hash = Column(String, nullable=False)
    state = Column(String, nullable=False)
    tokens = Column(Integer, nullable=False)
    created = Column(Float, default=now)
    user_message = Column(String, nullable=False)
    reply = Column(String)
    __table_args__ = (UniqueConstraint('owner','key'),)
class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True)
    value = Column(JSON)

def make_engine(url):
    if url.startswith('sqlite:///') and ':memory:' not in url:
        Path(url.removeprefix('sqlite:///')).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={'check_same_thread': False, 'timeout': 20})
    @event.listens_for(engine, 'connect')
    def pragma(conn, _):
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=20000')
    return engine
engine = make_engine(settings.database_url)
DB = sessionmaker(engine, expire_on_commit=False)
