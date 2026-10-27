"""Diagnostic compilation: forced TurboFan, not a performance measurement."""
import json,re,subprocess,sys
from pathlib import Path
import prototype as p
src,out=map(Path,sys.argv[1:3]);reparse='--reparse' in sys.argv[3:]
if not reparse:out.mkdir(parents=True,exist_ok=False)
q=p.q;records=[]
for mode in ('anchor-min','anchor-zero','anchor-native','plain'):
    file=src/f'n4096-{mode}-s{0 if mode=="plain" else 7}-O3.wasm'
    m=q.read(file);index=next(x[2][1] for x in m[1:] if x[:2]==['export','"merge"'])
    code='const fs=require("fs");let e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;e.init(123);e.merge();console.log("checksum",e.checksum());'
    command=['node','--no-liftoff','--print-wasm-code','--print-wasm-code-function-index='+index,'-e',code,str(file)]
    log=out/(mode+'.txt')
    if not reparse:
        result=subprocess.run(command,capture_output=True,text=True,timeout=30,check=True)
        log.write_text(result.stdout+'\nSTDERR\n'+result.stderr,encoding='utf-8')
    # --print-wasm-code emits other functions as well in this Node build.
    # Select the requested function from its explicit header, not the flag alone.
    blocks=[b for b in log.read_text(encoding='utf-8').split('--- WebAssembly code ---') if re.search(r'^index: '+index+r'$',b,re.M)]
    assert len(blocks)==1,(mode,len(blocks))
    block=blocks[0];(out/(mode+'-merge.txt')).write_text(block,encoding='utf-8')
    count={}
    for line in block.splitlines():
        match=re.search(r'\b(vp[a-z0-9]+)\b',line)
        if match:count[match[1]]=count.get(match[1],0)+1
    size=int(re.search(r'Instructions \(size = (\d+)\)',block)[1])
    records.append(dict(mode=mode,file=str(file),sha256=q.digest(file),function_index=index,flags=command[1:4],compiler='TurboFan',instruction_bytes=size,vector_instruction_occurrences=count))
q.save(out/'summary.json',records);print(json.dumps(records))
