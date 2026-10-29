"""Remove only core-semantics-irrelevant `name` custom sections, preserving other bytes."""
import argparse,hashlib,json,shutil
from pathlib import Path

def uleb(data,at):
    value=0
    for i in range(5):
        if at>=len(data):raise ValueError('truncated u32')
        b=data[at];at+=1
        if i==4 and b>15:raise ValueError('u32 overflow')
        value|=(b&127)<<(7*i)
        if not b&128:return value,at
    raise ValueError('u32 too long')

def strip(data):
    if data[:8]!=b'\x00asm\x01\x00\x00\x00':raise ValueError('core Wasm v1 required')
    result=bytearray(data[:8]);at=8;removed=[]
    while at<len(data):
        start=at;sid=data[at];length,body=uleb(data,at+1);end=body+length
        if end>len(data):raise ValueError('section exceeds input')
        name=None
        if sid==0:
            size,pos=uleb(data,body)
            if pos+size>end:raise ValueError('custom name exceeds section')
            name=data[pos:pos+size]
        if name==b'name':removed.append({'offset':start,'bytes':end-start})
        else:result.extend(data[start:end])
        at=end
    return bytes(result),removed

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);download=json.loads((source/'download.json').read_text());rows=[]
    for r in download['rows']:
        if not r['path'].endswith('.wasm'):continue
        data=(source/r['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256']
        normalized,removed=strip(data);dest=out/r['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(normalized)
        assert strip(normalized)==(normalized,[]),'idempotent stripping'
        rows.append({'path':r['path'],'sha256':hashlib.sha256(normalized).hexdigest(),'originalSha256':r['sha256'],'bytes':len(normalized),'removedNameSections':removed})
    (out/'download.json').write_text(json.dumps({'commit':download['commit'],'rows':rows,'skips':download['skips'],'normalization':'remove name custom section only'},indent=2))
    shutil.copy2(__file__,out/'r3-strip-name.py')
    (out/'sha256.json').write_text(json.dumps({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2))
    print(json.dumps({'files':len(rows),'changed':sum(bool(r['removedNameSections']) for r in rows)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.out)
