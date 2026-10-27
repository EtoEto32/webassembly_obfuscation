"""Known-method, compositional symbolic interpreter for the restricted corpus.

No source/manifest/seed input. Models exception tags as a finite sum type.
No generic decompiler claim. Fails closed for unknown instructions or recursion.
"""
import argparse,json,time
from pathlib import Path
import prototype as p
C=p.const
def neg(x):return p.expr('i32.eqz',x)
def both(a,b):
    if a==C(0) or b==C(0):return C(0)
    if a==C(1):return b
    if b==C(1) or a==b:return a
    if neg(a)==b or neg(b)==a:return C(0)
    return ('i32.and',a,b)
def either(a,b):
    if a==C(0):return b
    if b==C(0) or a==b:return a
    if a==C(1) or b==C(1) or neg(a)==b or neg(b)==a:return C(1)
    return ('i32.or',a,b)
def choose(c,a,b):
    if a==b:return a
    if a is None or b is None:raise ValueError('Incompatible control values')
    return p.expr('select',a,b,c)
def substitute(x,args):
    if x is None:return None
    if x[0]=='arg':return args[x[1]]
    if x[0] in ('i32.const','tag','null'):return x
    if x[0]=='tagis':return tagis(substitute(x[1],args),x[2])
    return p.expr(x[0],*(substitute(y,args) for y in x[1:]))
def tagis(value,tag):
    if value[0]=='tag':return C(value==tag)
    if value[0]=='select':
        a=tagis(value[1],tag);b=tagis(value[2],tag)
        if a==C(1) and b==C(0):return p.truth(value[3])
        if a==C(0) and b==C(1):return neg(value[3])
        return choose(value[3],a,b)
    if value[0]=='arg':return ('tagis',value,tag)
    raise ValueError('Unknown/null packet at a reference call boundary')
def flow(kind='normal',value=None,env=None,guard=None,target=None):
    return dict(kind=kind,value=value,env=dict(env or {}),guard=C(1) if guard is None else guard,target=target)
def merge(fs):
    out={}
    for f in fs:
        if f['guard']==C(0):continue
        key=(f['kind'],f['target'])
        if key not in out:out[key]=f;continue
        a=out[key];c=f['guard']
        out[key]=flow(f['kind'],choose(c,f['value'],a['value']),
            {k:choose(c,f['env'][k],a['env'][k]) for k in a['env']},either(a['guard'],c),f['target'])
    return list(out.values())
