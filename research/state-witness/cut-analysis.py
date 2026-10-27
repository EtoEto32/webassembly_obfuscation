"""Aggregate checkpoint experiments without treating repeated witnesses as bugs."""
import argparse,hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE=ROOT/'results/state-witness'

def main(out):
    out.mkdir(parents=True,exist_ok=False);experiments=[]
    variants=[('none','cut-inputs-zero-v1','cut-zero-v1','cut-zero-cross-v1'),
              ('entry-one','cut-inputs-entry-v1','cut-entry-v1','cut-entry-cross-v1'),
              ('after-one','cut-inputs-one-v1','cut-one-v1','cut-one-cross-v1'),
              ('after-two','cut-inputs-v1','cut-v1','cut-cross-v1')]
    for name,inputs,node,cross in variants:
        m=json.loads((BASE/inputs/'manifest.json').read_text());r=json.loads((BASE/node/'results.json').read_text())
        w=json.loads((BASE/cross/'results.json').read_text());assert w['matchesNode'] and w['rows']==r['rows']
        conditions=[]
        for backend in ('migrate','weave'):
            rr=[x for x in r['rows'] if x['backend']==backend and x['kind']=='observed']
            reached=[(x,s) for x in rr for s in x['scenarios'] if s['status']=='restored']
            failures=[(x,s) for x,s in reached if not s['entryMatches']]
            transient=[(x,s) for x,s in reached if not s['checkpointSegments']['matches'] and s['comparison']['segments']]
            hidden=[(x,s) for x,s in reached if not s['comparison']['segments'] and s['entryMatches'] and s['comparison']['guestMemory'] and s['comparison']['tableTags']]
            first=[];last=[]
            for x in rr:
                ss=[s for s in x['scenarios'] if s['status']=='restored']
                if ss:first.append(ss[0]);last.append(ss[-1])
            conditions.append({'backend':backend,'conditions':len(rr),'restored':len(reached),
              'entryMismatches':len(failures),'distinctSourceModulesWithEntryMismatch':sorted({x['source'] for x,s in failures}),
              'transientSegmentDifferences':len(transient),'finalSegmentOnlyDifferences':len(hidden),
              'firstReachedPolicy':{'attempts':len(first),'entryMismatches':sum(not s['entryMatches'] for s in first)},
              'lastReachedPolicyPostHoc':{'attempts':len(last),'entryMismatches':sum(not s['entryMatches'] for s in last)}})
        experiments.append({'variant':name,'distinctSeeds':len({x['source'] for x in m['cases']}),'generatedCases':len(m['cases']),
          'validTransformedBinaries':sum(e['status']=='valid' for c in m['cases'] for e in c['entries']),
          'continuousMismatches':sum(x['status']=='continuous-mismatch' for x in r['rows']),
          'singleGenerationSeconds':m.get('generationSeconds'),'conditions':conditions,
          'inputHashes':{x:hashlib.sha256((BASE/x/'sha256.json').read_bytes()).hexdigest() for x in (inputs,node,cross)}})
    result={'experiments':experiments,'note':'Distinct source modules are not independent root causes or confirmed bugs. Last-reached selection is post hoc.'}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/'cut-analysis.py')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    print(json.dumps([{'variant':x['variant'],'conditions':x['conditions']} for x in experiments]))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
