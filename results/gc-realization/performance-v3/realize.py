"""Construct a specified finite GC heap with exact node identity, restricted types."""
import argparse,collections,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.append(str(ROOT/'research/gc-witness'))
from witness import read,closure,type_text,vt,scalar,Unsupported,Empty,Budget

class Impossible(Exception):pass

def fields(model,node):
    t=model['types'][node['type']]
    return t['fields'] if t['kind']=='struct' else t['fields']*len(node['values'])

def validate_graph(model,nodes):
    if not nodes or len(nodes)>128:raise Budget('1..128 requested nodes')
    for i,node in enumerate(nodes):
        if set(node)!= {'type','values'}:raise Unsupported('node must contain type and values')
        k=node['type']
        if not isinstance(k,int) or not 0<=k<len(model['types']):raise Unsupported('bad type index')
        t=model['types'][k]
        if t['kind'] not in ('struct','array'):raise Unsupported('only struct/array target nodes')
        if t['kind']=='struct' and len(node['values'])!=len(t['fields']):raise Unsupported('field count')
        if len(node['values'])>128:raise Budget('128 values per node')
        for f,value in zip(fields(model,node),node['values']):
            v=f['value']
            if 'scalar' in v:
                if v['scalar'] not in ('i32','i64','i8','i16'):raise Unsupported('target scalars: integer/packed only')
                if not isinstance(value,int) or isinstance(value,bool):raise Unsupported('integer value expected')
                bits=64 if v['scalar']=='i64' else 32
                if not -(1<<(bits-1))<=value<1<<(bits-1):raise Unsupported('integer range')
            elif value is None:
                if not v['nullable']:raise Unsupported('null for nonnull field')
            else:
                if not isinstance(value,dict) or set(value)!={'node'}:raise Unsupported('reference must be null or node ID')
                j=value['node']
                if not isinstance(j,int) or not 0<=j<len(nodes):raise Unsupported('bad node ID')
                if 'index' not in v['ref'] or nodes[j]['type']!=v['ref']['index']:raise Unsupported('requires same concrete type index; subtype/alias type indices excluded')

def order_nodes(model,nodes,mode):
    deps=[]
    for node in nodes:
        deps.append({v['node'] for f,v in zip(fields(model,node),node['values']) if isinstance(v,dict) and (mode=='all-deps' or not f['mutable'])})
    if mode=='dfs-staged':
        marks={};order=[]
        def visit(i):
            if marks.get(i)==1:raise Impossible('immutable reference cycle')
            if marks.get(i)==2:return
            marks[i]=1
            for j in sorted(deps[i]):visit(j)
            marks[i]=2;order.append(i)
        for i in range(len(nodes)):visit(i)
        return order
    remaining=list(map(len,deps));users=collections.defaultdict(list)
    for i,ds in enumerate(deps):
        for d in ds:users[d].append(i)
    q=collections.deque(i for i,n in enumerate(remaining) if n==0);order=[]
    while q:
        i=q.popleft();order.append(i)
        for j in users[i]:
            remaining[j]-=1
            if remaining[j]==0:q.append(j)
    if len(order)!=len(nodes):raise Impossible('reference cycle' if mode=='all-deps' else 'immutable reference cycle')
    return order

