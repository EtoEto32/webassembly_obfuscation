import argparse,json,platform,random,shutil,statistics,subprocess,time,traceback
from pathlib import Path
import prototype as p
import recover as r
HERE=Path(__file__).resolve().parent
def save(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def snapshot(out):
    src=out/'sources';src.mkdir();records=[]
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),HERE/'plan.md',p.ROOT/'research/connectivity-elimination/prototype.py',p.ROOT/'research/stack-cycle/transform.py']:
        name=str(f.relative_to(p.ROOT)).replace('/','__').replace('\\','__');shutil.copyfile(f,src/name);records.append(dict(path=str(f.relative_to(p.ROOT)),sha256=p.digest(f),snapshot=name))
    save(out/'sources.json',records)
def fixture(kernel,k):
    code=['(local.set $h (local.get 0))']
    for j in range(k):
        c=f'(i32.and (local.get 2) (i32.const {1 if j%2==0 else 2147483648}))'
        if kernel=='blend':
            a=f'(i32.rotl (i32.add (local.get 0) (i32.const {j*123+17})) (i32.const {j%31+1}))'
            b=f'(i32.mul (i32.xor (local.get 1) (i32.const {j*311+91})) (i32.const {j*2+3}))'
            value=f'(i32.xor (local.get $h) (select {a} {b} {c}))'
        else:
            a=f'(i32.add (local.get $h) (i32.const {(j+1)*12345}))'
            b=f'(i32.rotl (i32.xor (local.get $h) (local.get 1)) (i32.const {j%31+1}))'
            if kernel=='rolling':c=f'(i32.and (i32.shr_u (local.get 0) (i32.const {j%8})) (i32.const 1))'
            value=f'(select {a} {b} {c})'
        code.append(f'(local.set $h {value})')
    return '(module (func (export "run") (param i32 i32 i32) (result i32) (local $h i32) '+''.join(code)+'(local.get $h)))'
def canonical(t):
    memo={}
    def f(x):
        if x in memo:return memo[x]
        import hashlib
        val=hashlib.sha256((x[0]+':'+':'.join(f(a) if isinstance(a,tuple) else str(a) for a in x[1:])).encode()).hexdigest();memo[x]=val;return val
    return f(t)
def main(out,small=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);snapshot(out)
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),node=json.loads(subprocess.check_output(['node','-e',"console.log(JSON.stringify({versions:process.versions,cpu:require('os').cpus()[0].model,logicalCPUs:require('os').cpus().length}))"],text=True)),wabt=p.w.tool('wat2wasm',['--version']),binaryen=p.w.tool('wasm-opt',['--version'])))
    rows=[];transforms=[];attacks=[];analysis=[];sources=[]
    try:
        for kernel in (('blend',) if small else ('blend','chain','rolling')):
            for k in ((4,) if small else (4,16,48)):
                label=f'{kernel}{k}';src=out/(label+'-source.wasm');p.compile(fixture(kernel,k),src);sources.append(dict(kernel=kernel,k=k,file=src.name,sha256=p.digest(src)))
                baseline=canonical(p.read(src)[2])
                for mode in p.MODES:
                    raw=out/f'{label}-{mode}-raw.wasm';transforms.append(dict(kernel=kernel,k=k,**p.transform(src,raw,mode)))
                    for opt in ('raw','O3'):
                        target=raw if opt=='raw' else out/f'{label}-{mode}-O3.wasm'
                        if opt=='O3':p.optimize(raw,target)
                        row=dict(kernel=kernel,k=k,mode=mode,opt=opt,file=target.name,bytes=target.stat().st_size,sha256=p.digest(target));rows.append(row)
                        recovered=out/(target.stem+'-recovered.wasm')
                        try:
                            attack=r.recover(target,recovered);attack['canonical_equal']=canonical(p.read(recovered)[2])==baseline
                            row['recovered']=recovered.name;row['recovered_sha256']=p.digest(recovered)
                            tree=p.binaryen_tree(target);times=[]
                            for rep in range(10):
                                tick=time.perf_counter();engine=r.Recover(tree);engine.run();elapsed=(time.perf_counter()-tick)*1000
                                if rep:times.append(elapsed)
                            analysis.append(dict(file=target.name,samples_ms=times,median_ms=statistics.median(times),steps=engine.steps,max_flows=engine.max_flows))
                        except Exception as ex:
                            attack=dict(status='unsupported' if isinstance(ex,ValueError) else 'implementation_error',error=str(ex),traceback=traceback.format_exc())
                        attacks.append(dict(file=target.name,**attack))
                        save(out/'manifest.json',dict(sources=sources,files=rows));save(out/'attacks.json',attacks)
                print(label,flush=True)
        save(out/'transforms.json',transforms);save(out/'analysis-timing.json',analysis)
        subprocess.run(['node',str(HERE/'check.cjs'),str(out)],check=True,timeout=180)
        save(out/'summary.json',dict(status='completed',targets=len(rows),recoveries=sum(x['status']=='recovered' for x in attacks),canonical_equal=sum(x.get('canonical_equal',False) for x in attacks)))
    except Exception as ex:
        save(out/'failure.json',dict(error=str(ex),traceback=traceback.format_exc()));raise
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');a.add_argument('--small',action='store_true');v=a.parse_args();main(v.output,v.small)
