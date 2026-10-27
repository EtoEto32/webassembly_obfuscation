"""Check the stronger pipeline: optimize original code before metering it."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import transform as t

HERE=Path(__file__).resolve().parent


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for n in ('preopt.py','transform.py'):
        shutil.copy2(HERE/n,out/'sources'/n)
    records=[]
    try:
        mf=json.loads((source/'manifest.json').read_text())
        for f in mf['fixtures']:
            src=source/f['name']/'original.wasm';post=out/(f['name']+'.wasm')
            t.w.tool('wasm-opt',[src,'-O3','-o',post]);t.w.tool('wasm-validate',[post])
            wat=t.w.tool('wasm2wat',[post,'--fold-exprs']);post.with_suffix('.wat').write_text(wat,encoding='utf8')
            row={'name':f['name'],'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'beforeBound':f['modes']['frontier']['summary']['prefix'][-1],'ifsAfterO3':wat.count('(if')}
            try:
                rep=t.transform(post,out/(f['name']+'-frontier.wasm'),'frontier');row.update(status='accepted',summary=rep['summary'])
            except ValueError as e:row.update(status='unsupported',reason=str(e))
            records.append(row)
        (out/'results.json').write_text(json.dumps(records,indent=2),encoding='utf8')
        print(json.dumps(records,indent=2))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
