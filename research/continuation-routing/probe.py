"""Record real tool support; module construction alone is not execution."""
import pathlib, subprocess, json, hashlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / (sys.argv[1] if len(sys.argv)>1 else 'results/invention-20261021/continuation-probe-v1')
OUT.mkdir(parents=True, exist_ok=False)
src = pathlib.Path(__file__).with_name('probe.wat')
binary = OUT / 'probe.wasm'
records = []
def call(name, args):
    p = subprocess.run([str(x) for x in args], cwd=ROOT, capture_output=True, text=True, timeout=30)
    records.append(dict(name=name, command=[str(x) for x in args], returncode=p.returncode, stdout=p.stdout, stderr=p.stderr))
    return p.returncode
call('assemble', [ROOT/'.tools/binaryen-version_133/bin/wasm-as.exe', src, '--all-features', '-o', binary])
script = "const fs=require('fs');const m=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1])));for(const x of [0,1,-1,2147483647,-2147483648]){const y=m.exports.run(x),e=(Math.imul(x,3)+1)|0;if(y!==e)throw Error('mismatch');}console.log('5 passed');"
for flags in [[], ['--experimental-wasm-stack-switching'], ['--experimental-wasm-wasmfx'], ['--experimental-wasm-wasmfx','--experimental-wasm-stack-switching']]:
    call('node '+str(flags), ['node', *flags, '-e', script, binary])
wast = OUT/'probe.wast'
tests = [(0,1),(1,4),(-1,-2),(2147483647,2147483646),(-2147483648,-2147483647)]
wast.write_text(src.read_text()+'\n'+'\n'.join('(assert_return (invoke "run" (i32.const %d)) (i32.const %d))'%t for t in tests), encoding='utf-8')
call('binaryen-execution', [ROOT/'.tools/binaryen-version_133/bin/wasm-shell.exe', wast])
(OUT/'records.json').write_text(json.dumps(records, indent=2),encoding='utf-8')
(OUT/'summary.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(), records=len(records), execution_passed=[r['name'] for r in records if r['returncode']==0 and r['name']!='assemble'], invention_validated=False),indent=2),encoding='utf-8')
print((OUT/'summary.json').read_text())
