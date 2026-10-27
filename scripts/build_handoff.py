"""Package ignored research outputs, preserving bytes without changing local originals."""
import argparse,collections,concurrent.futures,gzip,hashlib,json,os,subprocess,tarfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKIP_DIRS={'.git','.tools','.tf','.venv','node_modules','__pycache__','target'}
SECRET_FILES={'experiments/runtime-reference/pool-config.local.json','experiments/runtime-reference/fastpool-user.json',
 'data/upstream/wasm_evasion/malware_reproduction/rq3/replace_experiments/coinhive-32bits/cert_key.pem',
 'data/catalog/wasmizer/resolved-commit.json'}
PART_BYTES=40*1024*1024
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def enumerate_files():
 for top in sorted(ROOT.iterdir()):
  if top.name in SKIP_DIRS or top.name=='handoff':continue
  starts=[top]
  if top.name=='data':starts=[top/'catalog',top/'upstream']
  for start in starts:
   if start.is_file():yield start;continue
   if not start.is_dir():continue
   for path,ds,fs in os.walk(start):
    ds[:]=sorted(d for d in ds if d not in SKIP_DIRS)
    for name in sorted(fs):
     p=Path(path)/name;rel=p.relative_to(ROOT).as_posix()
     if rel in SECRET_FILES or p.is_symlink():continue
     yield p
def main(out):
 out.mkdir(parents=True,exist_ok=False);build=out/'.build';build.mkdir();archive=build/'supplemental.tar.gz'
 normal=set(x.decode('utf8') for x in subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=ROOT).split(b'\0') if x)
 files=list(enumerate_files());rows=[];supp=[];count=0;total=0;start=time.monotonic()
 def record(p):
  rel=p.relative_to(ROOT).as_posix();size=p.stat().st_size;route='git' if rel in normal and size<PART_BYTES else 'supplemental'
  return p,dict(path=rel,bytes=size,sha256=sha(p),route=route)
 with (out/'files.jsonl').open('w',encoding='utf8',newline='\n') as listing,concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for p,r in pool.map(record,files):
   rows.append(r);listing.write(json.dumps(r,ensure_ascii=True)+'\n');total+=r['bytes'];route=r['route']
   if route=='supplemental':supp.append((p,r))
   count+=1
   if count%20000==0:print(json.dumps(dict(phase='inventory',files=count,bytes=total)),flush=True)
 with archive.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,compresslevel=6,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
  for i,(p,r) in enumerate(supp):
   info=tarfile.TarInfo(r['path']);info.size=r['bytes'];info.mode=0o644;info.mtime=0
   with p.open('rb') as f:tar.addfile(info,f)
   if (i+1)%10000==0:print(json.dumps(dict(phase='archive',files=i+1,total=len(supp))),flush=True)
 parts=[]
 with archive.open('rb') as f:
  while True:
   b=f.read(PART_BYTES)
   if not b:break
   name='supplemental.tar.gz.part%03d'%(len(parts)+1);p=out/name;p.write_bytes(b);parts.append(dict(file=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
 summary=dict(version=1,date_jst='2026-10-27',files=len(rows),bytes=total,direct_git_files=sum(r['route']=='git' for r in rows),supplemental_files=len(supp),supplemental_uncompressed_bytes=sum(r['bytes'] for p,r in supp),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),parts=parts,excluded={'local_environments':['.tools/','.tf/','.venv/','**/node_modules/','**/target/','**/__pycache__/'],'git_metadata':['**/.git/'],'credentials':sorted(SECRET_FILES),'bulk_data':'data/ except catalog/ and upstream/ metadata/source','package_build':'handoff/.build/'},elapsed_s=round(time.monotonic()-start,3))
 (out/'package.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print(json.dumps(summary,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out.resolve())
