"""Static scan only. Sound prefix prefilter, then standard disassembly confirmation."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WABT=ROOT/'.tools/wabt-1.0.42/bin'


def uleb(data,pos):
    value=0
    for i in range(5):
        if pos>=len(data):raise ValueError('truncated LEB')
        byte=data[pos];pos+=1;value|=(byte&127)<<(7*i)
        if not byte&128:return value,pos
    raise ValueError('oversized LEB')


def candidates(data):
    if data[:8]!=b'\0asm\x01\0\0\0':raise ValueError('not core Wasm v1')
    pos=8;hits=0
    while pos<len(data):
        section=data[pos];size,begin=uleb(data,pos+1);end=begin+size
        if end>len(data):raise ValueError('section boundary')
        if section==10:
            payload=data[begin:end]
            for i,byte in enumerate(payload):
                if byte!=0xfd:continue
                try:code,_=uleb(payload,i+1)
                except ValueError:continue
                if 0x100<=code<=0x113:hits+=1
        pos=end
    return hits


def disassemble(path):
    cmd=[str(WABT/'wasm-objdump.exe'),'-d',str(path)];start=time.perf_counter()
    process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8',errors='replace')
    expired=[]
    def timeout():expired.append(True);process.kill()
    timer=threading.Timer(60,timeout);timer.start();counts=collections.Counter();lines=0
    try:
        for line in process.stdout:
            lines+=1
            match=re.search(r'\|\s+(\S+)',line)
            if match and '.relaxed_' in match.group(1):counts[match.group(1)]+=1
        error=process.stderr.read();code=process.wait()
    finally:timer.cancel()
    return {'command':cmd,'status':'disassembly_timeout' if expired else 'disassembly_error' if code else 'ok','returncode':code,'stderr':error[:8000],'relaxedInstructions':dict(counts),'linesScanned':lines,'seconds':time.perf_counter()-start}


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'nowaset-scan.py');shutil.copy2(source/'provenance.json',out/'provenance.json');provenance=json.loads((source/'provenance.json').read_text(encoding='utf8'));rows=[];start=time.perf_counter()
    try:
        for item in provenance['files']:
            file=source/item['file'];data=file.read_bytes()
            if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('source hash mismatch')
            command=[str(WABT/'wasm-validate.exe'),'--enable-all',str(file)]
            try:check=subprocess.run(command,capture_output=True,text=True,timeout=30)
            except subprocess.TimeoutExpired:row={'file':item['file'],'status':'validation_timeout'}
            else:
                if check.returncode:row={'file':item['file'],'status':'validation_rejected','stderr':check.stderr[:8000]}
                else:
                    hits=candidates(data);row={'file':item['file'],'status':'ok','prefixCandidates':hits,'relaxedInstructions':{}}
                    if hits:row.update(disassemble(file))
            rows.append(row)
        counts=collections.Counter()
        for row in rows:
            if row['status']=='ok':counts.update(row['relaxedInstructions'])
        result={'commit':provenance['commit'],'files':len(rows),'bytes':provenance['totalBytes'],'statuses':dict(collections.Counter(r['status'] for r in rows)),'candidateFiles':sum(r.get('prefixCandidates',0)>0 for r in rows),'filesWithRelaxed':sum(bool(r.get('relaxedInstructions')) and r['status']=='ok' for r in rows),'instructions':dict(counts),'rows':rows,'elapsedSeconds':time.perf_counter()-start,'method':'Validation, code-section scan for FD followed by ULEB 0x100..0x113 (including overlong encodings), then wasm-objdump confirmation for positive prefilter. No target Wasm executed. No candidate implies absence for this fixed opcode range only.'}
        (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ('rows','method')}))
    finally:
        (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
