import random
import itertools
import json
from dataclasses import asdict
from importlib.metadata import version
from typing import Protocol
from app.tasks.solvers import dependency, canonical_graph, evaluate, logic_solutions, canonical_logic, ordering, digest
from app.tasks.rules import candidates, apply, survivors, information

FAMILIES = ['dependencies','logic','ordering','induction','hypothesis']
NAMES = {'dependencies':'Dependency reasoning','logic':'Logical consistency','ordering':'Relational ordering','induction':'Rule induction','hypothesis':'Hypothesis testing'}
LESSONS = {
'dependencies': {'principle':'Follow what must come first. A circular chain makes completion impossible.', 'example':'If Course 1 requires Course 0, take 0 before 1. If 0 also requires 1, neither can begin.', 'strategy':'Trace prerequisites; look for a path back to its starting point.'},
'logic': {'principle':'Truth-tellers make true statements. Liars make false whole statements.', 'example':'A says “B is a truth-teller.” B says “A is a liar.” A must lie and B must tell the truth: both statements then match their roles.', 'strategy':'Assume one role, propagate its consequences, and test every speaker. “Or” includes both.'},
'ordering': {'principle':'Necessary means true in every valid order; false means true in none. Otherwise it is undetermined.', 'example':'A before B and B before C force A before C. With D unrelated, A before D is undetermined.', 'strategy':'Chain the constraints. For uncertainty, try building two opposite valid orders.'},
'induction': {'principle':'Test the stated candidates against every example. These examples do not identify a rule among all possible functions.', 'example':'For the candidates add 2 and multiply by 2: 1 → 3 rules out multiply by 2; the target 4 maps to 6.', 'strategy':'Eliminate rules using counterexamples; check that survivors agree on the target.'},
'hypothesis': {'principle':'Choose experiments that separate the visible candidate rules. Queries are part of the task.', 'example':'To distinguish add 2 from multiply by 2, querying 2 is unhelpful: both give 4. Query 1: the outputs are 3 and 2.', 'strategy':'Prefer a query that divides the remaining candidates into different output groups.'}}

class TaskAdapter(Protocol):
    def generate(self, config: dict, seed: int) -> dict: ...
    def validate(self, task: dict) -> bool: ...
    def public_payload(self, task: dict, phase: str) -> dict: ...
    def grade(self, task: dict, answer) -> bool: ...
    def hint(self, task: dict, index: int, observed_state: list) -> str: ...
    def explain(self, task: dict, answer, observed_state: list) -> dict: ...

def statement_text(s, names):
    op,*xs=s
    if op in ('telling-truth','lying'): return f'{names[xs[0]]} is a {"truth-teller" if op == "telling-truth" else "liar"}'
    children=[statement_text(x,names) for x in xs]
    if op == 'not': return f'It is not true that ({children[0]})'
    if op == '->': return f'If ({children[0]}), then ({children[1]})'
    if op == '<=>': return f'({children[0]}) if and only if ({children[1]})'
    return (' AND ' if op == 'and' else ' OR (inclusive) ').join(f'({x})' for x in children)

