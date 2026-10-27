import argparse,copy,itertools,json
from pathlib import Path
import prototype as p
import run
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);cs=0;ps=0
    for bits in range(1,6):
        mask=(1<<bits)-1
        for a,b,c in itertools.product(range(1<<bits),repeat=3):
            s=a^b^c;carry=((a&b)|(c&(a^b)))<<1;assert (s+carry)&mask==(a+b+c)&mask;cs+=1
    for bits in range(1,9):
        mask=(1<<bits)-1
        for x,m in itertools.product(range(1<<bits),repeat=2):assert ((x&m)+(x&(m^mask)))==x;ps+=1
    module,_=run.source(8,0);src=out/'source.wasm';p.compile(p.w.emit(module),src);refusals=[]
    for name in ('memory','division','extra_export','float_local'):
        m=copy.deepcopy(module);f=m[1]
        if name=='memory':m.insert(1,['memory','1'])
        elif name=='division':f[-1]=['i32.div_s',f[-1],p.g(2)]
        elif name=='extra_export':m.append(['export','"other"',['func','0']])
        else:f.insert(4,['local','f32'])
        file=out/(name+'.wasm');p.compile(p.w.emit(m),file)
        try:p.parse(file)
        except p.Unsupported as e:refusals.append(dict(file=file.name,reason=str(e)))
        else:raise AssertionError(name)
    result=dict(carry_save_comparisons=cs,partition_comparisons=ps,mismatches=0,profile_refusals=refusals);p.save(out/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
