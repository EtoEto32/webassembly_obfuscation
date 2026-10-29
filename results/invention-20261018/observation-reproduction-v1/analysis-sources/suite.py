"""Build a frozen multi-program experiment, including post-optimization probes."""
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path
import core, transform

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OPT=transform.TOOLS/'binaryen-version_133/bin/wasm-opt.exe'
MODES=['plain','output-only','random','frontier','mba']
LEVELS=['raw','O2','O3']
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x): Path(p).write_text(json.dumps(x,indent=2),encoding='utf-8')
def x(op,a,b): return [op,a,b]
X,Y,Z='v0','v1','v2'
S=x('add',x('add',x('mul',X,Y),x('mul',Z,X)),x('mul',Y,Z))
PROGRAMS={
 'product':x('mul',x('add',x('mul',X,Y),x('mul',Z,X)),x('add',x('mul',Y,Z),1)),
 'score-square':x('mul',S,S),
 'interpolation':x('add',x('add',X,x('mul',x('sub',Y,X),Z)),x('mul',x('sub',X,Y),x('add',x('mul',Z,Z),1))),
 'cubic-product':x('mul',x('add',x('mul',X,Y),Z),x('add',x('sub',X,Z),Y)),
 'determinant-control':x('sub',x('mul',X,Y),x('mul',Z,Z)),
}

def module(tree):
 return '''(module (memory (export "memory") 1 1)
 (func $run (export "run") (param i32 i32 i32) (result i32) %s)
 (func (export "checked") (param $p i32) (param $x i32) (param $y i32) (param $z i32) (result i32)
   (i32.store (i32.const 16) (local.get $p))
   (i32.add (call $run (local.get $x) (local.get $y) (local.get $z)) (i32.load (local.get $p))))
 (func (export "batch") (param $n i32) (param $s i32) (result i32) (local $acc i32)
   (block $exit (loop $loop (br_if $exit (i32.eqz (local.get $n)))
     (local.set $s (i32.add (i32.mul (local.get $s) (i32.const 1664525)) (i32.const 1013904223)))
     (local.set $acc (i32.xor (local.get $acc)
       (call $run (local.get $s) (i32.xor (local.get $s) (i32.const 123456789)) (i32.rotl (local.get $s) (i32.const 7)))))
     (local.set $n (i32.sub (local.get $n) (i32.const 1))) (br $loop))) (local.get $acc)))
 ''' % transform.emit(transform.wat(tree))

def mba(src,out):
 m=transform.parse(transform.tool('wasm2wat',[src,'--fold-exprs']))
 counts=[0]
 def visit(n):
  if not isinstance(n,list): return n
  e=transform.expression(n)
  if e is not None and isinstance(e,list):
   def lower(t):
    if not isinstance(t,list): return transform.wat(t)
    a,b=lower(t[1]),lower(t[2])
    if t[0]=='add':
     counts[0]+=1
     return ['i32.add',['i32.xor',a,b],['i32.shl',['i32.and',a,b],['i32.const','1']]]
    return ['i32.'+t[0],a,b]
   return lower(e)
  return list(map(visit,n))
 # Same pure-region mechanism; transforms also the ordinary batch LCG addition.
 # Restrict to the exported run function for a matched application scope.
 idx=next(n[2][1] for n in m if isinstance(n,list) and n[:2]==['export','"run"'])
 funcs=[n for n in m if isinstance(n,list) and n[0]=='func']
 f=funcs[int(idx)]; f[:]=visit(f)
 wp=Path(str(out)+'.wat');wp.write_text(transform.emit(m),encoding='utf-8')
 transform.tool('wat2wasm',[wp,'-o',out]);return counts[0]

