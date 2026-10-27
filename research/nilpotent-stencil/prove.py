"""SMT checks on extracted scalar models, not end-to-end SIMD verification."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time
import prototype as p
from run import save

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'.tools/encoding-synthesis-python'))
import z3
spec=importlib.util.spec_from_file_location('scalar_solver_common',HERE.parent/'lane-demand/prove.py')
common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);m=json.loads((a.input/'manifest.json').read_text());x,y=z3.BitVecs('x y',32);records=[]
    for row in m['files']:
        if 'kind' not in row:continue
        expected=common.zexpr(p.expanded(a.input/(row['model']+'.source.raw.wasm')),x,y);actual=common.zexpr(p.expanded(a.input/row['path']),x,y);s=z3.Solver();s.set(timeout=5000);s.add(expected!=actual);(a.output/(row['path']+'.smt2')).write_text(s.to_smt2(),encoding='utf-8');start=time.perf_counter();status=s.check();r=dict(path=row['path'],result=str(status),solver_ms=(time.perf_counter()-start)*1000)
        if status==z3.sat:r['model']=str(s.model())
        elif status==z3.unknown:r['reason']=s.reason_unknown()
        records.append(r)
    save(a.output/'proof.json',dict(z3=z3.get_version_string(),scope='Extracted scalar expressions over all 32-bit input pairs; no full SIMD/compiler proof.',records=records,unsat=sum(r['result']=='unsat' for r in records),sat=sum(r['result']=='sat' for r in records),unknown=sum(r['result']=='unknown' for r in records)))
    print(json.dumps({s:sum(r['result']==s for r in records) for s in ('unsat','sat','unknown')}))


if __name__=='__main__':main()
