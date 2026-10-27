# -*- coding: utf-8 -*-
import json
from pathlib import Path
import subprocess
import sys
import prototype as p
import attack

out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
tree=('or',('and',('var',0),('var',1)),('and',('var',2),('xor',('var',3),('const',p.MASK))))
p.save(p.w.plain_wat(4,'"run"',tree),out/'plain.wasm')
records=[]
for mode in ('span','constant','dependent'):
    path=out/(mode+'.wasm');meta=p.transform(out/'plain.wasm',path,mode)
    opt=out/(mode+'-O3.wasm');p.optimize(path,opt)
    for f in (path,opt):
        for method in ('direct','coefficient'):
            records.append({'file':f.name,'method':method,**attack.recover(f,out/(f.stem+'-'+method+'.wasm'),method)})
(out/'attack.json').write_text(json.dumps(records,indent=2),encoding='utf8')
print(json.dumps(records))