def generate(family, level, seed, split='practice'):
    rng=random.Random(seed)
    task={'family':family,'difficulty':level,'seed':seed,'split':split,'adapter_version':'1','validated':True}
    if family == 'dependencies':
        from reasoning_gym.graphs.course_schedule import CourseScheduleConfig, CourseScheduleDataset
        cfg=CourseScheduleConfig(min_num_courses=level+5,max_num_courses=level+5,min_num_prerequisites=1,max_num_prerequisites=min(level+1,4),min_cycle_length=3,max_cycle_length=min(level+3,level+5),size=1,seed=seed)
        raw=CourseScheduleDataset(cfg)[0]
        meta=raw['metadata']
        n=len(meta['courses']); edges=meta['prerequisites']
        solution, proof=dependency(n,edges)
        if str(solution).lower()!=raw['answer'].lower(): raise ValueError('Source/solver disagreement')
        task.update(source=f'reasoning-gym/{version("reasoning-gym")}:course_schedule',config=asdict(cfg),raw=raw,
          formal={'n':n,'edges':edges},solution=solution,proof=proof,fingerprint=canonical_graph(n,edges),
          instructions='Can you complete every course while respecting the prerequisites?',
          render={'kind':'dependency_graph','courses':list(range(n)),'edges':[{'prerequisite':b,'course':a} for a,b in edges]},response_schema={'kind':'boolean_choice'})
    elif family == 'logic':
        from reasoning_gym.logic.knights_knaves import KnightsKnavesConfig, KnightsKnavesDataset
        cfg=KnightsKnavesConfig(n_people=2 if level==1 else min(level+1,5),depth_constraint=2 if level<=2 else 3,width_constraint=2,size=1,seed=seed)
        raw=KnightsKnavesDataset(cfg)[0]; m=raw['metadata']; stmts=m['statements']; names=m['names']
        solutions=logic_solutions(stmts)
        if len(solutions)!=1 or solutions[0]!=list(m['solution']): raise ValueError('Ambiguous/source disagreement')
        task.update(source=f'reasoning-gym/{version("reasoning-gym")}:knights_knaves',config=asdict(cfg),raw=raw,
          formal={'statements':stmts},solution={str(i):'truth' if v else 'lie' for i,v in enumerate(solutions[0])},
          fingerprint=canonical_logic(stmts),instructions='Who tells the truth, and who lies? Truth-tellers always tell the truth. A liar’s whole statement is false.',
          render={'kind':'statements','people':[{'id':str(i),'name':name,'statement':statement_text(stmts[i],names)} for i,name in enumerate(names)]},response_schema={'kind':'roles'})
    elif family == 'ordering':
        n=level+3; order=list(range(n)); rng.shuffle(order)
        edges=[(order[i],order[j]) for i in range(n) for j in range(i+1,n) if rng.random()<(.23+level*.035)]
        if not edges: edges=[(order[0],order[1])]
        claim=rng.sample(range(n),2); solution,witnesses=ordering(n,edges,claim)
        labels=[chr(65+i) for i in range(n)]
        wrapper='schedule' if split=='probe' else 'abstract'
        task.update(source='human-fluid/native-v1',config={'n':n,'presentation':wrapper},formal={'n':n,'edges':edges,'claim':claim},solution=solution,proof={'orders':witnesses},
          fingerprint=digest([canonical_graph(n,[(b,a) for a,b in edges]),canonical_graph(n,[(b,a) for a,b in edges]+[(claim[1],claim[0])])]),
          instructions='Must the proposed relationship hold in every valid order?' if wrapper=='abstract' else 'A project has scheduling constraints. Is the proposed schedule relationship necessary?',
          render={'kind':'ordering','labels':labels,'premises':[f'{"Task " if wrapper=="schedule" else ""}{labels[a]} comes before {labels[b]}.' for a,b in edges], 'claim':f'{labels[claim[0]]} comes before {labels[claim[1]]}.','presentation':wrapper},response_schema={'kind':'three_way'})
    else:
        probe=split=='probe'
        cs=candidates(level,probe,seed%48); hidden=rng.choice(cs)['id']
        domain=list(range(-4,6)) if level<=2 else [[3,-2,4,1], [2,0,-1,4], [-3,2,1,0], [5,4,2,-2], [1,3,2,4], [4,2,-3,0], [8,5,-4,0,2], [5,0,-5,10]]
        rng.shuffle(domain)
        examples=[]
        if family=='induction':
            for x in domain[:6]:
                examples.append({'input':x,'output':apply(hidden,x)})
                if len(examples)>=3 and len(survivors(cs,examples))==1: break
            target=domain[-1]
            remaining=survivors(cs,examples)
            if len({json.dumps(apply(c['id'],target)) for c in remaining})!=1: raise ValueError('Ambiguous target')
        else: target=None
        task.update(source='human-fluid/native-v1',config={'grammar':'bounded-v1','presentation':'instrument' if probe else 'function'},formal={'rule':hidden,'domain':domain},solution=apply(hidden,target) if family=='induction' else hidden,
          fingerprint=digest([family,sorted(c['id'] for c in cs),hidden,examples,target]),instructions='Use the candidate rules to find the missing output.' if family=='induction' else 'Run experiments, observe the outputs, then identify the hidden rule. Queries are not hints.',
          render={'kind':family,'candidates':cs,'examples':examples,'target':target,'input_kind':'number' if level<=2 else 'list','presentation':'instrument' if probe else 'function'},response_schema={'kind':('number' if level<=2 else 'list') if family=='induction' else 'rule_choice'})
    if family=='ordering' and split=='probe':
        labels=task['render']['labels']; edges=task['formal']['edges']; a,b=task['formal']['claim']
        task['render']['schedule_rows']=[{'task':label,'prerequisites':[labels[x] for x,y in edges if y==i]} for i,label in enumerate(labels)]
        task['render']['claim']=f'Task {labels[a]} must be completed before Task {labels[b]}.'
    return json.loads(json.dumps(task))

def public(task):
    return {k:task[k] for k in ('family','difficulty','instructions','render','response_schema')}

def grade(task,answer):
    kind=task['response_schema']['kind']
    valid=False
    if kind=='boolean_choice': valid=type(answer) is bool
    elif kind=='roles': valid=isinstance(answer,dict) and set(answer)==set(task['solution']) and all(v in ('truth','lie') for v in answer.values())
    elif kind=='three_way': valid=isinstance(answer,str) and answer in ('true','false','undetermined')
    elif kind=='number': valid=type(answer) is int and abs(answer)<=10000
    elif kind=='list': valid=isinstance(answer,list) and len(answer)<=12 and all(type(x) is int and abs(x)<=10000 for x in answer)
    elif kind=='rule_choice': valid=isinstance(answer,str) and answer in [c['id'] for c in task['render']['candidates']]
    if not valid: raise ValueError('Choose or enter a complete answer in the requested format.')
    return answer==task['solution']

