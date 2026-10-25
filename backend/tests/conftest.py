import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from app import db as models
from app import main,auth

@pytest.fixture(scope='session')
def bank_rows():
    with models.DB() as db:
        rows=db.scalars(select(models.Bank)).all()
        assert len(rows)>=520,'Generate the content bank with python -m app.cli bank first.'
        return [{'family':r.family,'level':r.level,'split':r.split,'fingerprint':r.fingerprint,'task':r.task} for r in rows]

@pytest.fixture
def database(tmp_path,monkeypatch,bank_rows):
    engine=models.make_engine('sqlite:///'+str(tmp_path/'test.db'))
    models.Base.metadata.create_all(engine)
    with engine.begin() as conn: conn.exec_driver_sql('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'); conn.exec_driver_sql("INSERT INTO alembic_version VALUES ('0002')")
    factory=sessionmaker(engine,expire_on_commit=False)
    with factory.begin() as db: db.add_all([models.Bank(**r) for r in bank_rows])
    monkeypatch.setattr(main,'DB',factory);monkeypatch.setattr(auth,'DB',factory)
    # FastAPI's dependency resolves database's module globals.
    yield factory
    engine.dispose()

@pytest.fixture
def client(database):
    with TestClient(main.app) as client:
        client.headers['Origin']=main.settings.public_origin
        r=client.post('/api/v1/guest',json={}); assert r.status_code==200,r.text
        client.headers['X-CSRF-Token']=r.json()['csrf_token']
        yield client

def mutation(client,path,body=None,key=None,method='post'):
    import uuid
    return client.request(method,'/api/v1'+path,json=body or {},headers={'Idempotency-Key':key or str(uuid.uuid4())})

def start(client,mode='focus',family='dependencies'):
    r=mutation(client,'/sessions',{'mode':mode,**({'family':family} if mode=='focus' else {})})
    assert r.status_code==200,r.text
    s=r.json(); r=mutation(client,'/sessions/'+s['id']+'/next')
    assert r.status_code==200,r.text
    return r.json()
