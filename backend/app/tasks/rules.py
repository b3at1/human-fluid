"""Bounded shared grammar; compositions are reserved from practice."""
import math
from collections import Counter

SCALAR = {'plus2':'Add 2', 'times2':'Multiply by 2', 'minus3':'Subtract 3', 'negate':'Change the sign',
          'affine':'Multiply by 2, then add 1', 'square':'Square the input', 'squareplus':'Square, then add 1'}
LIST = {'reverse':'Reverse the list', 'sort':'Sort from low to high', 'even':'Keep even values',
        'positive':'Keep positive values', 'sorteven':'Keep even values, then sort',
        'reverseeven':'Keep even values, then reverse'}

def candidates(level, probe=False, variant=0):
    k=2+variant%4; m=2+(variant//4)%3; b=1+(variant//12)%4
    if level<=2:
        cs=[{'id':f'add:{k}','label':f'Add {k}'},
            {'id':f'mul:{m}','label':f'Multiply by {m}'},
            {'id':f'add:{-b}','label':f'Subtract {b}'},
            {'id':'negate','label':'Change the sign'}]
        if level==2:
            cs += [{'id':f'aff:{m}:{b}','label':f'Multiply by {m}, then add {b}'},
                   {'id':'square','label':'Square the input'}]
        if probe: cs += [{'id':'squareplus','label':'Square, then add 1'}]
        return cs
    cs=[{'id':'reverse','label':'Reverse the list'}, {'id':'sort','label':'Sort from low to high'},
        {'id':f'div:{k}','label':f'Keep values divisible by {k}'},
        {'id':f'above:{b-2}','label':f'Keep values greater than {b-2}'}]
    if level==4:
        cs += [{'id':f'sortdiv:{k}','label':f'Keep values divisible by {k}, then sort'},
               {'id':f'reversediv:{k}','label':f'Keep values divisible by {k}, then reverse'}]
    return cs

def apply(rule, x):
    parts=rule.split(':')
    if len(parts)>1:
        op=parts[0]; k=int(parts[1])
        if op=='add': return x+k
        if op=='mul': return x*k
        if op=='aff': return x*k+int(parts[2])
        if op=='above': return [v for v in x if v>k]
        filtered=[v for v in x if v%k==0]
        if op=='div': return filtered
        if op=='sortdiv': return sorted(filtered)
        if op=='reversediv': return filtered[::-1]
        raise ValueError('Unknown parameterized rule')
    if rule == 'plus2': return x+2
    if rule == 'times2': return x*2
    if rule == 'minus3': return x-3
    if rule == 'negate': return -x
    if rule == 'affine': return 2*x+1
    if rule == 'square': return x*x
    if rule == 'squareplus': return x*x+1
    if rule == 'reverse': return x[::-1]
    if rule == 'sort': return sorted(x)
    if rule == 'even': return [v for v in x if v%2==0]
    if rule == 'positive': return [v for v in x if v>0]
    if rule == 'sorteven': return sorted(v for v in x if v%2==0)
    if rule == 'reverseeven': return [v for v in x if v%2==0][::-1]
    raise ValueError('Unknown rule')

def survivors(cs, queries):
    return [c for c in cs if all(apply(c['id'],q['input']) == q['output'] for q in queries)]

def information(cs, x):
    groups = Counter(str(apply(c['id'],x)) for c in cs)
    n = len(cs)
    return round(-sum(v/n*math.log2(v/n) for v in groups.values()), 3) if n else 0
