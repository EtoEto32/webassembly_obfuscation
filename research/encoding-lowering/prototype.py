"""Range-proven relaxed swizzle lowering. An optimization hypothesis, not novelty.

Restricted pure straight-line profile. The finite range certificate concerns
instruction semantics; it does not certify protection strength.
"""
import argparse,importlib.util,pathlib,time,json
ROOT=pathlib.Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('swizzle',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
ALLOWED=set('module type func export param result local local.get local.set local.tee i32.const i32x4.splat i32x4.extract_lane v128.const v128.and v128.or v128.xor v128.not v128.bitselect i8x16.swizzle i8x16.relaxed_swizzle i8x16.eq i8x16.add i8x16.sub'.split())
def lower(src,dst,reverse=False):
    start=time.perf_counter();m=q.read(src)
    if any(e[0] not in ('type','func','export') for e in m[1:]):raise ValueError('pure module only')
    fs=[f for f in m[1:] if f[0]=='func']
    if len(fs)!=1:raise ValueError('one function only')
    f=fs[0]
    if any(e[0] not in ALLOWED for e in q.walk(f)):raise ValueError('unsupported instruction')
    params=[v for e in f[1:] if isinstance(e,list) and e[0]=='param' for v in e[1:]]
    locals_=[v for e in f[1:] if isinstance(e,list) and e[0]=='local' for v in e[1:]]
    if any(t not in ('i32','v128') for t in params+locals_):raise ValueError('type profile')
    env=[False]*len(params)+[True]*len(locals_);proof=[]
    def visit(e):
        op=e[0]
        if op=='local.get':return env[int(e[1])]
        if op=='v128.const':return all(x<16 for x in q.vconst(e))
        if op=='i32.const':return 0<=int(e[1],0)<16
        if op in ('local.set','local.tee'):
            if len(e)!=3:raise ValueError('folded assignment required')
            v=visit(e[2]);env[int(e[1])]=v;return v
        args=[x for x in e[1:] if isinstance(x,list)];flags=[visit(x) for x in args]
        if op in ('i8x16.swizzle','i8x16.relaxed_swizzle'):
            if len(flags)!=2:raise ValueError('folded swizzle required')
            before=op;changed=flags[1] and op==('i8x16.relaxed_swizzle' if reverse else 'i8x16.swizzle')
            if changed:e[0]='i8x16.swizzle' if reverse else 'i8x16.relaxed_swizzle'
            proof.append(dict(index=len(proof),input_range_proved=flags[1],changed=changed,from_op=before,to_op=e[0]))
            return flags[0] # all selected bytes and out-of-range zero are below 16
        if op=='v128.and':return any(flags)
        if op in ('v128.or','v128.xor'):return all(flags)
        if op=='v128.bitselect':return flags[0] and flags[1]
        if op=='i32x4.splat':return flags[0]
        return False
    for e in f[1:]:
        if isinstance(e,list) and e[0] not in ('type','param','result','local','export'):visit(e)
    q.compile(q.w.emit(m),dst)
    return dict(swizzles=len(proof),changed=sum(p['changed'] for p in proof),proof=proof,ms=(time.perf_counter()-start)*1000)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('output');a.add_argument('--reverse',action='store_true');v=a.parse_args();print(json.dumps(lower(v.source,v.output,v.reverse),indent=2))
