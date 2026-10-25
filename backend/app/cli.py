import argparse
import getpass
import json
import secrets
from pathlib import Path
from argon2 import PasswordHasher
from sqlalchemy import select
from alembic.config import Config
from alembic import command
from app.config import ROOT
from app.db import DB, Admin, engine
from app.tasks.bank import build_bank

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['migrate','bank','admin','verify-bank'])
    parser.add_argument('--username',default='owner')
    args=parser.parse_args()
    if args.action=='migrate':
        cfg=Config(str(ROOT/'backend/alembic.ini')); cfg.set_main_option('script_location',str(ROOT/'backend/app/db/migrations')); command.upgrade(cfg,'head')
    elif args.action=='bank':
        report=build_bank(); (Path(engine.url.database).parent/'bank-report.json').write_text(json.dumps(report,indent=2))
    elif args.action=='verify-bank':
        from app.verification import verify_bank
        print(json.dumps(verify_bank(),indent=2))
    else:
        password=getpass.getpass('New admin password (at least 12 characters): ')
        if len(password)<12 or password!=getpass.getpass('Confirm password: '): raise SystemExit('Passwords must match and have at least 12 characters.')
        with DB.begin() as db:
            if db.scalar(select(Admin).where(Admin.username==args.username)): raise SystemExit('Admin already exists.')
            db.add(Admin(username=args.username,password=PasswordHasher().hash(password)))
        print('Admin created. Sign in at /admin/login.')
if __name__=='__main__': main()
