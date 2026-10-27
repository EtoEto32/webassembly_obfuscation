"""Independent-engine checks, byte reproduction and binary-only attack repetitions."""
import argparse
import json
import random
import re
import shutil
import statistics
import subprocess
from pathlib import Path
import prototype as p
import recover as r
import run as producer


def oracle(f, word, length):
    if length > 32: return None
    state = 0
    for i in range(length): state = f['delta'][state][(word >> i) & 1]
    return (f['accept'] >> state) & 1


def audit(main, perf, out):
    main, perf, out = map(lambda x: Path(x).resolve(), (main, perf, out))
    out.mkdir(parents=True, exist_ok=False)
    verified = {}
    for folder in (main, perf):
        pins = json.loads((folder/'pins.json').read_text(encoding='utf-8'))
        for name, digest in pins.items(): assert p.q.digest(folder/name) == digest, name
        verified[folder.name] = len(pins)
    # Reproduce from current sources, including all recovered binaries.
    producer.run(out/'reproduction')
    manifest = json.loads((main/'manifest.json').read_text(encoding='utf-8'))
    reproduced = json.loads((out/'reproduction/manifest.json').read_text(encoding='utf-8'))
    assert [x['file'] for x in manifest['targets']] == [x['file'] for x in reproduced['targets']]
    for t in manifest['targets']:
        assert (main/t['file']).read_bytes() == (out/'reproduction'/t['file']).read_bytes(), t['file']

    specs = []
    protected = [t for t in manifest['targets'] if t['mode'] in ('reverse','mixed')]
    for t in protected:
        mod, funcs, _ = r.inspect(main/t['file'])
        width = t['info']['n']
        tables = [r.table(r.expression(f), 1 << width) for f in funcs[:3]]
        for a in range(3): mod.append(['export', '"helper'+str(a)+'"', ['func',str(a)]])
        dst = out/'helpers'/t['file']; p.q.compile(p.q.w.emit(mod), dst)
        specs.append(dict(file=str(dst.relative_to(out)), width=width, gates=t['info']['gates'],
                          delta=manifest['fixtures'][t['name']]['delta'], tables=tables))
    p.q.save(out/'helper-cases.json', specs)
    h = subprocess.run(['node', str(Path(__file__).with_suffix('.cjs')), str(out)], capture_output=True, text=True, timeout=60)
    (out/'helpers.stderr.txt').write_text(h.stderr, encoding='utf-8')
    if h.returncode: raise RuntimeError(h.stderr)
    helpers = json.loads(h.stdout); p.q.save(out/'helpers.json', helpers)

    # A separate interpreter executes wrappers; expected values use only the source DFA.
    inputs = [(0,0),(1,1),(1,3),(13,5),(75,7),(0xffffffff,32),(0x80000000,32),(7,33)]
    wabt = []
    for t in manifest['targets']:
        if t['mode'] == 'bad': continue
        mod = p.q.read(main/t['file'])
        runid = next(e[2][1] for e in mod[1:] if e[0]=='export' and e[1]=='"run"')
        for index, (word, length) in enumerate(inputs):
            mod.append(['func', ['export','"case'+str(index)+'"'], ['result','i32'],
                        ['call',runid,['i32.const',str(word)],['i32.const',str(length)]]])
        dst = out/'wabt'/t['file']; p.q.compile(p.q.w.emit(mod),dst)
        stdout = p.q.w.tool('wasm-interp',[dst,'--run-all-exports'])
        dst.with_suffix('.log').write_text(stdout,encoding='utf-8')
        for index, (word, length) in enumerate(inputs):
            want=oracle(manifest['fixtures'][t['name']],word,length)
            lines=[line for line in stdout.splitlines() if line.startswith('case'+str(index)+'()')]
            assert len(lines)==1, stdout
            if want is None: assert 'error: unreachable executed' in lines[0], lines[0]
            else: assert re.search(r'=> i32:'+str(want)+r'\s*$',lines[0]),lines[0]
        wabt.append(dict(file=t['file'],calls=len(inputs),traps=1,mismatches=0))
    p.q.save(out/'wabt.json',wabt)

    rejection = []
    def expect_reject(label, thunk):
        try: thunk()
        except ValueError as e: rejection.append(dict(label=label,error=str(e)))
        else: raise AssertionError('accepted '+label)
    base=main/'suffix001.source.wasm'
    mod=p.q.read(base); mod.append(['export','"extra"',['func','0']])
    extra=out/'extra-export.wasm'; p.q.compile(p.q.w.emit(mod),extra)
    expect_reject('source extra export',lambda:p.transform(extra,out/'must-not-exist-source.wasm'))
    mod=p.q.read(base)
    guard=next(e for e in p.q.walk(mod) if e[0]=='i32.gt_u')
    guard[2][1]='31'
    guardfile=out/'changed-guard.wasm';p.q.compile(p.q.w.emit(mod),guardfile)
    expect_reject('source changed length guard',lambda:p.transform(guardfile,out/'must-not-exist-guard.wasm'))
    for t in manifest['targets']:
        if t['mode']=='bad':
            expect_reject('forward consumer '+t['file'],lambda t=t:r.recover(main/t['file'],out/('must-not-exist-'+t['file'])))
    mod=p.q.read(main/protected[0]['file']);mod.append(['export','"extra"',['func','0']])
    extra=out/'encoded-extra-export.wasm';p.q.compile(p.q.w.emit(mod),extra)
    expect_reject('recovery extra export',lambda:r.recover(extra,out/'must-not-exist-encoded.wasm'))
    p.q.save(out/'rejections.json',rejection)

    work=[(t,k) for t in protected if t['seed'] in (0,221011) for k in range(5)]
    random.Random(221014).shuffle(work); attacks=[]
    for index,(t,repeat) in enumerate(work):
        dst=out/'attacks'/f'{index:02}.wasm'; report=r.recover(main/t['file'],dst)
        assert dst.read_bytes()==(main/(t['name']+'.source.wasm')).read_bytes()
        report.update(name=t['name'],mode=t['mode'],opt=t['opt'],repeat=repeat,file=t['file'],source_byte_equal=True)
        attacks.append(report)
    p.q.save(out/'attacks.json',attacks)
    attack_summary=[]
    for name in manifest['fixtures']:
        for opt in ('raw','O3'):
            row=dict(name=name,opt=opt)
            for mode in ('reverse','mixed'):
                a=[x for x in attacks if x['name']==name and x['opt']==opt and x['mode']==mode]
                row[mode]={key:statistics.median(x[key] for x in a) for key in ('total_ms','table_ms','orbit_ms')}
            row['total_ratio']=row['mixed']['total_ms']/row['reverse']['total_ms']
            attack_summary.append(row)
    result=dict(verified_pins=verified,reproduced_targets=len(manifest['targets']),
                unique_positive_binaries=len({t['sha256'] for t in manifest['targets'] if t['mode']!='bad'}),
                helper_checks=helpers,wabt_calls=sum(x['calls'] for x in wabt),wabt_traps=sum(x['traps'] for x in wabt),
                rejected_controls=len(rejection),attack_repetitions=len(attacks),attack_summary=attack_summary,
                limitations='Reproduction and repeats are not independent program cases. Helper states exhaustive only for widths 4,6,7; high bits tested all-zero/all-one, not exhaustively. No whole-tool formal proof.')
    p.q.save(out/'audit.json',result)
    snapshots=out/'sources';snapshots.mkdir()
    for file in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(file,snapshots/'__'.join(file.relative_to(p.ROOT).parts))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(result))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('performance');ap.add_argument('output');a=ap.parse_args()
    audit(a.main,a.performance,a.output)
