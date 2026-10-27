"""Compile a deliberately small WIT subset plus explicit effect policy to JS.

Official WIT validation is performed first with local Jco. Resource values in
the test adapter are already-lifted host slot/generation records, not raw
Canonical ABI borrow indices. This is not a complete WIT binding generator.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
JCO=ROOT/'.tools/component-resource/node_modules/@bytecodealliance/jco/dist/jco.js'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class Reader:
    def __init__(self,source):
        source=re.sub(r'//[^\n]*','',source)
        self.tokens=[];position=0
        for m in re.finditer(r'->|[A-Za-z][A-Za-z0-9-]*|[{}()<>:,;]',source):
            if source[position:m.start()].strip():raise ValueError('unsupported WIT lexical syntax')
            self.tokens.append(m.group());position=m.end()
        if source[position:].strip():raise ValueError('unsupported WIT trailing syntax')
        self.i=0;self.types={}
    def pop(self,expected=None):
        if self.i==len(self.tokens):raise ValueError('unexpected WIT EOF')
        t=self.tokens[self.i];self.i+=1
        if expected is not None and t!=expected:raise ValueError('expected '+expected+', got '+t)
        return t
    def peek(self):return self.tokens[self.i] if self.i<len(self.tokens) else None
    def typ(self):
        name=self.pop()
        if name in ('borrow','option','list'):
            self.pop('<');child=self.typ();self.pop('>');return [name,child]
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*',name):raise ValueError('type expected')
        return ['ref',name]
    def parse(self):
        self.pop('package');self.pop();self.pop(':');self.pop();self.pop(';')
        self.pop('interface');interface=self.pop();self.pop('{');function=None
        while self.peek()!='}':
            kind=self.pop();name=self.pop()
            if kind=='resource':
                self.pop(';');node={'kind':'resource'}
            elif kind in ('record','variant'):
                self.pop('{');fields=[]
                while self.peek()!='}':
                    field=self.pop()
                    if kind=='record':self.pop(':');ty=self.typ()
                    elif self.peek()=='(':self.pop('(');ty=self.typ();self.pop(')')
                    else:ty=None
                    fields.append([field,ty])
                    if self.peek()!=',':break
                    self.pop(',')
                self.pop('}');node={'kind':kind,'fields':fields}
                if len({f for f,t in fields})!=len(fields):raise ValueError('duplicate field')
            else:
                # In this grammar the already-popped tokens are function-name :
                if name!=':' or function is not None:raise ValueError('unsupported WIT declaration')
                self.pop('func');self.pop('(');arg=self.pop();self.pop(':');ty=self.typ();self.pop(')');self.pop('->');self.pop('u32');self.pop(';')
                function={'name':kind,'argument':arg,'type':ty};continue
            if name in self.types:raise ValueError('duplicate type')
            self.types[name]=node
        self.pop('}');self.pop('world');world=self.pop();self.pop('{');self.pop('import');self.pop(interface);self.pop(';');self.pop('}')
        if self.peek() is not None or function is None:raise ValueError('unsupported trailing declaration')
        return {'interface':interface,'world':world,'function':function,'types':self.types}

def generate(model,policy):
    f=model['function']
    if any(policy[k]!=v for k,v in [('interface',model['interface']),('function',f['name']),('argument',f['argument'])]):
        raise ValueError('policy entry mismatch')
    rules=policy['permissions'];used=set();lines=[];counter=[0]
    def fresh():counter[0]+=1;return 'x'+str(counter[0])
    def emit(ty,expr,path,stack=()):
        tag,name=ty
        if tag=='borrow':
            if name[0]!='ref' or model['types'].get(name[1],{}).get('kind')!='resource':raise ValueError('borrow target is not a resource')
            permission=rules.get(path)
            if permission not in ('read','write'):raise ValueError('missing/invalid effect at '+path)
            used.add(path);lines.append('resource('+expr+','+json.dumps(permission)+',deps);');return
        if tag=='option':
            lines.append('if ('+expr+' !== null) {');emit(name,expr,path+'/?',stack);lines.append('}');return
        if tag=='list':
            variable=fresh();lines.append('if (!Array.isArray('+expr+') || '+expr+'.length > 4096) throw Error("list shape/bound");')
            lines.append('for (const '+variable+' of '+expr+') {');emit(name,variable,path+'/*',stack);lines.append('}');return
        if tag!='ref' or name in stack:raise ValueError('unsupported/cyclic type')
        if name=='u32':lines.append('u32('+expr+');');return
        node=model['types'].get(name)
        if node is None:raise ValueError('unknown type '+name)
        if node['kind']=='record':
            lines.append('record('+expr+','+json.dumps([n for n,t in node['fields']])+');')
            for key,t in node['fields']:emit(t,expr+'['+json.dumps(key)+']',path+'/'+key,stack+(name,))
        elif node['kind']=='variant':
            lines.append('variant('+expr+'); switch ('+expr+'.tag) {')
            for key,t in node['fields']:
                lines.append('case '+json.dumps(key)+': {')
                if t is not None:emit(t,expr+'.val',path+'/@'+key,stack+(name,))
                else:lines.append('if (Object.hasOwn('+expr+',"val")) throw Error("payload on empty case");')
                lines.append('break; }')
            lines.append('default: throw Error("unknown variant"); }')
        else:raise ValueError('owned resources are outside this prototype')
    emit(f['type'],'value',f['argument'])
    if used!=set(rules):raise ValueError('unused policy path: '+str(sorted(set(rules)-used)))
    prelude='''"use strict";
function u32(x){if(!Number.isInteger(x)||x<0||x>4294967295)throw Error("u32");}
function record(x,keys){if(!x||typeof x!=="object"||Array.isArray(x)||Object.keys(x).length!==keys.length||keys.some(k=>!Object.hasOwn(x,k)))throw Error("record shape");}
function variant(x){if(!x||typeof x!=="object"||Array.isArray(x)||typeof x.tag!=="string"||Object.keys(x).some(k=>k!=="tag"&&k!=="val"))throw Error("variant shape");}
function resource(x,permission,deps){record(x,["slot","generation"]);u32(x.slot);u32(x.generation);deps.push({slot:x.slot,generation:x.generation,permission});}
exports.project=function(value){const deps=[];
'''
    return prelude+'\n'.join(lines)+'\nreturn deps;};\n'

def main(wit,policy_path,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for p in (wit,policy_path,HERE/'fence.py',HERE/'fence.cjs',HERE/'fence-plan.md'):shutil.copy2(p,out/'sources'/p.name)
    cmd=['node',str(JCO),'embed','--wit',str(wit),'--world-name','plugin','--dummy','-o',str(out/'wit-validated-dummy.wasm')]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
    (out/'wit-validation.json').write_text(json.dumps({'command':cmd,'status':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    start=time.perf_counter();model=Reader(wit.read_text(encoding='utf8')).parse();policy=json.loads(policy_path.read_text());generated=generate(model,policy);elapsed=time.perf_counter()-start
    (out/'project.cjs').write_text(generated,encoding='utf8');(out/'model.json').write_text(json.dumps(model,indent=2),encoding='utf8')
    negatives=[]
    for name,bad in [('missing',{'permissions':{k:v for k,v in policy['permissions'].items() if k!='value/@read'}}),
                     ('typo',{'permissions':{**policy['permissions'],'value/@reed':'read'}}),
                     ('permission',{'permissions':{**policy['permissions'],'value/@read':'execute'}})]:
        try:generate(model,{**policy,**bad})
        except ValueError as e:negatives.append({'name':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError('bad policy accepted')
    (out/'generation.json').write_text(json.dumps({'milliseconds':elapsed*1000,'generatedBytes':len(generated.encode()),'witSha256':sha(wit),'policySha256':sha(policy_path),'negativePolicies':negatives},indent=2),encoding='utf8')
    r=subprocess.run(['node',str(HERE/'fence.cjs'),str(out)],capture_output=True,text=True,timeout=60)
    (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('wit',type=Path);ap.add_argument('policy',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();main(a.wit.resolve(),a.policy.resolve(),a.output.resolve())
