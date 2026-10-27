import argparse,itertools,json
from pathlib import Path
import prototype as p
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);checks=0
    for bits in (1,2):
        mask=(1<<bits)-1
        for depth in (1,2,3,4):
            coeff=[3,1,3,1][:depth];allg=p.schedule(4,coeff)
            def gates(a,gs):
                a=list(a)
                for _,t,c,_ in gs:a[t]^=(a[(t-1)%4]*c+a[(t+1)%4])&mask
                return a
            for i in range(4):
                for j in range(4):
                    for mode in ('full','footprint','patch'):
                        selected=p.plan(4,coeff,{j},{i},mode)
                        for a in itertools.product(range(mask+1),repeat=4):
                            encoded=gates(a,allg)
                            for x in range(mask+1):
                                want=list(a);ret=want[j];want[i]=(ret+x)&mask;want=gates(want,allg)
                                got=gates(encoded,selected[::-1]);outcome=got[j];got[i]=(outcome+x)&mask;got=gates(got,selected)
                                assert got==want and outcome==ret;checks+=1
    # Negative input profiles are refused before writing an output file.
    src=out/'source.wasm';p.compile(p.source_text([i for i in range(128)],8,4),src);base=p.read(src);refusals=[]
    import copy
    for name in ('export_memory','base_mutation','field_outside','division','early_return'):
        m=copy.deepcopy(base);f=next(e for e in m[1:] if e[0]=='func');body=[e for e in f[1:] if e[0] not in p.DECL]
        if name=='export_memory':m.append(['export','"memory"',['memory','0']])
        elif name=='base_mutation':f.insert(f.index(body[2]),['local.set','3',p.c(0)])
        elif name=='field_outside':next(e for e in p.walk(f) if e[0]=='i32.load').insert(1,'offset=128')
        elif name=='division':f[-1]=['i32.div_u',p.c(1),p.c(0)]
        else:f[-1]=['return',f[-1]]
        try:p.profile(m,8,4)
        except p.Unsupported as e:refusals.append(dict(name=name,reason=str(e)))
        else:raise AssertionError(name)
    p.save(out/'summary.json',dict(scalar_model_comparisons=checks,mismatches=0,refusals=refusals));print(json.dumps(dict(comparisons=checks,refusals=len(refusals))))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
