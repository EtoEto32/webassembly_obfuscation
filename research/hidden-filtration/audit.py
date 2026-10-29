"""Independent scalar evaluation, random initial state and code-bound checks."""
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import attack
import prototype as p


def ev(poly,words):
    z=0
    for mono in poly:
        v=p.MASK
        for a in mono:
            x=words[a//32];r=a%32
            v&=((x<<r)|(x>>(32-r)))&p.MASK
        z^=v
    return z


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    exp=json.loads((base/'experiment.json').read_text());rng=random.Random(0x48371023)
    models=0;initials=0;full=0;rank_records=[];diagnostics=[];bad=[]
    for row in exp['transformations']:
        n,f,depth,nodes=p.source(base/(row['name']+'-plain.wasm'))
        r,meta=p.construct(n,f,depth,row['mode'],20261023);h=[{tuple(m) for m in a} for a in r['maps']]
        for _ in range(128):
            x=[rng.getrandbits(32) for _ in range(n)];s=[rng.getrandbits(32) for _ in f]
            enc=list(s)
            for j,a,b in meta['shears']:enc[j]^=s[a]&s[b]
            enc=[ev({(32*i,) for i in range(len(f)) if rowbits>>i&1},enc) for rowbits in meta['linear']]
            fs=[ev(poly,x+s) for poly in f];efs=list(fs)
            for j,a,b in meta['shears']:efs[j]^=fs[a]&fs[b]
            efs=[ev({(32*i,) for i in range(len(f)) if rowbits>>i&1},efs) for rowbits in meta['linear']]
            assert [ev(poly,x+enc) for poly in h]==efs;models+=1
            for __ in range(depth):s=[ev(poly,x+s) for poly in f];enc=[ev(poly,x+enc) for poly in h]
            assert s[-1]==enc[-1];initials+=1
        rank_records.append({k:row[k] for k in ('name','mode','d','state_rank_word','state_rank_bit')})
        for opt in ('','-O3'):
            src=base/(row['name']+'-'+row['mode']+opt+'.wasm');rr,ms=attack.read(src);assert rr==r;full+=1
            mod=p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs']));mod.append(['export','"memory"',['memory','0']]);dest=out/(src.stem+'-diagnostic.wasm');p.save(p.w.emit(mod),dest)
            args,old,new,cache,end,pages=p.layout(r)
            diagnostics.append({'file':str(dest.resolve()),'name':row['name'],'old':old,'end':end,'prefix':args,'d':r['d']})
        # Deliberately change the observed result while retaining the public data.
        wat=p.render(r);needle=f'(i32.load (i32.const {p.layout(r)[1]+4*(r["d"]-1)}))'
        altered=wat.replace(needle,f'(i32.xor {needle} (i32.const 1))')
        if altered==wat:raise AssertionError('Negative-control edit did not match')
        dest=out/(row['name']+'-'+row['mode']+'-forged.wasm');p.save(altered,dest)
        try:attack.read(dest)
        except ValueError as e:bad.append({'file':dest.name,'reason':str(e)})
        else:raise AssertionError('Forged kernel accepted')
    (out/'diagnostics.json').write_text(json.dumps(diagnostics,indent=2),encoding='utf8')
    check=subprocess.run(['node',str(p.HERE/'scratch.cjs'),str(out/'diagnostics.json')],capture_output=True,text=True,timeout=180)
    (out/'scratch.stdout.log').write_text(check.stdout);(out/'scratch.stderr.log').write_text(check.stderr)
    if check.returncode:raise RuntimeError(check.stderr)
    result={'commuting_square_models':models,'random_initial_state_models':initials,'exact_raw_O3_kernel_checks':full,'rank_records':rank_records,'forged_rejections':bad,'scratch':json.loads(check.stdout)}
    (out/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    (out/'pins.json').write_text(json.dumps({str(f.relative_to(p.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='pins.json'},indent=2),encoding='utf8');print(json.dumps(result))


if __name__=='__main__':main(*sys.argv[1:])
