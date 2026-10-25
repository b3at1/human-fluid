from sqlalchemy import select
from app.db import DB,Bank
from app.tasks.solvers import dependency,logic_solutions,canonical_graph,canonical_logic
from app.tasks.bank import assigned_split

def verify_bank():
    with DB() as db:
        rows=db.scalars(select(Bank)).all()
        for row in rows:
            t=row.task
            assert assigned_split(row.fingerprint)==row.split
            if row.family=='dependencies':
                f=t['formal']; answer,proof=dependency(f['n'],f['edges'])
                assert answer==t['solution']; assert row.fingerprint==canonical_graph(f['n'],f['edges'])
                if answer:
                    order=proof['order']; assert sorted(order)==list(range(f['n']))
                    assert all(order.index(b)<order.index(a) for a,b in f['edges'])
                else: assert all([b,a] in f['edges'] for a,b in zip(proof['cycle'],proof['cycle'][1:]))
            else:
                sol=logic_solutions(t['formal']['statements']); assert len(sol)==1
                assert {str(i):'truth' if v else 'lie' for i,v in enumerate(sol[0])}==t['solution']
                assert row.fingerprint==canonical_logic(t['formal']['statements'])
        return {'verified':len(rows),'source':'reasoning-gym==0.1.25','independent_solvers':True}
