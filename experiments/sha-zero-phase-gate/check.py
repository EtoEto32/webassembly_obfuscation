import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
HELPER=HERE.parent/'sha-phase-capacity/check.py'
spec=importlib.util.spec_from_file_location('capacity',HELPER)
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
j=c.j

def decode(z,phase):
    s=z[:]
    for i in range(8,phase): s=j.old.reference(s,j.K[i])
    return s

def encode(s,phase):
    z=s[:]
    for i in reversed(range(8,phase)): z=c.inverse(z,j.K[i])
    return z

def main():
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for phase in [8,9]:
        z=[0]*8
        s=decode(z,phase)
        assert encode(s,phase)==z
        assert encode(j.old.reference(s,j.K[phase]),phase+1)==z
        words=c.witness.prefix(z)+[0]*8
        words[phase]=1
        msg=b''.join(w.to_bytes(4,'big') for w in words)
        states,schedule=j.normal(msg,j.IV)
        assert states[phase]==s and schedule[phase]==1
        znext=encode(states[phase+1],phase+1)
        digest=hashlib.sha256(msg).hexdigest()
        assert c.digest(msg)==digest
        rows.append({'phase':phase,'message':msg.hex(),'W':1,'z':z,'znext':znext,
                     'trace':{str(b):states[b] for b in [8,9,10]},'digest':digest})
    assert rows[0]['znext']==[0]*7+[1]
    assert rows[1]['znext']==[0]*6+[1,2**32-1]
    assert rows[0]['z']==rows[1]['z'] and rows[0]['znext']!=rows[1]['znext']
    (out/'cases.json').write_text(json.dumps(rows,indent=2)+'\n')
    result={'python':platform.python_version(),'messages':2,'zero_W_identity_controls':2,
            'python_digest_checks':2,'common_handler_counterexample':True}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    prior=HERE.parent/'sha-phase-witness/artifacts'
    inputs=[HERE/'check.py',HERE/'verify.cjs',HERE/'protocol.json',HELPER,c.HELPER,
            c.witness.HELPER,j.HELPER,c.witness.BASE/'vendor/sha256.js']
    inputs += [prior/n for n in ['before.wasm','capture.raw.wasm','capture.O2.wasm','manifest.json']]
    inputs += [out/'cases.json',out/'results.json']
    manifest={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__': main()
