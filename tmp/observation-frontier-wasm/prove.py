"""Independent i32 expression check for the WABT-lifted arithmetic subset."""
from pathlib import Path
import os,sys,json,time
sys.path.insert(0,os.environ.get('WASM_SYNTH_DEPENDENCIES',r'C:\Users\ettotto\Documents\webassembly_obfuscation\.tools\encoding-synthesis-python'))
import z3
ROOT=Path(__file__).resolve().parent/'artifacts'

def expr(t,env):
    if type(t) is int: return z3.BitVecVal(t,32)
    if isinstance(t,str): return env[t]
    name,l,r=t; a=expr(l,env);b=expr(r,env)
    return {'add':lambda:a+b,'sub':lambda:a-b,'mul':lambda:a*b,'xor':lambda:a^b,'and':lambda:a&b,'or':lambda:a|b}[name]()

def prove(label,lhs,rhs):
    # Exact ring normalization avoids treating solver resource limits as effects.
    difference=z3.simplify(lhs-rhs,som=True)
    solver=z3.SolverFor('QF_BV');solver.set(timeout=3000)
    solver.add(difference!=0); start=time.perf_counter();v=solver.check()
    row={'label':label,'result':str(v),'seconds':time.perf_counter()-start,'normalization':'z3 simplify som=True'}
    if v==z3.unknown: row['reason']=solver.reason_unknown()
    return row

def main():
    output=ROOT/'proofs.json'
    if output.exists(): raise SystemExit('Refuse overwrite')
    data=json.loads((ROOT/'results.json').read_text()); rows=[];witnesses=[]
    a,b,c=z3.BitVecs('a b c',32);env={'a':a,'b':b,'c':c};target=(a+b)*c*c
    for item in data['results']:
        name=item['name'];atoms=[expr(t,env) for t in item['atomExpressions']]
        expected=a+b+c+(c*c if item['context'] else 0)
        rows.append(prove(name+':output',expr(item['outputExpression'],env),expected))
        for i,record in enumerate(item['verified']):
            d=record['decoder']; op=d[0]
            if op=='atom':value=atoms[d[1]]
            elif op=='not':value=~atoms[d[1]]
            else:
                x,y=atoms[d[1]],atoms[d[2]]
                value={'add':lambda:x+y,'sub':lambda:x-y,'mul':lambda:x*y,'xor':lambda:x^y,'and':lambda:x&y,'or':lambda:x|y}[op]()
            rows.append(prove(name+':one-op-'+str(i),value,target))
        if item['context']:
            index=item['atomExpressions'].index(['mul','c','c'])
            witness=['mul',['add',['atom',0],['atom',1]],['atom',index]]
            value=(atoms[0]+atoms[1])*atoms[index]
            rows.append(prove(name+':two-op-witness',value,target))
            witnesses.append({'name':name,'decoder':witness,'method':'explicit construction; not automatic two-operation synthesis'})
    result={'z3':z3.get_version_string(),'proofs':rows,'two_operation_witnesses':witnesses}
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(rows),'verdicts':{v:sum(r['result']==v for r in rows) for v in ['unsat','sat','unknown']},'two_operation_witnesses':len(witnesses)}))
    assert all(r['result']=='unsat' for r in rows)

if __name__=='__main__':main()
