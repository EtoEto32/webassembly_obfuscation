import json,subprocess,sys,time
from pathlib import Path
import prototype as p
q=p.q;src,learned,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);results=[]
for row in json.loads((src/'manifest.json').read_text()):
    if row['mode']!='native':continue
    t=time.perf_counter();target=src/row['file'];ops=p.copy_ops(q.read(target));obs=out/(target.stem+'-observed.wasm');p.probe(target,obs)
    answer=json.loads(subprocess.check_output(['node',str(Path(__file__).with_name('direct.cjs')),str(obs)],text=True,timeout=60))
    if not answer['zeroPhysicalOutsideWindow']:raise ValueError('outside-window data unsupported')
    dst=out/(target.stem+'-recovered.wasm');q.compile(p.wat(bytes(answer['plain']),ops),dst)
    same=q.digest(dst)==q.digest(learned/dst.name);assert same
    results.append(dict(file=target.name,recovered_file=dst.name,sha256=q.digest(dst),same_as_validated_recovery=same,total_elapsed_ms=1000*(time.perf_counter()-t),**answer))
q.save(out/'direct.json',results);print(json.dumps(dict(targets=len(results),reads=sum(x['logicalReadCalls'] for x in results),writes=0,byte_identical_to_validated_clones=len(results))))
