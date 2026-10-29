"""Same partition code and cases on Node and an official SpiderMonkey shell."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def main(pair,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('cross-engine.py','cross-engine.js','partition.cjs','setup-spidermonkey.py'):shutil.copy2(HERE/name,out/'sources'/name)
    shutil.copy2(pair,out/'pair.wasm');shutil.copy2(ROOT/'.tools/spidermonkey-150.0.1/provenance.json',out/'spidermonkey-provenance.json')
    node='''const fs=require('fs');globalThis.partitionApi=require('./sources/partition.cjs');globalThis.cloneMemory=structuredClone;globalThis.pairBytes=fs.readFileSync('./pair.wasm');globalThis.engineDescription={name:'Node',version:process.version,v8:process.versions.v8};globalThis.timerMode='native Node timers';globalThis.finishTest=r=>console.log('RESULT '+JSON.stringify(r));globalThis.failTest=e=>{console.error(e);process.exitCode=1;};require('./sources/cross-engine.js');'''
    shell='''var module={exports:{}};globalThis.setTimeout=function(){return 0;};globalThis.clearTimeout=function(){};load('./sources/partition.cjs');globalThis.partitionApi=module.exports;globalThis.cloneMemory=m=>deserialize(serialize(m,[],{SharedArrayBuffer:'allow'}),{SharedArrayBuffer:'allow'});globalThis.pairBytes=read('./pair.wasm','binary');globalThis.engineDescription={name:'SpiderMonkey',version:'150.0.1',build:getBuildConfiguration()};globalThis.timerMode='shell adapter disables per-batch timers; 30s subprocess deadline and unresolved-promise failure only';var completed=false;globalThis.finishTest=r=>{completed=true;print('RESULT '+JSON.stringify(r));};globalThis.failTest=e=>{print(String(e));throw e;};load('./sources/cross-engine.js');drainJobQueue();if(!completed)throw new Error('unresolved test; not counted as success');'''
    (out/'node.cjs').write_text(node,encoding='utf8');(out/'shell.js').write_text(shell,encoding='utf8');results={}
    try:
        for engine,cmd in [('node',['node','node.cjs']),('spidermonkey',[str(ROOT/'.tools/spidermonkey-150.0.1/js.exe'),'shell.js'])]:
            p=subprocess.run(cmd,cwd=out,text=True,capture_output=True,timeout=30)
            (out/(engine+'-run.json')).write_text(json.dumps({'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2),encoding='utf8')
            if p.returncode:raise RuntimeError(engine+': '+p.stderr+' '+p.stdout[:600])
            lines=[x[7:] for x in p.stdout.splitlines() if x.startswith('RESULT ')];assert len(lines)==1
            results[engine]=json.loads(lines[0]);(out/(engine+'-results.json')).write_text(json.dumps(results[engine],indent=2),encoding='utf8')
        for key in ('conditions','memoriesChecked','bytesCompared','rows','pairs','grow','negatives','shadowLabels'):assert results['node'][key]==results['spidermonkey'][key],key
        report={'sameResults':True,'conditionsPerEngine':results['node']['conditions'],'memoriesPerEngine':results['node']['memoriesChecked'],'bytesComparedPerEngine':results['node']['bytesCompared'],'pairCasesPerEngine':4,'growPerEngine':1,'negativePerEngine':3,'shadowPerEngine':1,'limitation':'Single-agent success path only; SpiderMonkey shell uses serialize/deserialize and disables per-batch timers. Browser deployment and concurrent workers not tested here.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('pair_wasm',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.pair_wasm.resolve(),a.output.resolve())
