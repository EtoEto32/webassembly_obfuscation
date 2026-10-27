"""Verify saved rank witnesses without using the family verifier."""
import itertools
import json
from pathlib import Path
import sys
from shared import h,a,load
saved=sys.modules.get('prototype');sys.modules['prototype']=h
verify=load('bf_fa_verify',h.HERE/'verify.py')
if saved is None:del sys.modules['prototype']
else:sys.modules['prototype']=saved


def main(cert_path,base,out):
    cert=json.loads(Path(cert_path).read_text());base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);checked=0;edges=0
    for n in (2,3):
        item=cert['dimension'+str(n)];rows=item['certificates'];expected=set(itertools.product(*(range(1<<(1<<i)) for i in range(n))))
        assert {tuple(row['source_tables']) for row in rows}==expected and len(rows)==len(expected)
        largest=0
        for row in rows:
            tables=row['source_tables'];ranks=row['ranks'];values=[]
            for state in range(1<<n):values.append(sum(((table>>(state% (1<<i)))&1)<<i for i,table in enumerate(tables)))
            roots=[s for s,v in enumerate(values) if s==v];assert roots==[row['target']];assert ranks[roots[0]]==0
            for s in range(1<<n):
                actual={values[s]^N[s^values[s]] for N in item['family']};assert actual==set(row['edges'][s])
                if s==roots[0]:assert actual=={s}
                else:assert all(ranks[t]<ranks[s] for t in actual)
                edges+=len(actual)
            largest=max(largest,max(ranks));checked+=1
        assert largest==item['bound']
    args=[verify.z3.BitVec('x',32),verify.z3.BitVec('y',32)];calls=0
    for name in ('mix8','select10','chain12'):
        original=verify.symbolic(base/(name+'-plain.wasm'),args)
        for opt in ('','-O3'):
            file=base/(name+'-coupled'+opt+'.wasm');mod=h.w.parse(h.w.tool('wasm2wat',[file,'--fold-exprs']));wanted=[]
            for j,(x,y) in enumerate(((0,0),(-1,-1),(-2147483648,2147483647),(0x12345678,0x89abcdef))):
                wanted.append(verify.z3.simplify(verify.z3.substitute(original,(args[0],verify.z3.BitVecVal(x,32)),(args[1],verify.z3.BitVecVal(y,32)))).as_long())
                mod.append(h.w.parse(f'(module (func (export "probe{j}") (result i32) (call 0 (i32.const {x}) (i32.const {y}))))')[1])
            dest=out/(file.stem+'-probe.wasm');h.save(h.w.emit(mod),dest);log=h.w.tool('wasm-interp',[dest,'--run-all-exports']);(out/(dest.stem+'.log')).write_text(log)
            for j,v in enumerate(wanted):assert f'probe{j}() => i32:{v}' in log;calls+=1
    result={'rank_witnesses':checked,'edges_checked':edges,'wabt_calls':calls,'mismatches':0};(out/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main(*sys.argv[1:])
