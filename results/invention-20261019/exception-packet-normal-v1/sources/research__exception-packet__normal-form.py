"""Commutative/associative scalar equality check, separate from EH recovery.

Only uses identities valid for total i32 arithmetic. No e-graph/synthesis search.
"""
import argparse,collections,json,hashlib
from pathlib import Path
import prototype as p
from run import save,snapshot,canonical
def normalize(root):
    memo={};keys={}
    def key(x):
        if x not in keys:keys[x]=canonical(x)
        return keys[x]
    def f(x):
        if x in memo:return memo[x]
        op=x[0]
        if op in ('i32.const','arg'):ans=x
        else:
            args=[f(a) for a in x[1:]]
            if op in ('i32.xor','i32.add','i32.mul','i32.and','i32.or'):
                terms=[]
                def collect(v):
                    if v[0]==op:
                        for a in v[1:]:collect(a)
                    else:terms.append(v)
                for a in args:collect(a)
                c=1 if op=='i32.mul' else 0xffffffff if op=='i32.and' else 0;rest=[]
                for a in terms:
                    if a[0]!='i32.const':rest.append(a);continue
                    v=a[1]
                    if op=='i32.xor':c^=v
                    elif op=='i32.add':c=(c+v)&0xffffffff
                    elif op=='i32.mul':c=(c*v)&0xffffffff
                    elif op=='i32.and':c&=v
                    else:c|=v
                if op=='i32.xor':rest=[a for a,n in collections.Counter(rest).items() if n%2]
                elif op in ('i32.and','i32.or'):rest=list(set(rest))
                identity=1 if op=='i32.mul' else 0xffffffff if op=='i32.and' else 0
                annihilator=0 if op in ('i32.mul','i32.and') else 0xffffffff if op=='i32.or' else None
                if annihilator is not None and c==annihilator:rest=[]
                if c!=identity or not rest:rest.append(p.const(c))
                rest.sort(key=key);ans=rest[0]
                for a in rest[1:]:ans=p.expr(op,ans,a)
            else:ans=p.expr(op,*args)
        memo[x]=ans;return ans
    return f(root)
def main(src,out):
    src=Path(src);out=Path(out);out.mkdir(parents=True,exist_ok=False);snapshot(out);m=json.loads((src/'manifest.json').read_text());records=[]
    for row in m['files']:
        lhs=p.read(src/f"{row['kernel']}{row['k']}-source.wasm")[2];rhs=p.read(src/row['recovered'])[2]
        a=normalize(lhs);b=normalize(rhs)
        records.append(dict(file=row['file'],source_normal=canonical(a),recovered_normal=canonical(b),equal=a==b))
    save(out/'results.json',records);save(out/'summary.json',dict(status='passed' if all(x['equal'] for x in records) else 'incomplete',targets=len(records),equal=sum(x['equal'] for x in records)))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');v=a.parse_args();main(v.input,v.output)
