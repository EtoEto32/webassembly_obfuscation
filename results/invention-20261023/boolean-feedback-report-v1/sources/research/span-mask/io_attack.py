# -*- coding: utf-8 -*-
import array
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import prototype as p
import attack


def table_bdd(data,n):
    bdd=attack.BDD(seconds=120);memo={}
    def chunk(value,width):
        if width==0:return value & 1
        key=value,width
        if key not in memo:
            half=1<<(width-1)
            lo=value & ((1<<half)-1);hi=value>>half
            memo[key]=bdd.mk(n-width,chunk(lo,width-1),chunk(hi,width-1))
        return memo[key]
    words=array.array('I');words.frombytes(data)
    if sys.byteorder!='little':words.byteswap()
    current=array.array('I',(chunk(word,5) for word in words))
    for var in range(n-6,-1,-1):
        current=array.array('I',(bdd.mk(var,current[i],current[i+1]) for i in range(0,len(current),2)))
    return bdd,current[0]


def main(main_path,out):
    main_path=Path(main_path);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    (out/'sources').mkdir()
    for name in ('prototype.py','attack.py','io_attack.py','enumerate.cjs'):
        shutil.copyfile(p.HERE/name,out/'sources'/name)
    manifest=json.loads((main_path/'manifest.json').read_text(encoding='utf8'))
    rows=[]
    for t in manifest['targets']:
        if t['form']!='O3' or t['mode'] not in ('plain','span','constant','dependent'):continue
        src=main_path/t['file'];name=t['fixture']+'-'+t['mode']
        # The protected arity is decoded from binary; plain uses its Wasm signature.
        if t['mode']=='plain':n,_,_=p.w.source(src);reader_ms=None
        else:record,reader_ms=attack.read(src);n=record['n']
        dest=out/(name+'.truth.bin')
        r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.HERE/'enumerate.cjs'),str(src),str(n),str(dest)],capture_output=True,text=True,timeout=240)
        (out/(name+'.stdout.txt')).write_text(r.stdout,encoding='utf8')
        (out/(name+'.stderr.txt')).write_text(r.stderr,encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        metrics=json.loads(r.stdout);start=time.perf_counter();b,root=table_bdd(dest.read_bytes(),n)
        compile_start=time.perf_counter();binary=out/(name+'-recovered.wasm');p.save(attack.render_bdd(n,b,root),binary)
        construction_ms=(compile_start-start)*1000;emission_ms=(time.perf_counter()-compile_start)*1000
        # Source is used ONLY after recovery to grade it.
        expected=manifest['fixtures'][t['fixture']]['bdd_digest']
        if b.digest(root)!=expected:raise AssertionError('Exhaustive learned BDD mismatch')
        entry={**t,**metrics,'reader_ms':reader_ms,'construction_ms':construction_ms,'emission_ms':emission_ms,
               'output_nodes':len(attack.reachable(b,root)),'bdd_digest':b.digest(root),'source_bdd_equal':True,
               'table_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'recovered_file':binary.name}
        rows.append(entry)
        (out/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
        print(json.dumps(entry),flush=True)
    (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()},indent=2),encoding='utf8')


if __name__=='__main__':main(*sys.argv[1:])
