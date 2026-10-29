"""Component resource lifecycle as computation trigger. Experimental, no novelty claim."""
import argparse, copy, importlib.util, json, random, struct, subprocess, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('resource_common',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
w=q.w;MASK=0xffffffff
JCO=ROOT/'.tools/component-resource/node_modules/@bytecodealliance/jco/dist/jco.js'
OPS={'add','sub','mul','xor','and','or','rotl','rotr','shl','shr_u','shr_s'}
STEPS=['add','xor','mul','rotl']
class Unsupported(ValueError):pass
def c(x):return ['i32.const',str(x&MASK)]
def g(x):return ['local.get',str(x)]
def jco(*args):
    r=subprocess.run(['node',str(JCO),*map(str,args)],capture_output=True,text=True,timeout=90)
    if r.returncode:raise RuntimeError(r.stderr+r.stdout)
    return r.stdout
def mod(expr):return ['module',['func',['export','"run"'],['param','i32','i32'],['result','i32'],expr]]
def source(src):
    m=q.read(src)
    if any(e[0] not in ('type','func','export') for e in m[1:]):raise Unsupported('pure module only')
    fs=[e for e in m[1:] if e[0]=='func'];ex=[e for e in m[1:] if e[0]=='export']
    if len(fs)!=1 or ex!=[['export','"run"',['func','0']]]:raise Unsupported('one run export')
    f=fs[0];ty=lambda name:[t for e in f[1:] if e[0]==name for t in e[1:]]
    if ty('param')!=['i32','i32'] or ty('result')!=['i32'] or any(t!='i32' for t in ty('local')):raise Unsupported('i32 ABI')
    env={0:g(0),1:g(1),**{i+2:c(0) for i in range(len(ty('local')))}}
    def walk(e):
        op=e[0]
        if op=='local.get':return env[int(e[1])]
        if op=='i32.const':return c(int(e[1],0))
        if op in ('local.set','local.tee'):
            v=walk(e[2]);env[int(e[1])]=v;return v if op=='local.tee' else None
        if op.startswith('i32.') and op[4:] in OPS:return [op,*map(walk,e[1:])]
        raise Unsupported('source op '+op)
    stack=[]
    for e in f[1:]:
        if e[0] not in ('type','param','result','local'):
            v=walk(e)
            if v is not None:stack.append(v)
    if len(stack)!=1:raise Unsupported('one expression')
    return stack[0]
def chain(expr):
    def hasx(e):return e==g(0) or any(hasx(t) for t in e[1:] if isinstance(t,list))
    steps=[];e=expr
    while e!=g(0):
        if len(e)!=3 or e[0] not in ['i32.'+o for o in STEPS]:raise Unsupported('left state chain')
        a,b=e[1:]
        if e[0] in ('i32.add','i32.xor','i32.mul') and not hasx(a) and hasx(b):a,b=b,a
        if hasx(b):raise Unsupported('payload depends on x')
        steps.append((e[0][4:],b));e=a
    if not 1<=len(steps)<=128:raise Unsupported('1..128 steps')
    return list(reversed(steps))
def transform(src,dst,mode='deferred',seed=37,broken=False):
    if mode not in ('plain','direct','immediate','deferred'):raise Unsupported('mode')
    start=time.perf_counter();expr=source(src);steps=chain(expr);afterread=time.perf_counter()
    if mode=='plain':
        out='(component (core '+w.emit(mod(expr))[1:]+' (core instance (instantiate 0)) (func (export "run") (param "x" u32) (param "y" u32) (result u32) (canon lift (core func 0 "run"))))'
    else:
        rng=random.Random(seed);names=['"e'+str(x)+'"' for x in rng.sample(range(100,1000),7)]
        funcs=[['func',['export',names[0]],['param','i32'],['global.set','0',g(0)]],['func',['export',names[1]],['result','i32'],['global.get','0']],['func',['export',names[2]],['param','i32','i32'],['i32.store',g(0),g(1)]]]
        for op,name in zip(STEPS,names[3:]):funcs.append(['func',['export',name],['param','i32'],['global.set','0',['i32.'+op,['global.get','0'],['i32.load',g(0)]]]])
        engine=['core','module',['memory','1','1'],['global',['mut','i32'],c(0)],*funcs]
        nodes=[engine,['core','instance',['instantiate','0']]]
        nodes += [['alias','core','export','0',name,['core','func']] for name in names]
        if mode!='direct':
            for k in range(4):nodes.append(['type',['resource',['rep','i32'],['dtor',str(k+3)]]])
            for k in range(4):nodes += [['core','func',['canon','resource.new',str(k)]],['core','func',['canon','resource.drop',str(k)]]]
        binding=[0,1,2]+(list(range(3,7)) if mode=='direct' else list(range(7,15)))
        inames=['"k'+str(x)+'"' for x in rng.sample(range(100,1000),len(binding))]
        imports=[]
        for i,n in enumerate(inames):
            sig=[['result','i32']] if i==1 else ([['param','i32','i32']] if i==2 else [['param','i32']])
            if mode!='direct' and i>=3 and i%2==1:sig.append(['result','i32'])
            imports.append(['import','"i"',n,['func',*sig]])
        body=[['call','0',g(0)]];alloc=list(range(len(steps)));rng.shuffle(alloc)
        if mode=='deferred':
            for i in alloc:
                op,pay=steps[i];body.append(['call','2',c(4*i),pay]);body.append(['local.set',str(2+i),['call',str(3+2*STEPS.index(op)),c(4*i)]])
            drops=list(range(len(steps)))
            if broken and len(drops)>1:drops[0],drops[1]=drops[1],drops[0]
            for i in drops:body.append(['call',str(4+2*STEPS.index(steps[i][0])),g(2+i)])
        else:
            for i,(op,pay) in enumerate(steps):
                k=STEPS.index(op)
                body.append(['call','2',c(4*i),pay]);body.append(['call',str(3+k),c(4*i)] if mode=='direct' else ['call',str(4+2*k),['call',str(3+2*k),c(4*i)]])
        body.append(['call','1']);locals_=[['local',*(['i32']*len(steps))]] if mode=='deferred' else []
        nodes.append(['core','module',*imports,['func',['export','"run"'],['param','i32','i32'],['result','i32'],*locals_,*body]])
        nodes.append(['core','instance',*[['export',n,['func',str(b)]] for n,b in zip(inames,binding)]])
        nodes.append(['core','instance',['instantiate','1',['with','"i"',['instance','1']]]])
        nodes.append(['func',['export','"run"'],['param','"x"','u32'],['param','"y"','u32'],['result','u32'],['canon','lift',['core','func','2','"run"']]])
        out=w.emit(['component',*nodes])
    dst=Path(dst)
    if dst.exists() or dst.with_suffix('.wat').exists():raise FileExistsError(dst)
    dst.parent.mkdir(parents=True,exist_ok=True);dst.with_suffix('.wat').write_text(out,encoding='utf-8');build=time.perf_counter()
    jco('parse',dst.with_suffix('.wat'),'-o',dst);end=time.perf_counter()
    return dict(mode=mode,steps=len(steps),seed=seed,read_ms=(afterread-start)*1000,build_ms=(build-afterread)*1000,compile_ms=(end-build)*1000,transform_ms=(end-start)*1000)
def transpile(src,dst):
    dst=Path(dst)
    if dst.exists():raise FileExistsError(dst)
    start=time.perf_counter();jco('transpile',src,'-o',dst,'--name','unit','--instantiation','async','--base64-cutoff','0','--no-wasi-shim','--no-typescript','--quiet')
    (dst/'package.json').write_text('{"type":"module"}\n',encoding='utf-8')
    return dict(transpile_ms=(time.perf_counter()-start)*1000,files={p.name:p.stat().st_size for p in dst.iterdir() if p.is_file()})
def leb(data,pos):
    n=0;shift=0
    while True:
        v=data[pos];pos+=1;n|=(v&127)<<shift
        if v<128:return n,pos
        shift+=7
        if shift>35:raise Unsupported('invalid LEB')
def read_component(src):
    data=Path(src).read_bytes()
    if data[:8]!=b'\0asm\x0d\0\x01\0':raise Unsupported('component header')
    pos=8;bins=[]
    while pos<len(data):
        sid=data[pos];size,pos=leb(data,pos+1);payload=data[pos:pos+size];pos+=size
        if sid==1:
            if payload[:8]!=b'\0asm\x01\0\0\0':raise Unsupported('core module section')
            bins.append(payload)
    text=jco('print',src);tree=w.parse(text.replace('(component','(module',1));tree[0]='component'
    with tempfile.TemporaryDirectory(prefix='resource-reader-') as tmp:
        modules=[]
        for i,b in enumerate(bins):
            p=Path(tmp)/str(i);p.write_bytes(b);modules.append(q.read(p))
    return tree,modules
class Evaluator:
    """Specialized symbolic interpreter of the PUBLIC canonical links, not a seed reader."""
    def __init__(self,tree,modules):
        self.instances=[];self.cf=[];self.rt={};self.f=[];self.export=None;self.handles={};self.next=0;self.peak=0;self.calls=0;self.events=[]
        types=0;mi=0
        for e in tree[1:]:
            if e[:2]==['core','module']:mi+=1
            elif e[:2]==['core','instance']:
                if e[2][0]=='instantiate':
                    it=e[2];m=modules[int(it[1])];bindings={x[1]:self.instances[int(x[2][1])]['exports'] for x in it[2:]}
                    imports=[];funcs=[];globs=[];exports={};arities=[];memory=None
                    sigs=[x[1] for x in m[1:] if x[0]=='type']
                    iid=len(self.instances)
                    for x in m[1:]:
                        if x[0]=='import':
                            if x[3][0]!='func':raise Unsupported('nonfunction import')
                            imports.append(bindings[x[1]][x[2]])
                            sig=sigs[int(next(t for t in x[3][1:] if t[0]=='type')[1])]
                            arities.append(sum(len(t)-1 for t in sig[1:] if t[0]=='param'))
                        elif x[0]=='func':
                            funcs.append(x);arities.append(sum(len(t)-1 for t in x[1:] if t[0]=='param'))
                        elif x[0]=='global':
                            if x[1]!=['mut','i32'] or x[2][0]!='i32.const':raise Unsupported('global profile')
                            globs.append(c(int(x[2][1],0)))
                        elif x[0]=='export':
                            if x[2][0]!='func':raise Unsupported('nonfunc export')
                            exports[x[1]]=('core',iid,int(x[2][1]))
                        elif x[0]=='memory':
                            if memory is not None or x[1:]!=['1','1']:raise Unsupported('private one-page memory')
                            memory={}
                        elif x[0]!='type':raise Unsupported('core section '+x[0])
                    self.instances.append(dict(imports=imports,funcs=funcs,globals=globs,exports=exports,arities=arities,memory=memory))
                else:
                    self.instances.append(dict(exports={x[1]:self.cf[int(x[2][1])] for x in e[2:]}))
            elif e[:3]==['alias','core','export']:
                if e[5]!=['core','func']:raise Unsupported('alias kind')
                self.cf.append(self.instances[int(e[3])]['exports'][e[4]])
            elif e[0]=='type':
                if e[1][0]=='resource':
                    if e[1][1]!=['rep','i32'] or e[1][2][0]!='dtor':raise Unsupported('resource profile')
                    self.rt[types]=self.cf[int(e[1][2][1])]
                types+=1
            elif e[:2]==['core','func']:
                if e[2][:1]!=['canon'] or e[2][1] not in ('resource.new','resource.drop'):raise Unsupported('canon builtin')
                self.cf.append((e[2][1],int(e[2][2])))
            elif e[0]=='func':
                ca=next(x for x in e[1:] if x[0]=='canon')
                if ca[:2]!=['canon','lift'] or ca[2][:2]!=['core','func']:raise Unsupported('lift')
                self.f.append(self.cf[int(ca[2][2])])
            elif e[0]=='export' and e[1]=='"run"':self.export=self.f[int(e[2][1])]
            else:raise Unsupported('component section '+str(e[:2]))
        if self.export is None:raise Unsupported('missing run')
    def call(self,fn,args):
        self.calls+=1
        if self.calls>10000:raise Unsupported('call budget')
        if fn[0]=='resource.new':
            self.next+=1;h=('handle',fn[1],self.next);self.handles[h]=args[0];self.peak=max(self.peak,len(self.handles));return h
        if fn[0]=='resource.drop':
            h=args[0]
            if not isinstance(h,tuple) or h[:2]!=('handle',fn[1]) or h not in self.handles:raise Unsupported('invalid or double drop')
            payload=self.handles.pop(h);self.events.append(fn[1]);self.call(self.rt[fn[1]],[payload]);return None
        _,iid,idx=fn;inst=self.instances[iid]
        if idx<len(inst['imports']):return self.call(inst['imports'][idx],args)
        f=inst['funcs'][idx-len(inst['imports'])];ls=[t for x in f[1:] if x[0]=='local' for t in x[1:]]
        if any(t!='i32' for t in ls):raise Unsupported('local type')
        env=list(args)+[c(0) for _ in ls];stack=[]
        def operands(es,n):
            vals=[walk(e) for e in es];missing=n-len(vals)
            if missing<0 or missing>len(stack):raise Unsupported('operand stack arity')
            if missing:vals=stack[-missing:]+vals;del stack[-missing:]
            return vals
        def walk(e):
            op=e[0]
            if op=='local.get':return env[int(e[1])]
            if op=='global.get':return inst['globals'][int(e[1])]
            if op=='i32.const':return c(int(e[1],0))
            if op in ('local.set','local.tee','global.set'):
                v=walk(e[2]) if len(e)>2 else stack.pop()
                (inst['globals'] if op=='global.set' else env)[int(e[1])]=v
                return v if op=='local.tee' else None
            if op=='call':return self.call(('core',iid,int(e[1])),operands(e[2:],inst['arities'][int(e[1])]))
            if op in ('i32.load','i32.store'):
                if inst['memory'] is None:raise Unsupported('missing memory')
                memarg=[a for a in e[1:] if not isinstance(a,list)]
                offset=0
                for a in memarg:
                    if a.startswith('offset='):offset=int(a[7:],0)
                    elif not a.startswith('align='):raise Unsupported('memory immediate')
                vals=operands([a for a in e[1:] if isinstance(a,list)],1 if op=='i32.load' else 2)
                if vals[0][0]!='i32.const':raise Unsupported('nonconstant address')
                addr=int(vals[0][1])+offset
                if not 0<=addr<=65532 or addr%4:raise Unsupported('aligned inbounds word')
                if op=='i32.load':return inst['memory'].get(addr,c(0))
                inst['memory'][addr]=vals[1];return None
            if op.startswith('i32.') and op[4:] in OPS:return [op,*operands(e[1:],2)]
            if op=='block':
                v=None
                for a in e[1:]:
                    if a[0] not in ('type','result'):v=walk(a)
                return v
            raise Unsupported('core op '+op)
        for e in f[1:]:
            if e[0] not in ('type','param','result','local'):
                v=walk(e)
                if v is not None:stack.append(v)
        if len(stack)>1:raise Unsupported('multivalue')
        return stack[0] if stack else None
    def recover(self):
        expr=self.call(self.export,[g(0),g(1)])
        if self.handles:raise Unsupported('live handles at return')
        if not isinstance(expr,list):raise Unsupported('nonscalar return')
        return expr,dict(calls=self.calls,allocations=self.next,peak_handles=self.peak,drops=len(self.events))
def recover(src,dst=None):
    start=time.perf_counter();tree,modules=read_component(src);t=time.perf_counter();ev=Evaluator(tree,modules);expr,stats=ev.recover();code=w.emit(mod(expr));end=time.perf_counter()
    if dst:q.compile(code,dst)
    return dict(stats,read_ms=(t-start)*1000,recovery_ms=(end-t)*1000,total_ms=(end-start)*1000,code=code)
def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    a=sp.add_parser('transform');a.add_argument('source');a.add_argument('output');a.add_argument('--mode',choices=['plain','direct','immediate','deferred'],default='deferred');a.add_argument('--seed',type=int,default=37)
    a=sp.add_parser('recover');a.add_argument('source');a.add_argument('output')
    a=sp.add_parser('transpile');a.add_argument('source');a.add_argument('output')
    args=ap.parse_args()
    result=transform(args.source,args.output,args.mode,args.seed) if args.cmd=='transform' else (recover(args.source,args.output) if args.cmd=='recover' else transpile(args.source,args.output))
    result.pop('code',None);print(json.dumps(result))
if __name__=='__main__':main()
