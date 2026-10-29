"""Minimal arithmetic-only diagnostics. No memory, imports, or security impact claim."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from oracle import ROOT,w,Program,Unsupported
HERE=Path(__file__).resolve().parent
def main(out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'minimal.py');shutil.copy2(HERE/'oracle.py',out/'oracle.py');files=[]
    for bits in (8,16,32,64):
        wat=f'''(module (func (export "run") (param i32) (result i32)
          (i32x4.extract_lane 0 (i{bits}x{128//bits}.relaxed_laneselect
            (v128.const i32x4 255 255 255 255) (v128.const i32x4 0 0 0 0)
            (i32x4.splat (local.get 0))))))'''
        p=out/f'lane{bits}.wat';p.write_text(wat);dst=p.with_suffix('.wasm');w.tool('wat2wasm',[p,'--enable-all','-o',dst]);files.append(dst.name)
    req=dict(directory=str(out),files=files,inputs=[[0],[128],[0x80808080],[0xffffffff]])
    (out/'request.json').write_text(json.dumps(req));shutil.copy2(HERE/'node.cjs',out/'node.cjs')
    cp=subprocess.run(['node',str(out/'node.cjs'),str(out/'request.json')],capture_output=True,text=True,timeout=30);cp.check_returncode();node=json.loads(cp.stdout);(out/'node.json').write_text(json.dumps(node,indent=2))
    shell="""var q=JSON.parse(read(scriptArgs[0])),rows=[];for(var f of q.files){var e=new WebAssembly.Instance(new WebAssembly.Module(read(q.directory+'/'+f,'binary'))).exports;for(var a of q.inputs){rows.push({file:f,inputs:a,outputs:[e.run(...a)>>>0]});}}print(JSON.stringify(rows));"""
    (out/'shell.js').write_text(shell);data=[]
    for compiler in ('baseline','ion','baseline+ion'):
        cp=subprocess.run([str(ROOT/'.tools/spidermonkey-150.0.1/js.exe'),'--wasm-compiler='+compiler,str(out/'shell.js'),str(out/'request.json')],capture_output=True,text=True,timeout=30)
        data.append(dict(compiler=compiler,code=cp.returncode,stderr=cp.stderr,rows=json.loads(cp.stdout) if cp.returncode==0 else [],stdout=cp.stdout if cp.returncode else ''))
    (out/'spidermonkey.json').write_text(json.dumps(data,indent=2))
    checks=[]
    for d in data:
        for r in d['rows']:
            if r['file']=='lane16.wasm':continue
            for policy in ('core-two','byte-compatible'):
                for mode in ('joint','pointwise'):
                    checks.append(dict(compiler=d['compiler'],file=r['file'],inputs=r['inputs'],outputs=r['outputs'],policy=policy,mode=mode,**Program(out/r['file'],policy).check(r['inputs'],r['outputs'],mode)))
    (out/'checks.json').write_text(json.dumps(checks,indent=2))
    summary=dict(bytes={f:(out/f).stat().st_size for f in files},mask128={d['compiler']:{r['file']:r['outputs'] for r in d['rows'] if r['inputs']==[128]} for d in data},nodeMask128={r['file']:r['outputs'] for r in node['rows'] if r['inputs']==[128]},note='core-two literal formula versus byte-compatible historical lowering; not an engine vulnerability finding')
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
    (out/'manifest.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='manifest.json'},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args();main(a.out.resolve())
