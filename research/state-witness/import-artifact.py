"""Build a source-only local artifact, including the strong generic baseline."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];RESULTS=ROOT/'results/state-witness'


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main(out):
    archive=out.with_suffix('.zip')
    if archive.exists():raise FileExistsError(archive)
    out.mkdir(parents=True,exist_ok=False)
    names=['prototype.py','guard-import.py','guard-import-plan.md','guard-import-proof.md','guard-import-controls.py','guard-import-controls.mjs',
        'guard-import-check.py','guard-import-ablation.py','guard-import-finite.py','guard-import-generic.py','guard-import-generic-plan.md',
        'guard-import-chain.py','guard-import-chain.mjs','guard-import-boundary.py','guard-import-boundary.mjs',
        'guard-import-cached.py','guard-import-cached-plan.md','guard-import-may-plan.md','guard-import-may-pair.py','guard-import-may-pair.mjs','guard-import-may-witness.py','guard-import-may-witness.mjs',
        'guard-import-direct.py','guard-import-direct-plan.md','guard-import-direct-test.py','guard-import-direct-chain.py','guard-import-direct-chain.mjs','guard-import-direct-chain-plan.md','guard-import-direct-lemma.py',
        'guard-environment.py','guard-environment-check.py','guard-protocol.py','guard-contract.py','guard-contract-check.py','guard-table.py','guard-table-check.py','guard-analysis.py']
    for name in names:
        target=out/'research/state-witness'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/name,target)
    for folder in ('logical-reset','connectivity-elimination'):
        target=out/'research'/folder/'prototype.py';target.parent.mkdir(parents=True);shutil.copy2(ROOT/'research'/folder/'prototype.py',target)
    shutil.copy2(HERE/'import-reproduce.py',out/'reproduce.py');shutil.copy2(HERE/'import-artifact-readme.md',out/'README.md')
    expected={'binaries':{},'results':{},'resultFiles':{'may-pair':'manifest.json','may-witness':'manifest.json','direct':'manifest.json','direct-pair':'manifest.json'}}
    for name in ('controls','boundary','chain'):
        for binary in (RESULTS/('guard-import-'+name+'-v1')).glob('*.wasm'):expected['binaries'][name+'/'+binary.name]=digest(binary)
    for name,directory in (('may','guard-import-may-controls-v1'),('may-pair','guard-import-may-pair-v2'),('direct','guard-import-direct-v1'),('direct-pair','guard-import-direct-pair-v1'),('direct-chain','guard-import-direct-chain-v2')):
        for binary in (RESULTS/directory).glob('*.wasm'):expected['binaries'][name+'/'+binary.name]=digest(binary)
    fields={'controls':['contracts','runtimeComparisons','apiCalls','hostCalls','cellWrites','preparationCalls','pureTagCalls'],
        'check':['contracts','unsat','unknown'],'ablation':['summary','contracts','samples'],'finite':['contracts','initialStores','equal','different','maxStates','transitions'],
        'generic':['contracts','statuses'],'boundary':['refusals','normalizations','entryCalls'],'chain':['contracts','apiCalls','hostCalls','preparationCalls','pureTagCalls']}
    for name,keys in fields.items():
        result=json.loads((RESULTS/('guard-import-'+name+'-v1')/'results.json').read_text());expected['results'][name]={key:result[key] for key in keys}
    extra={
        'cached':('guard-import-cached-v1',['contracts','statuses']),
        'may':('guard-import-may-controls-v1',fields['controls']),
        'may-check':('guard-import-may-check-v1',fields['check']),
        'may-finite':('guard-import-may-finite-v1',fields['finite']),
        'may-generic':('guard-import-may-generic-v1',['contracts','statuses']),
        'may-pair':('guard-import-may-pair-v2',['pairsPerEngine','entryCallsPerEngine','preparationCallsPerEngine','lemma']),
        'may-witness':('guard-import-may-witness-v1',['pairsPerEngine','apiCallsPerEngine','preparationCallsPerEngine']),
        'direct':('guard-import-direct-v1',fields['controls']+['isolatedImport']),
        'direct-pair':('guard-import-direct-pair-v1',['pairsPerEngine','apiCallsPerEngine','preparationCallsPerEngine','extractor']),
        'direct-chain':('guard-import-direct-chain-v2',['contracts','negativeWitnesses','maxApiLength','apiCalls','hostCalls','cellWrites','pureTagCalls','preparationCalls']),
        'direct-lemma':('guard-import-direct-lemma-v1',['unsat','unknown','generalBooleanCounterexample'])}
    for name,(directory,keys) in extra.items():
        result=json.loads((RESULTS/directory/expected['resultFiles'].get(name,'results.json')).read_text());expected['results'][name]={key:result[key] for key in keys}
    (out/'expected.json').write_text(json.dumps(expected,indent=2));hashes={p.relative_to(out).as_posix():digest(p) for p in out.rglob('*') if p.is_file()}
    (out/'source-sha256.json').write_text(json.dumps(hashes,indent=2))
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for path in sorted(out.rglob('*')):
            if path.is_file():bundle.write(path,path.relative_to(out).as_posix())
    print(json.dumps({'sourceFiles':len(hashes),'binariesToRegenerate':len(expected['binaries']),'archiveBytes':archive.stat().st_size,'archiveSha256':digest(archive)}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
