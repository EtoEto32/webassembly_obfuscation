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
                ('observability-v1','reproduction-v1/observability'),('boundary-v1','reproduction-v1/boundary'),
                ('external-v3','external-reproduction-v1'),('cut-inputs-v1','cut-inputs-reproduction-v1')]:
        for src in (BASE/a).rglob('*.wasm'):
            dst=BASE/b/src.relative_to(BASE/a)
            assert dst.is_file() and src.read_bytes()==dst.read_bytes(),str(src)
            pairs.append({'file':src.relative_to(ROOT).as_posix(),'rebuilt':dst.relative_to(ROOT).as_posix(),'sha256':digest(src)})
    for a,b in [('probe-v4','reproduction-v1/probe'),('spec-v4','reproduction-v1/spec'),('observability-v1','reproduction-v1/observability'),
                ('external-v3','external-reproduction-v1'),('cut-v1','cut-reproduction-v1')]:
        assert json.loads((BASE/a/'results.json').read_text())==json.loads((BASE/b/'results.json').read_text())
    upstream=0
    for dirname in ('wasm-migrate-build','wasm-migrate-reproduction','weave-build'):
        folder=ROOT/'.tools'/dirname;repairs={}
        for repair in folder.glob('build-repair*.json'):
            r=json.loads(repair.read_text());key=(r['file'],r['before']);assert key not in repairs
            repairs[key]=r['after']
        for name in ('provenance.json','extra-provenance.json'):
            if not (folder/name).is_file():continue
            for r in json.loads((folder/name).read_text())['rows']:
                p=folder/r.get('localPath',r['path']);expected=r['sha256'];seen=set()
                while (r['path'],expected) in repairs:
                    assert expected not in seen,'cyclic build repair chain';seen.add(expected)
                    expected=repairs[(r['path'],expected)]
                assert digest(p)==expected,str(p);upstream+=1
    additional=0
    for dirname,filename in [('wasm3-snapshot-review','provenance.json'),('wasm-r3-bench-review','download.json'),
                             ('whisk-review-v2','provenance.json'),('whisk-review-v2','extra-provenance.json')]:
        folder=ROOT/'.tools'/dirname
        for row in json.loads((folder/filename).read_text())['rows']:
            p=folder/row['path'];assert digest(p)==row['sha256'],str(p);additional+=1
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'audit.py')
    application_inputs=0
    for row in json.loads((BASE/'coverage-v1/results.json').read_text())['rows']:
        p=ROOT/row['source'];assert digest(p)==row['sha256'],str(p);application_inputs+=1
    folder=ROOT/'.tools/state-witness-ffmpeg-0.12.10-v1'
    for package in json.loads((folder/'provenance.json').read_text())['rows']:
        for row in package['files']:
            p=folder/row['file'];assert digest(p)==row['sha256'],str(p);application_inputs+=1
    archives=0
    for directory in ('minimal-bundle-replay-v1','import-bundle-replay-v1','import-bundle-replay-v2','import-bundle-replay-v3'):
        replay=json.loads((BASE/directory/'results.json').read_text());archive=(ROOT/replay['archive']).resolve();archive.relative_to(ROOT)
        assert digest(archive)==replay['archiveSha256'],str(archive);archives+=1
    recent_upstream=0
    for directory in ('state-witness-ffmpeg-glue-v2','state-witness-wizer-review-v1','state-witness-wasmtime-cli-v50.0.0'):
        folder=ROOT/'.tools'/directory;provenance=json.loads((folder/'provenance.json').read_text())
        for row in provenance['files']+provenance.get('source_files',[]):
            path=folder/row['file'];assert digest(path)==row['sha256'],str(path);recent_upstream+=1
    result={'manifests':manifests,'hashes':hashes,'links':links,'byteIdenticalBinaries':len(pairs),'upstreamSourceHashes':upstream,'additionalCorpusSourceHashes':additional,'applicationInputHashes':application_inputs,'artifactArchiveHashes':archives,'recentUpstreamHashes':recent_upstream,'pairs':pairs,
            'sourceHashes':{p.name:digest(p) for p in HERE.iterdir() if p.is_file()},
            'unrelatedFiles':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'paper/main.tex',ROOT/'paper/README.md']}}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:digest(p) for p in out.iterdir()},indent=2))
    print(json.dumps({k:v for k,v in result.items() if isinstance(v,int)}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
