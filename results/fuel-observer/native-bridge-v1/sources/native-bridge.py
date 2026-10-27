"""Experimental bridge, with an explicit empirical native-fuel offset."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt


class Stop(Exception):pass


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('native-bridge.py','native-bridge-plan.md'):shutil.copy2(HERE/name,out/'sources'/name)
    staging=out/'inputs';staging.mkdir();rows=[];witnesses=[];checks=0
    try:
        cfg=wt.Config();cfg.consume_fuel=True;engine=wt.Engine(cfg);mf=json.loads((source/'manifest.json').read_text());shutil.copy2(source/'manifest.json',staging/'manifest.json')
        for rec in mf['records']:
            folder=staging/rec['kind'];folder.mkdir()
            for name in ('target.wasm','target.json','oracle.json'):shutil.copy2(source/rec['kind']/name,folder/name)
            contract=json.loads((folder/'target.json').read_text());cases=[x for x in json.loads((folder/'oracle.json').read_text()) if x['x']==0];module=wt.Module(engine,(folder/'target.wasm').read_bytes())
            def reference(item,budget):
                node=0;q=0;remaining=budget;ledger=[];value=None;status='ok';events=0
                def adjust(target):
                    nonlocal q,remaining
                    delta=target-q;ledger.append(['reserve',target,delta])
                    if delta>remaining:raise Stop()
                    remaining-=delta;q=target
                try:
                    adjust(contract['nodes'][0]['bound'])
                    for e in item['events']:
                        i,v=e['label'];ledger.append(['event',i,v]);events+=1;node=contract['nodes'][node]['next'][str(i)+','+str(v)];adjust(contract['nodes'][node]['bound'])
                    value=item['value'];ledger.append(['return',value]);adjust(contract['nodes'][node]['terminalBound'])
                except Stop:status='budget'
                return {'status':status,'value':value,'credit':q,'remaining':remaining,'events':events,'ledger':ledger}
            for offset in (0,4):
                store=wt.Store(engine);node=q=remaining=events=0;ledger=[];started=False;inGuest=False;minimum=10**9
                def adjust(target):
                    nonlocal q,remaining,minimum
                    delta=target-q;ledger.append(['reserve',target,delta])
                    if delta>remaining:raise Stop()
                    remaining-=delta;q=target
                    if inGuest:
                        fuel=store.get_fuel()+delta
                        if fuel<0:raise ArithmeticError('negative native adjustment')
                        minimum=min(minimum,fuel);store.set_fuel(fuel)
                def mark(i,v):
                    nonlocal node,events,started
                    if i==-2147483648:
                        assert not started;started=True;return
                    assert started;ledger.append(['event',i,v]);events+=1;node=contract['nodes'][node]['next'][str(i)+','+str(v)];adjust(contract['nodes'][node]['bound'])
                inst=wt.Instance(store,module,[wt.Func(store,module.imports[0].type,mark)]);run=inst.exports(store)['run'];traps=mismatches=negative=ok=0
                try:
                    for budget in range(contract['whole']+2):
                        for item in cases:
                            node=q=events=0;remaining=budget;ledger=[];started=False;inGuest=False;value=None;status='ok';code=None
                            try:
                                adjust(contract['nodes'][0]['bound']);store.set_fuel(q+offset);inGuest=True
                                value=run(store,item['secret'],item['x'])&0xffffffff;ledger.append(['return',value]);adjust(contract['nodes'][node]['terminalBound'])
                            except Stop:status='budget'
                            except wt.Trap as e:status='native-trap';code=str(e.trap_code);traps+=1
                            except ArithmeticError:status='negative-native-adjustment';negative+=1
                            finally:inGuest=False
                            actual={'status':status,'value':value,'credit':q,'remaining':remaining,'events':events,'ledger':ledger};expected=reference(item,budget);checks+=1
                            if actual!=expected:
                                mismatches+=1
                                if sum(w['kind']==rec['kind'] and w['offset']==offset for w in witnesses)<3:witnesses.append({'kind':rec['kind'],'offset':offset,'secret':item['secret'],'budget':budget,'actual':actual,'expected':expected,'trapCode':code})
                            if status=='ok':ok+=1
                    rows.append({'kind':rec['kind'],'offset':offset,'calls':(contract['whole']+2)*len(cases),'nativeTraps':traps,'negativeAdjustments':negative,'mismatches':mismatches,'complete':ok,'minAdjustedFuel':minimum if minimum<10**9 else None})
                finally:store.close()
        report={'wasmtimePython':importlib.metadata.version('wasmtime'),'checks':checks,'rows':rows,'witnesses':witnesses,'limitation':'Offset 4 is an empirical value for the tested raw subset. Fixed compiler-source proof not completed; optimized binaries and arbitrary Wasm not covered.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'checks':checks,'rows':rows}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
