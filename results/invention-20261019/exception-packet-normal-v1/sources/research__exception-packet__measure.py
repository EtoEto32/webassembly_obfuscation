import argparse,json,random,shutil,statistics,subprocess
from pathlib import Path
import prototype as p
from run import save,snapshot
HERE=Path(__file__).resolve().parent
def main(src,out):
    src=Path(src);out=Path(out);out.mkdir(parents=True,exist_ok=False);snapshot(out)
    manifest=json.loads((src/'manifest.json').read_text());files=[]
    for row in manifest['files']:
        if row['opt']!='O3':continue
        m=p.binaryen_tree(src/row['file']);fn=next(x[2][1] for x in m[1:] if x[0]=='export' and x[1]=='"run"')
        text=p.w.emit(m)[:-1]+f'''(func (export "bench") (param $n i32) (param $s i32) (result i32) (local $i i32) (local $h i32)
          (loop $again
            (local.set $h (i32.xor (i32.rotl (local.get $h) (i32.const 1))
             (call {fn} (i32.add (local.get $s) (local.get $i)) (i32.xor (local.get $s) (i32.mul (local.get $i) (i32.const 1103515245))) (i32.mul (local.get $i) (i32.const 2654435761)))))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br_if $again (i32.lt_u (local.get $i) (local.get $n)))) (local.get $h)))'''
        target=out/row['file'];p.compile(text,target);files.append(dict(row,harness_sha256=p.digest(target)))
    jobs=[(f,rep) for f in files for rep in range(3)];random.Random(20261019).shuffle(jobs);records=[]
    for i,(f,rep) in enumerate(jobs):
        command=['node',str(HERE/'batch.cjs'),str(out/f['file']),f['kernel'],str(f['k'])]
        proc=subprocess.run(command,capture_output=True,text=True,timeout=45)
        if proc.returncode:raise RuntimeError(proc.stderr+proc.stdout)
        rec=json.loads(proc.stdout);records.append(dict(file=f['file'],repeat=rep,**rec))
        save(out/'samples.json',records)
        if i%12==0:print(i+1,len(jobs),flush=True)
    summary=[]
    for f in files:
        rs=[x for x in records if x['file']==f['file']];med=[x['median_ns'] for x in rs]
        summary.append(dict(**f,median_ns=statistics.median(med),process_medians_ns=med,min_ns=min(med),max_ns=max(med),maxRSS_KiB=[x['maxRSS_KiB'] for x in rs]))
    save(out/'summary.json',dict(status='completed',fresh_processes=len(jobs),files=summary))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');v=a.parse_args();main(v.input,v.output)
