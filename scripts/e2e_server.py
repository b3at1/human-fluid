"""Isolated synthetic browser-test profile. NEVER mounted in app.main."""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
root=Path(__file__).resolve().parents[1]
profile=tempfile.TemporaryDirectory(prefix='human-fluid-browser-')
os.environ['DATABASE_URL']='sqlite:///'+str(Path(profile.name)/'test.db')
os.environ['PUBLIC_ORIGIN']='http://localhost:5173'
os.environ['AI_PROVIDER']='local'
os.environ['AI_ENABLED']='true'
os.environ['AI_API_KEY']=''
os.environ['MPLCONFIGDIR']='/tmp/human-fluid-mpl'
from app.db import Base,engine,DB,Bank,Invite,Principal,Item,now
from sqlalchemy import create_engine,select,text
from app.auth import hash_token
from app import main,tutoring
from fastapi import Request
source=create_engine('sqlite:///'+str(root/'data/human-fluid.db'))
Base.metadata.create_all(engine)
with source.connect() as conn,DB.begin() as db:
    rows=conn.execute(select(Bank.__table__)).mappings().all()
    for row in rows:db.add(Bank(**dict(row)))
    db.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'));db.execute(text("INSERT INTO alembic_version VALUES ('0002')"))
class TestProvider:
    def estimate(self,messages):return 1000
    def generate(self,messages):return 'SYNTHETIC TEST PROVIDER: Follow each arrow from the prerequisite to the dependent course. This response verifies the discussion flow only.',150

tutoring.get_provider=lambda:TestProvider()
@main.app.get('/api/__test/solution/{id}')
def test_solution(id:str,request:Request):
    with DB() as db:
        p=main.principal(request,db);i=main.owned(db,Item,id,p);return {'answer':i.task['solution']}
@main.app.post('/api/__test/invite')
def test_invite():
    import secrets
    code=secrets.token_urlsafe(32)
    with DB.begin() as db:db.add(Invite(code_hash=hash_token(code),label='SYNTHETIC BROWSER TEST',expires=now()+600))
    return {'code':code}
# Test routes were appended after the production catchall. Reorder only here.
main.app.router.routes.sort(key=lambda r:0 if getattr(r,'path','').startswith('/api/__test') else 1)
import uvicorn
uvicorn.run(main.app,host='127.0.0.1',port=8000)
