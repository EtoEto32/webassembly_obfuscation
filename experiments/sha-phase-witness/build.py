import difflib
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
BASE=HERE.parent/'sha256-research-baseline'
HELPER=HERE.parent/'sha-joint-history-gate/check.py'
OLD=HERE.parent/'sha-prefix-reachability/artifacts/cases.json'
spec=importlib.util.spec_from_file_location('joint',HELPER)
joint=importlib.util.module_from_spec(spec);spec.loader.exec_module(joint)
M=2**32-1


def prefix(target):
    state=joint.IV[:];words=[]
    for i,a_new in enumerate(reversed(joint.old.encode(target))):
        a,b,c,d,e,f,g,h=state
        u=(a_new-joint.old.q(a,b,c)-h-joint.big1(e)-joint.choice(e,f,g))&M
        words.append((u-joint.K[i])&M)
        state=joint.old.reference(state,u)
    assert state==target
    return words


def main():
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    prior=json.loads(OLD.read_text())
    a=next(r for r in prior if r['target']==[0]*8)
    message_a=bytes.fromhex(a['message'])+bytes(32)
    # T_K8(0,0,0,0,0,0,0,-K8)=zero.
    predecessor=[0]*7+[(-joint.K[8])&M]
    assert joint.old.reference(predecessor,joint.K[8])==[0]*8
    message_b=b''.join(w.to_bytes(4,'big') for w in prefix(predecessor))+bytes(32)
    rows=[]
    for name,message,boundary in [('at8',message_a,8),('at9',message_b,9)]:
        words=[int.from_bytes(message[i:i+4],'big') for i in range(0,64,4)]
        state=joint.IV[:];trace={}
        for i in range(10):
            state=joint.old.reference(state,(words[i]+joint.K[i])&M)
            if i+1 in (8,9,10): trace[str(i+1)]=state[:]
        assert trace[str(boundary)]==[0]*8 and words[boundary]==0
        rows.append({'id':name,'message':message.hex(),'boundary':boundary,'W':words[boundary],
                     'trace':trace,'digest':hashlib.sha256(message).hexdigest()})
    assert rows[0]['trace']['9']!=rows[1]['trace']['10']
    assert rows[0]['digest']!=rows[1]['digest']
    (out/'cases.json').write_text(json.dumps(rows,indent=2)+'\n')
    source=(BASE/'artifacts/plain.wat').read_text()
    marker='(local.set $j (i32.add (local.get $j) (i32.const 1)))'
    assert source.count(marker)==1
    captures=[]
    for boundary in (8,9,10):
        stores='\n'.join(f'(i32.store (i32.const {640+32*(boundary-8)+4*i}) (local.get ${c}))' for i,c in enumerate('abcdefgh'))
        captures.append(f'(if (i32.and (i32.eq (local.get $p) (i32.const 1024)) (i32.eq (local.get $j) (i32.const {boundary}))) (then {stores}))')
    after=source.replace(marker,marker+'\n'+'\n'.join(captures))
    (out/'before.wat').write_text(source)
    (out/'capture.wat').write_text(after)
    (out/'capture.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),after.splitlines(True),fromfile='before.wat',tofile='capture.wat')))
    wabt=REPO/'.tools/wabt-1.0.42/bin';opt=REPO/'.tools/binaryen-version_133/bin/wasm-opt.exe'
    commands=[[wabt/'wat2wasm.exe',out/'before.wat','-o',out/'before.wasm'],
              [wabt/'wat2wasm.exe',out/'capture.wat','-o',out/'capture.raw.wasm'],
              [opt,out/'capture.raw.wasm','-O2','-o',out/'capture.O2.wasm'],
              [wabt/'wasm2wat.exe',out/'capture.O2.wasm','-o',out/'capture.O2.wat']]
    commands += [[wabt/'wasm-validate.exe',out/n] for n in ['before.wasm','capture.raw.wasm','capture.O2.wasm']]
    commands += [[wabt/'wat2wasm.exe','--version'],[opt,'--version']]
    logs=[]
    for command in commands:
        r=subprocess.run(list(map(str,command)),capture_output=True,text=True,timeout=60)
        logs.append({'command':list(map(str,command)),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (out/'build-log.json').write_text(json.dumps(logs,indent=2)+'\n');r.check_returncode()
    assert (out/'before.wasm').read_bytes()==(BASE/'artifacts/plain.raw.wasm').read_bytes()
    sources=[HERE/'build.py',HERE/'verify.cjs',HERE/'protocol.json',HELPER,OLD,
             HERE.parent/'sha-history-gate/check.py',BASE/'vendor/sha256.js',BASE/'artifacts/plain.wat']
    report={'python':platform.python_version(),'K8':joint.K[8],'K9':joint.K[9],
            'inputs':{str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            'artifacts':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in out.iterdir() if p.is_file()}}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(rows),'K8':joint.K[8],'K9':joint.K[9],'out':str(out)}))


if __name__=='__main__':main()