class Recover:
    def __init__(self,m):
        if any(x[0] not in ('type','tag','func','export') for x in m[1:]):raise ValueError('Module outside recovery profile')
        self.func={x[1]:x for x in m[1:] if x[0]=='func'};self.cache={};self.busy=set();self.steps=0;self.max_flows=0
        self.exports=[x for x in m[1:] if x[0]=='export']
        if len(self.exports)!=1 or self.exports[0][2][0]!='func':raise ValueError('One function export required')
        self.tags=sorted(x[1] for x in m[1:] if x[0]=='tag')
        if len(self.tags) not in (0,2):raise ValueError('Only zero/two-tag profile')
        types={x[1]:x[2] for x in m[1:] if x[0]=='type'}
        for tag in [x for x in m[1:] if x[0]=='tag']:
            if types[tag[2][1]]!=['func']:raise ValueError('Payload tags unsupported')
    def signature(self,f):
        return [(d[1],d[2]) for d in f[2:] if isinstance(d,list) and d[0]=='param']
    def summary(self,name):
        if name in self.cache:return self.cache[name]
        if name in self.busy:raise ValueError('Recursive call unsupported')
        self.busy.add(name);f=self.func[name];params=self.signature(f)
        env={n:('arg',i) for i,(n,t) in enumerate(params)}
        for d in f[2:]:
            if isinstance(d,list) and d[0]=='local':env[d[1]]=C(0) if d[2]=='i32' else ('null',)
        body=[x for x in f[2:] if isinstance(x,list) and x[0] not in ('type','param','local','result')]
        fs=self.sequence(body,[flow(env=env)])
        for z in fs:
            if z['kind']=='return':z['kind']='normal'
        fs=merge(fs)
        if len(fs)!=1 or fs[0]['kind']!='normal' or fs[0]['guard']!=C(1):raise ValueError('Function has unresolved effects/control')
        self.cache[name]=(params,fs[0]['value']);self.busy.remove(name);return self.cache[name]
    def sequence(self,xs,fs):
        for x in xs:
            nxt=[]
            for f in fs:
                if f['kind']!='normal':nxt.append(f);continue
                for g in self.eval(x,f['env']):g['guard']=both(f['guard'],g['guard']);nxt.append(g)
            fs=merge(nxt);self.max_flows=max(self.max_flows,len(fs))
            if len(fs)>256:raise ValueError('Flow budget exceeded')
        return fs
    def args(self,xs,env):
        states=[([],flow(env=env))];escaped=[]
        for x in xs:
            nxt=[]
            for values,f in states:
                for g in self.eval(x,f['env']):
                    g['guard']=both(f['guard'],g['guard'])
                    if g['kind']=='normal':nxt.append((values+[g['value']],g))
                    else:escaped.append(g)
            states=nxt
        return states,escaped
    def throw_value(self,v,env):
        if v[0]=='tag':return [flow('throw',v,env,target=v[1])]
        if v[0]=='select':
            out=[]
            for val,c in ((v[1],p.truth(v[3])),(v[2],neg(v[3]))):
                for f in self.throw_value(val,env):f['guard']=both(c,f['guard']);out.append(f)
            return merge(out)
        if v[0]=='arg' and len(self.tags)==2:
            test=tagis(v,('tag',self.tags[0]))
            return [flow('throw',('tag',t),env,test if i==0 else neg(test),t) for i,t in enumerate(self.tags)]
        raise ValueError('Unknown/null exception reference')
    def eval(self,x,env):
        self.steps+=1
        if self.steps>1000000:raise ValueError('Step budget exceeded')
        op=x[0]
        if op=='i32.const':return [flow(value=C(x[1]),env=env)]
        if op=='local.get':return [flow(value=env[x[1]],env=env)]
        if op=='ref.null':return [flow(value=('null',),env=env)]
        if op=='nop':return [flow(env=env)]
        if op=='unreachable':return [flow('trap',env=env)]
        if op in ('block','try_table'):
            label=x[1] if len(x)>1 and isinstance(x[1],str) else None
            body=[z for z in x[1:] if isinstance(z,list) and z[0] not in ('param','result','catch','catch_ref','catch_all','catch_all_ref')]
            fs=self.sequence(body,[flow(env=env)])
            if op=='try_table':
                catches=[z for z in x[1:] if isinstance(z,list) and z[0].startswith('catch')]
                for f in fs:
                    if f['kind']=='throw':
                        for ca in catches:
                            if ca[0] in ('catch_all','catch_all_ref') or ca[1]==f['target']:
                                f['kind']='br';f['target']=ca[-1];f['value']=f['value'] if ca[0].endswith('_ref') else None;break
            if label is not None:
                for f in fs:
                    if f['kind']=='br' and f['target']==label:f['kind']='normal';f['target']=None
            return merge(fs)
        if op=='if':
            cond=next(z for z in x[1:] if isinstance(z,list) and z[0] not in ('result','then','else'))
            yes=next(z[1:] for z in x[1:] if isinstance(z,list) and z[0]=='then')
            no=next((z[1:] for z in x[1:] if isinstance(z,list) and z[0]=='else'),[]);out=[]
            for cf in self.eval(cond,env):
                if cf['kind']!='normal':out.append(cf);continue
                for branch,g in ((yes,p.truth(cf['value'])),(no,neg(cf['value']))):
                    if g==C(0):continue
                    for f in self.sequence(branch,[flow(env=cf['env'])]):f['guard']=both(cf['guard'],both(g,f['guard']));out.append(f)
            return merge(out)
        if op=='throw':
            if len(x)!=2 or x[1] not in self.tags:raise ValueError('Nonempty/unknown tag')
            return [flow('throw',('tag',x[1]),env,target=x[1])]
        child=[z for z in x[1:] if isinstance(z,list)];states,out=self.args(child,env)
        for a,f in states:
            val=None;kind='normal';target=None;e=f['env'];g=f['guard']
            if op in ('local.set','local.tee'):
                e=dict(e);e[x[1]]=a[0];val=a[0] if op=='local.tee' else None
            elif op=='call':
                ps,result=self.summary(x[1])
                if len(ps)!=len(a):raise ValueError('Call arity')
                for (_,typ),value in zip(ps,a):
                    if typ!='i32':tagis(value,('tag',self.tags[0]))
                val=substitute(result,a)
            elif op=='throw_ref':
                for h in self.throw_value(a[0],e):h['guard']=both(g,h['guard']);out.append(h)
                continue
            elif op in ('return','br'):kind=op;val=a[0] if a else None;target=x[1] if op=='br' else None
            elif op=='drop':pass
            elif op=='ref.as_non_null':
                if a[0][0]=='null':raise ValueError('Null reference')
                val=a[0]
            elif op=='select' or op.startswith('i32.') and op[4:] in p.OPS1|p.OPS2:val=p.expr(op,*a)
            else:raise ValueError('Unsupported instruction '+op)
            out.append(flow(kind,val,e,g,target))
        return merge(out)
    def run(self):
        export=self.exports[0];params,result=self.summary(export[2][1])
        if any(t!='i32' for _,t in params):raise ValueError('Non-i32 exported function')
        if any(x[0] in ('tag','null') for x in p.walk(result)):raise ValueError('Reference escaped')
        return len(params),export[1],result
def recover(src,dst):
    start=time.perf_counter();m=p.binaryen_tree(src);parsed=time.perf_counter();r=Recover(m);n,name,e=r.run();end=time.perf_counter()
    text,info=p.wat(n,name,e,'plain');p.compile(text,dst)
    return dict(status='recovered',parse_ms=(parsed-start)*1000,analysis_ms=(end-parsed)*1000,steps=r.steps,max_flows=r.max_flows,functions_summarized=len(r.cache),**info)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');v=a.parse_args();print(json.dumps(recover(v.input,v.output)))
