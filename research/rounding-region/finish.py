"""Second engine, process-level performance, summaries and explicit controls."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
import prototype as p
import recover as r


def write_new(path,data):
    with path.open('x',encoding='utf-8') as f: json.dump(data,f,indent=2)


def evaluate(t,x):
    if t[0]=='v': return x[t[1]]
    if t[0]=='c': return t[1]
    a,b=evaluate(t[1],x),evaluate(t[2],x)
    return (a+b if t[0]=='add' else a*b)&p.MASK


def interpreter(directory):
    build=json.loads((directory/'build.json').read_text())
    inputs=json.loads((directory/'inputs.json').read_text())
    fixtures=json.loads((directory/'fixtures.json').read_text())
    dest=directory/'interpreter';dest.mkdir(exist_ok=False)
    rows=[]
    for row in build['conditions']:
        src=directory/row['file'];cases=[inputs[row['kernel']][i] for i in (0,143,-1,-2)]
        wat=p.w.tool('wasm2wat',[src]);extra=[]
        for i,x in enumerate(cases):
            arguments=' '.join(f'(i32.const {v if v<2**31 else v-2**32})' for v in x)
            extra.append(f'(func (export "case{i}") (result i32) (call 0 {arguments}))')
        wp=dest/(src.stem+'.wat');wp.write_text(wat.rstrip()[:-1]+'\n'+'\n'.join(extra)+')',encoding='utf-8')
        p.w.tool('wat2wasm',[wp,'-o',wp.with_suffix('.wasm')])
        output=p.w.tool('wasm-interp',[wp.with_suffix('.wasm'),'--run-all-exports'])
        expected=[evaluate(fixtures[row['kernel']]['tree'],x) for x in cases]
        for i,v in enumerate(expected):
            assert f'case{i}() => i32:{v}' in output,(row,expected,output)
        rows.append({'file':row['file'],'expected':expected,'output':output,'status':'passed'})
    write_new(directory/'interpreter.json',{'calls':len(rows)*4,'mismatches':0,'rows':rows})
    print(json.dumps({'interpreter_calls':len(rows)*4,'mismatches':0}),flush=True)


def controls(directory):
    # Keep a correct width but corrupt the exact residue. This must not be
    # accepted merely because the floating skeleton matches the known family.
    mod=p.w.parse(p.w.tool('wasm2wat',[directory/'mul2-fused-raw.wasm','--fold-exprs']))
    changed=0
    def walk(x):
        nonlocal changed
        if not isinstance(x,list):return
        if x[0]=='i32.and':
            x[1]=['i32.add',x[1],['i32.const','1']];changed+=1;return
        for child in x:walk(child)
    walk(mod);assert changed==1
    wp=directory/'wrong-residue.wat';wp.write_text(p.w.emit(mod),encoding='utf-8')
    binary=wp.with_suffix('.wasm');p.w.tool('wat2wasm',[wp,'-o',binary]);p.w.tool('wasm-validate',[binary])
    try:r.recover(binary,directory/'wrong-residue-recovered.wasm')
    except ValueError as exc:reason=str(exc)
    else:raise AssertionError('Wrong residue accepted')
    assert reason=='Wrong exact residue',reason
    # Deliberately outside the transform's source profile.
    unsupported={
      'memory':'(module (memory 1) (func (export "run") (param i32) (result i32) (i32.load (local.get 0))))',
      'float':'(module (func (export "run") (param f64) (result f64) (local.get 0)))',
      'division':'(module (func (export "run") (param i32 i32) (result i32) (i32.div_u (local.get 0) (local.get 1))))',
      'loop':'(module (func (export "run") (param i32) (result i32) (loop (result i32) (local.get 0))))'}
    rows=[]
    for name,wat in unsupported.items():
        wp=directory/('unsupported-'+name+'.wat');wp.write_text(wat,encoding='utf-8')
        binary=wp.with_suffix('.wasm');p.w.tool('wat2wasm',[wp,'-o',binary])
        try:p.source(binary)
        except ValueError as exc:rows.append({'case':name,'status':'rejected','reason':str(exc)})
        else:raise AssertionError('Unsupported input accepted')
    write_new(directory/'controls.json',{'wrong_residue_rejected':True,'reason':reason,'unsupported':rows})
    print(json.dumps({'wrong_residue_rejected':True,'unsupported_rejected':len(rows)}),flush=True)


def timing(directory):
    build=json.loads((directory/'build.json').read_text())
    jobs=[(x,i) for x in build['conditions'] for i in range(3)]
    random.Random(0x524e4745).shuffle(jobs)
    rows=[];dest=directory/'timing';dest.mkdir(exist_ok=False)
    worker=Path(__file__).with_name('check.cjs')
    for row,rep in jobs:
        result=subprocess.run(['node',str(worker),'--timing',str(directory/row['file']),str(row['n'])],capture_output=True,text=True,timeout=30)
        if result.returncode:raise RuntimeError(result.stderr)
        observation=json.loads(result.stdout)
        observation.update(file=row['file'],replicate=rep,median_ns=statistics.median(observation['samples_ns']))
        rows.append(observation);write_new(dest/f'{row["file"]}-{rep}.json',observation)
    write_new(directory/'timing.json',{'fresh_processes':len(rows),'rows':rows,
       'scope':'Three fresh processes per binary; 5000 warmup calls then seven batches of 10000. Host call and arguments included. No CPU isolation or JIT-tier tracing.'})
    print(json.dumps({'fresh_processes':len(rows)}),flush=True)


def summarize(directory):
    build=json.loads((directory/'build.json').read_text())
    correctness=json.loads((directory/'correctness.json').read_text())
    times=json.loads((directory/'timing.json').read_text())['rows']
    recovery={x['file']:x for x in build['recovery']}
    rows=[]
    for row in build['conditions']:
        group=[x for x in times if x['file']==row['file']]
        medians=[x['median_ns'] for x in group]
        rows.append({**row,'median_ns':statistics.median(medians),'process_medians_ns':medians,
                     'process_range_ns':[min(medians),max(medians)],'max_rss_kib':[x['max_rss_kib'] for x in group],
                     'analysis_ms':1000*recovery[row['file']]['median_seconds']})
    summary={'conditions':len(rows),'correctness_calls':correctness['calls'],'correctness_mismatches':correctness['mismatches'],
             'recovered':sum(x['status']=='recovered' for x in build['recovery']),
             'bad_width_mismatches':correctness['bad_width_mismatches'],'transforms':build['transforms'],'rows':rows}
    write_new(directory/'summary.json',summary)
    lines=['# 丸め補正の領域変換：O3実測','','実行は3 fresh processの各中央値の中央値。解析は5回のモデル解析中央値。異なる処理系の時間を直接割って保護強度としない。','',
           '|式|方式|補正領域数|実行 ns|bytes|解析 ms|','|---|---|---:|---:|---:|---:|']
    for row in rows:
        if row['opt']!='O3':continue
        trans=next((x for x in build['transforms'] if x['kernel']==row['kernel'] and x['mode']==row['mode']),None)
        regions=trans['regions'] if trans else 0
        lines.append(f'|{row["kernel"]}|{row["mode"]}|{regions}|{row["median_ns"]:.1f}|{row["bytes"]}|{row["analysis_ms"]:.4f}|')
    (directory/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('transforms','rows')}),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['interpreter','controls','timing','summarize']);ap.add_argument('directory',type=Path)
    a=ap.parse_args();globals()[a.action](a.directory)
