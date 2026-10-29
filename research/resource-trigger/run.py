import argparse,json,platform,random,subprocess,time
from pathlib import Path
import prototype as p
def expression(n,family):
    r=random.Random(200+family);e=p.g(0)
    for i in range(n):
        k=r.getrandbits(32);op=p.STEPS[i%4]
        if family==0:payload=['i32.xor',p.g(1),p.c(k)]
        elif family==1:payload=['i32.add',['i32.rotl',p.g(1),p.c(i+1)],p.c(k)]
        else:payload=['i32.xor',['i32.mul',p.g(1),p.c(k|1)],['i32.shr_u',p.g(1),p.c(i%31+1)]]
        e=['i32.'+op,e,payload]
    return e
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output');ap.add_argument('--sizes',default='8,24,64');a=ap.parse_args();d=Path(a.output);d.mkdir(parents=True,exist_ok=False)
    manifest=dict(protocol='resource-trigger-indexed-v3',rows=[],negative=[],refusals=[],environment=dict(python=platform.python_version(),os=platform.platform(),node=subprocess.check_output(['node','--version'],text=True).strip(),jco='1.27.0',optimizer='Jco opt bundled Binaryen 130.0.0 -O3 --strip-debug'))
    for n in map(int,a.sizes.split(',')):
      for family in range(3):
        name=f'n{n}-f{family}';expr=expression(n,family);source=d/(name+'-source.wasm');p.q.compile(p.w.emit(p.mod(expr)),source)
        for mode in ('plain','direct','immediate','deferred'):
          raw=d/(name+'-'+mode+'-raw.wasm');stat=p.transform(source,raw,mode,1000+n+family);opt=raw.with_name(raw.name.replace('-raw','-o3'));t=time.perf_counter();p.jco('opt',raw,'-o',opt,'--quiet','--','-O3','--strip-debug');optms=(time.perf_counter()-t)*1000
          for variant in (raw,opt):
            rec=variant.with_name(variant.stem+'-recovered.wasm');stats=p.recover(variant,rec);stats.pop('code');js=variant.with_suffix('');trans=p.transpile(variant,js)
            row=dict(id=variant.stem,n=n,family=family,mode=mode,opt=variant==opt,source=source.name,component=variant.name,recovered=rec.name,js=js.name,expression=expr,transform=stat,recovery=stats,transpile=trans,opt_ms=optms if variant==opt else None,component_bytes=variant.stat().st_size,source_bytes=source.stat().st_size,sha256=p.q.digest(variant),recovered_sha256=p.q.digest(rec))
            manifest['rows'].append(row);p.q.save(d/'manifest.json',manifest)
        broken=d/(name+'-broken.wasm');p.transform(source,broken,'deferred',1000+n+family,True);js=broken.with_suffix('');p.transpile(broken,js);manifest['negative'].append(dict(id=name,js=js.name,expression=expr))
        p.q.save(d/'manifest.json',manifest);print('built',name,flush=True)
    rejects={'x-payload':p.w.emit(p.mod(['i32.add',p.g(0),p.g(0)])),'division':p.w.emit(p.mod(['i32.div_u',p.g(0),p.g(1)])),'memory':'(module (memory 1) (func (export "run") (param i32 i32) (result i32) (local.get 0)))','extra-export':'(module (func (export "run") (export "other") (param i32 i32) (result i32) (local.get 0)))','too-many':p.w.emit(p.mod(expression(129,0)))}
    for label,code in rejects.items():
        src=d/('refuse-'+label+'.wasm');p.q.compile(code,src)
        try:p.transform(src,d/('unexpected-'+label+'.wasm'));status='unexpected_acceptance';error=None
        except p.Unsupported as e:status='refused';error=str(e)
        manifest['refusals'].append(dict(label=label,status=status,reason=error))
    p.q.save(d/'manifest.json',manifest)
    r=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(d/'manifest.json')],capture_output=True,text=True,timeout=120)
    (d/'check.log').write_text(r.stdout+r.stderr,encoding='utf-8');print(r.stdout,r.stderr)
    if r.returncode:raise RuntimeError('check process failed')
if __name__=='__main__':main()