def instrument(src,out):
 m=transform.parse(transform.tool('wasm2wat',[src,'--fold-exprs','--generate-names']))
 if any(isinstance(n,list) and n[0]=='import' for n in m): raise ValueError('probe requires no existing imports')
 fn=next(n[2][1] for n in m if isinstance(n,list) and n[:2]==['export','"run"'])
 f=next(n for n in m if isinstance(n,list) and n[:2]==['func',fn])
 locals_={};params=[];events=[]
 for n in f:
  if isinstance(n,list) and n[0]=='param':
   # WABT --generate-names emits one named parameter per declaration.
   if len(n)!=3 or n[2]!='i32': raise ValueError('unsupported probe parameter')
   params.append(n[1]);locals_[n[1]]='v'+str(len(params)-1)
  if isinstance(n,list) and n[0]=='local':
   if len(n)!=3 or n[2]!='i32': raise ValueError('unsupported probe local')
   locals_[n[1]]=0
 def visit(n):
  if not isinstance(n,list): return n,None
  op=n[0]
  if op in ('type','param','result','local'): return n,None
  if op=='local.get':
   expr=locals_[n[1]];new=n
  elif op=='i32.const': expr=int(n[1],0);new=n
  elif op in ('local.set','local.tee'):
   val,expr=visit(n[2]);locals_[n[1]]=expr;new=[op,n[1],val]
   if op=='local.set': return new,None
  elif op.startswith('i32.') and len(n)==3:
   a,ae=visit(n[1]);b,be=visit(n[2]);expr=[op[4:],ae,be];new=[op,a,b]
  else: raise ValueError('Unsupported run instruction '+op)
  ident=len(events);events.append({'id':ident,'expression':expr,'opcode':op})
  return ['call','$observe',['i32.const',str(ident)],new],expr
 newf=f[:2];final=None
 for n in f[2:]:
  v,e=visit(n);newf.append(v)
  if e is not None: final=e
 f[:]=newf
 m.insert(1,['import','"probe"','"observe"',['func','$observe',['param','i32','i32'],['result','i32']]])
 wp=Path(str(out)+'.wat');wp.write_text(transform.emit(m),encoding='utf-8')
 transform.tool('wat2wasm',[wp,'-o',out]);transform.tool('wasm-validate',[out])
 return {'events':events,'output_expression':final,'inputSHA256':h(src),'probeSHA256':h(out),
         'model':'all scalar i32 values of exported straight-line run, after Binaryen; not native JIT traces'}

def build(out):
 if out.exists(): raise ValueError('Refuse overwrite')
 out.mkdir(parents=True)
 plan={'date':'2026-10-18','programs':PROGRAMS,'targets':{n:core.target(t) for n,t in PROGRAMS.items()},
       'modes':MODES,'levels':LEVELS,'seed':20261018,'training':12,'holdout':128,'correctness_random':512,
       'timing':{'warmup_batches':12,'calls_per_batch':200000,'blocks':15,'order':'cyclic Latin square over 15 variants per program'},
       'flags':['--no-liftoff','--no-wasm-tier-up','--no-wasm-lazy-compilation','--trace-wasm-compilation-times'],
       'attack':{'operations':['add','sub','mul','xor','and','or'],'max_ops':2,'max_attempts':1000000},
       'scope':'Five controlled integer kernels, not five independent real-world applications. One no-applicable-region control.',
       'success':'Do not credit unsupported probes, bounded search failures, or 1-vs-2 operation differences as practical resistance.'}
 save(out/'plan.json',plan)
 source_dir=out/'sources';source_dir.mkdir()
 for p in HERE.glob('*.py'): shutil.copyfile(p,source_dir/p.name)
 for p in HERE.glob('suite*.cjs'): shutil.copyfile(p,source_dir/p.name)
 manifest={'planSHA256':h(out/'plan.json'),'environment':{'python':sys.version,'platform':platform.platform(),
   'wabt':transform.tool('wat2wasm',['--version']).strip(),
   'binaryen':subprocess.check_output([str(OPT),'--version'],text=True).strip()},'artifacts':[]}
 for name,tree in PROGRAMS.items():
  d=out/name;d.mkdir();base=d/'plain.wasm';wp=d/'plain.wat';wp.write_text(module(tree),encoding='utf-8')
  transform.tool('wat2wasm',[wp,'-o',base])
  for mode in MODES:
   src=d/(mode+'.wasm');start=time.perf_counter();info={}
   if mode in ('output-only','random','frontier'): info=transform.transform(base,src,mode)
   if mode=='mba': info={'additions':mba(base,src),'baseline':'x+y=(x xor y)+((x and y)<<1), self-written'}
   seconds=time.perf_counter()-start
   for level in LEVELS:
    file=d/(mode+'-'+level+'.wasm')
    if level=='raw': shutil.copyfile(src,file)
    else: subprocess.run([str(OPT),str(src),'-'+level,'-o',str(file)],check=True,capture_output=True,timeout=30)
    transform.tool('wasm-validate',[file]);dis=transform.tool('wasm2wat',[file,'--fold-exprs'])
    Path(str(file)+'.wat').write_text(dis,encoding='utf-8')
    probe=d/(mode+'-'+level+'-probe.wasm');meta=instrument(file,probe);save(Path(str(probe)+'.json'),meta)
    entry={'id':name+'/'+mode+'-'+level,'program':name,'mode':mode,'level':level,'file':str(file.relative_to(out)),
           'probe':str(probe.relative_to(out)),'sha256':h(file),'bytes':file.stat().st_size,
           'transform_seconds':seconds if mode!='plain' else None,'transform_info':info,
           'validation':'passed','probe_events':len(meta['events'])}
    manifest['artifacts'].append(entry)
  save(out/'manifest.json',manifest)
  print('built '+name,flush=True)
 save(out/'manifest.json',manifest)
 print('built '+str(len(manifest['artifacts']))+' variants',flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);args=ap.parse_args();build(args.out.resolve())
