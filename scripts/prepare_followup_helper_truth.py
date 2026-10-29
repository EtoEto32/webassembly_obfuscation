"""Extend preserved finite XOR fixtures to substitution; never load a full miner."""
import json
import re
import shutil
from pathlib import Path
from prepare_followup_paths import fields
from prepare_isolated_xor_controls import ALLOWED
from evaluate_followup_normalization import ROOT,OUT,WABT,sha,command


def main():
    dest=OUT/'normalization-helper-truth';assert not dest.exists();dest.mkdir()
    base=ROOT/'results/countermeasures/flattening-xor';old=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    assert sha(base/'isolated-xor.wat')==old['wat_sha256'] and sha(base/'cases.json')==old['cases_sha256']
    static=json.loads((OUT/'normalization-static.json').read_text(encoding='utf-8'))
    row=next(r for r in static['records'] if r['input_id']=='published-sub' and r['method']=='unmodified')
    source=ROOT/row['canonical_path'];assert sha(source)==row['canonical_sha256'];text=source.read_text(encoding='utf-8')
    additions=[];sources=[]
    for size,index in [(8,112),(16,118)]:
        body=next(b for _,_,b in fields(text) if re.match(r'  \(func \(;'+str(index)+r';\)',b))
        lines=body.splitlines();assert '(param i32 i32)' in lines[0]
        ops=[line.strip().split()[0].rstrip(')') for line in lines[2:] if line.strip()]
        assert set(ops)<=ALLOWED|{'i32.or','i32.shl'},set(ops)-(ALLOWED|{'i32.or','i32.shl'})
        assert 'call' not in body and 'global.set' not in body and 'memory.grow' not in body
        selected=dest/f'substitution-f{index}.wat.txt';selected.write_text(body,encoding='utf-8')
        name=f'xor{size}_sub';adapted=re.sub(r'^  \(func \(;\d+;\) \(type 7\)',f'  (func ${name}',body,count=1)
        assert adapted!=body;additions.extend([adapted,f'  (export "{name}" (func ${name}))\n'])
        sources.append(dict(function_index=index,length=size,path=str(selected.relative_to(ROOT)),sha256=sha(selected),
            opcode_set=sorted(set(ops)),source_module_sha256=row['sha256']))
    fixture=(base/'isolated-xor.wat').read_text(encoding='utf-8').rstrip();assert fixture.endswith(')')
    target=dest/'isolated-xor.wat';target.write_text(fixture[:-1]+''.join(additions)+')\n',encoding='utf-8')
    binary=target.with_suffix('.wasm');command(WABT/'wat2wasm.exe',target,'-o',binary);command(WABT/'wasm-validate.exe',binary)
    shutil.copyfile(base/'cases.json',dest/'cases.json')
    # The reviewed expressions operate on masked byte loads; these are finite identities, not a full-module proof.
    assert all(((a+b)-2*(a&b))&255==a^b for a in range(256) for b in range(256))
    assert all((((~a)&b)|(a&(~b)))&255==a^b for a in range(256) for b in range(256))
    assert all((i^1)+2*(i&1)==i+1 for i in range(17))
    manifest=dict(wasm_sha256=sha(binary),wat_sha256=sha(target),cases_sha256=sha(dest/'cases.json'),
        cases=old['cases'],hashing=False,imports=[],memory_pages=1,maximum_memory_pages=1,
        inherited_manifest_sha256=sha(base/'manifest.json'),new_sources=sources,byte_pairs_per_identity=65536,
        static_review='f112: (a+b)-2*(a&b), increment i-(0-1). f118: (~a&b)|(a&~b), increment (i xor 1)+2*(i&1). Same byte-loop/pointer role; finite extraction checks supplement correspondence labels.',
        scope='Manual helper-role ground truth for matching only; finite scratch-excluding tests, not whole-module equivalence or automatic normalization.')
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    runner=(ROOT/'scripts/check_isolated_xor_controls.cjs').read_text(encoding='utf-8')
    runner=runner.replace("../results/countermeasures/flattening-xor","../results/followup-evaluation-20261016/normalization-helper-truth")
    runner=runner.replace("['memory','stack','xor8_ref','xor8_flat','xor16_ref','xor16_flat']","['memory','stack','xor8_ref','xor8_flat','xor8_sub','xor16_ref','xor16_flat','xor16_sub']")
    runner=runner.replace("['ref','flat']","['ref','flat','sub']")
    output=ROOT/'scripts/check_followup_helper_truth.cjs'
    if output.exists():assert output.read_text(encoding='utf-8')==runner,'Preserve a different existing runner'
    else:output.write_text(runner,encoding='utf-8')
    print(json.dumps(dict(fixture=str(binary),cases=manifest['cases'],hashing=False)))


if __name__=='__main__':main()
