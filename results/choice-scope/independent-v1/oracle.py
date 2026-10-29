"""Restricted relational result-membership oracle. Not a new SMT algorithm.

Inputs are validated Wasm binaries. Unsupported features fail closed. Float
values remain bitvectors, preserving NaN payloads across copies/reinterprets.
"""
import argparse,importlib.util,itertools,json,re,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.tools/encoding-synthesis-python'))
import z3 as z
spec=importlib.util.spec_from_file_location('wat_reader',ROOT/'research/connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
class Unsupported(ValueError): pass
def bv(n,bits=32): return z.BitVecVal(n,bits)
def pack(xs): return z.Concat(*reversed(xs))
def lanes(v,bits): return [z.Extract(i+bits-1,i,v) for i in range(0,128,bits)]
def float_bits(s):
    sign=0x80000000 if s.startswith('-') else 0;s=s.lstrip('+-')
    if s.startswith('nan'): return sign|0x7f800000|(int(s.split(':')[1],0) if ':' in s else 0x400000)
    value=float.fromhex(s) if s.startswith('0x') else float(s)
    return struct.unpack('<I',struct.pack('<f',-value if sign else value))[0]

class Program:
    def __init__(self,path):
        self.path=Path(path)
        if self.path.stat().st_size>262144: raise Unsupported('binary size limit')
        w.tool('wasm-validate',[path,'--enable-all'])
        self.mod=w.parse(w.tool('wasm2wat',[path,'--fold-exprs','--enable-all']))
        if any(x[0] not in ('type','func','export') for x in self.mod[1:]): raise Unsupported('module declarations')
        fs=[x for x in self.mod[1:] if x[0]=='func'];es=[x for x in self.mod[1:] if x[0]=='export']
        if len(fs)!=1 or es!=[['export','"run"',['func','0']]]: raise Unsupported('one exported run required')
        f=fs[0]
        def fields(k): return [t for x in f[1:] if isinstance(x,list) and x[0]==k for t in x[1:]]
        self.params=fields('param');self.localtypes=fields('local');self.results=fields('result')
        if any(t!='i32' for t in self.params+self.results) or not self.results or len(self.results)>64: raise Unsupported('i32 interface required')
        if any(t not in ('i32','f32','v128') for t in self.localtypes): raise Unsupported('local type')
        self.body=[x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','result','local')]
        allowed={'local.get','local.set','local.tee','drop','nop','i32.const','f32.const','v128.const',
                 'f32.reinterpret_i32','i32.reinterpret_f32','f32.neg','f32.abs','f32.add',
                 'i32.xor','i32.and','i32.or','i32.add','i32.sub','i32.mul','i32.shl','i32.shr_u','i32.shr_s',
                 'v128.xor','v128.and','v128.or','v128.not','v128.bitselect',
                 'i8x16.swizzle','i8x16.relaxed_swizzle','return',
                 *[f'i{n}x{128//n}.splat' for n in (8,16,32)],
                 *[f'i{n}x{128//n}.extract_lane_{s}' for n in (8,16) for s in ('s','u')],
                 'i32x4.extract_lane',*[f'i{n}x{128//n}.relaxed_laneselect' for n in (8,32,64)]}
        pending=list(self.body);seen=0
        while pending:
            e=pending.pop();seen+=1
            if seen>4096 or len(self.localtypes)>512: raise Unsupported('expression/local limit')
            if e[0] not in allowed: raise Unsupported('instruction '+e[0])
            pending.extend(x for x in e[1:] if isinstance(x,list))
        # Inspect the whole body, including otherwise unused expressions.
        self.model([0]*len(self.params))

    def model(self,inputs,independent=False):
        if len(inputs)!=len(self.params): raise ValueError('input count')
        local=[bv(n) for n in inputs]+[bv(0,128 if t=='v128' else 32) for t in self.localtypes]
        constraints=[];profiles={};fresh=0;sites=0
        def profile(name):
            nonlocal sites
            key=name+('_'+str(sites) if independent else '');sites+=1
            if key not in profiles: profiles[key]=z.Bool('r_'+key)
            return profiles[key]
        def value(e):
            nonlocal fresh
            if not isinstance(e,list) or not e: raise Unsupported('non-expression')
            op=e[0]
            if op=='local.get': return local[int(e[1])]
            if op in ('local.set','local.tee'):
                v=value(e[2]);local[int(e[1])]=v;return v if op=='local.tee' else None
            if op=='drop': value(e[1]);return None
            if op=='nop': return None
            if op=='i32.const': return bv(int(e[1],0))
            if op=='f32.const': return bv(float_bits(e[1]))
            if op=='v128.const':
                m=re.fullmatch(r'i(8|16|32|64)x\d+',e[1])
                if not m: raise Unsupported('vector constant shape')
                bits=int(m[1]);xs=[bv(int(n,0),bits) for n in e[2:]]
                if len(xs)*bits!=128: raise Unsupported('vector size')
                return pack(xs)
            if op in ('f32.reinterpret_i32','i32.reinterpret_f32'): return value(e[1])
            if op in ('f32.neg','f32.abs'):
                a=value(e[1]);return a^bv(0x80000000) if op=='f32.neg' else a&bv(0x7fffffff)
            if op=='f32.add':
                a,b=map(value,e[1:]);fa=z.fpBVToFP(a,z.Float32());fb=z.fpBVToFP(b,z.Float32());fr=z.fpAdd(z.RNE(),fa,fb)
                out=z.BitVec('nan_or_sum_'+str(fresh),32);fresh+=1
                canonical=z.And(z.Implies(z.fpIsNaN(fa),a&bv(0x7fffffff)==bv(0x7fc00000)),z.Implies(z.fpIsNaN(fb),b&bv(0x7fffffff)==bv(0x7fc00000)))
                nan_constraint=z.If(canonical,out&bv(0x7fffffff)==bv(0x7fc00000),out&bv(0x7fc00000)==bv(0x7fc00000))
                constraints.append(z.simplify(z.If(z.fpIsNaN(fr),nan_constraint,out==z.fpToIEEEBV(fr))))
                return out
            if op in ('i32.xor','i32.and','i32.or','i32.add','i32.sub','i32.mul','v128.xor','v128.and','v128.or'):
                a,b=map(value,e[1:]);name=op.split('.')[1]
                return {'xor':lambda:a^b,'and':lambda:a&b,'or':lambda:a|b,'add':lambda:a+b,'sub':lambda:a-b,'mul':lambda:a*b}[name]()
            if op in ('i32.shl','i32.shr_u','i32.shr_s'):
                a,b=map(value,e[1:]);b=b&31
                return a<<b if op=='i32.shl' else z.LShR(a,b) if op=='i32.shr_u' else a>>b
            if op=='v128.not': return ~value(e[1])
            if op=='v128.bitselect':
                a,b,m=map(value,e[1:]);return (a&m)|(b&~m)
            m=re.fullmatch(r'i(8|16|32)x\d+\.splat',op)
            if m:
                bits=int(m[1]);a=value(e[1]);return pack([z.Extract(bits-1,0,a)]*(128//bits))
            m=re.fullmatch(r'i(8|16|32)x\d+\.extract_lane(_u|_s)?',op)
            if m:
                bits=int(m[1]);v=lanes(value(e[2]),bits)[int(e[1])]
                return z.SignExt(32-bits,v) if m[2]=='_s' else z.ZeroExt(32-bits,v)
            if op in ('i8x16.swizzle','i8x16.relaxed_swizzle'):
                a,b=map(value,e[1:]);xs=lanes(a,8);r=profile('swizzle') if 'relaxed' in op else z.BoolVal(False);out=[]
                for j in lanes(b,8):
                    v=xs[0]
                    for k in range(1,16): v=z.If((j&15)==k,xs[k],v)
                    out.append(z.If(z.Or(z.ULT(j,16),z.And(r,z.ULT(j,128))),v,bv(0,8)))
                return pack(out)
            m=re.fullmatch(r'i(8|32|64)x\d+\.relaxed_laneselect',op)
            if m:
                bits=int(m[1]);a,b,mask=map(value,e[1:]);r=profile('laneselect');out=[]
                for x,y,k in zip(lanes(a,bits),lanes(b,bits),lanes(mask,bits)):
                    out.append(z.If(r,z.If(z.Extract(bits-1,bits-1,k)==1,x,y),(x&k)|(y&~k)))
                return pack(out)
            raise Unsupported('instruction '+op)
        outputs=[]
        for e in self.body:
            if e[0]=='return':
                outputs.extend(value(x) for x in e[1:]);break
            v=value(e)
            if v is not None: outputs.append(v)
        if len(outputs)!=len(self.results) or any(v.size()!=32 for v in outputs): raise Unsupported('result shape')
        return [z.simplify(v) for v in outputs],constraints,profiles

    def check(self,inputs,observed,mode='joint',timeout_ms=2000):
        start=time.perf_counter();outputs,cs,ps=self.model(inputs,independent=mode=='independent-site')
        if len(observed)!=len(outputs): raise ValueError('output count')
        eqs=[a==bv(b) for a,b in zip(outputs,observed)];calls=0;unknowns=[]
        def query(extra):
            nonlocal calls
            s=z.Solver();s.set(timeout=timeout_ms);s.add(*cs,*extra);calls+=1;r=s.check()
            if r==z.unknown: unknowns.append(s.reason_unknown())
            return str(r)
        if mode=='pointwise':
            answers=[query([e]) for e in eqs]
            status='unsat' if 'unsat' in answers else 'unknown' if 'unknown' in answers else 'sat'
        elif mode=='enumerated':
            answers=[]
            for vals in itertools.product((False,True),repeat=len(ps)):
                a=query(eqs+[p==v for p,v in zip(ps.values(),vals)]);answers.append(a)
                if a=='sat': break
            status='sat' if 'sat' in answers else 'unknown' if 'unknown' in answers else 'unsat'
        elif mode in ('joint','independent-site'): status=query(eqs)
        else: raise ValueError('mode')
        return dict(status=status,queries=calls,milliseconds=(time.perf_counter()-start)*1000,unknown_reasons=unknowns)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('wasm',type=Path);ap.add_argument('inputs',help='JSON i32 array');ap.add_argument('outputs',help='JSON i32 array');ap.add_argument('--mode',default='joint',choices=['joint','pointwise','independent-site','enumerated']);a=ap.parse_args()
    try: print(json.dumps(Program(a.wasm).check(json.loads(a.inputs),json.loads(a.outputs),a.mode)))
    except Unsupported as e: print(json.dumps(dict(status='unsupported',reason=str(e))));sys.exit(2)
