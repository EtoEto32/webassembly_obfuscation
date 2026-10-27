"""Create a local source-only reproducibility bundle; never publishes it."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main(out):
    archive=out.with_suffix('.zip')
    if archive.exists():raise FileExistsError(archive)
    out.mkdir(parents=True,exist_ok=False)
    names=['diagnose.py','prototype.py','guard-environment.py','guard-environment-controls.py','guard-environment-controls.mjs',
        'guard-environment-interleave.py','guard-environment-interleave.mjs','guard-environment-check.py','guard-environment-plan.md',
        'guard-protocol.py','guard-contract.py','guard-contract-check.py','guard-table.py','guard-table-check.py','guard-analysis.py','guard-terminal-fast.py']
    for name in names:
        target=out/'research/state-witness'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/name,target)
    for folder in ('logical-reset','connectivity-elimination'):
        target=out/'research'/folder/'prototype.py';target.parent.mkdir(parents=True);shutil.copy2(ROOT/'research'/folder/'prototype.py',target)
    shutil.copy2(HERE/'minimal-reproduce.py',out/'reproduce.py');shutil.copy2(HERE/'minimal-artifact-readme.md',out/'README.md')
    # Include the plan as evidence but remove its unavailable larger-repo links from the package navigation.
    reference=ROOT/'results/state-witness';expected={'binaries':{}}
    for old,new in [('guard-environment-controls-v1','controls'),('guard-environment-interleave-v1','interleave')]:
        for binary in sorted((reference/old).glob('*.wasm')):expected['binaries'][new+'/'+binary.name]=digest(binary)
    expected['controls']={'apiCalls':274,'preparationApiCalls':272,'cellWrites':48,'pureReferenceTagCalls':52}
    expected['interleave']={'apiCalls':12,'preparationApiCalls':8,'cellWrites':4}
    (out/'expected.json').write_text(json.dumps(expected,indent=2))
    hashes={path.relative_to(out).as_posix():digest(path) for path in sorted(out.rglob('*')) if path.is_file()}
    (out/'source-sha256.json').write_text(json.dumps(hashes,indent=2))
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for path in sorted(out.rglob('*')):
            if path.is_file():bundle.write(path,path.relative_to(out).as_posix())
    print(json.dumps({'sourceFiles':len(hashes),'sourceBytes':sum(path.stat().st_size for path in out.rglob('*') if path.is_file()),'archive':str(archive),'archiveBytes':archive.stat().st_size,'archiveSha256':digest(archive)}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
