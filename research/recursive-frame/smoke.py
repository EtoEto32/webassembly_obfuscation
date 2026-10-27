import json,sys
from pathlib import Path
import prototype as p
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
p.compile(p.source_text(2654435761,2246822519,7),out/'plain.wasm')
rows=[]
for mode in ('fixed','dynamic','bad'):
    row=p.transform(out/'plain.wasm',out/(mode+'.wasm'),mode)
    p.tool('wasm-opt',[out/(mode+'.wasm'),'-O3','-o',out/(mode+'.O3.wasm')])
    (out/(mode+'.O3.wat')).write_bytes(p.tool('wasm2wat',[out/(mode+'.O3.wasm'),'--fold-exprs','--no-debug-names']))
    rows.append(row)
p.save(out/'rows.json',rows);p.save(out/'commands.json',p.LOG)
print(json.dumps(rows))
