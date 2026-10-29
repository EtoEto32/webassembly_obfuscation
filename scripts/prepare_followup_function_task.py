"""Attach grading-only names in auxiliary copies, verify core identity, extract features."""
import hashlib
import json
import re
import time
import uuid
from pathlib import Path
from audit_corpora import sections
from analyze_corpus import Reader
from audit_normalization_signatures import signatures,TYPES
from prepare_followup_paths import fields
from evaluate_followup_normalization import ROOT,OUT,WABT,sha,command,wat,transform,read_plan


def uleb(n):
    out=bytearray()
    while True:
        b=n&127;n>>=7;out.append(b|(128 if n else 0))
        if not n:return bytes(out)


def encode_section(ident,payload):return bytes([ident])+uleb(len(payload))+payload


def core(data):
    return data[:8]+b''.join(encode_section(s['id'],s['payload']) for s in sections(data) if s['id']!=0)


def defined_indices(path):
    imported=len(signatures(path)['imported_functions'])
    section=next(s for s in sections(path.read_bytes()) if s['id']==3)
    count=Reader(section['payload']).uint()
    return list(range(imported,imported+count))


def type_shapes(path):
    result=[]
    for section in sections(path.read_bytes()):
        if section['id']!=1:continue
        r=Reader(section['payload'])
        for _ in range(r.uint()):
            assert r.byte()==0x60
            params=[TYPES[r.byte()] for _ in range(r.uint())];returns=[TYPES[r.byte()] for _ in range(r.uint())]
            result.append(json.dumps([params,returns],separators=(',',':')))
        assert r.pos==len(r.data)
    return result


def functions(text):return [b for _,_,b in fields(text) if b.startswith('  (func ')]


def fingerprint(body,types):
    # Features are derived solely from the real, name-ignoring canonical WAT.
    cleaned=re.sub(r'\(;.*?;\)','',body,flags=re.S)
    cleaned=re.sub(r';;[^\n]*','',cleaned)
    cleaned=re.sub(r'^  \(func\s+\$\S+','  (func',cleaned,count=1)
    cleaned=re.sub(r'\(type \d+\)','',cleaned,count=1)
    cleaned=re.sub(r'\(type (\d+)\)',lambda m:'(type_shape '+types[int(m[1])]+')',cleaned)
    cleaned=re.sub(r'\b(call|return_call|ref\.func)\s+\d+\b',r'\1 FUNCTION',cleaned)
    assert '$origin_' not in cleaned
    tokens=' '.join(cleaned.split())
    return hashlib.sha256(tokens.encode('utf-8')).hexdigest()


def named_copy(source,target):
    data=source.read_bytes();parts=[]
    for section in sections(data):
        if section['id']==0 and Reader(section['payload']).text()=='name':continue
        parts.append(encode_section(section['id'],section['payload']))
    indices=defined_indices(source);total=indices[-1]+1
    mapping=bytearray(uleb(total))
    for index in range(total):
        name=f'origin_{index:06d}'.encode();mapping.extend(uleb(index)+uleb(len(name))+name)
    payload=uleb(4)+b'name'+b'\x01'+uleb(len(mapping))+mapping
    target.write_bytes(data[:8]+b''.join(parts)+encode_section(0,payload))
    assert core(data)==core(target.read_bytes()),'Name annotation changed core module'
    command(WABT/'wasm-validate.exe',target)


def main():
    pp,plan=read_plan();destination=OUT/'normalization-function-features.json';assert not destination.exists()
    static_path=OUT/'normalization-static.json';static=json.loads(static_path.read_text(encoding='utf-8'))
    assert static['status']=='static-validation-complete' and len(static['records'])==77
    truth_path=OUT/'normalization-helper-truth/checks.json';truth=json.loads(truth_path.read_text(encoding='utf-8'))
    assert truth['passed'] and truth['cases']==698 and truth['helper_calls']==2094 and not truth['whole_miner_loaded']
    work=OUT/'normalization-matching-artifacts'/uuid.uuid4().hex;work.mkdir(parents=True)
    origins={};source_headers={};rows=[]
    status=dict(status='running',rows=rows,origins=origins,normalization_plan_sha256=sha(pp),
        static_result_sha256=sha(static_path),helper_truth_sha256=sha(truth_path),runtime_executed=False)
    def save():
        (work/'progress.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    try:
        for item in plan['inputs']:
            source=ROOT/item['path'];indices=defined_indices(source);source_headers[item['id']]=[b.splitlines()[0] for b in functions(wat(source))]
            assert len(indices)==len(source_headers[item['id']])
            if item['truth']=='index-preserving-generated-control':
                baseline=item['family']+'-baseline';assert source_headers[item['id']]==source_headers[baseline]
                origins[item['id']]=indices
            elif item['truth']=='reviewed-helper-pairs-only':
                origins[item['id']]=item['reviewed_function_indices'];assert set(origins[item['id']])<=set(indices)
            else:origins[item['id']]=[]
            auxiliary_source=work/(item['id']+'--grading-names.wasm');named_copy(source,auxiliary_source)
            for method in plan['methods']:
                row=next(r for r in static['records'] if r['input_id']==item['id'] and r['method']==method['id'])
                actual=ROOT/row['path'];assert sha(actual)==row['sha256']
                canonical_path=ROOT/row['canonical_path'];assert sha(canonical_path)==row['canonical_sha256']
                auxiliary=work/(item['id']+'--'+method['id']+'--grading.wasm')
                started=time.perf_counter();transform(auxiliary_source,auxiliary,method,True)
                elapsed=(time.perf_counter()-started)*1000
                assert core(auxiliary.read_bytes())==core(actual.read_bytes()),'Auxiliary processing differs in core content: '+str(auxiliary)
                actual_functions=functions(canonical_path.read_text(encoding='utf-8'));named_functions=functions(wat(auxiliary,True))
                assert len(actual_functions)==len(named_functions)
                types=type_shapes(actual);extracted=[];started=time.perf_counter()
                for position,(body,named) in enumerate(zip(actual_functions,named_functions)):
                    match=re.match(r'  \(func \$origin_(\d+)(?=\s|\))',named)
                    extracted.append(dict(output_definition_position=position,origin_index=int(match[1]) if match else None,
                        fingerprint=fingerprint(body,types)))
                feature_ms=(time.perf_counter()-started)*1000
                rows.append(dict(input_id=item['id'],family=item['family'],method=method['id'],functions=extracted,
                    actual_sha256=row['sha256'],auxiliary_path=str(auxiliary.relative_to(ROOT)).replace('\\','/'),
                    auxiliary_sha256=sha(auxiliary),noncustom_sha256=hashlib.sha256(core(actual.read_bytes())).hexdigest(),
                    noncustom_equal=True,auxiliary_preprocessing_ms=elapsed,feature_extraction_ms=feature_ms))
                save();print(json.dumps(dict(completed=len(rows),input=item['id'],method=method['id'])),flush=True)
        assert len(rows)==77
        status.update(status='all-auxiliary-core-content-matches-real-outputs',evaluator_sha256=sha(Path(__file__)),
            fixed_queries_per_method=sum(len(v) for v in origins.values()),
            scope='Canonical syntax fingerprints; grading provenance names are absent from features. Preserve unavailable origins; no semantic-equivalence or detector claim.')
        save();destination.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(status=status['status'],rows=len(rows),queries_per_method=status['fixed_queries_per_method'])))
    except Exception as error:
        status.update(status='failed',error=str(error));save();raise


if __name__=='__main__':main()
