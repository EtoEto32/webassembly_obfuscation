"""Restricted real-Wasm compiler for weighted synchronizing decoder experiment."""
import argparse, importlib.util, json, random, struct, time
from pathlib import Path
import model
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('sync_tools',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
def c(v):return ['i32.const',str(v&model.MASK)]
def local(v):return ['local.get',str(v)]
def blob(data):return '"'+''.join('\\%02x'%x for x in data)+'"'
def const(e):return int(e[1],0)&model.MASK if isinstance(e,list) and len(e)==2 and e[0]=='i32.const' else None

def helper(n,length):
    return '''(func (param i32 i32 i32 i32) (result i32) (local i32 i32 i32)
      (block (loop (br_if 1 (i32.ge_u (local.get 4) (i32.const LENGTH)))
       (local.set 5 (i32.add (local.get 3) (i32.mul (i32.add (i32.mul (i32.load8_u (i32.add (i32.const 64) (local.get 4))) (i32.const N)) (local.get 2)) (i32.const 12))))
       (local.set 6 (i32.load (local.get 5)))
       (local.set 0 (i32.add (local.get 0) (i32.add (i32.mul (i32.load offset=4 (local.get 5)) (local.get 1)) (i32.load offset=8 (local.get 5)))))
       (local.set 2 (local.get 6)) (local.set 4 (i32.add (local.get 4) (i32.const 1))) (br 0))) (local.get 0))'''.replace('LENGTH',str(length)).replace('N',str(n))

def source(rounds,seed):
    rng=random.Random(seed);coeff=[];parts=['(module (func (export "run") (param i32 i32) (result i32) (local i32) (local.set 2 (local.get 0))']
    def mix(a,b):return q.w.emit(['i32.add',['i32.add',local(2),['i32.mul',local(1),c(a)]],c(b)])
    for _ in range(rounds):
        ab=[rng.getrandbits(32)|1 for _ in range(4)];coeff.append(ab)
        parts.append('(local.set 2 (i32.xor (i32.rotl (local.get 2) (i32.const 5)) (local.get 1)))')
        parts.append('(if (i32.and (local.get 2) (i32.const 1)) (then (local.set 2 '+mix(*ab[:2])+')) (else (local.set 2 '+mix(*ab[2:])+')))')
        parts.append('(local.set 1 (i32.xor (local.get 1) (i32.rotl (local.get 2) (i32.const 13))))')
    return ' '.join(parts)+' (i32.xor (local.get 2) (local.get 1))))',coeff

def match(e):
    if not isinstance(e,list) or len(e)!=3 or e[0]!='i32.add':return None
    b=const(e[2]);left=e[1]
    if b is None or not isinstance(left,list) or len(left)!=3 or left[0]!='i32.add':return None
    x,mul=left[1:]
    if not isinstance(x,list) or x[0]!='local.get' or not isinstance(mul,list) or len(mul)!=3 or mul[0]!='i32.mul':return None
    y,a=mul[1],const(mul[2])
    if a is None or not isinstance(y,list) or y[0]!='local.get':return None
    return x,y,a,b

def transform(src,dst,n,seed,mode):
    if n not in (4,8,16):raise ValueError('state count must be 4, 8 or 16')
    start=time.perf_counter();mod=q.read(src);funcs=[v for v in mod[1:] if v[0]=='func'];exports=[v for v in mod[1:] if v[0]=='export']
    if len(funcs)!=1 or exports!=[['export','"run"',['func','0']]] or any(v[0] not in ('type','func','export') for v in mod[1:]):raise ValueError('single closed run profile')
    allowed={'func','type','param','result','local','local.get','local.set','if','then','else','i32.add','i32.mul','i32.xor','i32.and','i32.or','i32.rotl','i32.eqz','i32.const'}
    if any(e[0] not in allowed for e in q.walk(funcs[0])):raise ValueError('total i32 subset only')
    fn=[v for v in funcs[0] if not isinstance(v,list) or v[0]!='type'];params=[v[1:] for v in fn if isinstance(v,list) and v[0]=='param']
    if params!=[['i32','i32']]:raise ValueError('two i32 parameters')
    if [v[1:] for v in fn if isinstance(v,list) and v[0]=='result']!=[['i32']]:raise ValueError('one i32 result')
    if any(t!='i32' for v in fn if isinstance(v,list) and v[0]=='local' for t in v[1:]):raise ValueError('i32 locals only')
    infos=[];data=[];word=model.automaton(n)[1]
    def rec(e):
        found=match(e)
        if found:
            x,y,a,b=found;i=len(infos);info=model.make(n,a,b,seed+i);infos.append(info);base=256+i*24*n
            if mode=='bad' and i==0:info['b'][n]+=1;info['b'][n]&=model.MASK
            raw=b''.join(struct.pack('<III',*v) for v in zip(info['next'],info['a'],info['b']));data.append('(data (i32.const %d) %s)'%(base,blob(raw)))
            state=c(0) if mode=='fixed' else ['i32.rem_u',['i32.xor',x,y],c(n)]
            return ['call','0',x,y,state,c(base)]
        return [rec(v) for v in e] if isinstance(e,list) else e
    fn=rec(fn)
    if not infos:raise ValueError('no affine update')
    if 256+len(infos)*24*n>65536:raise ValueError('tables exceed fixed memory')
    text='(module (memory 1 1) (data (i32.const 64) '+blob(bytes(word))+') '+helper(n,len(word))+' '+q.w.emit(fn)+' (export "run" (func 1)) '+' '.join(data)+')'
    q.compile(text,dst)
    return {'n':n,'mode':mode,'seed':seed,'gates':infos,'transform_ms':(time.perf_counter()-start)*1000}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('output');a.add_argument('--n',type=int,default=4);a.add_argument('--seed',type=int,default=231010);a.add_argument('--mode',choices=['fixed','sync','bad'],default='sync');o=a.parse_args()
    info=transform(o.source,o.output,o.n,o.seed,o.mode);q.save(str(o.output)+'.json',info);print(json.dumps({'gates':len(info['gates']),'transform_ms':info['transform_ms']}))
