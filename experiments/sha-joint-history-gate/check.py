import gzip
import hashlib
import importlib.util
import json
import platform
import re
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'sha256-research-baseline'
HELPER=HERE.parent/'sha-history-gate/check.py'
spec=importlib.util.spec_from_file_location('history',HELPER)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
MASK=2**32-1
vendor=(BASE/'vendor/sha256.js').read_text()
K=[int(x,16) for x in re.findall(r'0x[0-9A-Fa-f]+',vendor.split('var K = [')[1].split(']')[0])]
IV=[int(re.search(r'this\._'+c+r' = (0x[0-9a-f]+)',vendor)[1],16) for c in 'abcdefgh']


def small0(x): return old.rotr(x,7)^old.rotr(x,18)^(x>>3)
def small1(x): return old.rotr(x,17)^old.rotr(x,19)^(x>>10)
def big1(x): return old.rotr(x,6)^old.rotr(x,11)^old.rotr(x,25)
def choice(x,y,z): return z^(x&(y^z))


def eword(history,k):
    return (history[k]+history[k+4]-old.q(*history[k+1:k+4]))&MASK


def wword(history,index,k):
    # Recover W_(index-1-k); k <= 15 accesses at most history[23].
    e=[eword(history,k+j) for j in range(1,5)]
    return (history[k]-old.q(*history[k+1:k+4])-e[3]-big1(e[0])-choice(*e[:3])-K[index-1-k])&MASK


def observer(history,index):
    assert len(history)==24 and 24<=index<=64
    state=history[:4]+[eword(history,j) for j in range(4)]
    words=[wword(history,index,k) for k in reversed(range(16))]
    return state,words


def advance(history,index,mutate=False):
    # No input block, original working state, or W array is available here.
    a,b,c,d=[wword(history,index,k) for k in (1,6,14,15)]
    w=(small1(a)+b+small0(c)+d)&MASK
    if mutate and index==24: w^=1
    e=[eword(history,j) for j in range(4)]
    head=(e[3]+big1(e[0])+choice(*e[:3])+K[index]+w+old.q(*history[:3]))&MASK
    return [head]+history[:23]


def normal(block,initial):
    words=[int.from_bytes(block[j:j+4],'big') for j in range(0,64,4)]
    for i in range(16,64):
        words.append((small1(words[i-2])+words[i-7]+small0(words[i-15])+words[i-16])&MASK)
    states=[initial[:]]
    for i in range(64): states.append(old.reference(states[-1],(K[i]+words[i])&MASK))
    return states,words


def prologue(block,initial):
    # Separate prologue: retain only W0..23, then return A23..A0.
    words=[int.from_bytes(block[j:j+4],'big') for j in range(0,64,4)]
    state=initial[:];history=[]
    for i in range(24):
        if i>=16:
            words.append((small1(words[i-2])+words[i-7]+small0(words[i-15])+words[i-16])&MASK)
        state=old.reference(state,(K[i]+words[i])&MASK)
        history.insert(0,state[0])
    return history


def padded(message):
    result=message+b'\x80'
    result+=bytes((56-len(result)%64)%64)
    return result+(8*len(message)).to_bytes(8,'big')


def main():
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    index=json.loads((BASE/'artifacts/inputs.json').read_text())
    bundle=(BASE/'artifacts/inputs.bin').read_bytes()
    assert hashlib.sha256(bundle).hexdigest()==index['bundle_sha256']
    ids={'empty','abc','long-known'}|{'length-'+str(n) for n in [0,1,31,32,55,56,63,64,65,127,128,129,255,256]}|{'boundary-'+str(n) for n in [511,512,513]}
    randoms=[r for r in index['cases'] if r['id'].startswith('random-') and r['length']<=1024][:16]
    selected=[r for r in index['cases'] if r['id'] in ids]+randoms
    assert ids.issubset({r['id'] for r in selected})
    rows=[];checks=0;blocks=0;negatives=0;observations=[]
    for case in selected:
        message=bundle[case['offset']:case['offset']+case['length']]
        expected=hashlib.sha256(message).hexdigest()
        assert expected==case['expected']
        chain=IV[:];badchain=IV[:]
        data=padded(message)
        for offset in range(0,len(data),64):
            block=data[offset:offset+64]
            states,words=normal(block,chain)
            history=prologue(block,chain)
            bad=prologue(block,badchain)
            for i in range(24,65):
                recovered,window=observer(history,i)
                assert recovered==states[i]
                assert window==words[i-16:i]
                observations.append({'case':case['id'],'block':offset//64,'boundary':i,'history':history,
                                     'recovered_state':recovered,'recovered_W':window})
                checks+=1
                if i<64:
                    history=advance(history,i)
                    bad=advance(bad,i,True)
            final=history[:4]+[eword(history,j) for j in range(4)]
            chain=[(a+b)&MASK for a,b in zip(chain,final)]
            badfinal=bad[:4]+[eword(bad,j) for j in range(4)]
            badchain=[(a+b)&MASK for a,b in zip(badchain,badfinal)]
            blocks+=1
        digest=b''.join(x.to_bytes(4,'big') for x in chain).hex()
        baddigest=b''.join(x.to_bytes(4,'big') for x in badchain).hex()
        assert digest==expected
        negatives+=int(baddigest!=expected)
        rows.append({**case,'digest':digest,'mutated_digest':baddigest})
    assert negatives>0
    raw=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in observations).encode()
    (out/'observations.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0))
    (out/'cases.json').write_text(json.dumps(rows,indent=2)+'\n')
    dependencies=[HERE/'check.py',HERE/'protocol.json',HELPER,BASE/'vendor/sha256.js',BASE/'artifacts/inputs.json',BASE/'artifacts/inputs.bin']
    result={'python':platform.python_version(),'cases':len(rows),'blocks':blocks,'joint_state_recoveries':checks,
            'word_recoveries':24*checks,'full_hash_mismatches':0,'negative_hash_mismatches':negatives,
            'uncompressed_trace_sha256':hashlib.sha256(raw).hexdigest(),
            'source_hashes':{str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies},
            'artifact_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if 'hash' not in k or k.endswith('mismatches')},indent=2))


if __name__=='__main__': main()