def generate(model,nodes,mode='staged',fault=None,return_nodes=False):
    start=time.perf_counter_ns();validate_graph(model,nodes);ts=model['types'];live=set(closure(ts))
    if any(n['type'] not in live for n in nodes):raise Impossible('requested type has no finite constructor witness')
    order=order_nodes(model,nodes,mode);locals_=['(local $n%d (ref $t%d))'%(i,n['type']) for i,n in enumerate(nodes)];steps=[];patches=[];available={};seeds={};built=set();helper_count=0;final_count=0
    def expr(v,value):
        if 'scalar' in v:return '('+('i64' if v['scalar']=='i64' else 'i32')+'.const '+str(value)+')'
        if value is None:return '(ref.null $t%d)'%v['ref']['index']
        return '(local.get $n%d)'%value['node']
    def constructor(i,values):
        if ts[i]['kind']=='array':return '(array.new_fixed $t%d %d %s)'%(i,len(values),' '.join(values))
        return '(struct.new $t%d %s)'%(i,' '.join(values))
    def seed(i):
        nonlocal helper_count
        if i in available:return '(local.get '+available[i]+')'
        if i in seeds:return '(local.get '+seeds[i]+')'
        if i not in live:raise Impossible('required seed type not constructible')
        t=ts[i]
        if t['kind']=='func':raise Unsupported('function seed')
        values=[]
        if t['kind']=='struct':
            for f in t['fields']:
                v=f['value']
                if 'scalar' in v:values.append(scalar(v))
                elif 'index' not in v['ref']:raise Unsupported('abstract seed')
                elif v['nullable']:values.append('(ref.null $t%d)'%v['ref']['index'])
                else:values.append(seed(v['ref']['index']))
        name='$h%d'%helper_count;helper_count+=1;locals_.append('(local '+name+' (ref $t%d))'%i);steps.append('(local.set '+name+' '+constructor(i,values)+')');seeds[i]=name
        return '(local.get '+name+')'
    for i in order:
        node=nodes[i];k=node['type'];values=[]
        if fault=='merge-final' and k in available:
            steps.append('(local.set $n%d (local.get %s))'%(i,available[k]));built.add(i);continue
        for j,(f,value) in enumerate(zip(fields(model,node),node['values'])):
            v=f['value'];actual=expr(v,value)
            if not f['mutable'] or 'scalar' in v or value is None or (isinstance(value,dict) and value['node'] in built):initial=actual
            else:
                if v['nullable']:initial=expr(v,None)
                elif mode=='null-patch':raise Impossible('nonnull mutable field cannot be initialized with null')
                else:initial=seed(v['ref']['index'])
                if ts[k]['kind']=='array':patches.append('(array.set $t%d (local.get $n%d) (i32.const %d) %s)'%(k,i,j,actual))
                else:patches.append('(struct.set $t%d %d (local.get $n%d) %s)'%(k,j,i,actual))
            values.append(initial)
        steps.append('(local.set $n%d %s)'%(i,constructor(k,values)));built.add(i);available.setdefault(k,'$n%d'%i);final_count+=1
    if fault!='omit-patches':steps+=patches
    construction_steps=list(steps)
    checks=[]
    for i,node in enumerate(nodes):
        k=node['type'];t=ts[k]
        if t['kind']=='array':checks.append('(i32.eq (array.len (local.get $n%d)) (i32.const %d))'%(i,len(node['values'])))
        for j,(f,value) in enumerate(zip(fields(model,node),node['values'])):
            v=f['value'];packed=v.get('scalar') in ('i8','i16');op=t['kind']+'.get'+('_u' if packed else '')
            get='(%s $t%d %s)'%(op,k,('%d (local.get $n%d)'%(j,i)) if t['kind']=='struct' else '(local.get $n%d) (i32.const %d)'%(i,j))
            if 'scalar' in v:
                expected=value&((1<<(8 if v['scalar']=='i8' else 16))-1) if packed else value
                checks.append('(%s.eq %s %s)'%('i64' if v['scalar']=='i64' else 'i32',get,expr(v,expected)))
            elif value is None:checks.append('(ref.is_null '+get+')')
            else:checks.append('(ref.eq '+get+' '+expr(v,value)+')')
        for j in range(i):checks.append('(i32.eqz (ref.eq (local.get $n%d) (local.get $n%d)))'%(i,j))
    locals_.append('(local $ok i32)');steps.append('(local.set $ok (i32.const 1))')
    steps+=['(local.set $ok (i32.and (local.get $ok) '+c+'))' for c in checks];steps.append('(local.get $ok)')
    wat='(module\n'+type_text(model)+'\n(func (export "run") (result i32) '+' '.join(locals_)+'\n'+'\n'.join(steps)+'))'
    extra={}
    if return_nodes:
        results=' '.join('(ref $t%d)'%n['type'] for n in nodes)
        returns=['(local.get $n%d)'%i for i in range(len(nodes))]
        wat='(module\n'+type_text(model)+'\n(func (export "make") (result '+results+') '+' '.join(locals_)+'\n'+'\n'.join(construction_steps+returns)+'))'
        params=' '.join('(param $n%d (ref $t%d))'%(i,n['type']) for i,n in enumerate(nodes))
        verify=['(local.set $ok (i32.const 1))']+['(local.set $ok (i32.and (local.get $ok) '+c+'))' for c in checks]+['(local.get $ok)']
        extra['observer_wat']='(module\n'+type_text(model)+'\n(func (export "check") '+params+' (result i32) (local $ok i32)\n'+'\n'.join(verify)+'))'
    return dict(wat=wat,mode=mode,order=order,helper_allocations=helper_count,final_allocations=final_count,patches=len(patches),checks=len(checks),generation_ms=(time.perf_counter_ns()-start)/1e6,**extra)

def enumerated(model,nodes):
    """Independent finite-state construction rules; does not call closure/order_nodes."""
    if len(nodes)+len(model['types'])>14:raise Budget('enumeration bound')
    n=len(nodes);frontier=[(0,0)];seen=set(frontier);success=False
    while frontier:
        known,done=frontier.pop()
        if done==(1<<n)-1:success=True
        transitions=[]
        for k,t in enumerate(model['types']):
            if known>>k&1:continue
            possible=t['kind']=='array'
            if t['kind']=='struct':possible=all('scalar' in f['value'] or f['value']['nullable'] or known>>f['value']['ref']['index']&1 for f in t['fields'])
            if possible:transitions.append((known|(1<<k),done))
        for i,node in enumerate(nodes):
            if done>>i&1:continue
            possible=True
            for f,v in zip(fields(model,node),node['values']):
                if not isinstance(v,dict):continue
                if not f['mutable'] and not (done>>v['node']&1):possible=False;break
                if f['mutable'] and not f['value']['nullable'] and not (known>>nodes[v['node']]['type']&1):possible=False;break
            if possible:transitions.append((known|(1<<node['type']),done|(1<<i)))
        for nxt in transitions:
            if nxt not in seen:seen.add(nxt);frontier.append(nxt)
    return success,len(seen)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('graph',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--mode',choices=['staged','dfs-staged','all-deps','null-patch'],default='staged');a=ap.parse_args()
    try:
        r=generate(read(a.input),json.loads(a.graph.read_text()),a.mode);a.output.write_text(r.pop('wat'));print(json.dumps(dict(status='generated',**r)))
    except (Unsupported,Empty,Budget,Impossible) as e:print(json.dumps(dict(status=type(e).__name__,reason=str(e))));raise SystemExit(2)
