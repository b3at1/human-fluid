from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')
class Start(Strict):
    mode: Literal['mixed','focus','check','probe']='mixed'
    family: Literal['dependencies','logic','ordering','induction','hypothesis'] | None=None
class Submission(Strict):
    answer: Any
    confidence: float | None=Field(None,ge=0,le=1)
class Query(Strict):
    input: Any
class HintRequest(Strict):
    index: int=Field(ge=0,le=2)
class Draft(Strict):
    scratchpad: str=Field('',max_length=6000)
    answer: Any=None
    confidence: float | None=Field(None,ge=0,le=1)
class Reflection(Strict):
    category: Literal['missing constraint','untested alternative','wrong rule','execution mistake','unclear instruction','other'] | None=None
    note: str=Field('',max_length=3000)
class Report(Strict):
    category: Literal['confusing','incorrect','accessibility','other']
    note: str=Field('',max_length=1000)
class SessionChange(Strict):
    state: Literal['active','paused','abandoned']
class LevelChange(Strict):
    level: int=Field(ge=1,le=4)
class Confirm(Strict):
    confirm: bool
class Redeem(Strict):
    code: str=Field(min_length=20,max_length=100)
class Chat(Strict):
    message: str=Field(min_length=1,max_length=2000)
    include_scratchpad: bool=False
    @field_validator('message')
    @classmethod
    def nonblank(cls,v):
        if not v.strip(): raise ValueError('Message cannot be blank')
        return v
class Login(Strict):
    username: str=Field(min_length=1,max_length=80)
    password: str=Field(min_length=1,max_length=200)
class NewInvite(Strict):
    label: str=Field(min_length=1,max_length=80)
    days: int=Field(7,ge=1,le=90)
    daily_limit: int=Field(30,ge=1,le=30)
class Toggle(Strict):
    enabled: bool
class SnapshotEdge(Strict):
    prerequisite: int=Field(ge=0,le=20)
    course: int=Field(ge=0,le=20)
class SnapshotPerson(Strict):
    id: str=Field(max_length=10)
    name: str=Field(max_length=80)
    statement: str=Field(max_length=4000)
class SnapshotRule(Strict):
    id: str=Field(max_length=80)
    label: str=Field(max_length=200)
class SnapshotObservation(Strict):
    input: int | list[int]
    output: int | list[int]
    @field_validator('input','output')
    @classmethod
    def bound_values(cls,v):
        values=v if isinstance(v,list) else [v]
        if len(values)>12 or any(abs(x)>10000 for x in values): raise ValueError('Observation out of bounds')
        return v
class SnapshotScheduleRow(Strict):
    task: str=Field(max_length=20)
    prerequisites: list[str]=Field(max_length=12)
class SnapshotRender(Strict):
    kind: Literal['dependency_graph','statements','ordering','induction','hypothesis']
    schedule_rows: list[SnapshotScheduleRow] | None=Field(None,max_length=12)
    courses: list[int] | None=Field(None,max_length=20)
    edges: list[SnapshotEdge] | None=Field(None,max_length=100)
    people: list[SnapshotPerson] | None=Field(None,max_length=6)
    labels: list[str] | None=Field(None,max_length=12)
    premises: list[str] | None=Field(None,max_length=50)
    claim: str | None=Field(None,max_length=1000)
    candidates: list[SnapshotRule] | None=Field(None,max_length=12)
    examples: list[SnapshotObservation] | None=Field(None,max_length=12)
    target: int | list[int] | None=None
    input_kind: Literal['number','list'] | None=None
    presentation: Literal['abstract','schedule','function','instrument'] | None=None
    @field_validator('labels','premises')
    @classmethod
    def bound_strings(cls,v):
        if v and any(len(x)>2000 for x in v): raise ValueError('Content too long')
        return v
class SnapshotMessage(Strict):
    message: str=Field(max_length=2000)
    reply: str=Field(max_length=12000)
class ReviewSnapshot(Strict):
    instructions: str=Field(max_length=2000)
    render: SnapshotRender
    answer: Any
    steps: list[str]=Field(max_length=50)
    queries: list[SnapshotObservation]=Field(default_factory=list,max_length=12)
    scratchpad: str=Field('',max_length=6000)
    discussion: list[SnapshotMessage]=Field(default_factory=list,max_length=30)
    @field_validator('answer')
    @classmethod
    def bound_answer(cls,v):
        import json
        if len(json.dumps(v))>1000: raise ValueError('Answer too long')
        return v
    @field_validator('steps')
    @classmethod
    def bound_steps(cls,v):
        if any(len(x)>4000 for x in v): raise ValueError('Step too long')
        return v
class RestoredEntry(Strict):
    family: Literal['dependencies','logic','ordering','induction','hypothesis']
    difficulty: int=Field(ge=1,le=4)
    mode: Literal['mixed','focus','check','probe']
    correct: bool | None=None
    assisted: bool
    created: float=Field(ge=0,le=4102444800)
    reflection: Reflection=Field(default_factory=Reflection)
    provenance: str=Field(max_length=200)
    review: ReviewSnapshot | None=None
class Restore(Strict):
    schema_version: Literal[1]
    history: list[RestoredEntry]=Field(max_length=2000)
