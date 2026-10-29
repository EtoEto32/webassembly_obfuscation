"""Bounded replay of the existing Binaryen type fuzzer; not a new fuzzer."""
import argparse,collections,hashlib,json,platform,statistics,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOOL=ROOT/'.tools/binaryen-version_133/bin/wasm-fuzz-types.exe'
def main(out,seeds):
 out.mkdir(parents=True,exist_ok=False);rows=[]
 for seed in range(seeds):
  t=time.perf_counter_ns()
  try:
   p=subprocess.run([str(TOOL),'--seed',str(seed),'--verbose'],capture_output=True,text=True,timeout=10)
   status='passed' if p.returncode==0 else 'failed';stdout=p.stdout;stderr=p.stderr;code=p.returncode
  except subprocess.TimeoutExpired as e:
   status='timeout';stdout=str(e.stdout or '');stderr=str(e.stderr or '');code=None
  duration=(time.perf_counter_ns()-t)/1e6
  (out/('%d.stdout'%seed)).write_text(stdout,encoding='utf8');(out/('%d.stderr'%seed)).write_text(stderr,encoding='utf8')
  rows.append(dict(seed=seed,status=status,exit_code=code,wall_ms=duration))
 (out/'rows.json').write_text(json.dumps(rows,indent=2))
 report=dict(tool=str(TOOL.relative_to(ROOT)),tool_sha256=hashlib.sha256(TOOL.read_bytes()).hexdigest(),version=subprocess.check_output([str(TOOL),'--version'],text=True).strip(),platform=platform.platform(),workloads=seeds,status=dict(collections.Counter(r['status'] for r in rows)),median_process_wall_ms=statistics.median(r['wall_ms'] for r in rows),max_process_wall_ms=max(r['wall_ms'] for r in rows))
 (out/'report.json').write_text(json.dumps(report,indent=2));files=[dict(file=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in out.iterdir() if p.is_file()]
 (out/'manifest.json').write_text(json.dumps(files,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--seeds',type=int,default=64);a=ap.parse_args();main(a.out,a.seeds)
