"""Verify and restore the ignored research outputs without overwriting differing files."""
import argparse,gzip,hashlib,json,os,shutil,tarfile,tempfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]

def io_path(p):
 # Use extended Windows paths for deep source trees without changing machine policy.
 if os.name!='nt':return p
 s=str(p.absolute())
 if s.startswith('\\\\?\\'):return p
 return Path('\\\\?\\UNC\\'+s[2:] if s.startswith('\\\\') else '\\\\?\\'+s)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main(package,destination,verify_only):
 package=package.resolve();destination=destination.resolve();meta=json.loads((package/'package.json').read_text(encoding='utf8'));records=[json.loads(x) for x in (package/'files.jsonl').read_text(encoding='utf8').splitlines()];expected={r['path']:r for r in records if r['route']=='supplemental'}
 with tempfile.TemporaryDirectory(prefix='wasm-handoff-') as temp:
  archive=Path(temp)/'archive.tar.gz'
  with archive.open('wb') as out:
   for part in meta['parts']:
    source=package/part['file']
    if source.stat().st_size!=part['bytes'] or sha(source)!=part['sha256']:raise ValueError('part checksum: '+part['file'])
    with source.open('rb') as f:shutil.copyfileobj(f,out)
  if sha(archive)!=meta['archive_sha256']:raise ValueError('archive checksum')
  seen=set();restored=0;matched=0
  with tarfile.open(archive,'r|gz') as tar:
   for member in tar:
    name=member.name;parts=PurePosixPath(name).parts
    if not member.isfile() or '\\' in name or ':' in name or PurePosixPath(name).is_absolute() or '..' in parts or name not in expected or name in seen:raise ValueError('unexpected archive member: '+name)
    target=destination.joinpath(*parts).resolve()
    if os.path.commonpath([str(destination),str(target)])!=str(destination):raise ValueError('outside destination')
    target=io_path(target)
    r=expected[name]
    if member.size!=r['bytes']:raise ValueError('member size: '+name)
    exists=target.exists()
    if exists and (not target.is_file() or sha(target)!=r['sha256']):raise ValueError('refusing different existing file: '+name)
    reader=tar.extractfile(member);h=hashlib.sha256();writer=None
    if not verify_only and not exists:target.parent.mkdir(parents=True,exist_ok=True);writer=target.open('xb')
    try:
     while True:
      chunk=reader.read(1024*1024)
      if not chunk:break
      h.update(chunk)
      if writer:writer.write(chunk)
    finally:
     if writer:writer.close()
    if h.hexdigest()!=r['sha256']:raise ValueError('member checksum: '+name)
    seen.add(name);matched+=exists;restored+=not exists and not verify_only
  if seen!=set(expected):raise ValueError('missing archive members')
 print(json.dumps(dict(verified_members=len(seen),existing_identical=matched,restored=restored,verify_only=verify_only)))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,default=ROOT/'handoff/snapshot-20261027');ap.add_argument('--destination',type=Path,default=ROOT);ap.add_argument('--verify-only',action='store_true');a=ap.parse_args();main(a.package,a.destination,a.verify_only)
