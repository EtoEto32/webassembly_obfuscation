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
M=(1<<32)-1

def input_offset(p):
    e=[(p[k]+p[k+4]-j.old.q(*p[k+1:k+4]))&M for k in range(4)]
    return (e[3]+j.big1(e[0])+j.choice(*e[:3])+j.old.q(*p[:3]))&M

def input_encode(p,u): return (input_offset(p)+u)&M
def input_decode(p,v): return (v-input_offset(p))&M
def shift(p,v): return [v]+p[:7]

def main():
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    protocol=json.loads((HERE/'protocol.json').read_text())
    rows=[]; messages=[]
    for state in [[0]*8,[0]*7+[1]]:
        p=j.old.encode(state)
        for u in protocol['inputs_u']:
            v=input_encode(p,u); after=shift(p,v)
            expected=j.old.reference(state,u)
            assert j.old.decode(after)==expected
            assert after==j.old.history_step(p,u)
            assert input_decode(p,v)==u
            rows.append({'state':state,'p':p,'u':u,'v':v,'after':after,'normal_next':expected})
        words=c.witness.prefix(state)+[0]*8
        message=b''.join(w.to_bytes(4,'big') for w in words)
        states,schedule=j.normal(message,j.IV)
        assert states[8]==state and schedule[8]==0
        digest=hashlib.sha256(message).hexdigest();assert c.digest(message)==digest
        messages.append({'message':message.hex(),'state8':state,'W8':0,
                         'v8':input_encode(p,j.K[8]),'digest':digest})
    assert messages[0]['v8']!=messages[1]['v8']
    assert (messages[1]['v8']-messages[0]['v8'])&M==1
    result={'python':platform.python_version(),'local_checks':len(rows),'python_full_digest_checks':2,
            'same_i_W_different_v':True,'Wasm_executed':False,
            'decision':'input encoder retains state dependency and existing nonlinear recurrence; not adopted'}
    for name,value in [('cases.json',{'local':rows,'messages':messages}),('results.json',result)]:
        (out/name).write_text(json.dumps(value,indent=2)+'\n')
    files=[HERE/'audit.py',HERE/'protocol.json',HELPER,c.HELPER,c.witness.HELPER,j.HELPER,
           c.witness.BASE/'vendor/sha256.js',out/'cases.json',out/'results.json']
    manifest={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
