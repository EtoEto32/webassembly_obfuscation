"""Prepare export-only research derivatives without executing any Wasm code."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
TARGET=OUT/'derived-export-only'
TARGET.mkdir(exist_ok=True)
def sha(data):return hashlib.sha256(data).hexdigest()
def leb(data,pos):
    value=0;shift=0;start=pos
    while True:
        byte=data[pos];pos+=1;value|=(byte&127)<<shift
        if not byte&128:return value,pos
        shift+=7
        assert shift<=35 and pos-start<=5
def encode(value):
    out=bytearray()
    while True:
        byte=value&127;value>>=7;out.append(byte|(128 if value else 0))
        if not value:return bytes(out)
def sections(data):
    assert data[:8]==b'\x00asm\x01\x00\x00\x00'
    pos=8;out=[]
    while pos<len(data):
        start=pos;ident=data[pos];size,pos=leb(data,pos+1)
        end=pos+size;assert end<=len(data)
        out.append((ident,data[start:end],data[pos:end]));pos=end
    return out

review_bytes=(OUT/'cryptonight-hash-abi-review.json').read_bytes()
review=json.loads(review_bytes)
manifest=json.loads((OUT/'glue-control-input.json').read_text())
items={r['sha256']:r for r in manifest['modules']}
records=[]
for checked in review['modules']:
    item=items[checked['sha256']]
    original=(ROOT/item['object']).read_bytes();assert sha(original)==checked['sha256']
    wat=subprocess.check_output([str(ROOT/'.tools/wabt-1.0.42/bin/wasm2wat.exe'),
                                  str(ROOT/item['object']),'--generate-names'],text=True)
    imported=re.findall(r'^  \(import [^\n]+\(func (\$[^\s()]+)',wat,re.M)
    defined=re.findall(r'^  \(func (\$[^\s()]+)',wat,re.M)
    names=imported+defined
    assert len(names)==len(set(names))
    index=names.index(checked['function'])
    export_name=b'__research_hash'
    before=sections(original);out=bytearray(original[:8]);found=False
    for ident,raw,payload in before:
        if ident!=7:out.extend(raw);continue
        assert not found;found=True
        count,pos=leb(payload,0);entries=payload[pos:]
        # Preserve every existing entry byte. Read them only to reject duplicate name.
        offset=pos;existing=[]
        for _ in range(count):
            length,offset=leb(payload,offset)
            name=payload[offset:offset+length];offset+=length
            kind=payload[offset];offset+=1;_,offset=leb(payload,offset)
            existing.append((name,kind))
        assert offset==len(payload) and export_name not in [n for n,k in existing]
        new_entry=encode(len(export_name))+export_name+b'\x00'+encode(index)
        changed=encode(count+1)+entries+new_entry
        out.extend(b'\x07'+encode(len(changed))+changed)
    assert found
    derived=bytes(out);after=sections(derived)
    assert len(before)==len(after)
    preserved=[]
    for (ident,raw,payload),(ident2,raw2,payload2) in zip(before,after):
        assert ident==ident2
        if ident!=7:assert raw==raw2
        preserved.append(dict(section_id=ident,original_raw_sha256=sha(raw),
                              derivative_raw_sha256=sha(raw2),unchanged=raw==raw2))
    assert sum(not r['unchanged'] for r in preserved)==1
    assert all(r['unchanged'] for r in preserved if r['section_id'] in [1,2,3,4,5,6,8,9,10,11,12])
    path=TARGET/(sha(derived)+'.wasm');path.write_bytes(derived)
    subprocess.run([str(ROOT/'.tools/wabt-1.0.42/bin/wasm-validate.exe'),str(path)],check=True,capture_output=True)
    records.append(dict(method=item['method'],original_sha256=sha(original),derivative_sha256=sha(derived),
        original_object=item['object'],derivative_object=str(path.relative_to(ROOT)),
        original_bytes=len(original),derivative_bytes=len(derived),added_export=export_name.decode(),
        internal_function=checked['function'],function_index=index,sections=preserved,
        original_glue=item['glue'],original_glue_sha256=item['glue_sha256'],
        preparation_status='Only export section changed; WABT static validation passed. Not instantiated or executed.',
        hash_correctness='unverified',throughput='not measured'))
report=dict(date='2026-10-08',partial_abi_review_sha256=sha(review_bytes),modules=records,
    execution_authorized=False,executed_hashes=0,
    requirements_before_runtime=['Confirm professor permission for local hash execution on this university PC.',
        'Run only in an isolated network-disabled environment with finite time and memory limits.',
        'Use noInitialRun=true; do not invoke the original randomized mining/demo main.',
        'Capture original-glue instance exports to access __research_hash(input_pointer,output_pointer,length); initialize host/stack/memory correctly.',
        'Validate independent public CryptoNight v0 outputs before timing; a candidate ABI and unchanged code do not prove correctness.',
        'Report derivative SHA separately and describe the added export. Do not treat this as an unchanged published module or successful completed evaluation.'],
    scope='Five partial-ABI-reviewed modules. Boguscf and encodearith not prepared. Existing public-vector manifest, original artifacts, runtime hosts and past logs are unchanged.',
    limitations='An export changes module metadata and may affect engine compilation decisions; identical code/data sections do not prove identical timing. No new instructions or imports were inserted.')
(OUT/'cryptonight-export-only-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(prepared_derivatives=len(records),changed_sections='export only',executed_hashes=0)))
