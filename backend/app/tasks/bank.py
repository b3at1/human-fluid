import json
from collections import Counter
from sqlalchemy import select, func
from app.db import DB, Bank
from app.tasks.engine import generate
from app.tasks.solvers import digest

BANK_VERSION='rg-0.1.25-adapter-1'

def assigned_split(fingerprint):
    return 'check' if int(fingerprint[:8],16)%5==0 else 'practice'

def build_bank(practice=50, check=15, max_attempts=20000):
    report={'version':BANK_VERSION,'accepted':{},'rejected':{},'max_attempts_per_level':max_attempts}
    with DB() as db:
        for family in ('dependencies','logic'):
            for level in range(1,5):
                counts=Counter(dict(db.execute(select(Bank.split,func.count()).where(Bank.family==family,Bank.level==level).group_by(Bank.split)).all()))
                known=set(db.scalars(select(Bank.fingerprint).where(Bank.family==family,Bank.level==level)))
                rejected=Counter()
                for index in range(max_attempts):
                    if counts['practice']>=practice and counts['check']>=check: break
                    seed=level*10000000+index
                    try:
                        task=generate(family,level,seed)
                        fp=task['fingerprint']; split=assigned_split(fp)
                        if fp in known: rejected['duplicate_structure']+=1; continue
                        known.add(fp)
                        if counts[split]>=(practice if split=='practice' else check): continue
                        task['split']=split
                        db.add(Bank(family=family,level=level,split=split,fingerprint=fp,task=task)); counts[split]+=1
                    except (ValueError,IndexError,AssertionError) as e:
                        rejected[str(e)[:100]]+=1
                db.commit()
                key=f'{family}/{level}'; report['accepted'][key]=dict(counts); report['rejected'][key]=dict(rejected)
                print(key,dict(counts),flush=True)
                if counts['practice']<practice or counts['check']<check:
                    raise RuntimeError(f'Content target not met for {key} after {max_attempts} bounded attempts: {dict(counts)}')
    return report

def get_task(db,family,level,split,seed,excluded):
    if family in ('dependencies','logic'):
        rows=db.scalars(select(Bank).where(Bank.family==family,Bank.level==level,Bank.split==('check' if split=='check' else 'practice')).order_by(Bank.fingerprint)).all()
        eligible=[r for r in rows if r.fingerprint not in excluded]
        if not eligible: raise ValueError('No fresh verified content remains at this level. Try another family or level.')
        return eligible[seed%len(eligible)].task
    for offset in range(200):
        try:
            t=generate(family,level,seed+offset,split)
        except ValueError:
            # A rejected candidate must not abort the bounded issuance loop.
            continue
        if t['fingerprint'] in excluded: continue
        if split != 'probe' and assigned_split(t['fingerprint']) != split: continue
        return t
    raise ValueError('No fresh verified item found within the generation bound.')
