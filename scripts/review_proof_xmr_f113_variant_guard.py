"""Relate the f113 caller guard to recorded v0 inputs; no runtime execution."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
b=(P/'xmr-original-f111-complete.wat.txt').read_text().splitlines()
a=(P/'xmr-flattening-f111-complete.wat.txt').read_text().splitlines()
def alpha(lines):
    names={}
    return [re.sub(r'\$l\d+',lambda m:names.setdefault(m[0],f'$L{len(names)}'),x.strip()) for x in lines]
assert alpha(b[2:640])==alpha(a[2:640])
guard='\n'.join(b[456:479])
assert all(x in guard for x in ['i32.load offset=2098672','i32.const 4','i32.ge_s','br_if $B5'])
assert 'local.get $p3\n    i32.store offset=2098672' in '\n'.join(b[:30])
wrapper=(P/'xmr-original-f35-complete.wat.txt').read_text()
assert wrapper.rstrip() in (P/'xmr-flattening.wat').read_text()
manifest=json.loads((P/'glue-control-input.json').read_text())
vectors=[v for v in manifest['vectors'] if bytes.fromhex(v['hex'])[0]<7]
assert len(vectors)==3
runner=(ROOT/'experiments/runtime-reference/proof-xmr-benchmark.cjs').read_text()
assert "spec.vectors.filter(v=>Buffer.from(v.hex,'hex')[0]<7)" in runner
report=json.loads((P/'xmr-repeated-throughput-20261008.json').read_text())
assert report['algorithm']=='cn/0'
assert report['script_sha256']==hashlib.sha256((ROOT/'experiments/runtime-reference/proof-xmr-benchmark.cjs').read_bytes()).hexdigest()
sources=[]
with zipfile.ZipFile(ROOT/'data/archives/proof-of-theft.zip') as z:
    selections=[('main.cpp',58,69),('crypto/slow-hash.c',281,299),('crypto/variant4_random_math.h',179,227)]
    for suffix,start,end in selections:
        name='supp-materials/artifact/samples/xmr-wasm/src/'+suffix
        text=z.read(name).decode();lines=text.splitlines()
        excerpt='\n'.join(lines[start-1:end])+'\n'
        path=P/('xmr-f113-variant-source-'+Path(suffix).name+'.txt');path.write_text(excerpt)
        sources.append(dict(path=name,line_range=[start,end],excerpt=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
output=dict(function='$f113',guard='p3 (variant) >= 4, signed comparison; false exits block B5 before sole direct call.',
    reference_call_line=640,reference_guard_lines=[457,479],
    reference_and_flattened_prefix_alpha_equivalent_lines=[3,640],
    measured_input_first_bytes=[bytes.fromhex(v['hex'])[0] for v in vectors],
    wrapper_rule='First byte < 7 selects variant 0; otherwise first byte minus 6.',
    benchmark_script_sha256=report['script_sha256'],source_excerpts=sources,
    source_correspondence='f113 signature(pointer,height), seed byte 0xda and generated-operation loop agree with v4_random_math_init; source/binary historical identity is not proven.',
    interpretation='The reviewed direct caller does not enter f113 for the recorded v0 inputs. Its confirmed flattening entry cannot directly explain the measured v0 execution-time decrease.',
    limitations=['No dynamic instrumentation or comprehensive indirect-call reachability proof.',
                 'Unused code may still affect compilation, memory/layout and file-level static metrics; those indirect effects were not measured.',
                 'No new hashing; result concerns the stored runner input rule and reviewed call site.'])
(P/'xmr-f113-variant-guard-review.json').write_text(json.dumps(output,indent=2)+'\n')
print('f113 caller requires variant >=4; recorded three v0 inputs select0; reference/flattened prefix alpha-matches.')
