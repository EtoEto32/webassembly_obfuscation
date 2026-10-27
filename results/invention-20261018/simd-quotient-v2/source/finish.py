import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import prototype as p


def main(out,compare=None):
    read=lambda name:json.loads((out/name).read_text())
    m=read('manifest.json');runtime=read('runtime.json');inputs=read('interpreter-inputs.json');checks=[]
    for row in m['records']:
        mod=p.w.parse(p.w.tool('wasm2wat',[row['path'],'--fold-exprs','--no-debug-names']))
        for i,case in enumerate(inputs):
            mod.append(['func',['export','"case'+str(i)+'"'],['result','i32'],['call','0',*([['i32.const',str(v)] for v in case['args']])]])
        target=out/(Path(row['path']).stem+'-interp.wasm');p.emit(target,p.w.emit(mod))
        log=p.w.tool('wasm-interp',[target,'--run-all-exports']);actual=[int(v) for v in re.findall(r'case\d+\(\) => i32:(\d+)',log)]
        expected=[c['expected'][row['kernel']] for c in inputs]
        checks.append({'file':row['path'],'expected':expected,'actual':actual,'log':log,'mismatch':actual!=expected})
    (out/'interpreter.json').write_text(json.dumps(checks,indent=2))
    # Complete one-byte checks of the algebraic simulation relation.
    total=0;errors=0
    for a in range(256):
        total+=1;errors+=(max(1-a,0)>0)!=(a==0)
        for b in range(256):
            d=max(a-b,0);r=max(b-a,0);ne=max(d,r)
            encoded=[d,r,max(1-r,0),max(1-d,0),max(1-ne,0),ne,min(a,b),max(a,b),min(max(a,b),max(1-min(a,b),0))]
            expected=[a>b,a<b,a>=b,a<=b,a==b,a!=b,bool(a) and bool(b),bool(a) or bool(b),bool(a)!=bool(b)]
            total+=len(encoded);errors+=sum((z>0)!=v for z,v in zip(encoded,expected))
    algebra={'comparisons':total,'mismatches':errors,'invalid_and_one_counterexample':{'a':2,'Q_a':True,'Q_a_and_one':False}}
    (out/'algebra.json').write_text(json.dumps(algebra,indent=2));assert errors==0
    # Guards: a bitmask of noncanonical bytes cannot be replaced by Q.
    guards=[]
    bad=out/'numeric-bitmask.wasm';p.emit(bad,'(module (func (export "run") (param i32) (result i32) (i8x16.bitmask (i8x16.splat (local.get 0)))))')
    for action in ('transform','recover'):
        try:p.recover(bad) if action=='recover' else p.transform(bad,out/'bad-unexpected.wasm','fused')
        except ValueError as e:guards.append({'action':action,'status':'rejected','reason':str(e)})
        else:raise AssertionError('Noncanonical output accepted')
    parity=out/'parity.wasm';base=p.node('i8x16.splat',p.node('local.get','0'))
    e=p.node('i8x16.gt_u',p.node('v128.and',base,p.ONE),p.ZERO)
    p.emit(parity,p.module(1,'"run"',p.node('i8x16.bitmask',e)))
    recovered=out/'parity-recovered.wasm';p.recover(parity,recovered)
    cp=subprocess.run(['node','-e',
      'const fs=require("fs");let errors=0;for(const f of process.argv.slice(1)){const run=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports.run;for(let x=0;x<256;x++)errors+=run(x)!==((x&1)?65535:0);}console.log(JSON.stringify({calls:512,mismatches:errors}));if(errors)process.exitCode=1;',str(parity),str(recovered)],capture_output=True,text=True,timeout=30)
    if cp.returncode:raise RuntimeError(cp.stdout+cp.stderr)
    (out/'guards.json').write_text(json.dumps({'guards':guards,'parity':json.loads(cp.stdout)},indent=2))
    c=read('correctness.json');assert (c['conditions'],c['calls'],c['mismatches'])==(54,3649536,0)
    assert len(checks)==27 and not any(x['mismatch'] for x in checks)
    assert len(m['attacks'])==27 and all(x['status']=='ok' and x['same_formula'] for x in m['attacks'])
    assert len(runtime)==81 and set(Counter(r['path'] for r in runtime).values())=={3}
    table=[];lines=['# O3 comparison','','Times include JavaScript calling and argument lookup costs. Analysis excludes WABT/parse and does not share a cache between repetitions.','','|Kernel|Mode|Bytes|Median ns|Process median range ns|Analysis median ms|Analysis range ms|','|---|---|---:|---:|---:|---:|---:|']
    for a in m['attacks']:
        rs=[x for x in runtime if x['path']==a['path']];meds=[statistics.median(x['samples_ns']) for x in rs];ats=a['samples_seconds']
        row={k:a[k] for k in ('kernel','mode','opt','path','bytes')};row.update({'runtime_median_ns':statistics.median(meds),'process_medians_ns':meds,'analysis_ms':a['median_ms']});table.append(row)
        if a['opt']=='O3':lines.append(f"|{a['kernel']}|{a['mode']}|{a['bytes']}|{statistics.median(meds):.2f}|{min(meds):.2f}–{max(meds):.2f}|{a['median_ms']:.4f}|{min(ats)*1000:.4f}–{max(ats)*1000:.4f}|")
    (out/'summary.json').write_text(json.dumps(table,indent=2));(out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    versions={'python':platform.python_version(),'os':platform.platform(),'wabt':p.w.tool('wat2wasm',['--version']).strip(),'binaryen':p.w.tool('wasm-opt',['--version']).strip(),**{k:runtime[0][k] for k in ('node','v8','cpu')}}
    (out/'environment.json').write_text(json.dumps(versions,indent=2))
    comparison=None
    if compare:
        other=json.loads((compare/'manifest.json').read_text());count=0
        for a,b in zip(m['attacks'],other['attacks']):
            for key in ('path','recovered'):
                assert Path(a[key]).read_bytes()==Path(b[key]).read_bytes();count+=1
        comparison={'other':str(compare),'identical_binaries':count,'note':'v2 has additional input guards and per-analysis memoization'}
    snapshot=out/'source';snapshot.mkdir(exist_ok=True)
    for f in Path(__file__).parent.iterdir():
        if f.is_file() and f.suffix in ('.md','.py','.cjs','.ps1'):shutil.copy2(f,snapshot/f.name)
    shutil.copy2(Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py',snapshot/'dependency-wasm-common.py')
    hashes={str(f.relative_to(out)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file() and f.name!='audit.json'}
    audit={'status':'passed','conditions':54,'calls':3649536,'wabt_calls':108,'algebra_comparisons':total,'recovered':27,'unsupported':0,'crash':0,'runtime_processes':81,'comparison':comparison,'hashes':hashes}
    (out/'audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps({k:v for k,v in audit.items() if k!='hashes'}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);a=ap.parse_args();main(a.output,a.compare)
