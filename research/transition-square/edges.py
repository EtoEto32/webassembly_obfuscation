"""Additional coverage: high-bit literals, constants via complement, sharing."""
import json,subprocess,sys
from pathlib import Path
import prototype as p
B=lambda i,n=0:('bit',i,n)
O=lambda op,a,b:(op,a,b)
def main(dest):
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    a,b,c=B(31),B(0),B(17,1)
    cases={'high':a,'same-and':O('and',a,a),'same-or':O('or',a,a),'tautology':O('or',a,B(31,1)),
      'contradiction':O('and',a,B(31,1)),'shared':O('or',O('and',a,b),O('and',a,c))}
    # check.cjs adds all low two-bit words, four boundary values and 512 full-word random inputs.
    p.q.save(out/'cases.json',{k:{'bits':2,'tree':v} for k,v in cases.items()});rows=[];attacks=[]
    for name,t in cases.items():
        src=out/(name+'-plain-raw.wasm');p.q.compile(p.plain(t),src)
        for mode in ('plain','base','square'):
            raw=out/(name+'-'+mode+'-raw.wasm')
            if mode!='plain':p.transform(src,raw,mode,213074)
            for opt in ('raw','O3'):
                f=out/(name+'-'+mode+'-'+opt+'.wasm')
                if opt=='O3':p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',f])
                rows.append({'name':name,'mode':mode,'opt':opt,'file':f.name})
                if mode=='square':
                    dst=out/(f.stem+'-recovered.wasm');attacks.append({'file':f.name,**p.recover(f,dst)})
                    rows.append({'name':name,'mode':'recovered','opt':opt,'file':dst.name})
    p.q.save(out/'manifest.json',rows);p.q.save(out/'attacks.json',attacks)
    proc=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=60)
    (out/'checks.stdout.txt').write_text(proc.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(proc.stderr,encoding='utf-8')
    if proc.returncode:raise RuntimeError(proc.stderr)
    facts=json.loads(proc.stdout);p.q.save(out/'checks.json',facts)
    p.q.save(out/'sha256.json',[{'file':str(f.relative_to(p.ROOT)).replace('\\','/'),'sha256':p.q.digest(f)} for f in [p.HERE/'edges.py',p.HERE/'prototype.py',p.HERE/'check.cjs']+list(out.rglob('*')) if f.is_file()])
    print(json.dumps({'conditions':len(rows),'calls':facts['calls'],'mismatches':facts['mismatches'],'recovered':len(attacks)}))
if __name__=='__main__':main(sys.argv[1])
