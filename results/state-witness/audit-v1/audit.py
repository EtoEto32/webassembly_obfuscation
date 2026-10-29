"""Check immutable evidence and byte-identical local reproduction."""
import argparse,hashlib,json,re,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE=ROOT/'results/state-witness'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main(out):
    manifests=hashes=links=0
    for file in BASE.rglob('sha256.json'):
        for name,value in json.loads(file.read_text()).items():
            target=(file.parent/name).resolve();target.relative_to(file.parent.resolve())
            assert target.is_file() and digest(target)==value,str(target);hashes+=1
        manifests+=1
    for doc in HERE.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf8')):
            if '://' in link or link.startswith('#'):continue
            assert (doc.parent/link.split('#')[0]).resolve().exists(),(str(doc),link);links+=1
    pairs=[]
    for a,b in [('probe-v4','reproduction-v1/probe'),('spec-v4','reproduction-v1/spec'),
                ('observability-v1','reproduction-v1/observability'),('boundary-v1','reproduction-v1/boundary')]:
        for src in (BASE/a).rglob('*.wasm'):
            dst=BASE/b/src.relative_to(BASE/a)
            assert dst.is_file() and src.read_bytes()==dst.read_bytes(),str(src)
            pairs.append({'file':src.relative_to(ROOT).as_posix(),'rebuilt':dst.relative_to(ROOT).as_posix(),'sha256':digest(src)})
    for a,b in [('probe-v4','reproduction-v1/probe'),('spec-v4','reproduction-v1/spec'),('observability-v1','reproduction-v1/observability')]:
        assert json.loads((BASE/a/'results.json').read_text())==json.loads((BASE/b/'results.json').read_text())
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'audit.py')
    result={'manifests':manifests,'hashes':hashes,'links':links,'byteIdenticalBinaries':len(pairs),'pairs':pairs,
            'sourceHashes':{p.name:digest(p) for p in HERE.iterdir() if p.is_file()},
            'unrelatedFiles':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'paper/main.tex',ROOT/'paper/README.md']}}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:digest(p) for p in out.iterdir()},indent=2))
    print(json.dumps({k:v for k,v in result.items() if isinstance(v,int)}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
