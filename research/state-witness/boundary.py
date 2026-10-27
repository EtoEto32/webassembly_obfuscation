"""Explicit acceptance/rejection boundaries; not a conformance-suite replacement."""
import argparse,hashlib,json,shutil
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent


def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    cases=[
        ('empty','(module)',True),
        ('orphan-data','(module (data "x") (func (export "drop") data.drop 0))',True),
        ('orphan-elem','(module (func) (elem func 0) (func (export "drop") elem.drop 0))',True),
        ('two-tables','(module (table 0 2 funcref) (table 0 3 funcref))',True),
        ('four-tables','(module (table 0 funcref) (table 0 funcref) (table 0 funcref) (table 0 funcref))',True),
        ('imports','(module (import "x" "f" (func)))',False),
        ('start','(module (func) (start 0))',False),
        ('extern-table','(module (table 0 externref))',False),
        ('ref-api','(module (func (export "ref") (param funcref)))',False),
        ('ref-global','(module (global funcref (ref.null func)))',False),
        ('memory-limit','(module (memory 257 257))',False),
        ('table-limit','(module (table 4097 funcref))',False),
        ('five-tables','(module (table 0 funcref) (table 0 funcref) (table 0 funcref) (table 0 funcref) (table 0 funcref))',False),
        ('reserved-export','(module (func (export "__sw_pages")))',False)]
    for name,wat,expected in cases:
        src=out/f'{name}.wasm';k.p.compile_wat(wat,src)
        try:
            result=k.transform(src,out/f'{name}-observed.wasm');accepted=True;reason=None
        except ValueError as e:accepted=False;reason=str(e)
        assert accepted==expected,(name,accepted)
        rows.append({'name':name,'accepted':accepted,'reason':reason})
    shutil.copy2(__file__,out/'boundary.py')
    (out/'results.json').write_text(json.dumps({'rows':rows},indent=2))
    (out/'sha256.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir()},indent=2))
    print(json.dumps({'accepted':sum(x['accepted'] for x in rows),'rejected':sum(not x['accepted'] for x in rows)}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
