"""Validate exact Wasm bytes and independently check a snapshot certificate.

Exit 0 = accepted under reported host preconditions; exit 2 = rejected.
Acceptance is not an all-input mathematical proof or automatic host enforcement.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import time

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=load('byte_checker',HERE/'byte-checker.py');b=load('boundary_tools',HERE/'boundary.py')
REQUIRED=['nonshared memory32','exclusive writer interval through view consumption','trusted host',
          'frozen read set and arguments','instantiate the exact certified bytes']

def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate JSON key')
        result[key]=value
    return result

def reject_constant(value):raise ValueError('non-finite JSON constant')
def main(wasm,certificate,out):
    started=time.perf_counter();data=wasm.read_bytes();cert_bytes=certificate.read_bytes()
    validation='not-run';cert=None
    try:
        if len(cert_bytes)>2*1024*1024:raise ValueError('certificate size bound')
        cert=json.loads(cert_bytes,object_pairs_hook=unique_object,parse_constant=reject_constant)
        if not isinstance(cert,dict):raise ValueError('certificate object required')
    except (ValueError,UnicodeError,RecursionError) as e:
        verdict={'accepted':False,'reason':'certificate JSON: '+str(e)[:200]}
    else:
        if cert.get('schema')!='restricted-snapshot-contract-v1' or cert.get('export')!='callback' or cert.get('signature')!='(i32,i32,i32)->()' or cert.get('memory_export')!='memory':
            verdict={'accepted':False,'reason':'certificate schema or entry contract mismatch'}
        else:
            with tempfile.TemporaryDirectory(prefix='effect-check-',dir=out.parent) as temp:
                binary=Path(temp)/'input.wasm';binary.write_bytes(data)
                try:b.p.w.tool('wasm-validate',[binary])
                except RuntimeError as e:
                    validation='failed';verdict={'accepted':False,'reason':'standard binary validation failed','diagnostic':str(e)[:1000]}
                else:
                    validation='passed';verdict=c.check(data,cert.get('analysis',{}),cert.get('wasm_sha256'))
    result={'wasm_sha256':hashlib.sha256(data).hexdigest(),'certificate_sha256':hashlib.sha256(cert_bytes).hexdigest(),
            'checker_source_sha256':hashlib.sha256((HERE/'byte-checker.py').read_bytes()).hexdigest(),
            'standardBinaryValidation':validation,'verdict':verdict,'required_embedding':REQUIRED,
            'validation_and_check_ms':(time.perf_counter()-started)*1000}
    with out.open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
    print(json.dumps({'accepted':verdict['accepted'],'mode':verdict.get('mode'),'reason':verdict.get('reason')}))
    return 0 if verdict['accepted'] else 2
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('wasm',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();raise SystemExit(main(a.wasm.resolve(),a.certificate.resolve(),a.output.resolve()))
