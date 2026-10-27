"""Independent WABT engine; wrappers preserve original public memory index."""
import argparse
import hashlib
import json
from pathlib import Path
import prototype as p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((a.input/'manifest.json').read_text());records=[]
    cases=[(0,0),(0,64),(65535,1),(65535,2),(0xffffffff,0),(0xffffffff,1)]
    for entry in manifest['files']:
        module=p.w.parse(p.w.tool('wasm2wat',[a.input/entry['path'],'--fold-exprs','--no-debug-names']))
        d=manifest['models'][entry['model']]
        for pointer,length in cases:
            m=module[:]
            m.append(['func',['export','"check"'],['result','i32'],['memory.fill',['i32.const','0'],['i32.const','91'],['i32.const','65536']],['call','0',['i32.const',str(pointer)],['i32.const',str(length)]]])
            for addr in (0,1,65534,65535):m.append(['func',['export','"byte'+str(addr)+'"'],['result','i32'],['i32.load8_u',['i32.const',str(addr)]]])
            target=a.output/(Path(entry['path']).stem+'.'+str(pointer)+'-'+str(length)+'.wasm');p.compile_wat(p.w.emit(m),target)
            text=p.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(text,encoding='utf-8')
            trap=length>0 and pointer+length>65536;q=0
            if not trap:
                for _ in range(length):q=d['trans'][q][1]
                value=(d['final']>>q)&1
                assert 'check() => i32:'+str(value)+'\n' in text,(entry,pointer,length,text)
            else:assert 'check() => error:' in text,(entry,pointer,length,text)
            for addr in (0,1,65534,65535):assert 'byte'+str(addr)+'() => i32:91\n' in text
            records.append(dict(path=entry['path'],pointer=pointer,length=length,trap=trap))
    result=dict(engine='WABT 1.0.42',calls=len(records),memory_probes=4*len(records),mismatches=0,records=records,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.output/'checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='records'}))

if __name__=='__main__':main()
