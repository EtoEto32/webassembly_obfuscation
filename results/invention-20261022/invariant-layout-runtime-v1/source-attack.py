"""Binary-only, family-specific behavioral recovery of memory access helpers."""
import argparse,copy,json,subprocess,time
from pathlib import Path
import prototype as p

def params(f,tag):return [a for t in f[1:] if isinstance(t,list) and t[0]==tag for a in t[1:] if not a.startswith('$')]
def recover(src,dst,work):
    start=time.perf_counter();m=p.q.read(src);pages,data=p.initial(m)
    if not pages:raise ValueError('identification requires nonempty memory')
    funcs=[x for x in m[1:] if x[0]=='func']
    load=[i for i,f in enumerate(funcs) if params(f,'param')==['i64'] and params(f,'result')==['i32']]
    store=[i for i,f in enumerate(funcs) if params(f,'param')==['i64','i32'] and not params(f,'result')]
    if len(load)!=1 or len(store)!=1:raise ValueError('unique helper types unavailable')
    work=Path(work);work.mkdir(parents=True,exist_ok=False)
    probe=copy.deepcopy(m)
    probe.extend([['export','"__load"',['func',str(load[0])]],['export','"__store"',['func',str(store[0])]],['export','"__physical"',['memory','0']]])
    file=work/'probe.wasm';p.q.compile(p.sx.emit(probe),file)
    prepared=time.perf_counter()
    r=subprocess.run(['node',str(Path(__file__).with_name('identify.cjs')),str(file)],capture_output=True,text=True,timeout=30)
    (work/'stdout.txt').write_text(r.stdout,encoding='utf8');(work/'stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    info=json.loads(r.stdout);p.q.save(work/'identification.json',info)
    if info['kind'] is None:raise ValueError('no candidate layout matched helper behavior')
    # No source file, generation seed or manifest is used. Indexes are obtained from this binary.
    bound=f'(if (i64.gt_u (local.get 0) (i64.const {pages*65536-4})) (then (unreachable)))'
    replacements={load[0]:p.sx.parse(f'(module (func (param i64) (result i32) {bound} (i32.load (i32.wrap_i64 (local.get 0)))))')[1],
      store[0]:p.sx.parse(f'(module (func (param i64 i32) {bound} (i32.store (i32.wrap_i64 (local.get 0)) (local.get 1))))')[1]}
    n=copy.deepcopy(m);idx=0
    for k,x in enumerate(n[1:],1):
        if x[0]=='func':
            if idx in replacements:n[k]=replacements[idx]
            idx+=1
    p.setdata(n,p.codec(data,'fixed' if info['kind']=='fixed' else 'transport',True))
    p.q.compile(p.sx.emit(n),dst)
    stats=dict(status='recovered_candidate',layout=info['kind'],helper_indices=dict(load=load[0],store=store[0]),
       identification_calls=sum(x['calls'] for x in info['records']),read_prepare_ms=(prepared-start)*1000,
       identify_rewrite_ms=(time.perf_counter()-prepared)*1000,total_ms=(time.perf_counter()-start)*1000,
       source_or_seed_supplied=False,universal_binary_equivalence_proved=False)
    p.q.save(work/'result.json',stats);return stats

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('work');a=ap.parse_args();print(recover(a.input,a.output,a.work))
