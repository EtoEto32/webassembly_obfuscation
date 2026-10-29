import argparse,json,subprocess
from pathlib import Path
import prototype as p
import recover as r
from run import save,snapshot
def main(src,out):
    src=Path(src);out=Path(out);out.mkdir(parents=True,exist_ok=False);snapshot(out);records=[]
    for kernel in ('blend','chain','rolling'):
        raw=src/f'{kernel}16-shared-raw.wasm'
        for mode in ('all-features','reordered'):
            target=out/f'{kernel}-{mode}.wasm'
            if mode=='all-features':p.w.tool('wasm-opt',[raw,'--all-features','-O3','-o',target])
            else:
                tree=p.binaryen_tree(raw);tags=[x for x in tree[1:] if x[0]=='tag'];funcs=[x for x in tree[1:] if x[0]=='func']
                tree=['module',*[x for x in tree[1:] if x[0] not in ('tag','func')],*reversed(tags),*reversed(funcs)]
                p.compile(p.w.emit(tree),target)
            try:p.w.tool('wasm2wat',[target,'--enable-all','--fold-exprs']);wabt=dict(status='readable')
            except RuntimeError as ex:wabt=dict(status='tool_unsupported',error=str(ex))
            rec=out/f'{kernel}-{mode}-recovered.wasm';attack=r.recover(target,rec)
            records.append(dict(file=target.name,recovered=rec.name,source=str(raw.resolve()),mode=mode,wabt=wabt,attack=attack,sha256=p.digest(target),recovered_sha256=p.digest(rec)))
    save(out/'manifest.json',records)
    code=r'''const fs=require('fs'),path=require('path');const d=process.argv[1],rows=JSON.parse(fs.readFileSync(path.join(d,'manifest.json')));const load=f=>{const b=fs.readFileSync(f);if(!WebAssembly.validate(b))throw Error('Invalid binary');return new WebAssembly.Instance(new WebAssembly.Module(b)).exports.run;};let seed=0x512312ef;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;};let calls=0,errors=0;for(const row of rows){const a=load(row.source),b=load(path.join(d,row.file)),c=load(path.join(d,row.recovered));for(let i=0;i<512;i++){const x=[rnd(),rnd(),rnd()];const values=[a(...x),b(...x),c(...x)];calls+=3;if(values.some(v=>v!==values[0]))errors++;}}console.log(JSON.stringify({calls,errors}));if(errors)process.exitCode=1;'''
    result=subprocess.run(['node','-e',code,str(out)],capture_output=True,text=True,check=True,timeout=60);save(out/'correctness.json',json.loads(result.stdout))
    save(out/'summary.json',dict(status='completed',targets=len(records),wabt_unsupported=sum(x['wabt']['status']=='tool_unsupported' for x in records),recoveries=len(records)))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');v=a.parse_args();main(v.input,v.output)
