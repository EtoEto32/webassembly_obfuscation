import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import prototype as p


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('mutation_io',p.HERE/'io-recover.py');attack=importlib.util.module_from_spec(spec);spec.loader.exec_module(attack)
    cases=json.loads((base/'cases.json').read_text());targets=json.loads((base/'manifest.json').read_text());rows=[];generated=[]
    for t in targets:
        if t['mode'] not in ('plain','canonical','representative'):continue
        c=next(x for x in cases if x['name']==t['name']);dest=out/(Path(t['file']).stem+'-io-recovered.wasm')
        r=attack.recover(base/t['file'],dest,c['n'],c['k'])
        # Source state is used only by the scorer after the attack returns.
        wanted=p.representative(c['initial'],c['erased_bits'])
        if r['initial_representative']!=wanted:raise AssertionError('IO representative differs')
        ref=base/(t['name']+'-canonical-raw-recovered.wasm')
        if t['mode']!='plain' and dest.read_bytes()!=ref.read_bytes():raise AssertionError('binary and IO recoveries differ')
        rows.append({**t,**r});generated.append({**t,'mode':'io-recovered','file':dest.name})
    p.q.save(out/'cases.json',cases);p.q.save(out/'manifest.json',generated);p.q.save(out/'attacks.json',rows)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout);(out/'checks.stderr.txt').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    c=json.loads(r.stdout);p.q.save(out/'checks.json',c);print(json.dumps(dict(attacks=len(rows),queries=sum(x['queries'] for x in rows),calls=c['calls'],mismatches=c['mismatches'])),flush=True)


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
