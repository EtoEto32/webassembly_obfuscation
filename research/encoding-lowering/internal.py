import prototype as p
import json,sys,subprocess,random,statistics
src=p.ROOT/sys.argv[1];out=p.ROOT/sys.argv[2];out.mkdir(parents=True,exist_ok=False)
rows=json.loads((src/'manifest.json').read_text());jobs=[]
wrapper=p.q.w.parse('''(module (func (export "bench") (param i32 i32 i32 i32) (result i32)
 (block (loop (br_if 1 (i32.eqz (local.get 0)))
  (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
  (local.set 3 (call 0 (local.get 1) (i32.xor (local.get 1) (local.get 2)) (local.get 3)))
  (local.set 2 (i32.add (local.get 2) (local.get 3)))
  (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0))) (local.get 3)))''')[1]
for row in rows:
    for kind in ('original','lowered'):
        f=row['source'] if kind=='original' else src/row['file'];m=p.q.read(f);m.append(wrapper)
        target=out/(kind+'-'+row['file']);p.q.compile(p.q.w.emit(m),target)
        jobs.extend((row['file'],kind,target,rep) for rep in range(5))
random.Random(291021).shuffle(jobs);raw=[]
for name,kind,target,rep in jobs:
    r=json.loads(subprocess.check_output(['node',str(p.ROOT/'research/encoding-lowering/internal.cjs'),str(target)],text=True,timeout=30));raw.append(dict(r,file=name,kind=kind,replicate=rep))
    (out/'runtime.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
summary=[]
for row in rows:
    group=[x for x in raw if x['file']==row['file']];assert len({x['checksum'] for x in group})==1
    med={k:[statistics.median(x['ns']) for x in group if x['kind']==k] for k in ('original','lowered')}
    summary.append(dict(file=row['file'],process_medians=med,ratio=statistics.median(med['lowered'])/statistics.median(med['original'])))
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({'processes':len(raw),'ratios':[(x['file'],x['ratio']) for x in summary]}))
