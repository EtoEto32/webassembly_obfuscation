"""Resolve four scalar SMT timeouts with an explicitly checked selector partition."""
import argparse,json,time
from pathlib import Path
import prototype as p
from verify import model,z3
from run import save,snapshot
def main(src,earlier,out):
    src=Path(src);out=Path(out);out.mkdir(parents=True,exist_ok=False);snapshot(out)
    old=json.loads(Path(earlier).read_text());todo=[x for x in old['proofs'] if x['status']=='unknown'];variables=z3.BitVecs('x y z',32);records=[]
    for row in todo:
        name=row['file'];k=int(name.split('-')[0].removeprefix('blend')) if hasattr(str,'removeprefix') else int(name.split('-')[0][5:])
        lhs=p.read(src/f'blend{k}-source.wasm')[2];rhs=p.read(src/(Path(name).stem+'-recovered.wasm'))[2]
        predicates=set()
        def inspect(t,seen):
            if t in seen:return
            seen.add(t)
            if t[0]=='select':
                c=t[3]
                if any(x[0]=='arg' and x[1]!=2 for x in p.walk(c)):raise ValueError('Nonselector variable in predicate')
                predicates.add(c);inspect(t[1],seen);inspect(t[2],seen)
            elif t[0]=='arg':
                if t[1]==2:raise ValueError('Selector escapes into data result')
            else:
                for x in t[1:]:
                    if isinstance(x,tuple):inspect(x,seen)
        inspect(lhs,set());inspect(rhs,set());cases=[]
        for value in (0,1,0x80000000,0x80000001):
            decisions={};guards=[]
            for c in predicates:
                zc=model(c,variables);constant=z3.simplify(z3.substitute(zc,(variables[2],z3.BitVecVal(value,32)))).as_long()!=0
                solver=z3.Solver();solver.set(timeout=10000);solver.add((variables[2]&0x80000001)==value,(zc!=0)!=constant)
                status=str(solver.check());guards.append(status)
                if status!='unsat':raise ValueError('Partition did not determine a predicate')
                decisions[c]=constant
            memo={}
            def specialize(t):
                if t in memo:return memo[t]
                if t[0]=='select':ans=specialize(t[1] if decisions[t[3]] else t[2])
                elif t[0] in ('arg','i32.const'):ans=t
                else:ans=p.expr(t[0],*(specialize(x) for x in t[1:]))
                memo[t]=ans;return ans
            a=model(specialize(lhs),variables);b=model(specialize(rhs),variables);solver=z3.Solver();solver.set(timeout=10000);solver.add(a!=b)
            (out/f'{name}-{value}.smt2').write_text(solver.to_smt2(),encoding='utf-8');start=time.perf_counter();status=str(solver.check());ms=(time.perf_counter()-start)*1000
            cases.append(dict(selector_bits=value,predicate_proofs=guards,result=status,ms=ms))
        records.append(dict(file=name,predicate_count=len(predicates),cases=cases));save(out/'results.json',records)
    save(out/'summary.json',dict(status='passed' if all(c['result']=='unsat' for r in records for c in r['cases']) else 'incomplete',targets=len(records),case_proofs=sum(len(x['cases']) for x in records),predicate_proofs=sum(len(c['predicate_proofs']) for r in records for c in r['cases'])))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('earlier');a.add_argument('output');v=a.parse_args();main(v.input,v.earlier,v.output)
