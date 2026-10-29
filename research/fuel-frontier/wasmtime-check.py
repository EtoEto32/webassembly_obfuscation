"""Bounded independent-runtime check of F, including a manual schedule baseline."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import shutil
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
DEPS=ROOT/'.tools/import-alias-quotient-python';sys.path.insert(0,str(DEPS))
import wasmtime as wt


class Stop(Exception):pass


def oracle(secret,x):
    mid=0
    for i in range(1,14):
        x=((x^13)*1664525+1013904223)&0xffffffff
        if i==(12 if secret&1 else 1):mid=x>>28
    return {'value':x>>24,'events':[[100,mid]]}


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();shutil.copy2(HERE/'wasmtime-check.py',out/'sources/wasmtime-check.py')
    staging=out/'inputs';staging.mkdir();shutil.copy2(source/'manifest.json',staging/'manifest.json')
    mf=json.loads((source/'manifest.json').read_text());engine=wt.Engine();checks=0;manualChecks=0;rows=[]
    matches=[(i*1013904223)&0xffffffff for i in range(1024) if oracle(0,(i*1013904223)&0xffffffff)==oracle(1,(i*1013904223)&0xffffffff)]
    rng=random.Random(2026102411);chosen=rng.sample(matches,8);values=[0,1,0x7fffffff,0x80000000,0xffffffff]+[rng.getrandbits(32) for _ in range(59)]
    try:
        for rec in mf['records']:
            if rec['status']!='accepted':continue
            s=rec['modes']['frontier']['summary'];prefix=[max(x['prefix'][i] for x in rec['independentCost']) for i in range(len(s['prefix']))]
            assert prefix==s['prefix'];delta=[prefix[0]]+[b-a for a,b in zip(prefix,prefix[1:])]
            for mode in ['original',*rec['modes'],'manual']:
                name=rec['name']+('' if mode in ('original','manual') else '-'+mode)+'.wasm';src=staging/name
                if not src.exists():shutil.copy2(source/name,src)
                module=wt.Module(engine,src.read_bytes());store=wt.Store(engine)
                budget=spent=j=0;events=[]
                def charge(v):
                    nonlocal budget,spent
                    if not 0<=v<=2**53-1:raise AssertionError('invalid charge')
                    if v>budget:raise Stop()
                    budget-=v;spent+=v
                def mark(i,v):
                    nonlocal j
                    events.append([i&0xffffffff,v&0xffffffff,spent,budget])
                    if mode=='manual':j+=1;charge(delta[j])
                imports=[]
                for item in module.imports:
                    callback={'mark':mark,'charge':charge,'pad':lambda total:charge(total-spent)}[item.name]
                    imports.append(wt.Func(store,item.type,callback))
                inst=wt.Instance(store,module,imports);run=inst.exports(store)['run']
                def one(secret,p,b):
                    nonlocal budget,spent,j,events
                    budget=b;spent=j=0;events=[];value=None;status='complete'
                    try:
                        if mode=='manual':charge(delta[0])
                        value=run(store,secret,p)&0xffffffff
                    except Stop:status='budget'
                    return {'status':status,'value':value,'events':events,'spent':spent,'budget':budget}
                try:
                    for p in values:
                        for secret in (0,1):
                            a=one(secret,p,10000);assert a['status']=='complete';assert {'value':a['value'],'events':[e[:2] for e in a['events']]}==oracle(secret,p);checks+=1
                    if mode=='original':continue
                    pairs=failures=0
                    for p in chosen:
                        for b in range(sum(s['segment'])+3):
                            a=one(0,p,b);c=one(1,p,b);pairs+=1;failures+=a!=c
                    if mode in ('frontier','whole','segment','manual'):assert failures==0
                    if mode=='manual':manualChecks+=pairs
                    rows.append({'pipeline':rec['name'],'mode':mode,'pairs':pairs,'different':failures})
                finally:store.close()
        result={'wasmtimePython':importlib.metadata.version('wasmtime'),'seed':2026102411,'matchingPayloadsSampled':chosen,'allMatchingPayloads':len(matches),'valueChecks':checks,'manualBudgetPairs':manualChecks,'rows':rows,
          'limitation':'8 of 60 matching payload pairs sampled; budget values exhaustive only for each tested finite fixture bound. Logical source-opcode accounting, not native engine fuel.'}
        (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
