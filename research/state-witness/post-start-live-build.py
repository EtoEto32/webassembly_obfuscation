"""Fixed-input drop omission and appended non-mutating observers, no WAT roundtrip."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
EXE=ROOT/'.tools/state-witness-census-graph-target/release/start-drop-sites.exe'
EXPECTED='be2c97605366b78f3f13e21b52e81a55a79e1f29c133b03a68ec187b1a2ec41a'
def digest(data):return hashlib.sha256(data).hexdigest()
def uint(n):
    result=bytearray()
    while n>=128:result.append((n&127)|128);n>>=7
    result.append(n);return bytes(result)
def readuint(data,pos):
    value=shift=0
    while True:
        b=data[pos];pos+=1;value|=(b&127)<<shift
        if b<128:return value,pos
        shift+=7;assert shift<35
def text(s):
    raw=s.encode();return uint(len(raw))+raw
def instrument(raw,meta):
    sections=[];pos=8;seen=set();total=len(meta['dataLengths']);typeindex=len(meta['types']);probes=[f'__lifetime_{n}' for n in range(total)]
    for name in probes:assert not any(e['name']==name for e in meta['exports'])
    while pos<len(raw):
        ident=raw[pos];length,start=readuint(raw,pos+1);payload=raw[start:start+length];pos=start+length
        if ident in (1,3,7,10):
            count,body=readuint(payload,0);tail=payload[body:];added=bytearray()
            if ident==1:assert count==typeindex;added.extend(bytes([0x60,0,1,0x7f]));increment=1
            elif ident==3:added.extend(uint(typeindex)*total);increment=total
            elif ident==7:
                for n,name in enumerate(probes):added.extend(text(name)+bytes([0])+uint(meta['functionCount']+n))
                increment=total
            else:
                for segment in range(total):
                    # zero locals; dst=0, src=1, len=0; memory.init; return 1
                    body=bytes([0,0x41,0,0x41,1,0x41,0,0xfc,8])+uint(segment)+uint(0)+bytes([0x41,1,0x0b]);added.extend(uint(len(body))+body)
                increment=total
            payload=uint(count+increment)+tail+added;seen.add(ident)
        sections.append(bytes([ident])+uint(len(payload))+payload)
    assert seen=={1,3,7,10};return raw[:8]+b''.join(sections)
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);raw=source.read_bytes();assert digest(raw)==EXPECTED
    run=subprocess.run([str(EXE),str(source)],capture_output=True,text=True,encoding='utf8',timeout=60);assert run.returncode==0,run.stderr;meta=json.loads(run.stdout)
    assert len(meta['drops'])==len(meta['dataLengths'])==7320 and all(meta['dataLengths'])
    assert {d['function'] for d in meta['drops']}=={meta['start']}
    assert sorted(d['segment'] for d in meta['drops'])==list(range(7320))
    mutant=bytearray(raw)
    for drop in meta['drops']:mutant[drop['offset']:drop['end']]=bytes([1])*(drop['end']-drop['offset'])
    paths={'retained.wasm':bytes(mutant),'observed-original.wasm':instrument(raw,meta),'observed-retained.wasm':instrument(mutant,meta)}
    validation=[]
    for name,data in paths.items():
        path=out/name;path.write_bytes(data)
        run=subprocess.run([str(ROOT/'.tools/wabt-1.0.42/bin/wasm-validate.exe'),'--enable-all',str(path)],capture_output=True,text=True,encoding='utf8',timeout=60)
        validation.append({'file':name,'code':run.returncode,'stderr':run.stderr});assert run.returncode==0,run.stderr
    meta.update(source=str(source.resolve()),sourceSha256=EXPECTED,patchedDropCount=len(meta['drops']),probePrefix='__lifetime_',validation=validation,extractorSha256=digest(EXE.read_bytes()))
    (out/'manifest.json').write_text(json.dumps(meta,indent=2))
    for name in ('post-start-live-plan.md','post-start-live-build.py','post-start-live-preflight.py','post-start-live-bindings.py'):shutil.copy2(HERE/name,out/name)
    shutil.copy2(HERE/'census-native/src/bin/start-drop-sites.rs',out/'start-drop-sites.rs')
    (out/'sha256.json').write_text(json.dumps({p.name:digest(p.read_bytes()) for p in out.iterdir()},indent=2))
    print(json.dumps({'probes':len(meta['dataLengths']),'dropsOmitted':len(meta['drops']),'pureConstantExports':meta['pureConstantExports'],'validation':validation}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
