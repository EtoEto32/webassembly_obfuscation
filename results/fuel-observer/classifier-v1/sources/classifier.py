"""CART-like examples from attributed external data; no novel learning claim."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import random
import shutil
import subprocess
import zipfile
import transform as t

HERE=Path(__file__).resolve().parent
SEED=2026102414


def impurity(rows):
    counts=Counter(r['class'] for r in rows)
    return Fraction(len(rows))-sum(Fraction(c*c,len(rows)) for c in counts.values())


def train(rows,limit,depth=0):
    counts=Counter(r['class'] for r in rows);label=min(counts,key=lambda k:(-counts[k],k))
    if depth==limit or len(counts)==1:return {'class':label,'samples':len(rows)}
    choices=[]
    for f in range(4):
        for v in sorted(set(r['features'][f] for r in rows))[:-1]:
            a=[r for r in rows if r['features'][f]<=v];b=[r for r in rows if r['features'][f]>v]
            choices.append((impurity(a)+impurity(b),f,v,a,b))
    if not choices:return {'class':label,'samples':len(rows)}
    cost,f,v,a,b=min(choices,key=lambda x:x[:3])
    if cost>=impurity(rows):return {'class':label,'samples':len(rows)}
    return {'feature':f,'threshold':v,'left':train(a,limit,depth+1),'right':train(b,limit,depth+1)}


def predict(tree,word):
    depth=0
    while 'class' not in tree:
        feature=(word>>(8*tree['feature']))&255;depth+=1
        tree=tree['left' if feature<=tree['threshold'] else 'right']
    label=tree['class']
    # Each tested predicate costs 7 expressions + the if. Leaf: call3/set2/get1.
    return {'value':label,'events':[{'label':[200,label],'cost':8*depth+3}],'total':8*depth+6,'depth':depth}


def compile_tree(tree):
    if 'class' in tree:
        c=str(tree['class']);return [['call','0',['i32.const','200'],['i32.const',c]],['local.set','2',['i32.const',c]]]
    expr=['i32.le_u',['i32.and',['i32.shr_u',['local.get','0'],['i32.const',str(8*tree['feature'])]],['i32.const','255']],['i32.const',str(tree['threshold'])]]
    return [['if',expr,['then',*compile_tree(tree['left'])],['else',*compile_tree(tree['right'])]]]


def pack(features):return sum(x<<(8*i) for i,x in enumerate(features))


def boundaries(tree):
    if 'class' in tree:return []
    words=[]
    for v in (max(0,tree['threshold']-1),tree['threshold'],min(255,tree['threshold']+1)):
        f=[50]*4;f[tree['feature']]=v;words.append(pack(f))
    return words+boundaries(tree['left'])+boundaries(tree['right'])


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();rng=random.Random(SEED)
    for name in ('classifier.py','classifier.cjs','classifier-plan.md','transform.py','guard.cjs'):shutil.copy2(HERE/name,out/'sources'/name)
    shutil.copy2(t.ROOT/'research/connectivity-elimination/prototype.py',out/'sources/wat-helper.py')
    (out/'data').mkdir()
    for name in ('iris.zip','README.md'):shutil.copy2(HERE/'data'/name,out/'data'/name)
    try:
        raw=zipfile.ZipFile(HERE/'data/iris.zip').read('bezdekIris.data');labels=['Iris-setosa','Iris-versicolor','Iris-virginica']
        data=[]
        for i,line in enumerate(raw.decode().splitlines()):
            if not line:continue
            parts=line.split(',');features=[int(Fraction(s)*10) for s in parts[:4]]
            data.append({'index':i,'features':features,'class':labels.index(parts[4]),'secret':pack(features),'x':0})
        assert len(data)==150 and all(0<=x<256 for r in data for x in r['features'])
        training=[]
        for label in range(3):
            rows=[r for r in data if r['class']==label];rng.shuffle(rows);training.extend(r['index'] for r in rows[:35])
        (out/'data/dataset.json').write_text(json.dumps({'labels':labels,'trainingIndices':sorted(training),'data':data},indent=2),encoding='utf8')
        randoms=[rng.getrandbits(32) for _ in range(2048)];corners=[pack(f) for f in itertools.product((0,255),repeat=4)];records=[]
        for limit in (2,3,4,5):
            kind='iris-depth-'+str(limit);folder=out/kind;folder.mkdir();model=train([r for r in data if r['index'] in training],limit)
            (folder/'model.json').write_text(json.dumps(model,indent=2),encoding='utf8')
            module=['module',['type',['func',['param','i32','i32']]],['import','"env"','"mark"',['func',['type','0']]],['func',['param','i32','i32'],['result','i32'],['local','i32'],*compile_tree(model),['local.get','2']],['export','"run"',['func','1']]]
            (folder/'original.wat').write_text(t.w.emit(module),encoding='utf8');src=folder/'original.wasm';t.w.tool('wat2wasm',[folder/'original.wat','-o',src])
            report=t.transform(src,folder/'target.wasm',True)
            for stem in ('original','target'):
                t.w.tool('wasm-opt',[folder/(stem+'.wasm'),'-O3','-o',folder/(stem+'-O3.wasm')]);t.w.tool('wasm-validate',[folder/(stem+'-O3.wasm')])
            oracle=[{'secret':r['secret'],'x':0,'datasetIndex':r['index'],'holdout':r['index'] not in training,**predict(model,r['secret'])} for r in data]
            for word in corners+randoms+boundaries(model):oracle.append({'secret':word,'x':0,**predict(model,word)})
            (folder/'oracle.json').write_text(json.dumps(oracle,indent=2),encoding='utf8')
            hold=[r for r in data if r['index'] not in training]
            records.append({'kind':kind,'maxDepth':limit,'holdoutCorrect':sum(predict(model,r['secret'])['value']==r['class'] for r in hold),'holdoutN':len(hold),'paths':report['pathCount'],'rows':report['rowCount'],'whole':report['whole'],'sourceBytes':report['sourceBytes'],'targetBytes':report['targetBytes'],'optimizedBytes':(folder/'target-O3.wasm').stat().st_size,'sidecarBytes':(folder/'target.json').stat().st_size,'transformSeconds':report['seconds']})
        (out/'manifest.json').write_text(json.dumps({'seed':SEED,'records':records,'dataset':'UCI Iris, DOI10.24432/C56C76, bezdekIris.data','datasetSha256':hashlib.sha256(raw).hexdigest()},indent=2),encoding='utf8')
        cmd=['node',str(HERE/'classifier.cjs'),str(out)];r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
