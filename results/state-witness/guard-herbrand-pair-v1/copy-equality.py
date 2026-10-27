"""Ordinary equality WP on a generic finite graph, independent of the Wasm solver.

Not an implementation of the entire ESOP 2005 interprocedural algorithm.
Terms are ('c', constant) or (variable-space, identifier). Conditions are
conjunctions of equalities; None denotes false and () denotes true.
"""
from collections import defaultdict, deque

def normalize(atoms):
    if atoms is None: return None
    # Connected components of the equality graph; avoid sharing K's union-find.
    adjacency=defaultdict(set)
    for left,right in atoms:
        if left==right: continue
        adjacency[left].add(right);adjacency[right].add(left)
    visited=set();answer=[]
    for start in sorted(adjacency):
        if start in visited: continue
        pending=[start];group=[];visited.add(start)
        while pending:
            current=pending.pop();group.append(current)
            for target in adjacency[current]:
                if target not in visited: visited.add(target);pending.append(target)
        constants={term[1] for term in group if term[0]=='c'}
        if len(constants)>1: return None
        group.sort();answer.extend((group[0],term) for term in group[1:])
    return tuple(sorted(answer))

def meet(*conditions):
    if any(value is None for value in conditions):return None
    return normalize(atom for value in conditions for atom in value)

def substitute(condition,mapping):
    if condition is None:return None
    return normalize((mapping.get(left,left),mapping.get(right,right)) for left,right in condition)

def arbitrary(condition,variables):
    """Universal elimination on the normalized equality-conjunction domain."""
    if condition is None:return None
    return None if any(left in variables or right in variables for left,right in condition) else condition

def wp(steps,following):
    condition=following
    for step in reversed(steps):
        operation=step['op']
        if operation=='require':condition=meet(condition,step['condition'])
        elif operation=='parallel':condition=substitute(condition,step['mapping'])
        elif operation=='shared-input':
            # Each cell independently has a shared arbitrary input. Sequential
            # elimination composes independent optional choices, without the
            # K-specific no-write/all-write mask reduction.
            for n,(left,right) in enumerate(step['pairs']):
                fresh=('input',n)
                updated=arbitrary(substitute(condition,{left:fresh,right:fresh}),{fresh})
                condition=meet(condition,updated) if step['optional'] else updated
        else:raise ValueError('Unknown generic instruction '+operation)
    return condition

def solve(graph,max_iterations=1024):
    conditions=[() for _ in graph];calls=0
    for iteration in range(max_iterations):
        updated=[]
        for edges in graph:
            incoming=[]
            for edge in edges:
                post=() if edge['target'] is None else conditions[edge['target']]
                incoming.append(wp(edge['steps'],post));calls+=1
            updated.append(meet(*incoming))
        if updated==conditions:return dict(conditions=conditions,iterations=iteration+1,wpCalls=calls)
        conditions=updated
    raise ValueError('Generic fixed-point iteration limit')

def solve_worklist(graph,max_facts=250000):
    """Standard distributive fact propagation, including joint contradictions."""
    predecessors=[[] for _ in graph]
    for source,edges in enumerate(graph):
        for edge in edges:
            if edge['target'] is not None:predecessors[edge['target']].append((source,edge))
    facts=[set() for _ in graph];impossible=set();queue=deque();calls=0;count=0
    def add(state,condition):
        nonlocal count
        if state in impossible:return
        if condition is None:
            impossible.add(state);facts[state].clear();queue.append((state,None));return
        for atom in condition:
            if atom not in facts[state]:facts[state].add(atom);queue.append((state,atom));count+=1
        if count>max_facts:raise ValueError('Generic fact bound')
    for state,edges in enumerate(graph):
        for edge in edges:add(state,wp(edge['steps'],()));calls+=1
    rounds=0
    while True:
        while queue:
            state,atom=queue.popleft()
            if atom is not None and state in impossible:continue
            for source,edge in predecessors[state]:
                if source not in impossible:
                    add(source,wp(edge['steps'],None if atom is None else (atom,)));calls+=1
        conditions=[None if state in impossible else normalize(value) for state,value in enumerate(facts)];rounds+=1
        for state,value in enumerate(conditions):
            if value is None and state not in impossible:add(state,None)
        if not queue:return dict(conditions=conditions,iterations=rounds,wpCalls=calls,factsInserted=count)
