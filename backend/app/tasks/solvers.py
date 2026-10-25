"""Independent solvers: no calls to source grading functions."""
import itertools
import hashlib
import json
from collections import defaultdict

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def dependency(n, edges):
    outgoing = {i: [] for i in range(n)}
    degree = [0] * n
    for a, b in edges:
        outgoing[b].append(a)
        degree[a] += 1
    ready = sorted(i for i in range(n) if degree[i] == 0)
    order = []
    while ready:
        u = ready.pop(0)
        order.append(u)
        for v in outgoing[u]:
            degree[v] -= 1
            if degree[v] == 0: ready.append(v)
    if len(order) == n: return True, {'order': order}
    visited, stack = set(), []
    def walk(u):
        if u in stack: return stack[stack.index(u):] + [u]
        if u in visited: return None
        visited.add(u)
        stack.append(u)
        for v in outgoing[u]:
            cycle = walk(v)
            if cycle: return cycle
        stack.pop()
    for u in range(n):
        cycle = walk(u)
        if cycle: return False, {'cycle': cycle}
    raise ValueError('Missing cycle witness')

def canonical_graph(n, edges):
    # Isomorphism-invariant partition by in/out degrees, then exact canonical
    # enumeration inside partitions. Not a seed or label fingerprint.
    incoming, outgoing = [0]*n, [0]*n
    for a,b in edges: incoming[a] += 1; outgoing[b] += 1
    groups = defaultdict(list)
    for i in range(n): groups[(incoming[i], outgoing[i])].append(i)
    parts = [groups[k] for k in sorted(groups)]
    best = None
    for p in itertools.product(*(itertools.permutations(g) for g in parts)):
        labels = list(itertools.chain.from_iterable(p))
        mapping = {old: new for new, old in enumerate(labels)}
        rep = tuple(sorted((mapping[a], mapping[b]) for a,b in edges))
        if best is None or rep < best: best = rep
    return digest([n, best])

def evaluate(stmt, assignment):
    op, *xs = stmt
    if op == 'telling-truth': return assignment[xs[0]]
    if op == 'lying': return not assignment[xs[0]]
    vals = [evaluate(x, assignment) for x in xs]
    if op == 'not': return not vals[0]
    if op == 'and': return all(vals)
    if op == 'or': return any(vals)
    if op == '->': return not vals[0] or vals[1]
    if op == '<=>': return vals[0] == vals[1]
    raise ValueError('Unknown logical operator')

def logic_solutions(statements):
    return [list(a) for a in itertools.product([False, True], repeat=len(statements))
            if all(evaluate(s, a) == a[i] for i,s in enumerate(statements))]

def canonical_logic(statements):
    def rename(s, mapping):
        if s[0] in ('telling-truth','lying'): return [s[0], mapping[s[1]]]
        children = [rename(x, mapping) for x in s[1:]]
        if s[0] in ('and','or','<=>'): children.sort(key=lambda x: json.dumps(x))
        return [s[0], *children]
    reps = []
    for p in itertools.permutations(range(len(statements))):
        mapping = {old:new for new,old in enumerate(p)}
        reps.append(json.dumps([rename(statements[old],mapping) for old in p]))
    return digest(min(reps))

def ordering(n, edges, claim):
    reach = [[False]*n for _ in range(n)]
    for a,b in edges: reach[a][b] = True
    for k in range(n):
        for i in range(n):
            for j in range(n): reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
    a,b = claim
    result = 'true' if reach[a][b] else 'false' if reach[b][a] else 'undetermined'
    def witness(extra):
        ok, proof = dependency(n, [(v,u) for u,v in edges + [extra]])
        if not ok: raise ValueError('Invalid ordering witness')
        return proof['order']
    witnesses = [witness((a,b)),witness((b,a))] if result == 'undetermined' else [witness((a,b) if result == 'true' else (b,a))]
    return result, witnesses
