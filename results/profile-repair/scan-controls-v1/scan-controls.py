"""Check static scanner with actual positives, overlong LEB and false positives."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import prototype as p

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('scanner',HERE/'nowaset-scan.py');scanner=importlib.util.module_from_spec(spec);spec.loader.exec_module(scanner)


def leb(n):
    out=bytearray()
    while n>=128:out.append((n&127)|128);n>>=7
    out.append(n);return bytes(out)


def overlong(data):
    result=data[:8];pos=8;replacements=0
    while pos<len(data):
        sid=data[pos];size,begin=scanner.uleb(data,pos+1);payload=data[begin:begin+size];pos=begin+size
        if sid==10:
            count,cursor=scanner.uleb(payload,0);rebuilt=leb(count)
            for _ in range(count):
                length,start=scanner.uleb(payload,cursor);body=payload[start:start+length];cursor=start+length
                replacements+=body.count(b'\xfd\x80\x02');body=body.replace(b'\xfd\x80\x02',b'\xfd\x80\x82\x00');rebuilt+=leb(len(body))+body
            assert cursor==len(payload);payload=rebuilt
        result+=bytes([sid])+leb(len(payload))+payload
    assert replacements==1;return result


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'scan-controls.py');shutil.copy2(HERE/'nowaset-scan.py',out/'nowaset-scan.py');rows=[]
    try:
        records=json.loads((source/'results.json').read_text(encoding='utf8'))['rows']
        for row in records:
            file=source/(row['name']+'-source.wasm');data=file.read_bytes();assert scanner.candidates(data)>=row['sites']
            actual=scanner.disassemble(file);assert actual['status']=='ok';assert actual['relaxedInstructions'].get(p.RELAXED,0)==row['sites'];rows.append({'name':row['name'],'expected':row['sites'],'actual':actual['relaxedInstructions']})
        over=out/'overlong.wasm';over.write_bytes(overlong((source/'single-source.wasm').read_bytes()));p.w.tool('wasm-validate',[over]);assert scanner.candidates(over.read_bytes())==1
        actual=scanner.disassemble(over);assert actual['status']=='ok' and actual['relaxedInstructions']=={p.RELAXED:1};rows.append({'name':'overlong','expected':1,'actual':actual['relaxedInstructions']})
        custom=out/'custom-only.wasm';payload=b'\0\xfd\x80\x02';custom.write_bytes(b'\0asm\x01\0\0\0'+b'\0'+leb(len(payload))+payload);p.w.tool('wasm-validate',[custom]);assert scanner.candidates(custom.read_bytes())==0;rows.append({'name':'custom-only','expected':0,'actual':0})
        immediate=out/'immediate.wasm';p.compile_mod(['module',['func',['export','"run"'],['param','i32','i32'],['result','i32'],p.c(32893)]],immediate)
        assert scanner.candidates(immediate.read_bytes())==1;actual=scanner.disassemble(immediate);assert actual['status']=='ok' and actual['relaxedInstructions']=={};rows.append({'name':'immediate-false-positive','expected':0,'prefilter':1,'actual':0})
        report={'controls':len(rows),'rows':rows,'limitation':'Prefix scan is only a necessary-condition filter. Positive findings require standard disassembly.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'controls':len(rows)}))
    finally:
        (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
