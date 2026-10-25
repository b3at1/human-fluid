"""Transparent rule policy. Propensities deliberately remain null."""
from dataclasses import dataclass
from typing import Protocol
from sqlalchemy import select
from app.db import Attempt, Item, Review, Session, now
from app.tasks.engine import FAMILIES

POLICY_VERSION='rules-1'
@dataclass
class TeachingAction:
    family: str
    level: int
    rationale: str
    review_id: str | None = None
class TeachingPolicy(Protocol):
    def select_next(self, observation: dict, eligible_actions: list) -> TeachingAction: ...

class RulePolicy:
    def select_next(self, observation, eligible_actions):
        if observation.get('due'):
            r=observation['due'][0]
            return TeachingAction(r.family,r.level,'Due review: practice a fresh related structure.',r.id)
        family=min(eligible_actions,key=lambda f:observation['counts'].get(f,0))
        return TeachingAction(family,observation['levels'].get(family,1),'Broad coverage: '+('continue focused practice.' if len(eligible_actions)==1 else 'practice the least-exposed family.'))

def choose(db,principal,session,items):
    position=len(items)
    if session.mode in ('check','probe'):
        family=FAMILIES[position%5] if session.mode=='check' else 'ordering'
        return TeachingAction(family,2,'Fixed check configuration; curriculum adaptation is suspended.' if session.mode=='check' else 'Exploratory presentation transfer: ordering constraints in a scheduling wrapper.')
    families=[session.family] if session.family else FAMILIES
    counts={f:0 for f in families}
    for i in items:
        if i.task['family'] in counts: counts[i.task['family']]+=1
    due=db.scalars(select(Review).where(Review.owner==principal.id,Review.completed==False,Review.family.in_(families))).all()
    due=[r for r in due if r.due<=now() or db.get(Attempt,r.attempt_id).created<session.created]
    review_count=sum(bool(i.policy.get('review_id')) for i in items)
    if review_count>=session.total//2: due=[]
    return RulePolicy().select_next({'due':due,'counts':counts,'levels':principal.levels},families)

def adapt(db,principal,task):
    family=task['family']; level=task['difficulty']
    if level!=principal.levels.get(family,1): return
    rows=db.execute(select(Attempt,Item).join(Item,Item.id==Attempt.item_id).join(Session,Session.id==Item.session_id).where(Attempt.owner==principal.id,Attempt.assisted==False,Session.mode.in_(['mixed','focus'])).order_by(Attempt.created.desc())).all()
    rows=[(a,i) for a,i in rows if i.task['family']==family and i.task['difficulty']==level][:6]
    distinct=len(set(i.task['fingerprint'] for _,i in rows))
    correct=sum(a.correct for a,_ in rows)
    levels=dict(principal.levels)
    if len(rows)>=6 and correct>=5 and distinct>1: levels[family]=min(4,level+1)
    elif len(rows)>=5 and correct<=2: levels[family]=max(1,level-1)
    principal.levels=levels
