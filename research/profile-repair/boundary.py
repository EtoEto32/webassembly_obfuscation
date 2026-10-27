"""Independent runtime controls for partial normalization and rejected features."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import prototype as p
from fixtures import module, sw

HERE=Path(__file__).resolve().parent


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('boundary.py','prototype.py','fixtures.py','run.cjs'):shutil.copy2(HERE/name,out/'sources'/name)
    try:
        pair=p.read(source/'different_indices_pair-source.wasm')
        cases=[]
        for selected in ([],[0],[1],[0,1]):
            files=[]
            for profile in (None,0,1):
                target=out/('pair-mask'+str(sum(1<<i for i in selected))+'-profile'+str(profile)+'.wasm')
                p.compile_mod(p.rewritten(pair,selected,profile),target);files.append(target.name)
            cases.append({'name':str(selected),'files':files})
        request={'directory':str(out),'inputs':[[255,0],[1,1],[0,0]],'rows':cases}
        (out/'request.json').write_text(json.dumps(request),encoding='utf8')
        run=subprocess.run(['node',str(HERE/'run.cjs'),str(out/'request.json')],capture_output=True,text=True,timeout=30)
        (out/'node.json').write_text(run.stdout,encoding='utf8')
        if run.returncode:raise RuntimeError(run.stderr)
        actual=json.loads(run.stdout)
        for mask,row in zip((0,1,2,3),actual['rows']):
            assert row['results']['pair-mask'+str(mask)+'-profile0.wasm']==[0,0,0]
            assert row['results']['pair-mask'+str(mask)+'-profile1.wasm']==([255,1,0] if mask in (1,2) else [0,0,0])
        primitive=out/'primitive.wasm';p.compile_mod(module([sw(p.g(0),p.g(1))],p.g(2)),primitive)
        primitive_program=p.read(primitive)
        for profile in (0,1):p.compile_mod(p.rewritten(primitive_program,[],profile),out/('primitive-profile'+str(profile)+'.wasm'))
        inputs=[[a,index] for a in range(256) for index in range(256)]
        primitive_request={'directory':str(out),'inputs':inputs,'rows':[{'name':'primitive','files':['primitive-profile0.wasm','primitive-profile1.wasm','primitive.wasm']}]}
        (out/'primitive-request.json').write_text(json.dumps(primitive_request),encoding='utf8')
        run=subprocess.run(['node',str(HERE/'run.cjs'),str(out/'primitive-request.json')],capture_output=True,text=True,timeout=30)
        if run.returncode:raise RuntimeError(run.stderr)
        values=json.loads(run.stdout);(out/'primitive-node.json').write_text(run.stdout,encoding='utf8')
        observed=values['rows'][0]['results']
        strict=[a if i<16 else 0 for a,i in inputs];masked=[a if i<128 else 0 for a,i in inputs]
        assert observed['primitive-profile0.wasm']==strict
        assert observed['primitive-profile1.wasm']==masked
        assert observed['primitive.wasm'] in (strict,masked)
        native_profile=0 if observed['primitive.wasm']==strict else 1
        rejected=[]
        unsupported={
            'memory':'(module (memory 1) (func (export "run") (param i32 i32) (result i32) (local.get 0)))',
            'import':'(module (import "env" "f" (func)) (func (export "run") (param i32 i32) (result i32) (local.get 0)))',
            'loop':'(module (func (export "run") (param i32 i32) (result i32) (loop (result i32) (local.get 0))))',
            'float':'(module (func (export "run") (param i32 i32) (result i32) (i32.reinterpret_f32 (f32.const 0))))',
            'division':'(module (func (export "run") (param i32 i32) (result i32) (i32.div_u (local.get 0) (local.get 1))))',
            'other_lane':'(module (func (export "run") (param i32 i32) (result i32) (i8x16.extract_lane_u 1 (i8x16.relaxed_swizzle (i8x16.splat (local.get 0)) (i8x16.splat (local.get 1))))))',
            'other_vector':'(module (func (export "run") (param i32 i32) (result i32) (i8x16.extract_lane_u 0 (i8x16.relaxed_swizzle (v128.const i32x4 0 1 2 3) (i8x16.splat (local.get 1))))))',
        }
        for name,text in unsupported.items():
            target=out/(name+'.wasm');p.compile_mod(p.w.parse(text),target)
            try:p.read(target)
            except ValueError as e:rejected.append({'name':name,'status':'unsupported_valid_wasm','reason':str(e)})
            else:raise AssertionError('accepted '+name)
        invalid_weights=0
        for weights in ([],[0,1],[-1,1],[True,1],[1]):
            try:p.synthesize(pair,weights)
            except ValueError:invalid_weights+=1
            else:raise AssertionError('invalid weights')
        zero=out/'zero-sites.wasm';p.compile_mod(module([],p.g(0)),zero);assert p.synthesize(p.read(zero))['selected']==[]
        report={'pairChecks':actual['calls'],'pairResults':actual,'primitiveChecks':values['calls'],'nativeProfile':native_profile,'rejections':rejected,'invalidWeightRejections':invalid_weights,'zeroSiteAccepted':True,'limitation':'Local generated functions; explicit profile models are not additional hardware architectures.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        print(json.dumps({k:v for k,v in report.items() if k not in ('pairResults','rejections')}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args();main(args.source.resolve(),args.output.resolve())
