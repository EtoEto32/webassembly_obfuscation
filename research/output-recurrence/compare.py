"""Equal extraction/validation budget for source, history and quotient."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time
import tracemalloc
import prototype as p
from run import save
def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);manifest=json.loads((a.input/'manifest.json').read_text());records=[]
    for f in manifest['files']:
        if 'kind' in f:continue
        samples=[];core=[]
        for _ in range(5):
            begin=time.perf_counter();d,stats=p.extract(a.input/f['path'],a.output,f['mode']);samples.append((time.perf_counter()-begin)*1000)
        for _ in range(31):
            begin=time.perf_counter();q=p.quotient(d) if f['mode']=='source' else d;code=p.wat(q,'quotient');core.append((time.perf_counter()-begin)*1000)
        tracemalloc.start();p.wat(p.quotient(d) if f['mode']=='source' else d,'quotient');_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        target=a.output/(Path(f['path']).stem+'.canonical.wasm');p.compile_wat(code,target);reference=a.input/(f['model']+'.quotient.raw.wasm');same=target.read_bytes()==reference.read_bytes();assert same
        records.append(dict(f,extract_validate_samples_ms=samples,extract_validate_median_ms=statistics.median(samples),canonical_emit_samples_ms=core,canonical_emit_median_ms=statistics.median(core),python_heap_peak_bytes=peak,same_as_quotient=same))
    save(a.output/'comparison.json',records);save(a.output/'scripts.json',{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (Path(__file__),Path(p.__file__))});print(json.dumps(dict(conditions=len(records),canonical_matches=sum(r['same_as_quotient'] for r in records))))
if __name__=='__main__':main()
