import argparse,copy,itertools,json
from pathlib import Path
import prototype as p
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);checks=0
    for bits in (1,2):
        mod=1<<bits;mask=mod-1;rot=lambda a:((a<<1)|(a>>(bits-1)))&mask
        for kind in range(3):
            def f(a,b,i):
                c=1+2*(i%2)
                return rot((a*c+b)&mask) if kind==0 else (((a^b)*c+rot(a))&mask if kind==1 else rot((a+b)&mask)^((a*c)&mask))
            for initial in itertools.product(range(mod),repeat=4):
                for count in range(5):
                    for inputs in itertools.product(range(mod),repeat=count):
                        sequential=list(initial)
                        for x in inputs:
                            for i in range(4):sequential[i]=f(sequential[i],x if i==0 else sequential[i-1],i)
                        diagonal=list(initial)
                        for tick in range(count+3):
                            old=diagonal[:]
                            for i in range(4):
                                if i<=tick<count+i:diagonal[i]=f(old[i],inputs[tick] if i==0 else old[i-1],i)
                        assert diagonal==sequential;checks+=1
    src=out/'source.wasm';spec=dict(coeff=[100003,100019,100043,100049],kind=0,r=7,n=4);p.compile(p.w.emit(p.source(spec['coeff'],0,7)),src);base=p.read(src);refusals=[]
    for name in ('export_memory','guard_change','input_mutation','intermediate_store'):
        m=copy.deepcopy(base);f=next(e for e in m[1:] if e[0]=='func');lp=next(e for e in p.walk(f) if e[0]=='loop')
        if name=='export_memory':m.append(['export','"memory"',['memory','0']])
        elif name=='guard_change':next(e for e in p.walk(f) if e[0]=='i32.gt_u')[2]=p.c(65535)
        elif name=='input_mutation':lp.insert(2,p.st(1,p.c(0)))
        else:lp.insert(2,['i32.store',p.c(0),p.c(42)])
        file=out/(name+'.wasm');p.compile(p.w.emit(m),file)
        try:p.parse_source(p.read(file))
        except p.Unsupported as e:refusals.append(dict(file=file.name,reason=str(e)))
        else:raise AssertionError(name)
    recovery_refusals=[]
    for name in ('wrong_stop','wrong_predecessor'):
        m=p.build(spec,'mixed',broken=name=='wrong_stop')
        if name=='wrong_predecessor':
            shuffle=next(e for e in p.walk(m) if e[0]=='i8x16.shuffle');shuffle[1:5]=['0','1','2','3']
        file=out/(name+'.wasm');p.compile(p.w.emit(m),file)
        try:p.extract(file)
        except p.Unsupported as e:recovery_refusals.append(dict(file=file.name,reason=str(e)))
        else:raise AssertionError(name)
    result=dict(model_comparisons=checks,mismatches=0,profile_refusals=refusals,recovery_refusals=recovery_refusals)
    p.save(out/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
