"""Evaluate the tool's separate deobfuscation path on known-correct scalars."""
import json,pathlib,sys
import run as common

out=(common.ROOT/sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
baseline=common.ROOT/sys.argv[2]
rows=[]
for row in json.loads((baseline/'results.json').read_text(encoding='utf-8')):
    if row['group']!='scalar':continue
    d=out/row['name'];d.mkdir();src=common.ROOT/row['source'];binary=d/'deob.wasm';wat=d/'deob.wat'
    command,stdout=common.command([common.DIS,'wasm','deob',src,'--out',wat,'--emit-wasm',binary,'--no-cache','--json'],d/'deob')
    result={'name':row['name'],'command':command,'wasm_generated':binary.exists(),'wat_generated':wat.exists()}
    if binary.exists():
        result.update(bytes=binary.stat().st_size,sha256=common.sha(binary),input_byte_identical=binary.read_bytes()==src.read_bytes())
        validation,_=common.command([common.WABT/'wasm-validate.exe',binary],d/'validate');result['validation']=validation
        if validation['status']=='success':
            check,s=common.command(['node',common.HERE/'check.cjs',binary,baseline/row['name']/'tests.json'],d/'check')
            result['check']=json.loads(s) if check['status']=='success' else check
    rows.append(result);common.save(out/'results.json',rows)
common.save(out/'sha256.json',[{'file':common.rel(p),'sha256':common.sha(p)} for p in [common.HERE/'deob.py']+list(out.rglob('*')) if p.is_file()])
print(json.dumps({'inputs':len(rows),'generated':sum(r['wasm_generated'] for r in rows),'byte_identical':sum(r.get('input_byte_identical',False) for r in rows)}))
