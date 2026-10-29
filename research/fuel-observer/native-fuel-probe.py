"""Measure native fuel; deliberately do not assume the source cost model matches it."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();shutil.copy2(HERE/'native-fuel-probe.py',out/'sources/native-fuel-probe.py')
    staging=out/'inputs';staging.mkdir();rows=[];checks=0
    try:
        cfg=wt.Config();cfg.consume_fuel=True;engine=wt.Engine(cfg);manifest=json.loads((source/'manifest.json').read_text());shutil.copy2(source/'manifest.json',staging/'manifest.json')
        for rec in manifest['records']:
            folder=staging/rec['kind'];folder.mkdir();oracle=json.loads((source/rec['kind']/'oracle.json').read_text());chosen=[x for x in oracle if x['x']==0]
            for name in ('oracle.json','target.json'):shutil.copy2(source/rec['kind']/name,folder/name)
            for name in ('original.wasm','target.wasm','target-O3.wasm'):
                shutil.copy2(source/rec['kind']/name,folder/name);module=wt.Module(engine,(folder/name).read_bytes());store=wt.Store(engine);observed=[];initial=1000000
                def mark(i,v):observed.append({'label':[i,v],'nativePrefix':initial-store.get_fuel()})
                instance=wt.Instance(store,module,[wt.Func(store,module.imports[0].type,mark)]);run=instance.exports(store)['run']
                try:
                    for item in chosen:
                        observed=[];initial=1000000;store.set_fuel(initial);value=run(store,item['secret'],item['x'])&0xffffffff;assert value==item['value'];checks+=1
                        traces=[x for x in observed if x['label'][0]!=-2147483648];assert [x['label'] for x in traces]==[x['label'] for x in item['events']]
                        nativeTotal=initial-store.get_fuel();full=observed
                        observed=[];initial=item['total'];store.set_fuel(initial);status='ok';trapCode=None
                        try:run(store,item['secret'],item['x'])
                        except wt.Trap as e:status='trap';trapCode=str(e.trap_code)
                        rows.append({'kind':rec['kind'],'file':name,'secret':item['secret'],'logicalTotal':item['total'],'nativeTotal':nativeTotal,'fullEvents':full,'logicalPrefix':[x['cost'] for x in item['events']],'sourceAmountOnly':{'status':status,'trapCode':trapCode,'events':observed}})
                finally:store.close()
        report={'wasmtimePython':importlib.metadata.version('wasmtime'),'checks':checks,'rows':rows,'limitation':'Measurement only; no general upper-bound theorem connecting native fuel to the logical source-opcode model. Default engine settings except consume_fuel=true.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'checks':checks,'sourceAmountTraps':sum(x['sourceAmountOnly']['status']=='trap' for x in rows),'nativeExceedsLogical':sum(x['nativeTotal']>x['logicalTotal'] for x in rows)}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