def hint(task,index,queries):
    f=task['family']; r=task['render']
    if f=='dependencies':
        e=r['edges'][0]
        return [LESSONS[f]['strategy'],f'Begin at Course {e["prerequisite"]}. Follow its outgoing arrows, keeping a list of visited courses.',f'Course {e["course"]} requires Course {e["prerequisite"]}. Continue that chain; does any path revisit a course?'][index]
    if f=='logic':
        p=r['people'][0]
        return [LESSONS[f]['strategy'],f'Try assigning {p["name"]} the truth-teller role, then test their complete statement.',f'Under that assumption, “{p["statement"]}” must be true. Now check whether each other speaker can keep a consistent role.'][index]
    if f=='ordering':
        return [LESSONS[f]['strategy'],f'Use this constraint first: {r["premises"][0]}',f'Try a complete order beginning with {r["labels"][task["proof"]["orders"][0][0]]}. Test the claim against every constraint.'][index]
    remaining=survivors(r['candidates'],queries if f=='hypothesis' else r['examples'])
    if f=='hypothesis':
        best=max(task['formal']['domain'],key=lambda x:information(remaining,x))
        return [LESSONS[f]['strategy'],f'{len(remaining)} candidates remain after your observations.',f'Try input {best}. Under a uniform prior it distinguishes {information(remaining,best)} bits of uncertainty.'][index]
    e=r['examples'][0]
    return [LESSONS[f]['strategy'],f'Check each candidate against {e["input"]} → {e["output"]}.',f'{len(remaining)} candidate(s) survive all examples. Apply each survivor to {r["target"]} and compare.'][index]

def explain(task,answer,queries):
    f=task['family']; r=task['render']; result={'steps':[],'answer':task['solution'],'source':task['source'],'adapter_version':task['adapter_version']}
    if f=='dependencies':
        proof=task['proof']; result['witness']=proof
        if task['solution']: result['steps']=['Completion is possible. Take courses in this order: '+ ' → '.join(str(x) for x in proof['order'])+'.','Every prerequisite appears before the course that requires it. Isolated courses can be taken at any point.']
        else: result['steps']=['Completion is impossible. The arrows form this cycle: '+' → '.join(str(x) for x in proof['cycle'])+'.','Each course in this loop requires another course in the loop to be completed first. There is no valid starting point.']
    elif f=='logic':
        stmts=task['formal']['statements']; rows=[]
        for a in itertools.product([False,True],repeat=len(stmts)):
            values=[evaluate(s,a) for s in stmts]; valid=all(a[i]==v for i,v in enumerate(values))
            rows.append({'roles':['truth' if v else 'lie' for v in a],'statements':values,'consistent':valid})
        result['truth_table']=rows
        actual=[task['solution'][str(i)]=='truth' for i in range(len(stmts))]
        result['steps']=[f'{p["name"]} is a {"truth-teller" if actual[i] else "liar"}; their whole statement evaluates to {str(evaluate(stmts[i],actual)).lower()}.' for i,p in enumerate(r['people'])]
        bad=next(row for row in rows if not row['consistent']); index=next(i for i,v in enumerate(bad['statements']) if v!=(bad['roles'][i]=='truth'))
        result['steps'].append(f'Rejected alternative {bad["roles"]}: {r["people"][index]["name"]} has a statement whose truth does not match their assigned role. The full table has exactly one consistent assignment.')
    elif f=='ordering':
        result['witness']={'orders':[[r['labels'][i] for i in p] for p in task['proof']['orders']]}
        result['steps']=[{'true':'The claim follows from a directed chain of the premises.','false':'The reverse relationship follows from the premises, so the proposed claim cannot hold.','undetermined':'Neither direction is forced. These two valid complete orders give opposite answers.'}[task['solution']], 'Check each displayed ordering against every premise.']
    else:
        hidden=task['formal']['rule']; label=next(c['label'] for c in r['candidates'] if c['id']==hidden)
        result['steps']=[f'The rule is: {label}.']
        for e in (r['examples'] if f=='induction' else queries): result['steps'].append(f'{e["input"]} → {apply(hidden,e["input"])}')
        if f=='induction': result['steps'].append(f'Apply it to the target: {r["target"]} → {task["solution"]}. All surviving candidates agree on this output.')
        else:
            cs=r['candidates']; analysis=[]
            for q in queries:
                before=survivors(cs,analysis); gain=information(before,q['input']); analysis.append(q)
                result['steps'].append(f'Query {q["input"]} separated candidates by {gain} bits under the uniform prior; {len(survivors(cs,analysis))} remained.')
            best=max(task['formal']['domain'],key=lambda x:information(cs,x))
            result['steps'].append(f'An informative initial alternative was {best}: {information(cs,best)} bits. Stopping once one candidate remains is sufficient. This is an instructional metric, not an intelligence score.')
    return result
