"""Expose vector helpers for a known-API chosen-write decoder recovery task."""
import argparse, json, subprocess, time
from pathlib import Path
from run import p,q,HERE

def expose(src,dst):
    m=q.read(src);fs=[f for f in m[1:] if f[0]=='func'];ids=[]
    for i,f in enumerate(fs):
        ps=[x[1:] for x in f[1:] if isinstance(x,list) and x[0]=='param']
        rs=[x[1:] for x in f[1:] if isinstance(x,list) and x[0]=='result']
        if ps!=[['v128']] or rs!=[['v128']]:continue
        v=p.ZERO
        for k in range(4):v=f'(i32x4.replace_lane {k} {v} (local.get {k}))'
        text=f'''(module (func (export "__candidate{i}") (param i32 i32 i32 i32) (result i32 i32 i32 i32)
          (local v128) (local.set 4 (call {i} {v}))
          {' '.join(f'(i32x4.extract_lane {j} (local.get 4))' for j in range(4))}))'''
        m.extend(q.w.parse(text)[1:]);ids.append(i)
    if not ids:raise q.Unsupported('no v128 -> v128 helper; not protection success')
    m.append(['export','"__physical"',['memory','0']]);q.compile(q.w.emit(m),dst)
    return ids

def main(src,dst):
    dst=Path(dst);dst.mkdir(parents=True,exist_ok=False);t=time.perf_counter();ids=expose(src,dst/'exposed.wasm');ready=time.perf_counter()
    r=subprocess.run(['node',str(HERE/'recover.cjs'),str(dst.resolve())],capture_output=True,text=True,timeout=60)
    (dst/'stdout.txt').write_text(r.stdout,encoding='utf-8');(dst/'stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr)
    q.save(dst/'pipeline.json',dict(input=str(src),input_sha256=q.digest(src),candidate_ids=ids,reader_compile_ms=(ready-t)*1000,total_ms=(time.perf_counter()-t)*1000))
    print(r.stdout)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');a=ap.parse_args();main(a.input,a.output)
