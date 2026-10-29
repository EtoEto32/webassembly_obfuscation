"""Read saved artifacts; run a WABT cross-engine check without source generators."""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/observation-synthesis'))
import transform as wasm
MASK=2**32-1

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reference(profile,row,args):
    if profile=='table':
        a,n=args;q=0
        for _ in range(n&63):
            shift=q+1;a^=(2654435761*shift)&MASK
            a=((a<<shift)|(a>>(32-shift)))&MASK
            a=(a*(3+2*q)+17*shift)&MASK
            q=(q+((a^(a>>11))&(row['N']-1)))&(row['N']-1)
        return a
    a,b,n=args;k=row['kernel']
    for _ in range(n&63):
        if k=='quadratic':u,v=a*a+3*b+5,b*b+3*a+5
        elif k=='quadratic-wide':u,v=a*a+2654435761*b+2246822519,b*b+2654435761*a+2246822519
        elif k=='cubic':u,v=a**3+2*a*b+b+7,b**3+2*a*b+a+7
        elif k=='coupled':u,v=a*a*b+3*a+b*b+11,b*b*a+3*b+a*a+11
        else:raise ValueError(k)
        a,b=u&MASK,v&MASK
    return (a+b+7*a*b)&MASK

def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args()
    out=args.output.resolve();out.mkdir();rows=[];inventory={}
    base=ROOT/'results/invention-20261018'
    groups=[('table',base/'table-transport-v3',base/'table-transport-reproduction-v1'),
            ('symmetric',base/'symmetric-state-v4',base/'symmetric-state-reproduction-v1')]
    for profile,first,d in groups:
        m=load(d/'manifest.json');old=load(first/'manifest.json');checks=load(d/'checks.json');inputs=load(d/'inputs.json')
        assert {a['file']:a['sha256'] for a in m['artifacts']}=={a['file']:a['sha256'] for a in old['artifacts']}
        assert all(r['mismatches']==0 and r.get('unexpectedTraps',0)==0 for r in checks['rows'])
        assert all(a['status']=='recovered' and a['execution_queries']==0 for a in m['attacks'])
        selected=[inputs[i*(len(inputs)-1)//31] for i in range(32)]
        for index,a in enumerate(m['artifacts']):
            src=d/a['file'];assert sha(src)==a['sha256'];inventory[str(src.relative_to(ROOT))]=a['sha256']
            tree=wasm.parse(wasm.tool('wasm2wat',[src,'--fold-exprs']))
            ex=next(n for n in tree if isinstance(n,list) and n[:2]==['export','"run"'])
            run=ex[2][1];tree.remove(ex)
            for i,values in enumerate(selected):
                tree.append(['func',['export',f'"case_{i}"'],['result','i32'],
                             ['call',run,*[['i32.const',str(v if v<2**31 else v-2**32)] for v in values]]])
            wat=out/f'{profile}-{index}.wat';binary=wat.with_suffix('.wasm')
            wat.write_text(wasm.emit(tree),encoding='utf-8')
            wasm.tool('wat2wasm',[wat,'-o',binary]);wasm.tool('wasm-validate',[binary])
            command=[str(wasm.WABT/'wasm-interp.exe'),str(binary),'--run-all-exports']
            try:
                r=subprocess.run(command,capture_output=True,text=True,timeout=30)
            except subprocess.TimeoutExpired:
                rows.append({'profile':profile,'file':a['file'],'status':'timeout'});continue
            log=out/f'{profile}-{index}.log';log.write_text(r.stdout+r.stderr,encoding='utf-8')
            values={int(i):int(v)&MASK for i,v in re.findall(r'case_(\d+)\(\) => i32:(-?\d+)',r.stdout)}
            if r.returncode or len(values)!=32:
                rows.append({'profile':profile,'file':a['file'],'status':'process-failed' if r.returncode else 'unparsed-or-trap','returncode':r.returncode,'observed':len(values)});continue
            comparisons=[{'args':v,'expected':reference(profile,a,v),'actual':values[i]} for i,v in enumerate(selected)]
            mismatches=sum(c['expected']!=c['actual'] for c in comparisons)
            rows.append({'profile':profile,'file':a['file'],'status':'mismatch' if mismatches else 'matched',
                         'cases':32,'mismatches':mismatches,'comparisons':comparisons})
    result={'wabt':wasm.tool('wasm-interp',['--version']).strip(),'artifacts':len(rows),
            'cases':sum(r.get('cases',0) for r in rows),'mismatches':sum(r.get('mismatches',0) for r in rows),
            'status_counts':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},
            'rows':rows,'original_binary_hashes':inventory,
            'sourceSHA256':sha(Path(__file__)),'note':'32 sampled inputs per binary, WABT interpreter vs independent Python arithmetic. Finite cross-engine check, not proof.'}
    (out/'cross-engine.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (out/'followup-audit.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','original_binary_hashes')},indent=2))
    if any(r['status']!='matched' for r in rows):raise SystemExit(1)

if __name__=='__main__':main()
