"""Check published hard cases AND their unobfuscated targets. No novelty claim."""
import ast
import hashlib
import itertools
import json
import random
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
COMMIT='af44b8ad7c8ec548d431463475e93b0118e77a29'
DOCKER=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
IMAGE='wasm-research-cobra:af44b8a'
SOURCE=ROOT/'source'/f'CoBRA-{COMMIT}'
DATA=SOURCE/'test/datasets/gamba/qsynth_ea.txt'
lines=DATA.read_text().splitlines()
targets=[14,85,152]  # Preselected from upstream's residual diagnostics; all 2 vars.
seed=90217

def parse(s):
    return ast.parse(s.strip(),mode='eval').body

def names(node):
    return sorted({x.id for x in ast.walk(node) if isinstance(x,ast.Name)})

def op_count(node):
    return sum(isinstance(x,(ast.BinOp,ast.UnaryOp)) for x in ast.walk(node))

def evaluate(node, values, w):
    mask=(1<<w)-1
    def ev(n):
        if isinstance(n,ast.Constant) and type(n.value) is int: return n.value&mask
        if isinstance(n,ast.Name): return values[n.id]&mask
        if isinstance(n,ast.UnaryOp):
            a=ev(n.operand)
            if isinstance(n.op,ast.Invert): return (~a)&mask
            if isinstance(n.op,ast.USub): return (-a)&mask
            if isinstance(n.op,ast.UAdd): return a
        if isinstance(n,ast.BinOp):
            a,b=ev(n.left),ev(n.right)
            op=n.op
            if isinstance(op,ast.Add): return (a+b)&mask
            if isinstance(op,ast.Sub): return (a-b)&mask
            if isinstance(op,ast.Mult): return (a*b)&mask
            if isinstance(op,ast.BitAnd): return a&b
            if isinstance(op,ast.BitOr): return a|b
            if isinstance(op,ast.BitXor): return a^b
            if isinstance(op,(ast.LShift,ast.RShift)):
                # These upstream cases use literal in-range shifts; do not
                # silently assume Wasm shift-count semantics for arbitrary text.
                if not isinstance(n.right,ast.Constant) or not 0 <= b < w:
                    raise ValueError('shift outside validated subset')
                return ((a<<b) if isinstance(op,ast.LShift) else (a>>b))&mask
        raise ValueError('unsupported AST: '+ast.dump(node))
    return ev(node)

def points(vs,w):
    if w==4:
        return [dict(zip(vs,p)) for p in itertools.product(range(16),repeat=len(vs))]
    mask=(1<<w)-1
    boundary=[0,1,2,mask,mask-1,1<<(w-1),(1<<(w-1))-1]
    out=[dict(zip(vs,p)) for p in itertools.product(boundary,repeat=len(vs))]
    rng=random.Random(seed+w)
    out += [{v:rng.getrandbits(w) for v in vs} for _ in range(2048)]
    return out

cases=[]
for line in targets:
    a,b=lines[line-1].rsplit(',',1)
    cases.append({'label':f'qsynth_line_{line}','source':a,'target':b})
cases += [
 {'label':'add_control','source':'(x&y)+(x|y)','target':'x+y'},
 {'label':'product_control','source':'(x&y)*(x|y)+(x&~y)*(~x&y)','target':'x*y'},
 {'label':'boolean_shadow_control','source':'x*y-(x&y)','target':'x*y-(x&y)'}]

report={'commit':COMMIT,'datasetSha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),
        'seed':seed,'image':IMAGE,'note':'end-to-end timings include container startup; no solver performance claim',
        'z3':'not built; independent finite checks only','runs':[]}
for case in cases:
  for w in (4,32,64):
    a,b=parse(case['source']),parse(case['target'])
    vs=sorted(set(names(a)+names(b)))
    ps=points(vs,w)
    failures=[p for p in ps if evaluate(a,p,w)!=evaluate(b,p,w)]
    if failures: raise AssertionError({'case':case['label'],'w':w,'counterexample':failures[0]})
    # Source and target both tested, including controls, without silent dedup.
    for role in ('source','target'):
      container=f'wasm-cobra-probe-{len(report["runs"])}'
      cmd=[DOCKER,'run','--rm','--name',container,'--network','none','--read-only',
           '--memory','512m','--cpus','1','--pids-limit','128','--entrypoint','/usr/bin/timeout',
           IMAGE,'25s','/build/tools/cobra-cli/cobra-cli','--mba',case[role],'--bitwidth',str(w)]
      started=time.perf_counter()
      try:
        r=subprocess.run(cmd,text=True,capture_output=True,timeout=40)
        status='unsupported' if 'Unsupported:' in r.stderr else ('returned' if r.returncode==0 else 'error')
        if r.returncode==124: status='timeout'
        output=r.stdout.strip()
        check={'kind':'not checked'}
        if output and r.returncode==0:
          try:
            outast=parse(output)
            if set(names(outast))-set(vs): raise ValueError('unexpected output variables')
            bad=next((p for p in ps if evaluate(outast,p,w)!=evaluate(b,p,w)),None)
            check={'kind':'finite input comparison','cases':len(ps),'counterexample':bad,
                   'inputOps':op_count(parse(case[role])), 'outputOps':op_count(outast),
                   'targetOps':op_count(b),'exactTargetAst':ast.dump(outast)==ast.dump(b)}
          except (ValueError,SyntaxError) as err: check={'kind':'parser limitation','message':str(err)}
        record={'label':case['label'],'role':role,'width':w,'input':case[role],
          'target':case['target'],'status':status,'exitCode':r.returncode,
          'stdout':r.stdout,'stderr':r.stderr,'outputCheck':check}
      except subprocess.TimeoutExpired:
        subprocess.run([DOCKER,'stop','--time','1',container],capture_output=True,timeout=10)
        record={'label':case['label'],'role':role,'width':w,'status':'host timeout'}
      record['wallSeconds']=time.perf_counter()-started
      report['runs'].append(record)
      (ROOT/'probe-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
      print(case['label'],w,role,record['status'],flush=True)
