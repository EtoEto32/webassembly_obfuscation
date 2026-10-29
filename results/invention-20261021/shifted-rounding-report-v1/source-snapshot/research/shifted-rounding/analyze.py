import json
import shutil
import subprocess
import sys
from pathlib import Path
import prototype as p
import recover

main=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
profiles=recover.prepare_profiles(out/'profiles')
rows=json.loads((main/'manifest.json').read_text());results=[];targets=[]
fixtures=json.loads((main/'fixtures.json').read_text())
for row in rows:
    if row['mode'] not in ('grid0','shifted'):continue
    src=main/row['file'];dst=out/(src.stem+'-recovered.wasm')
    try:r=recover.recover(src,profiles,dst)
    except p.base.Unsupported as e:
        results.append(dict(file=row['file'],status='unsupported',reason=str(e)));continue
    # Original data is used only by this scoring harness after recovery.
    gold=fixtures[row['kernel']]
    def tree(nodes,i):
        t=nodes[i];return t if t[0]=='input' else [t[0],tree(nodes,t[1]),tree(nodes,t[2])]
    same=tree(r['nodes'],r['root'])==tree(gold['nodes'],gold['root'])
    # Normalize input list/tuple differences in the independent JSON oracle.
    same=json.dumps(tree(r['nodes'],r['root']))==json.dumps(tree(gold['nodes'],gold['root']))
    assert same,(row,r)
    results.append(dict(file=row['file'],status='recovered',same_ordered_dag=True,**r))
    targets.append(dict(kernel=row['kernel'],mode='recovered',file=dst.name))
p.q.save(out/'recovery.json',results);p.q.save(out/'manifest.json',targets)
for name in ('fixtures.json','inputs.json','quant-raw.wasm','quant-O3.wasm'):shutil.copy2(main/name,out/name)
proc=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=90)
(out/'check-stdout.txt').write_text(proc.stdout,encoding='utf-8');(out/'check-stderr.txt').write_text(proc.stderr,encoding='utf-8')
proc.check_returncode()
print(json.dumps(dict(recovered=len(targets),unsupported=len(results)-len(targets),checks=json.loads(proc.stdout))))
