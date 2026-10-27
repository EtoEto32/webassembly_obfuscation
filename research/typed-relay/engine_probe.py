"""Reduce the independent-interpreter discrepancy; record, do not hide, failures."""
import argparse
import json
from pathlib import Path
import subprocess
import prototype as p


def invoke(args,timeout=2):
    try:
        r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout)
        return dict(status='completed' if r.returncode==0 else 'tool_error',returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    except subprocess.TimeoutExpired:
        return dict(status='timeout',timeout_seconds=timeout)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    records=[]
    for mode in ['plain','direct_ref','tail_ref','call_relay','tail_relay']:
        if mode=='plain':text='(module (func (export "run") (result i32) (i32.add (i32.const 7) (i32.const 11))))'
        else:
            wrapper='' if mode in ('direct_ref','tail_ref') else '''(func $relay (param i32 i32 (ref $op)) (result i32)
              ('''+('return_call_ref' if mode=='tail_relay' else 'call_ref')+''' $op (local.get 0) (local.get 1) (local.get 2)))'''
            call=('return_call_ref $op' if mode=='tail_ref' else 'call_ref $op') if not wrapper else 'call $relay'
            text='''(module (type $op (func (param i32 i32) (result i32)))
                (func $add (type $op) (param i32 i32) (result i32) (i32.add (local.get 0) (local.get 1)))
                '''+wrapper+'''(func (export "run") (result i32) ('''+call+''' (i32.const 7) (i32.const 11) (ref.func $add)))
                (elem declare func $add))'''
        binary=a.output/(mode+'.wasm');p.compile_wat(text,binary)
        script=a.output/(mode+'.wast');script.write_text(text+'\n(assert_return (invoke "run") (i32.const 18))\n',encoding='utf-8')
        node=invoke(['node','-e','const f=require("fs"); console.log(new WebAssembly.Instance(new WebAssembly.Module(f.readFileSync(process.argv[1]))).exports.run());',binary])
        wabt=invoke([p.w.WABT/'wasm-interp.exe',binary,*p.FLAGS,'--run-all-exports'])
        binaryen=invoke([p.w.BINARYEN/'wasm-shell.exe',script])
        records.append(dict(mode=mode,expected=18,node=node,wabt=wabt,binaryen=binaryen))
    for mode in ['live_operand','locals','nested']:
        header='''(module (type $op (func (param i32 i32) (result i32)))
            (func $add (type $op) (param i32 i32) (result i32) (i32.add (local.get 0) (local.get 1)))
            (func $relay (param i32 i32 (ref $op)) (result i32)
              (return_call_ref $op (local.get 0) (local.get 1) (local.get 2)))'''
        c='(call $relay (i32.const 7) (i32.const 11) (ref.func $add))'
        if mode=='live_operand':b='(i32.add (i32.const 99) '+c+')';expected=117
        elif mode=='locals':b='(local i32 i32) (local.set 1 (i32.const 99)) (i32.add '+c+' (local.get 1))';expected=117
        else:b='(call $relay (i32.const 99) '+c+' (ref.func $add))';expected=117
        text=header+'(func (export "run") (result i32) '+b+') (elem declare func $add))'
        binary=a.output/(mode+'.wasm');p.compile_wat(text,binary)
        script=a.output/(mode+'.wast');script.write_text(text+'\n(assert_return (invoke "run") (i32.const 117))\n',encoding='utf-8')
        node=invoke(['node','-e','const f=require("fs"); console.log(new WebAssembly.Instance(new WebAssembly.Module(f.readFileSync(process.argv[1]))).exports.run());',binary])
        wabt=invoke([p.w.WABT/'wasm-interp.exe',binary,*p.FLAGS,'--run-all-exports'])
        binaryen=invoke([p.w.BINARYEN/'wasm-shell.exe',script])
        records.append(dict(mode=mode,expected=expected,node=node,wabt=wabt,binaryen=binaryen))
    (a.output/'results.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(records))


if __name__=='__main__':main()
