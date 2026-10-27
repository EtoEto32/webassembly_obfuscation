"""Verify a freshly unpacked source-only artifact using shared tool binaries."""
import argparse,hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main(archive,out):
    out.mkdir(parents=True,exist_ok=False);root=(out/'root').resolve();root.mkdir()
    with zipfile.ZipFile(archive) as bundle:
        assert sum(v.file_size for v in bundle.infolist())<8*1024*1024
        for info in bundle.infolist():
            target=(root/info.filename).resolve();target.relative_to(root)
            assert not info.is_dir() and not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(bundle.read(info))
    env=os.environ.copy();env['WASM_TOOLS_ROOT']=str(ROOT/'.tools');env['PYTHONPATH']=os.pathsep.join(str(ROOT/'.tools'/name) for name in ('import-alias-quotient-python','encoding-synthesis-python'));env['PYTHONDONTWRITEBYTECODE']='1'
    run=subprocess.run([sys.executable,str(root/'reproduce.py')],cwd=root,env=env,text=True,encoding='utf8',capture_output=True,timeout=240)
    result={'archive':str(archive),'archiveSha256':digest(archive),'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,
        'scope':'Fresh extraction; research sources resolved inside artifact, public tools reused from pinned local environment; no download or publication.'}
    if run.returncode==0:result['reproduction']=json.loads((root/'results/state-witness/reproduction.json').read_text())
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({f.relative_to(out).as_posix():digest(f) for f in out.rglob('*') if f.is_file()},indent=2))
    assert run.returncode==0,run.stderr;print(run.stdout)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('archive',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.archive,v.out)
