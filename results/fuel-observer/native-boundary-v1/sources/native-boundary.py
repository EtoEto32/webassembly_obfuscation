"""Falsify the empirical native-fuel bridge with short boundary intervals."""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import transform as t

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt


class Stop(Exception): pass


def fixture(count,work,release):
    body=[['local.set','2',['local.get','1']],['if',['local.get','0'],['then',*[
        ['local.set','2',['i32.xor',['local.get','2'],['i32.const',str(j+1)]]] for j in range(work)
    ]],['else']]]
    for j in range(count):
        def call(v): return ['call','0',['i32.const',str(500+j)],['i32.const',str(v)]]
        body.append(['if',['local.get','0'],['then',call(1)],['else',call(0)]] if release and j==0 else call(0))
    body.append(['local.get','2'])
    module=['module',['import','"env"','"mark"',['func',['param','i32','i32']]],
        ['func',['export','"run"'],['param','i32','i32'],['result','i32'],['local','i32'],*body]]
    oracle=[]
    for secret in (0,1):
        value=17
        if secret:
            for j in range(work): value^=j+1
        cost=4+4*work*secret; events=[]
        for j in range(count):
            cost+=3+(2 if release and j==0 else 0)
            events.append({'label':[500+j,secret if release and j==0 else 0],'cost':cost})
        oracle.append({'secret':secret,'x':17,'value':value,'events':events,'total':cost+1})
    return t.w.emit(module),oracle


def expected(contract,item,budget):
    q=node=0; remaining=budget; ledger=[]; value=None; status='ok'
    def adjust(target):
        nonlocal q,remaining
        delta=target-q; ledger.append(['reserve',target,delta])
        if delta>remaining: raise Stop()
        remaining-=delta; q=target
    try:
        adjust(contract['nodes'][0]['bound'])
        for event in item['events']:
            i,v=event['label']; ledger.append(['event',i,v])
            node=contract['nodes'][node]['next'][str(i)+','+str(v)]
            adjust(contract['nodes'][node]['bound'])
        value=item['value']; ledger.append(['return',value]); adjust(contract['nodes'][node]['terminalBound'])
    except Stop: status='budget'
    return {'status':status,'value':value,'credit':q,'remaining':remaining,'ledger':ledger}


def main(out):
    out.mkdir(parents=True,exist_ok=False); (out/'sources').mkdir()
    for name in ('native-boundary.py','native-boundary-plan.md','transform.py'): shutil.copy2(HERE/name,out/'sources'/name)
    cfg=wt.Config(); cfg.consume_fuel=True; engine=wt.Engine(cfg)
    rows=[]; witnesses=[]; ample=[]; checks=0
    try:
        for count in (0,1,2,4,8,16,32):
            for work in (0,1,4,16):
                for release in (False,True):
                    name=f'n{count}-w{work}-r{int(release)}'; folder=out/name; folder.mkdir()
                    wat,oracle=fixture(count,work,release); (folder/'original.wat').write_text(wat,encoding='utf8')
                    t.w.tool('wat2wasm',[folder/'original.wat','-o',folder/'original.wasm'])
                    contract=t.transform(folder/'original.wasm',folder/'target.wasm')
                    (folder/'oracle.json').write_text(json.dumps(oracle,indent=2),encoding='utf8')
                    subprocess.run([str(ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe'),str(folder/'target.wasm'),'-O3','-o',str(folder/'target-O3.wasm')],check=True,capture_output=True)
                    for binary in ('target.wasm','target-O3.wasm'):
                        t.w.tool('wasm-validate',[folder/binary]); module=wt.Module(engine,(folder/binary).read_bytes())
                        store=wt.Store(engine); q=remaining=node=0; ledger=[]; started=False; nativeEvents=[]; inGuest=False; ampleMode=False
                        def adjust(target):
                            nonlocal q,remaining
                            delta=target-q; ledger.append(['reserve',target,delta])
                            if delta>remaining: raise Stop()
                            remaining-=delta; q=target
                            if inGuest:
                                fuel=store.get_fuel()+delta
                                if fuel<0: raise ArithmeticError('negative fuel adjustment')
                                store.set_fuel(fuel)
                        def mark(i,v):
                            nonlocal node,started
                            nativeEvents.append({'label':[i,v],'remaining':store.get_fuel()})
                            if ampleMode: return
                            if i==t.START:
                                assert not started; started=True; return
                            assert started; ledger.append(['event',i,v])
                            node=contract['nodes'][node]['next'][str(i)+','+str(v)]
                            adjust(contract['nodes'][node]['bound'])
                        inst=wt.Instance(store,module,[wt.Func(store,module.imports[0].type,mark)])
                        run=inst.exports(store)['run']
                        try:
                            ampleMode=True
                            for item in oracle:
                                store.set_fuel(1000000); nativeEvents=[]
                                value=run(store,item['secret'],item['x'])&0xffffffff
                                assert value==item['value']
                                assert [e['label'] for e in nativeEvents if e['label'][0]!=t.START]==[e['label'] for e in item['events']]
                                ample.append({'case':name,'file':binary,'secret':item['secret'],'sourceTotal':item['total'],'nativeTotal':1000000-store.get_fuel(),'nativeEvents':nativeEvents})
                            ampleMode=False
                            for offset in (0,4):
                                counts=Counter(); mismatch=0; calls=0
                                for budget in range(contract['whole']+2):
                                    for item in oracle:
                                        q=node=0; remaining=budget; ledger=[]; nativeEvents=[]; started=False; inGuest=False; value=None; status='ok'; code=None
                                        try:
                                            adjust(contract['nodes'][0]['bound']); store.set_fuel(q+offset); inGuest=True
                                            value=run(store,item['secret'],item['x'])&0xffffffff
                                            ledger.append(['return',value]); adjust(contract['nodes'][node]['terminalBound'])
                                        except Stop: status='budget'
                                        except wt.Trap as e: status='native-trap'; code=str(e.trap_code)
                                        except ArithmeticError: status='negative-native-adjustment'
                                        finally: inGuest=False
                                        actual={'status':status,'value':value,'credit':q,'remaining':remaining,'ledger':ledger}
                                        reference=expected(contract,item,budget); calls+=1; checks+=1; counts[status]+=1
                                        if actual!=reference:
                                            mismatch+=1
                                            if mismatch<=2: witnesses.append({'case':name,'file':binary,'offset':offset,'budget':budget,'secret':item['secret'],'actual':actual,'expected':reference,'nativeEvents':nativeEvents,'trapCode':code})
                                rows.append({'case':name,'file':binary,'offset':offset,'calls':calls,'mismatches':mismatch,'statuses':dict(counts),'whole':contract['whole']})
                        finally: store.close()
        report={'wasmtimePython':importlib.metadata.version('wasmtime'),'fixtures':56,'checks':checks,'rows':rows,'witnesses':witnesses,'ample':ample,'meaning':'Falsification of our empirical bridge, not a runtime vulnerability. Offset values fixed before test.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        print(json.dumps({'fixtures':56,'checks':checks,'mismatchConditions':sum(r['mismatches']>0 for r in rows),'mismatches':sum(r['mismatches'] for r in rows),'statuses':dict(sum((Counter(r['statuses']) for r in rows),Counter()))}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('output',type=Path); main(ap.parse_args().output.resolve())
