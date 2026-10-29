"""Initial-state, rejection and deliberately incorrect-round controls."""
import argparse
import json
from pathlib import Path
import subprocess
import transform as t
import recover


def run(out):
    folder=out/'edges';folder.mkdir(exist_ok=False);rows=[]
    for kernel in ('arx','blend','carry'):
        src=out/(kernel+'-plain.wasm');rows.append({'kernel':kernel,'variant':'plain','opt':'raw','path':str(src.resolve())})
        for seed in (17,29):
            for initial in (0xffffffff,0x12345678):
                binary=folder/(kernel+'-'+str(seed)+'-'+str(initial)+'.wasm')
                t.transform(src,binary,'masked',seed,initial=initial)
                for opt in ('raw','O3'):
                    p=binary if opt=='raw' else binary.with_name(binary.stem+'-O3.wasm')
                    if opt!='raw':t.w.tool('wasm-opt',[binary,'-O3','-o',p])
                    rows.append({'kernel':kernel,'variant':'initial'+str(initial),'opt':opt,'path':str(p.resolve())})
    manifest=folder/'manifest.json';manifest.write_text(json.dumps({'records':rows,'attacks':[]},indent=2))
    result=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(manifest)],capture_output=True,text=True,timeout=30)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    (folder/'check.log').write_text(result.stdout+result.stderr)
    bad={
        'memory':'(module (memory 1) (func (export "run") (param i32) (result i32) (i32.load (local.get 0))))',
        'variable-shift':'(module (func (export "run") (param i32 i32) (result i32) (i32.shr_u (local.get 0) (local.get 1))))',
        'division':'(module (func (export "run") (param i32 i32) (result i32) (i32.div_u (local.get 0) (local.get 1))))',
        'branch':'(module (func (export "run") (param i32) (result i32) (if (result i32) (local.get 0) (then (i32.const 1)) (else (i32.const 0)))))'
    }
    rejected=[]
    for name,text in bad.items():
        wp=folder/(name+'.wat');wp.write_text(text);bp=wp.with_suffix('.wasm');t.w.tool('wat2wasm',[wp,'-o',bp]);t.w.tool('wasm-validate',[bp])
        try:t.transform(bp,folder/(name+'-unexpected.wasm'))
        except ValueError as e:rejected.append({'case':name,'status':'explicitly_rejected','reason':str(e)})
        else:raise AssertionError(name)
    wrong=folder/'wrong-rounds.wasm';t.transform(out/'arx-plain.wasm',wrong,'masked',17,rounds=1)
    negative=folder/'negative.json';negative.write_text(json.dumps({'records':[
        {'kernel':'arx','variant':'plain','opt':'raw','path':str((out/'arx-plain.wasm').resolve())},
        {'kernel':'arx','variant':'wrong','opt':'raw','path':str(wrong.resolve())}],'attacks':[]}))
    cp=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(negative)],capture_output=True,text=True,timeout=30)
    # Keep the negative result separately, then restore the initial-state report.
    if cp.returncode!=1:raise AssertionError('Wrong-round control was not detected: '+cp.stdout+cp.stderr)
    wrong_result=json.loads((folder/'correctness.json').read_text());(folder/'negative-correctness.json').write_text(json.dumps(wrong_result,indent=2))
    cp=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(manifest)],capture_output=True,text=True,timeout=30)
    if cp.returncode:raise RuntimeError(cp.stdout+cp.stderr)
    try: recover.recover(wrong)
    except RuntimeError as e:
        if str(e) != 'insufficient_round_bound': raise
        bound_control = str(e)
    else: raise AssertionError('Recovery accepted insufficient round count')
    report={'unsupported':rejected,'wrong_round_calls':wrong_result['calls'],'wrong_round_mismatches':wrong_result['mismatches'],
            'recovery_bound_control':bound_control}
    (folder/'controls.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();run(a.output)
