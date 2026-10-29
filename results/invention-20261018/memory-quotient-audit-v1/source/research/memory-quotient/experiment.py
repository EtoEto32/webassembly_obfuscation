"""Build, project, attack, validate and measure the predeclared memory quotient gate."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import time
import transform as T
from attack import recover

HERE=Path(__file__).resolve().parent
OPT=T.TOOLS/'binaryen-version_133/bin/wasm-opt.exe'


def js(name,*args):
    return subprocess.check_output([shutil.which('node'),str(HERE/name),*map(str,args)],text=True,timeout=60)


def run(out):
    out.mkdir(parents=True,exist_ok=False);(out/'source').mkdir()
    for p in HERE.iterdir():
        if p.suffix in ['.py','.cjs','.md']:shutil.copy2(p,out/'source'/p.name)
    manifest={'rows':[],'truth':{},'transformations':[]};rng=random.Random(2026101806)
    for n in [32,128,512]:
        data=bytes(rng.getrandbits(8) for _ in range(n))
        for shift in [0,1]:
            name=f'n{n}-s{shift}';manifest['truth'][name]=data.hex()
            original=out/(name+'-original.wasm');T.assemble(T.source_module(data,shift),original)
            projected=out/(name+'-projected.wasm');record=T.transform(original,projected)
            record.update({'fixture':name});manifest['transformations'].append(record)
            for opt in ['raw','O2','O3']:
                for mode,src in [('original',original),('projected',projected)]:
                    dst=src
                    if opt!='raw':
                        dst=out/f'{name}-{mode}-{opt}.wasm'
                        subprocess.run([str(OPT),str(src),'-'+opt,'-o',str(dst)],check=True,capture_output=True,timeout=30)
                        T.W.tool('wasm-validate',[dst])
                    manifest['rows'].append({'fixture':name,'n':n,'shift':shift,'mode':mode,
                                             'optimization':opt,'wasm':dst.name})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(js('observe.cjs',out).strip())
    answers=json.loads((out/'public-answers.json').read_text())['rows'];attacks=[]
    for response in answers:
        row=next(r for r in manifest['rows'] if r['wasm']==response['wasm'])
        begin=time.perf_counter_ns();a=recover(response['answers'],row['n'],row['shift'])
        elapsed=time.perf_counter_ns()-begin
        # Ground truth is accessed only after reconstruction.
        source=bytes.fromhex(manifest['truth'][row['fixture']]);representative=bytes(a['representative'])
        a.update({'wasm':response['wasm'],'attack_ns':elapsed,'exact_original':representative==source})
        dst=out/f"{row['fixture']}-recovered-{row['optimization']}.wasm"
        T.assemble(T.source_module(representative,row['shift']),dst)
        manifest['rows'].append({**row,'mode':'recovered','wasm':dst.name})
        attacks.append(a)
    # Construct different source memories with identical projected binaries for each paired fixture.
    collisions=[]
    for n in [32,128,512]:
        original=out/f'n{n}-s1-original.wasm';data=bytes.fromhex(manifest['truth'][f'n{n}-s1'])
        alt=bytes(x^0xa5 for x in data);alt_src=out/f'n{n}-alternative.wasm';alt_dst=out/f'n{n}-alternative-projected.wasm'
        T.assemble(T.source_module(alt,1),alt_src);T.transform(alt_src,alt_dst)
        same=alt_dst.read_bytes()==(out/f'n{n}-s1-projected.wasm').read_bytes()
        assert same and alt_src.read_bytes()!=original.read_bytes()
        collisions.append({'n':n,'different_source':True,'identical_projected_bytes':same})
    # Without a known-zero suffix, the full chain has an unanchored component.
    control=recover([0]*65535,65536,0)
    assert control['free_components']==1 and control['preimage_bits']==8
    try:recover([1],0,0)
    except ValueError:incomplete_rejected=True
    else:raise AssertionError('Bad schema accepted')
    rejection=[]
    base=T.source_module(bytes(range(16)),0)
    import copy
    variants=[]
    a=copy.deepcopy(base);a.append(['export','"memory"',['memory','0']]);variants.append(('exported_memory',a))
    a=copy.deepcopy(base);a[-1].insert(-1,['i32.store8',['i32.const','0'],['i32.const','0']]);variants.append(('store',a))
    a=copy.deepcopy(base);a[-1][-1][2][-1]=['i32.const','0'];variants.append(('different_addresses',a))
    for label,module in variants:
        src=out/f'negative-{label}.wasm';T.assemble(module,src)
        try:T.transform(src,out/f'negative-{label}-unexpected.wasm')
        except ValueError as e:rejection.append({'name':label,'status':'rejected','reason':str(e)})
        else:raise AssertionError('Unsupported module accepted: '+label)
    for row in manifest['rows']:
        b=(out/row['wasm']).read_bytes();row.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (out/'attacks.json').write_text(json.dumps({'rows':attacks,'collisions':collisions,
        'no_anchor_control':{'free_components':control['free_components'],'preimage_bits':control['preimage_bits']},
        'incomplete_rejected':incomplete_rejected,'unsupported_inputs':rejection},indent=2),encoding='utf-8')
    print(js('check.cjs',out).strip())
    performances=[]
    for row in manifest['rows']:
        trials=[json.loads(js('measure.cjs',out/row['wasm'],max(1,row['n']>>row['shift']))) for _ in range(3)]
        medians=[statistics.median(t['ns_per_call']) for t in trials]
        performances.append({'wasm':row['wasm'],'median_ns':statistics.median(medians),
            'process_median_min_ns':min(medians),'process_median_max_ns':max(medians),
            'median_peak_RSS_KiB':statistics.median(t['maxRSS_KiB'] for t in trials),'trials':trials})
    (out/'performance.json').write_text(json.dumps({'rows':performances},indent=2),encoding='utf-8')
    print(json.dumps({'attack_conditions':len(attacks),'exact_original':sum(a['exact_original'] for a in attacks),
        'collisions':len(collisions),'performance_processes':len(performances)*3}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);run(ap.parse_args().output)
