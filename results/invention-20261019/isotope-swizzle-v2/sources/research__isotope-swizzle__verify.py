import argparse,json
from pathlib import Path
import prototype as q
def reference(t,args):
    def nibble(t,vs):
        if isinstance(t,int):return vs[t]&15
        return q.op_eval(t[0],nibble(t[1],vs),nibble(t[2],vs))
    return sum(nibble(t,[(x>>(8*k))&255 for x in args])<<(8*k) for k in range(4))
def main(data,out):
    data=Path(data);out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=json.loads((data/'manifest.json').read_text());models=json.loads((data/'models.json').read_text());records=[]
    inputs=[(0,0,0),(15,15,15),(255,255,255),(-1,0,-1),(0x7fffffff,-2147483648,17),(0x0f0f0f0f,0xf0f0f0f0,0x12345678),(0x01020304,0x0f0e0d0c,0xaabbccdd),(16,31,32)]
    for row in rows:
        for key in ('file','recovered'):
            f=data/row[key];blob=''.join('\\%02x'%b for b in f.read_bytes());lines=['(module binary "'+blob+'")']
            for args in inputs:
                want=reference(models[row['kernel']],args);params=' '.join(f'(i32.const {x})' for x in args);lines.append(f'(assert_return (invoke "run" {params}) (i32.const {want}))')
            dst=out/(f.stem+'.wast');dst.write_text('\n'.join(lines),encoding='utf-8');log=q.tool('wasm-shell',[dst]);dst.with_suffix('.log').write_text(log,encoding='utf-8');records.append(dict(file=f.name,checks=len(inputs),status='pass'))
    q.save(out/'records.json',records);q.save(out/'summary.json',dict(binaryen_checks=sum(r['checks'] for r in records),files=len(records),all_pass=True));print(json.dumps(json.loads((out/'summary.json').read_text())))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('output');v=p.parse_args();main(v.data,v.output)
