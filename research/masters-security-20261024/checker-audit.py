"""Run a second byte/stack derivation against frozen effect certificates."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import statistics
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
c=load('byte_checker',HERE/'byte-checker.py');b=load('boundary',HERE/'boundary.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('byte-checker.py','checker-audit.py','checker-plan.md'):shutil.copy2(HERE/name,out/'sources'/name)
    records=[];mutations=[];results=ROOT/'results/masters-security-20261024'
    for dataset in ('compiler-v2','effects-audit-v1','library-v1'):
        source=results/dataset;manifest=json.loads((source/'manifest.json').read_text())
        for row in manifest:
            if row.get('status','built')!='built':continue
            file=source/row['file'];data=file.read_bytes();digest=sha(file);assert digest==row['sha256']
            b.p.w.tool('wasm-validate',[file])
            proposal=row['summary'];start=time.perf_counter();verdict=c.check(data,proposal,digest);elapsed=(time.perf_counter()-start)*1000
            records.append({'dataset':dataset,'file':file.name,'sha256':digest,'producerKind':proposal['kind'],
              'check_ms':elapsed,'verdict':verdict})
            if proposal['kind']=='ranges' and verdict['accepted']:
                for k in range(len(proposal['writes'])):
                    bad=copy.deepcopy(proposal);bad['writes'].pop(k);v=c.check(data,bad,digest)
                    mutations.append({'dataset':dataset,'file':file.name,'mutation':'omit-symbolic-write','index':k,'rejected':not v['accepted']})
                    assert not v['accepted']
                for label,change in [('offset',lambda w:w.update(offset=(w['offset']+1)&0xffffffff)),
                    ('length',lambda w:w.update(length=['const',0]))]:
                    if not proposal['writes']:continue
                    bad=copy.deepcopy(proposal);change(bad['writes'][0]);v=c.check(data,bad,digest)
                    # A zero-length replacement might be syntactically unchanged.
                    if bad==proposal:continue
                    mutations.append({'dataset':dataset,'file':file.name,'mutation':label,'rejected':not v['accepted']});assert not v['accepted']
                bad=copy.deepcopy(proposal);bad['writes'].append({'addr':['arbitrary'], 'length':['const',1], 'offset':0})
                assert not c.check(data,bad,digest)['accepted']
                mutations.append({'dataset':dataset,'file':file.name,'mutation':'malformed-expression','rejected':True})
            assert not c.check(data,proposal,'0'*64)['accepted']
    ranged=[r for r in records if r['producerKind']=='ranges'];checked=[r for r in ranged if r['verdict']['accepted']]
    rejected=[r for r in ranged if not r['verdict']['accepted']]
    summary={'validatedBinaries':len(records),'rangeProposals':len(ranged),'rangeAccepted':len(checked),'rangeRejected':len(rejected),
      'fullProposals':sum(r['producerKind']=='full' for r in records),
      'wrongDigestRejected':len(records),'structuralMutationsRejected':len(mutations),
      'medianCheckMs':statistics.median(r['check_ms'] for r in records),
      'checkerLines':len((HERE/'byte-checker.py').read_text().splitlines()),'producerLines':len((HERE/'effects.py').read_text().splitlines()),
      'note':'no formal proof; exact syntactic membership may reject safe overapproximations; mutation rejection does not prove each mutation unsound'}
    (out/'audit.json').write_text(json.dumps({'summary':summary,'records':records,'mutations':mutations},indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    print(json.dumps(summary));print(json.dumps([{'dataset':r['dataset'],'file':r['file'],'reason':r['verdict'].get('reason'),'derived':r['verdict'].get('derived')} for r in rejected]))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
