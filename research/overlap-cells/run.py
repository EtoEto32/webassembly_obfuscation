import argparse,json,platform,subprocess
from pathlib import Path
import prototype as p
def main(out,small=False):
    d=Path(out);d.mkdir(parents=True,exist_ok=False);m=dict(rows=[],negative=[],refusals=[],environment=dict(python=platform.python_version(),os=platform.platform(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt='1.0.42',binaryen='133'))
    for n,rounds in ([(4,2)] if small else [(8,1),(16,2),(32,3)]):
      for family in range(3):
        prefix=f'n{n}-f{family}';src=d/(prefix+'-source.wasm');p.q.compile(p.fixture(n,rounds,family),src);_,rules,_=p.source(src);canon=d/(prefix+'-canonical.wasm');p.plain_canonical(src,canon)
        for mode in ('plain','single','pair-zero','pair-noise','pair-recode'):
          raw=d/(prefix+'-'+mode+'-raw.wasm');st=p.transform(src,raw,mode,111+n+family);o3=raw.with_name(raw.name.replace('-raw','-o3'));p.q.tool('wasm-opt',[raw,'-O3','--strip-debug','-o',o3]);p.w.tool('wasm-validate',[o3])
          for f in (raw,o3):
            attack=None;rec=None;match=None
            if mode!='plain':
              rec=f.with_name(f.stem+'-recovered.wasm');attack=p.recover(f,rec,diagnostics=True);attack.pop('code');match=p.q.digest(rec)==p.q.digest(canon)
            m['rows'].append(dict(id=f.stem,n=n,family=family,rounds=rounds,mode=mode,opt=f==o3,file=f.name,source=src.name,canonical=canon.name,rules=rules,recovered=rec.name if rec else None,canonical_match=match,attack=attack,transform=st,bytes=f.stat().st_size,sha256=p.q.digest(f),recovered_sha256=p.q.digest(rec) if rec else None))
            p.q.save(d/'manifest.json',m)
        broken=d/(prefix+'-broken.wasm');p.transform(src,broken,'pair-recode',111+n+family,True);m['negative'].append(dict(file=broken.name,n=n,rules=rules));p.q.save(d/'manifest.json',m);print('built',prefix,flush=True)
    # Valid Wasm outside the accepted transformation profile, not protection successes.
    for label,code in [('memory','(module (memory 1) (func (export "run") (param i64) (result i64) (local.get 0)))'),('nonbijective',p.fixture(4,1,0).replace('(i32.add (local.get 1)', '(i32.and (local.get 1)',1)),('too-many',p.fixture(32,5,0))]:
        src=d/('refuse-'+label+'.wasm');p.q.compile(code,src)
        try:p.transform(src,d/('unexpected-'+label+'.wasm'));status='unexpected_acceptance';reason=None
        except p.Unsupported as e:status='refused';reason=str(e)
        m['refusals'].append(dict(label=label,status=status,reason=reason))
    p.q.save(d/'manifest.json',m);result=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(d/'manifest.json')],capture_output=True,text=True,timeout=180);(d/'check.log').write_text(result.stdout+result.stderr,encoding='utf-8');print(result.stdout,result.stderr)
    if result.returncode:raise RuntimeError('check process')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');a.add_argument('--small',action='store_true');v=a.parse_args();main(v.output,v.small)
