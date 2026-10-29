"""Check frozen experiment integrity and concrete boundary-contract negatives."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import effects

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('boundary',HERE/'boundary.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('contract-audit.py','contract-audit.cjs','effects.py','certify.py'):
        shutil.copy2(HERE/name,out/'sources'/name)
    results=ROOT/'results/masters-security-20261024';pins={}
    for name in ('probe-v2','audit-v1','boundary-v1','boundary-audit-v1','compiler-v1','compiler-v2','effects-audit-v1','consumer-v1','consumer-v2','query-v1','fence-v1','fence-v2','fence-v3','component-fence-v1','component-fence-v2','component-fence-v3','fence-performance-v1','fence-performance-v2','library-v1','checker-audit-v1','checker-audit-v2','checker-cli-audit-v1','literature-v1','literature-v2','fence-file-v1','fence-file-v2','fence-file-v3','fence-teardown-v1','fence-teardown-v2','fence-shapes-v1','fence-shapes-v2','fence-negatives-v1','effect-plan-v1','effect-plan-v2','effect-performance-v1'):
        directory=results/name;hashes=json.loads((directory/'sha256.json').read_text())
        for relative,expected in hashes.items():assert sha(directory/relative)==expected,(name,relative)
        pins[name]=len(hashes)
    recomputed=0
    for name in ('compiler-v2','effects-audit-v1','library-v1'):
        for e in json.loads((results/name/'manifest.json').read_text()):
            binary=results/name/e['file'];b.p.w.tool('wasm-validate',[binary])
            actual=effects.summary(b.p.w.parse(b.p.w.tool('wasm2wat',[binary,'--fold-exprs'])))
            assert actual==e['summary'];recomputed+=1
    # A matching binary hash cannot authenticate an arbitrary write summary.
    binary=results/'compiler-v1/metadata-rust2.wasm'
    actual=effects.summary(b.p.w.parse(b.p.w.tool('wasm2wat',[binary,'--fold-exprs'])))
    forged={'kind':'ranges','writes':[],**{k:v for k,v in actual.items() if k not in ('kind','writes')}}
    assert actual!=forged and actual['writes']
    (out/'forged-summary.json').write_text(json.dumps({'wasm_sha256':sha(binary),'forged':forged,'derived':actual,'matchingHashIsNotProof':True},indent=2),encoding='utf8')
    r=subprocess.run(['node',str(HERE/'contract-audit.cjs'),str(results/'boundary-v1'),str(out/'negatives.json')],capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stderr
    for p in HERE.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
    for p in HERE.glob('*.cjs'):
        r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);assert r.returncode==0,r.stderr
    paper={'paper/main.tex':'db94c578a9d573b700756daeebaabfbcbfc3fa0c896ac1a47d491bc09cc12225',
           'paper/README.md':'10e8eee3c2f27f66a7f2df2d4807f4aca97bde8a49eb8f2a3be186e6d550f2d0'}
    for file,expected in paper.items():assert sha(ROOT/file)==expected
    (out/'audit.json').write_text(json.dumps({'verifiedFiles':pins,'recomputedSummaries':recomputed,'validatedBinaries':recomputed,
       'matchingHashDoesNotValidateForgedSummary':True,'paperFilesUnchangedSinceTaskStart':paper},indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'pins':sum(pins.values()),'recomputedSummaries':recomputed,'contractCounterexamples':3,'forgedSummaryDetectedByReanalysis':True}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path)
    main(ap.parse_args().output.resolve())
