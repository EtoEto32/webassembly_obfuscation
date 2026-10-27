"""Positive controls outside the generator's default shift, plus refusal checks."""
import argparse
from pathlib import Path
import prototype as p
import attack
from run import models,save,command


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);ds=models();selected={'cubic_shift0':ds['cubic'],'even_quartic_shift7':['i32.mul',p.const(2),ds['quartic']]};files=[];records=[]
    for name,e in selected.items():
        shift=0 if name.startswith('cubic') else 7
        src=a.output/(name+'.source.wasm');dst=a.output/(name+'.stencil.wasm');rec=a.output/(name+'.recovered.wasm')
        p.compile_wat(p.scalar_dag(e),src);code,_=p.lifted(e,'constant',shift=shift);p.compile_wat(code,dst);stats=attack.recover(dst,rec);records.append(dict(name=name,shift=shift,**stats))
        files.extend(dict(model=name,path=f.name) for f in (src,dst,rec))
    save(a.output/'manifest.json',dict(models=selected,files=files));save(a.output/'analysis.json',records);correct=command(['node',Path(__file__).resolve().parent.parent/'lane-demand/check.cjs',a.output]);save(a.output/'correctness.json',correct);print(str(correct['calls'])+' matched')


if __name__=='__main__':main()
