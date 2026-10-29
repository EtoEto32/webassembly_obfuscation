"""Compile a tiny typed effect recipe; permissions are determined by opcodes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import fence

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compile_recipe(model,recipes):
    f=model['function'];root=model['types'][f['type'][1]]
    if root['kind']!='variant' or set(recipes)!={k for k,t in root['fields']}:raise ValueError('exact top-level variant coverage required')
    lines=[];permissions={};serial=[0]
    def fresh():serial[0]+=1;return 'r'+str(serial[0])
    def path(s,env):
        if not isinstance(s,str) or not re.fullmatch(r'\$[a-z]+(?:\.[a-z][a-z0-9-]*)*',s):raise ValueError('resource path syntax')
        parts=s[1:].split('.')
        if parts[0] not in env:raise ValueError('unknown path variable')
        ty,expr,p=env[parts[0]]
        for key in parts[1:]:
            if ty[0]!='ref' or model['types'].get(ty[1],{}).get('kind')!='record':raise ValueError('field on non-record')
            fields=dict(model['types'][ty[1]]['fields'])
            if key not in fields:raise ValueError('unknown field')
            words=key.split('-');js=words[0]+''.join(w[:1].upper()+w[1:] for w in words[1:])
            ty=fields[key];expr+='['+json.dumps(js)+']';p+='/'+key
        return ty,expr,p
    def block(ops,env,registers,depth=0):
        if depth>16 or not isinstance(ops,list) or len(ops)>128:raise ValueError('recipe shape/bound')
        for op in ops:
            if not isinstance(op,dict):raise ValueError('operation object required')
            kind=next((k for k in ('read','write','for','ifSome') if k in op),None)
            if kind is None:raise ValueError('unknown opcode')
            ty,expr,p=path(op[kind],env)
            if kind in ('read','write'):
                if ty[0]!='borrow' or model['types'].get(ty[1][1],{}).get('kind')!='resource':raise ValueError('resource endpoint required')
                if p in permissions and permissions[p]!=kind:raise ValueError('multi-permission leaf outside this compiler subset')
                permissions[p]=kind
                if kind=='read':
                    if set(op)!={'read','as'} or not isinstance(op['as'],str) or op['as'] in registers:raise ValueError('read result binding')
                    variable=fresh();registers[op['as']]=variable
                    lines.append('const '+variable+'=ops.length; ops.push({op:"read",file:'+expr+'});')
                else:
                    if set(op)=={'write','literal'} and isinstance(op['literal'],str) and len(op['literal'].encode())<=16384:
                        value='literal:'+json.dumps(op['literal'])
                    elif set(op)=={'write','from'} and isinstance(op['from'],str) and op['from'] in registers:value='from:'+registers[op['from']]
                    else:raise ValueError('write operand or forbidden attribute')
                    lines.append('ops.push({op:"write",file:'+expr+','+value+'});')
                lines.append('if(ops.length>8192)throw Error("effect plan bound");')
            else:
                if set(op)!={kind,'as','body'} or not re.fullmatch('[a-z]+',str(op['as'])) or op['as'] in env:raise ValueError('iteration binding')
                required='list' if kind=='for' else 'option'
                if ty[0]!=required:raise ValueError('wrong iteration type')
                if kind=='ifSome' and ty[1][0]=='option':raise ValueError('nested option recipe outside this subset')
                variable=fresh();new={**env,op['as']:(ty[1],variable,p+('/*' if kind=='for' else '/?'))}
                if kind=='for':lines.append('for(const '+variable+' of '+expr+'){')
                else:lines.append('if('+expr+'!==undefined){ const '+variable+'='+expr+';')
                block(op['body'],new,registers.copy(),depth+1);lines.append('}')
    for key,ty in root['fields']:
        lines.append('case '+json.dumps(key)+': {')
        block(recipes[key],{'value':(ty,'value.val',f['argument']+'/@'+key)} if ty else {},{})
        lines.append('break; }')
    policy={'interface':model['interface'],'function':f['name'],'argument':f['argument'],'permissions':permissions}
    shape=fence.generate(model,policy,'jco-host')
    code=shape+'''
const validateShape=exports.project;
exports.build=function(value){
 validateShape(value,()=>({slot:0,generation:0}));
 const ops=[];switch(value.tag){
'''+ '\n'.join(lines)+'''
 default:throw Error('unknown recipe variant');}
 return ops;
};
'''
    return code,policy

def main(source,out):
    hashes=json.loads((source/'sha256.json').read_text())
    for relative,digest in hashes.items():assert sha(source/relative)==digest
    assert sha(HERE/'fence.wit')==sha(source/'sources/fence.wit'),'component fixture and recipe schema differ'
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('effect-plan.py','effect-engine.cjs','effect-plan.cjs','effect-plan-plan.md','effect-recipes.json','fence-runtime.cjs','fence.py','fence.wit'):
        shutil.copy2(HERE/name,out/'sources'/name)
    model=fence.Reader((HERE/'fence.wit').read_text()).parse();recipes=json.loads((HERE/'effect-recipes.json').read_text())
    code,policy=compile_recipe(model,recipes);(out/'builder.cjs').write_text(code,encoding='utf8')
    (out/'derived-policy.json').write_text(json.dumps(policy,indent=2),encoding='utf8')
    mutants=[]
    for name in ('unknown-op','undefined-read','unknown-path','permission-override','missing-case','async-attribute'):
        bad=copy.deepcopy(recipes)
        if name=='unknown-op':bad['write']=[{'send':'$value'}]
        if name=='undefined-read':bad['copy'][1]['from']='absent'
        if name=='unknown-path':bad['copy'][1]['write']='$value.missing'
        if name=='permission-override':bad['write'][0]['permission']='read'
        if name=='missing-case':bad.pop('idle')
        if name=='async-attribute':bad['write'][0]['await']=True
        try:compile_recipe(model,bad)
        except ValueError as e:mutants.append({'name':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError(name)
    (out/'compile.json').write_text(json.dumps({'builderBytes':len(code.encode()),'rejectedRecipes':mutants},indent=2),encoding='utf8')
    (out/'source.json').write_text(json.dumps({'path':str(source),'hashes':hashes},indent=2),encoding='utf8')
    try:
        r=subprocess.run(['node',str(HERE/'effect-plan.cjs'),str(source),str(out)],capture_output=True,text=True,timeout=60)
        (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
        assert r.returncode==0,r.stderr;print(r.stdout)
    finally:(out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
