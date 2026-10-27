"""Independent direct-recipe byte oracle vs generated JS and local file I/O."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import fence

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('effect_plan',HERE/'effect-plan.py')
compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

WIT='''package research:audit;
interface storage {
 resource file;
 record pair { source-file: borrow<file>, target-file: borrow<file>, }
 record group { initial: borrow<file>, copies: list<pair>, backup: option<borrow<file>>, }
 variant request { chain(group), matrix(list<list<pair>>), optional(option<pair>), }
 prepare: func(value: request) -> u32;
}
world plugin { import storage; }
'''

def recipe(seed):
    r=random.Random(seed);literal=r.choice(['','x\x00z','日本語\n','line\n'+str(seed)])
    pair=[{'read':'$item.source-file','as':'local'},
          {'write':'$item.target-file','from':'local'}]
    # Same path remains read-only or write-only; aliases may still share objects.
    if r.getrandbits(1):pair.insert(1,{'write':'$item.target-file','from':'initial'})
    body=[{'read':'$value.initial','as':'initial'},
          {'for':'$value.copies','as':'item','body':pair},
          {'ifSome':'$value.backup','as':'backup','body':[{'write':'$backup','from':'initial'},
             {'write':'$backup','literal':literal}]}]
    return {'chain':body,
      'matrix':[{'for':'$value','as':'row','body':[{'for':'$row','as':'item','body':[
        {'read':'$item.source-file','as':'data'},{'write':'$item.target-file','from':'data'}]}]}],
      'optional':[{'ifSome':'$value','as':'item','body':[
        {'read':'$item.source-file','as':'data'},{'write':'$item.target-file','from':'data'}]}]}

def direct(recipes,value,initial):
    state=list(initial);counts={'reads':0,'writes':0}
    def resolve(text,env):
        parts=text[1:].split('.');v=env[parts[0]]
        for p in parts[1:]:
            words=p.split('-');v=v[words[0]+''.join(w.title() for w in words[1:])]
        return v
    def run(block,env,values):
        for op in block:
            if 'read' in op:
                values[op['as']]=bytes(state[resolve(op['read'],env)]);counts['reads']+=1
            elif 'write' in op:
                data=op['literal'].encode('utf8') if 'literal' in op else values[op['from']]
                state[resolve(op['write'],env)]=data;counts['writes']+=1
            else:
                kind='for' if 'for' in op else 'ifSome';target=resolve(op[kind],env)
                items=target if kind=='for' else ([] if target is None else [target])
                for item in items:run(op['body'],{**env,op['as']:item},values.copy())
    run(recipes[value['tag']],{'value':value['val']},{})
    return {'files':[x.hex() for x in state],**counts}

def inputs(seed):
    r=random.Random(seed)
    pair=lambda:{'sourceFile':r.randrange(3),'targetFile':r.randrange(3)}
    rows=[]
    for i in range(48):
        if i%3==0:v={'tag':'chain','val':{'initial':r.randrange(3),'copies':[pair() for _ in range(i%7)],'backup':None if i%2 else r.randrange(3)}}
        elif i%3==1:v={'tag':'matrix','val':[[pair() for _ in range(r.randrange(5))] for _ in range(i%5)]}
        else:v={'tag':'optional','val':pair() if i%2 else None}
        raw=[b'',bytes(range(256)),bytes([0xff,0x00,0xc3,0x28]),'日本語'.encode(),bytes([i])*16384]
        initial=[raw[r.randrange(len(raw))] for _ in range(3)]
        rows.append((v,initial))
    return rows

def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('effect-compiler-audit.py','effect-compiler-audit.cjs','effect-compiler-audit-plan.md','effect-plan.py','effect-engine.cjs','fence.py','fence-runtime.cjs'):
        shutil.copy2(HERE/name,out/'sources'/name)
    (out/'schema.wit').write_text(WIT,encoding='utf8')
    command=['node',str(fence.JCO),'embed','--wit',str(out/'schema.wit'),'--world-name','plugin','--dummy','-o',str(out/'wit-validated.wasm')]
    validation=subprocess.run(command,capture_output=True,text=True,timeout=60)
    (out/'validation.json').write_text(json.dumps({'command':command,'returncode':validation.returncode,'stdout':validation.stdout,'stderr':validation.stderr},indent=2))
    assert validation.returncode==0,validation.stderr
    model=fence.Reader(WIT).parse();cases=[];compile_negatives=[]
    for seed in range(2026102400,2026102412):
        recipes=recipe(seed);code,policy=compiler.compile_recipe(model,recipes);module=str(seed)+'.cjs'
        (out/module).write_text(code,encoding='utf8')
        (out/(str(seed)+'.recipe.json')).write_text(json.dumps(recipes,ensure_ascii=False,indent=2),encoding='utf8')
        for v,initial in inputs(seed):cases.append({'module':module,'value':v,'initial':[x.hex() for x in initial],'expected':direct(recipes,v,initial)})
        bad=copy.deepcopy(recipes);bad['chain'].append({'write':'$value.backup','from':'local'})
        # Type-correct endpoint but loop-local read must not escape scope.
        bad['chain'][-1]={'ifSome':'$value.backup','as':'last','body':[{'write':'$last','from':'local'}]}
        try:compiler.compile_recipe(model,bad)
        except ValueError as e:compile_negatives.append({'seed':seed,'reason':str(e)})
        else:raise AssertionError('out-of-scope read accepted')
    (out/'cases.json').write_text(json.dumps(cases,separators=(',',':')),encoding='utf8')
    (out/'compile-negatives.json').write_text(json.dumps(compile_negatives,indent=2),encoding='utf8')
    try:
        r=subprocess.run(['node',str(HERE/'effect-compiler-audit.cjs'),str(out)],capture_output=True,text=True,timeout=60)
        (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
        assert r.returncode==0,r.stderr;print(r.stdout)
    finally:(out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
