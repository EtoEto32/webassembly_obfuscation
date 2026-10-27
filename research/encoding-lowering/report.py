import prototype as p
import sys,json,statistics,hashlib
root=p.ROOT;main=root/sys.argv[1];internal=root/sys.argv[2];out=root/sys.argv[3];out.mkdir(parents=True,exist_ok=False)
rows=json.loads((main/'manifest.json').read_text());stats=json.loads((internal/'summary.json').read_text());raw=json.loads((internal/'runtime.json').read_text())
md=['|kernel/seed/mode|中央値の時間比|元process中央値の範囲(ns)|変換後の範囲(ns)|置換命令数|byte差|','|---|---:|---:|---:|---:|---:|'];records=[]
for s in stats:
    r=next(r for r in rows if r['file']==s['file']);a=s['process_medians']['original'];b=s['process_medians']['lowered']
    md.append('|%s|%.4f|%.3f–%.3f|%.3f–%.3f|%d|%+d|'%(s['file'],s['ratio'],min(a),max(a),min(b),max(b),r['lowering']['changed'],r['bytes']-r['source_bytes']))
    assert p.q.digest(r['source'])==p.q.digest(main/r['file'].replace('.wasm','-strict.wasm'))
    records.append(dict(file=r['file'],inverse_byte_identical=True,source_sha256=p.q.digest(r['source']),lowered_sha256=p.q.digest(main/r['file'])))
(out/'comparison.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
(out/'identity.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
files=[pathlib for pathlib in (root/'research/encoding-lowering').glob('*') if pathlib.is_file()]
files += [root/'research/isotope-swizzle/prototype.py',root/'research/isotope-swizzle/bench.cjs',root/'research/connectivity-elimination/prototype.py']
protocol=dict(script_hashes={str(f.relative_to(root)):p.q.digest(f) for f in files},internal_processes=len(raw),internal_warmup=100000,internal_batches=9,internal_batch=200000,internal_order_seed=291021,internal_post_wrapper_optimization=False,js_boundary_processes=108,linear_memory_bytes=0,extra_v128_locals=0,new_algorithm_novelty_established=False)
(out/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
print(json.dumps({'verified_inverse':len(records),'internal_processes':len(raw)}))
