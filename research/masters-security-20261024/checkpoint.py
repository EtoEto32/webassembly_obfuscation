"""Freeze local progress and verify recorded artifacts without overwriting history."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];RESULTS=ROOT/'results/masters-security-20261024'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out,used):
    artifact_hashes={str(p.relative_to(ROOT)):sha(p) for p in HERE.iterdir() if p.is_file()}
    for file in (ROOT/'README.md',ROOT/'research/STATUS.md'):artifact_hashes[str(file.relative_to(ROOT))]=sha(file)
    manifests={};pins=0;failed=[]
    for manifest in sorted(RESULTS.glob('*/sha256.json')):
        for relative,digest in json.loads(manifest.read_text()).items():
            if sha(manifest.parent/relative)!=digest:failed.append(str(manifest.parent/relative))
            pins+=1
        manifests[str(manifest.relative_to(ROOT))]=sha(manifest)
    assert not failed,failed
    links=0;missing=[]
    for md in HERE.glob('*.md'):
        text=md.read_text(encoding='utf8')
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if re.match(r'[A-Za-z]+:',target) or target.startswith('#'):continue
            target=target.split('#')[0]
            if not target:continue
            links+=1
            if not (md.parent/target).exists():missing.append((md.name,target))
    assert not missing,missing
    state={'dateUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'scope':'Three Wasm security invention hypotheses; strong patent novelty remains unestablished',
      'quota_observation':{'usedPercent':used,'remainingPercent':max(0,100-used),'isExactTokenBalance':False,
        'history':[{'usedPercent':51,'remainingPercent':49},{'usedPercent':0,'remainingPercent':100}],
        'note':'usage display changed with a different resetsAt; cause unknown; requested remaining-20-percent threshold not reached'},
      'priority':'A then B then C for the next experiment; not a patentability probability',
      'latest_results':{
        'A_component':{'directory':'component-fence-v3','decisions':2178,'mismatches':0},
        'A_files':{'directory':'fence-file-v3','conditions':288,'mismatches':0,'rejected':64,'controlledFailures':6},
        'A_teardown':{'directory':'fence-teardown-v2','conditions':60,'closedFDs':180},
        'A_shapes':{'directory':'fence-shapes-v2','componentCalls':336,'bindingChecks':14,'mismatches':0},
        'A_negatives':{'directory':'fence-negatives-v1','negativeCases':6,'correctedControls':6},
        'A_performance':{'directory':'fence-performance-v2','independentProcesses':20,'ratioRangeToCorrectManual':[0.960,1.081]},
        'A_revision2':{'directory':'effect-plan-v2','conditions':288,'mismatches':0,'invalidRecipesRejected':6,'externalExecutorCasesRejected':2,
            'mechanism':'same typed concrete read/write plan drives authorization dependency and synchronous execution'},
        'A_revision2_performance':{'directory':'effect-performance-v1','independentProcesses':15,'ratioRangeToCorrectManual':[0.992,1.005]},
        'A_revision2_strong_baseline':{'directory':'effect-performance-v2','independentProcesses':20,'ratioRangeToManualSinglePlan':[0.994,1.018],'securityAdvantageOverCorrectManual':False},
        'A_revision2_compiler':{'directory':'effect-compiler-audit-v1','unitCases':576,'seedConfigurations':12,'distinctRecipes':6,'mismatches':0},
        'A_boundary_supplement':{'directory':'abi-preflight-v4','componentCalls':45,'mismatches':0,'performanceDirectory':'abi-performance-v2','memoSlowerCases':5,'totalCases':6,'adoptedAsInvention':False},
        'B_library':{'directory':'library-v1','conditions':48,'inputs':1680,'savedBeforeBytes':147000,'savedAfterBytes':147000},
        'B_checker':{'directory':'checker-audit-v2','binaries':224,'rangeAccepted':98,'mutationsRejected':501},
        'B_cli':{'directory':'checker-cli-audit-v1','acceptedControl':1,'rejectedMalformedCases':12},
        'C':'initial model equals correct semaphore; general generator unimplemented'},
      'pending':['nontrivial technical novelty beyond close prior art','third-party application-level benefits',
        'general WIT binding coverage and contract completeness','concurrent/external effect admission',
        'complete patent search; unacquired leads remain','independently verified formal soundness'],
      'failed_runs':{'fence-shapes-v1':'Jco mkdir EPERM before component execution; retained separately',
        'abi-preflight-v1':'test import object mismatch; not a security rejection',
        'abi-performance-v1':'completed but non-memo baseline had unnecessary key construction; v2 is the corrected primary comparison'},
      'audit':{'pinnedFilesChecked':pins,'localMarkdownLinksChecked':links},
      'artifact_hashes':artifact_hashes,'result_manifests':manifests}
    with out.open('x',encoding='utf8') as f:json.dump(state,f,indent=2)
    print(json.dumps({'sources':len(artifact_hashes),'manifests':len(manifests),'pins':pins,'links':links}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--used-percent',type=int,required=True)
    a=ap.parse_args();main(a.output.resolve(),a.used_percent)
