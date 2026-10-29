"""Replay binaries, cross-engine samples, and check profile/domain boundaries."""
import argparse, copy, json, platform, re, shutil, struct, subprocess
from fractions import Fraction
from pathlib import Path
import prototype as p


def run(main, runtime, output):
    main, runtime, out = map(lambda x: Path(x).resolve(), (main, runtime, output))
    out.mkdir(parents=True, exist_ok=False)
    pins = []
    for root in (main, runtime):
        saved = json.loads((root/'pins.json').read_text())
        for name, digest in saved.items():
            assert p.q.digest(root/name) == digest, (root, name)
        pins.append(dict(directory=str(root),verified=len(saved)))
    manifest = json.loads((main/'manifest.json').read_text())
    replay, interpreter = [], []
    samples = [(0,0),(-128,-128),(127,127),(-128,127),(127,-128),(-1,1),(1,-1),(-2147483648,2147483647)]
    for target in manifest['targets']:
        dst = out/target['file']
        if target['mode'] == 'recovered':
            src = out/target['file'].replace('.recovered.wasm','.wasm')
            p.recover(src,dst)
        elif target['opt'] == 'raw':
            p.transform(main/(target['name']+'.source.wasm'),dst,target['mode'])
        else:
            src = out/target['file'].replace('.O3.','.raw.')
            p.q.tool('wasm-opt',[src,'-O3','--enable-simd','-o',dst])
            p.q.w.tool('wasm-validate',[dst])
        assert dst.read_bytes() == (main/target['file']).read_bytes(), target['file']
        replay.append(dict(file=target['file'],byte_equal=True))
        if target['mode'] == 'bad':
            continue
        mod = p.q.read(dst)
        for i,(x,y) in enumerate(samples):
            mod += p.q.w.parse(f'(module (func (export "case{i}") (result i32) (call 0 (i32.const {x}) (i32.const {y}))))')[1:]
        probe = out/(dst.stem+'.interp.wasm')
        p.q.compile(p.q.w.emit(mod),probe)
        result = subprocess.run([str(p.ROOT/'.tools/wabt-1.0.42/bin/wasm-interp.exe'),str(probe),'--run-all-exports'],capture_output=True,text=True,timeout=30)
        assert result.returncode == 0, result.stderr
        observed = [int(v) for v in re.findall(r'case\d+\(\) => i32:(\d+)',result.stdout)]
        f = manifest['fixtures'][target['name']]
        expected = []
        for x,y in samples:
            x,y = ((x&255)^128)-128, ((y&255)^128)-128
            expected.append(sum(w*max(a*x+b*y+c,0) for w,(a,b,c) in zip(f['weights'],f['rows']))&0xffffffff)
        assert observed == expected, (target['file'],observed,expected)
        (out/(dst.stem+'.interp.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        interpreter.append(dict(file=target['file'],calls=len(samples),mismatches=0))
    controls = []
    base = p.q.read(main/'axis.source.wasm')
    for name in ('exported-memory','extra-memory-effect','changed-input-domain','preactivation-overflow'):
        mod = copy.deepcopy(base)
        f = next(e for e in mod[1:] if e[0]=='func')
        if name == 'exported-memory':
            mod.append(['export','"memory"',['memory','0']])
        elif name == 'extra-memory-effect':
            f.insert(-1,['drop',['memory.grow',['i32.const','1']]])
        elif name == 'changed-input-domain':
            e = next(e for e in p.q.walk(f) if e[0]=='i32.extend8_s')
            e[:] = ['local.get','0']
        else:
            fixture = copy.deepcopy(manifest['fixtures']['axis'])
            fixture['rows'][0] = [2**24,0,0]
            values = [r[j] for j in range(3) for r in fixture['rows']]+fixture['weights']
            blob = ''.join('\\'+format(v,'02x') for v in struct.pack('<16i',*values))
            mod = [e for e in mod if not isinstance(e,list) or e[0]!='data']
            mod.append(['data',['i32.const','0'],'"'+blob+'"'])
        src = out/(name+'.wasm')
        p.q.compile(p.q.w.emit(mod),src)
        try:
            p.read(src)
        except ValueError as exc:
            controls.append(dict(name=name,valid_wasm=True,rejected=True,reason=str(exc)))
        else:
            raise AssertionError('accepted unsupported profile: '+name)
    # At a noninteger point the fixture's two predicates differ. This is outside
    # the experiment's domain and refutes extension to arbitrary real inputs.
    rows = manifest['fixtures']['axis']['rows'][:2]
    x,y = Fraction(-1,2), Fraction(1)
    z = [a*x+b*y+c for a,b,c in rows]
    B = next(t for t in manifest['targets'] if t['name']=='axis' and t['mode']=='mix')['meta']['mixers'][0]['matrix']
    left = [max(sum(b*v for b,v in zip(row,z)),0) for row in B]
    right = [sum(b*max(v,0) for b,v in zip(row,z)) for row in B]
    assert left != right
    domain = dict(x=str(x),y=str(y),z=list(map(str,z)),matrix=B,relu_Bz=list(map(str,left)),B_relu_z=list(map(str,right)),equal=False)
    groups = []
    for name,fixture in manifest['fixtures'].items():
        for group in p.groups(fixture['rows']):
            a,b = [fixture['rows'][i] for i in group]
            assert any(a[i]*b[j] != a[j]*b[i] for i in range(3) for j in range(3))
            sig = p.signature(a)
            assert 0 < sum(sig) < len(sig)
            groups.append(dict(name=name,group=group,nonproportional=True,positive_points=sum(sig),domain=len(sig)))
    env = dict(python=platform.python_version(),platform=platform.platform(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.q.w.tool('wasm-interp',['--version']).strip(),binaryen=p.q.tool('wasm-opt',['--version']).strip())
    report = dict(pins=pins,replay=replay,interpreter=interpreter,controls=controls,domain_counterexample=domain,groups=groups,environment=env)
    p.q.save(out/'audit.json',report)
    for name in ('audit.py','prototype.py'):
        shutil.copy2(Path(__file__).with_name(name),out/('source-'+name))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(replayed=len(replay),interpreter_calls=sum(x['calls'] for x in interpreter),controls=len(controls))))


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    for name in ('main','runtime','output'):ap.add_argument(name)
    a=ap.parse_args();run(a.main,a.runtime,a.output)
