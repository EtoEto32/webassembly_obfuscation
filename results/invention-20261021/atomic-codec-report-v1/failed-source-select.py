"""Check automatic selection by exact binary equality to already tested modes."""
import json,sys
from pathlib import Path
import prototype as p
main=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False);rows=[]
for profile,mode in [('full','native-neg'),('counter','native-affine')]:
    dst=out/(profile+'.wasm');r=p.transform(main/(profile+'-source.wasm'),dst,'auto')
    r.update(profile=profile,byte_match=p.q.digest(dst)==p.q.digest(main/(profile+'-'+mode+'-raw.wasm')))
    assert r['mode']==mode and r['byte_match'];rows.append(r)
(out/'selection.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))
