"""Exercise i64 bit 31/32/63 and signed constants separately from the main corpus."""
from dataclasses import asdict
import argparse
import json
from pathlib import Path
import prototype as p
from run import command,save,HERE


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    positions=[0,31,32,63];d=p.m.DFA([[(q+1)%4,(q+2)%4] for q in range(4)],10,3)
    rows=[[0,0] for _ in range(64)]
    for q,i in enumerate(positions):rows[i]=[1<<positions[j] for j in d.trans[q]]
    n=p.m.NFA(rows,1<<63,(1<<31)|(1<<63));p.s.compile_wat(p.nfa_wat(n),out/'edge.raw.wasm')
    manifest=dict(models=dict(edge=asdict(d)),files=[]);analysis=[]
    for opt in ('raw','O2','O3'):
        target=out/('edge.'+opt+'.wasm')
        if opt!='raw':p.w.tool('wasm-opt',[out/'edge.raw.wasm','-'+opt,'-o',target])
        extracted,template=p.extract(p.s.read(target),out);recovered,report=p.attack(extracted,'subset')
        assert p.m.equivalent(d,recovered)[0]
        rec=out/(target.stem+'.recovered.wasm');p.s.compile_wat(p.dfa_wat(recovered),rec)
        for path,flag in [(target,False),(rec,True)]:manifest['files'].append(dict(path=path.name,model='edge',opt=opt,recovered=flag))
        analysis.append(dict(path=target.name,template=template,**report))
    save(out/'manifest.json',manifest);save(out/'analysis.json',analysis)
    check=json.loads(command(['node',HERE/'check.cjs',out]));save(out/'checks.json',check);print(json.dumps(check))


if __name__=='__main__':main()
