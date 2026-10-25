"""Consistent SQLite online backup; restore only with the server stopped."""
import argparse
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.db import engine
p=argparse.ArgumentParser();p.add_argument('action',choices=['backup','restore']);p.add_argument('file',type=Path);p.add_argument('--confirm-replace',action='store_true');a=p.parse_args()
live=Path(engine.url.database)
if a.action=='backup':
    if a.file.exists():raise SystemExit('Refusing to overwrite an existing backup.')
    a.file.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(live) as source,sqlite3.connect(a.file) as target:source.backup(target)
    print('Consistent backup created. Protect it as private user data.')
else:
    if not a.confirm_replace:raise SystemExit('Stop the application, then pass --confirm-replace to restore the full database.')
    if not a.file.is_file():raise SystemExit('Backup file does not exist.')
    with sqlite3.connect(f'file:{a.file.resolve()}?mode=ro',uri=True) as source:
        if source.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise SystemExit('Backup integrity check failed.')
        with sqlite3.connect(live) as target:source.backup(target)
    print('Database restored. Restart the single application instance.')
