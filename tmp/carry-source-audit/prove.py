"""Independent bit-vector equivalence checks; unknown is NOT a proof."""
import ast, hashlib, json, os, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('WASM_SYNTH_DEPENDENCIES',r'C:\Users\ettotto\Documents\webassembly_obfuscation\.tools\encoding-synthesis-python'))
import z3
z3.set_param('memory_max_size',512)
data=json.loads((ROOT/'probe-results.json').read_text())
checks=[]
seen=set()

def translate(text,w,env):
  def ev(n):
    if isinstance(n,ast.Constant) and type(n.value) is int: return z3.BitVecVal(n.value,w)
    if isinstance(n,ast.Name): return env.setdefault(n.id,z3.BitVec(n.id,w))
    if isinstance(n,ast.UnaryOp):
      a=ev(n.operand)
      if isinstance(n.op,ast.Invert): return ~a
      if isinstance(n.op,ast.USub): return -a
      if isinstance(n.op,ast.UAdd): return a
    if isinstance(n,ast.BinOp):
      a,b=ev(n.left),ev(n.right)
      if isinstance(n.op,ast.Add): return a+b
      if isinstance(n.op,ast.Sub): return a-b
      if isinstance(n.op,ast.Mult): return a*b
      if isinstance(n.op,ast.BitAnd): return a&b
      if isinstance(n.op,ast.BitOr): return a|b
      if isinstance(n.op,ast.BitXor): return a^b
      if isinstance(n.op,(ast.LShift,ast.RShift)):
        if not isinstance(n.right,ast.Constant) or not 0 <= n.right.value < w:
          raise ValueError('shift outside subset')
        return a<<b if isinstance(n.op,ast.LShift) else z3.LShR(a,b)
    raise ValueError(ast.dump(n))
  return ev(ast.parse(text.strip(),mode='eval').body)

for r in data['runs']:
  for kind,left in [('input-target',r['input']),('output-target',r.get('stdout',''))]:
    if not left.strip(): continue
    w=r['width']; right=r['target']; key=(w,left.strip(),right.strip())
    if key in seen: continue
    seen.add(key)
    env={}; a,b=translate(left,w,env),translate(right,w,env)
    solver=z3.SolverFor('QF_BV'); solver.set(timeout=3000,random_seed=90217)
    solver.add(a!=b)
    started=time.perf_counter(); result=solver.check()
    row={'case':r['label'],'role':r['role'],'width':w,'kind':kind,
         'left':left,'right':right,'result':str(result),'seconds':time.perf_counter()-started}
    if result==z3.sat: row['counterexample']={k:solver.model().eval(v,model_completion=True).as_long() for k,v in env.items()}
    if result==z3.unknown: row['reason']=solver.reason_unknown()
    checks.append(row)
    (ROOT/'proof-results.json').write_text(json.dumps({'z3':z3.get_version_string(),'timeoutMs':3000,
       'probeResultsSha256':hashlib.sha256((ROOT/'probe-results.json').read_bytes()).hexdigest(),
       'checks':checks},indent=2),encoding='utf-8')
    print(row['case'],w,kind,row['result'],flush=True)
