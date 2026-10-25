import itertools
import pytest
from hypothesis import given,strategies as st,settings
from app.tasks.solvers import dependency,canonical_graph,evaluate,logic_solutions,ordering
from app.tasks.engine import generate,public,grade,explain
from app.tasks.rules import apply,survivors,information
from app.tasks.bank import assigned_split, get_task

@given(st.integers(0,1000000),st.integers(1,4),st.sampled_from(['ordering','induction','hypothesis']))
@settings(max_examples=100,deadline=None)
def test_native_instances(seed,level,family):
    t=get_task(None,family,level,'practice',seed,set());assert grade(t,t['solution'])
    p=public(t);assert not {'solution','formal','seed','fingerprint','raw','proof'}&set(p)
    if family=='ordering':
        f=t['formal'];valid=[p for p in itertools.permutations(range(f['n'])) if all(p.index(a)<p.index(b) for a,b in f['edges'])]
        a,b=f['claim'];values={p.index(a)<p.index(b) for p in valid}
        expected='undetermined' if len(values)>1 else 'true' if True in values else 'false'
        assert expected==t['solution']
        for p in t['proof']['orders']: assert tuple(p) in valid
    elif family=='induction':
        rem=survivors(t['render']['candidates'],t['render']['examples'])
        assert rem and all(apply(c['id'],t['render']['target'])==t['solution'] for c in rem)
    else:
        q=[{'input':x,'output':apply(t['formal']['rule'],x)} for x in t['formal']['domain']]
        assert t['formal']['rule'] in [c['id'] for c in survivors(t['render']['candidates'],q)]

def test_dependency_regression():
    edges=[[2,3],[1,3],[0,3]]
    ok,proof=dependency(4,edges);assert ok and proof['order'][0]==3
    assert all(proof['order'].index(b)<proof['order'].index(a) for a,b in edges)
    assert dependency(3,[[1,0],[2,1],[0,2]])[0] is False
    assert dependency(4,[])[1]['order']==[0,1,2,3]

def test_ambiguous_induction_is_rejected_and_issuance_retries():
    with pytest.raises(ValueError, match='Ambiguous target'):
        generate('induction',4,163)
    task=get_task(None,'induction',4,'practice',163,set())
    assert task['seed']!=163
    assert grade(task,task['solution'])
    remaining=survivors(task['render']['candidates'],task['render']['examples'])
    assert remaining and all(apply(c['id'],task['render']['target'])==task['solution'] for c in remaining)

def test_rejected_native_candidates_still_have_a_retry_bound(monkeypatch):
    from app.tasks import bank
    seeds=[]
    def invalid(family,level,seed,split):
        seeds.append(seed)
        raise ValueError('Ambiguous target')
    monkeypatch.setattr(bank,'generate',invalid)
    with pytest.raises(ValueError, match='generation bound'):
        bank.get_task(None,'induction',4,'practice',163,set())
    assert seeds==list(range(163,363))

def test_isomorphism():
    assert canonical_graph(4,[[2,3],[1,3],[0,3]])==canonical_graph(4,[[0,2],[1,2],[3,2]])
    from app.tasks.solvers import canonical_logic
    assert canonical_logic([['telling-truth',1],['lying',0]])==canonical_logic([['lying',1],['telling-truth',0]])

@pytest.mark.parametrize('op,expected', [('and',False),('or',True),('->',False),('<=>',False)])
def test_compound_semantics(op,expected):
    assert evaluate([op,['telling-truth',0],['telling-truth',1]],[True,False])==expected

def test_whole_liar_statement():
    assert evaluate(['and',['telling-truth',0],['telling-truth',1]],[True,False]) is False
    assert evaluate(['not',['telling-truth',0]],[False]) is True
    assert len(logic_solutions([['telling-truth',0]]))==2

def test_bank_solver_witnesses_and_split(bank_rows):
    from app.tasks.solvers import canonical_logic
    seen={}
    for row in bank_rows:
        t=row['task']; assert assigned_split(t['fingerprint'])==row['split']
        old=seen.setdefault((row['family'],t['fingerprint']),row['split']);assert old==row['split']
        if row['family']=='dependencies':
            f=t['formal'];ok,proof=dependency(f['n'],f['edges']);assert ok==t['solution']
            if ok: assert all(proof['order'].index(b)<proof['order'].index(a) for a,b in f['edges'])
            else: assert all([b,a] in f['edges'] for a,b in zip(proof['cycle'],proof['cycle'][1:]))
        else:
            sols=logic_solutions(t['formal']['statements']);assert len(sols)==1
            assert {str(i):'truth' if v else 'lie' for i,v in enumerate(sols[0])}==t['solution']

@pytest.mark.parametrize('family',['dependencies','logic'])
@pytest.mark.parametrize('level',[1,2,3,4])
def test_actual_source_adapter(family,level):
    t=generate(family,level,5012);assert t==generate(family,level,5012)
    assert t['source'].startswith('reasoning-gym/0.1.25:');assert t['raw']['metadata']
    assert grade(t,t['solution']);assert explain(t,t['solution'],[])['steps']

@pytest.mark.parametrize('wrong',[None,1,'true',[],{'answer':True}])
def test_invalid_shapes_not_wrong_outcomes(wrong):
    t=generate('dependencies',1,31)
    with pytest.raises(ValueError):grade(t,wrong)

def test_information_gain():
    cs=[{'id':'plus2'},{'id':'times2'}]
    assert information(cs,2)==0;assert information(cs,1)==1
