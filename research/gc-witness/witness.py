"""Restricted final-GC type witness planner; explicit failures, no guest execution."""
import argparse,collections,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CHECKER=ROOT/'.tools/gc-witness-target/release/gc-witness-types.exe'
class Unsupported(Exception):pass
class Budget(Exception):pass
class Empty(Exception):pass

def read(path):
    cp=subprocess.run([str(CHECKER),str(path)],capture_output=True,text=True,timeout=20);cp.check_returncode()
    model=json.loads(cp.stdout)
    if model['status']!='supported':raise Unsupported(model['reason'])
    for t in model['types']:
        for v in [f['value'] for f in t.get('fields',[])]+t.get('params',[])+t.get('results',[]):
            if 'ref' in v and not v['nullable'] and 'index' not in v['ref']:
                raise Unsupported('non-null abstract reference')
    return model

def deps(t,arrays=False):
    if t['kind']=='func' or t['kind']=='array' and not arrays:return []
    return [f['value']['ref']['index'] for f in t['fields'] if 'ref' in f['value'] and not f['value']['nullable']]

def closure(types,arrays=False):
    """Linear AND-dependency worklist. arrays=True reproduces conservative edge rule."""
    ds=[set(deps(t,arrays)) for t in types];pending=list(map(len,ds));rev=collections.defaultdict(list)
    for i,children in enumerate(ds):
        for c in children:rev[c].append(i)
    q=collections.deque(i for i,n in enumerate(pending) if n==0);order=[]
    while q:
        i=q.popleft();order.append(i)
        for p in rev[i]:
            pending[p]-=1
            if pending[p]==0:q.append(p)
    return order

def memo_order(types):
    """Independent strong baseline: three-colour recursive DFS with memoized results."""
    mark={};order=[]
    def visit(i):
        if i in mark:return mark[i]==2
        mark[i]=1
        if all(visit(c) for c in deps(types[i])):
            mark[i]=2;order.append(i);return True
        mark[i]=3;return False
    for i in range(len(types)):visit(i)
    return order

def vt(v):
    if 'scalar' in v:return v['scalar']
    h=v['ref'];h='$t'+str(h['index']) if 'index' in h else h['abstract']
    return '(ref '+('null ' if v['nullable'] else '')+h+')'
def type_text(model):
    lines=[]
    for g in model['groups']:
        items=[]
        for i in range(g['start'],g['start']+g['length']):
            t=model['types'][i];k=t['kind']
            if k=='func':body='func '+''.join('(param '+vt(v)+')' for v in t['params'])+''.join('(result '+vt(v)+')' for v in t['results'])
            else:
                fields=[('(mut '+vt(f['value'])+')') if f['mutable'] else vt(f['value']) for f in t['fields']]
                body=k+' '+(' '.join('(field '+f+')' for f in fields) if k=='struct' else fields[0])
            items.append('(type $t%d (%s))'%(i,body))
        lines.append('(rec '+' '.join(items)+')')
    return '\n'.join(lines)

def scalar(v):
    s=v['scalar'];s='i32' if s in ('i8','i16') else s
    return '(v128.const i32x4 0 0 0 0)' if s=='v128' else '('+s+'.const 0)'
def default_value(v,construct):
    if 'scalar' in v:return scalar(v)
    if v['nullable']:
        h=v['ref'];h='$t'+str(h['index']) if 'index' in h else h['abstract'];return '(ref.null '+h+')'
    return construct(v['ref']['index'],())

def generate(model,target,path=(),mode='worklist',node_budget=4096,depth_budget=64,return_root=False):
    """Path consists of field indices or 'e' (element 0); leaves must be references.
    Only the selected array nodes are nonempty. No alias-diversity claim.
    """
    types=model['types'];start=time.perf_counter_ns()
    order=memo_order(types) if mode=='memo' else closure(types)
    live=set(order)
    if target not in live:raise Empty('no finite construction in supported fragment')
    locals_=[];steps=[];memo={};calls=0;stubs=set();depth=0;allocations=0
    def build(i,rest):
        nonlocal calls,depth,allocations
        key=(i,tuple(rest))
        if mode!='tree' and key in memo:return '(local.get '+memo[key]+')'
        calls+=1
        if calls>node_budget:raise Budget('node budget')
        depth+=1
        if depth>depth_budget:raise Budget('depth budget')
        if i not in live:raise Empty('path requires empty type')
        t=types[i];k=t['kind']
        def field(v,next_path=None):
            if next_path is None:return default_value(v,build)
            if 'ref' not in v or 'index' not in v['ref']:raise Unsupported('path must traverse concrete references')
            return build(v['ref']['index'],next_path)
        if k=='func':
            if rest:raise Unsupported('path through function')
            stubs.add(i);expr='(ref.func $stub%d)'%i
        elif k=='array':
            if rest:
                if rest[0]!='e':raise Unsupported('array path requires e')
                expr='(array.new_fixed $t%d 1 %s)'%(i,field(t['fields'][0]['value'],rest[1:]))
            else:expr='(array.new_fixed $t%d 0)'%i
            allocations+=1
        else:
            if rest and (not isinstance(rest[0],int) or not 0<=rest[0]<len(t['fields'])):raise Unsupported('bad field path')
            values=[field(f['value'],rest[1:] if rest and rest[0]==j else None) for j,f in enumerate(t['fields'])]
            expr='(struct.new $t%d %s)'%(i,' '.join(values));allocations+=1
        depth-=1
        if mode=='tree':return expr
        name='$v'+str(len(locals_));locals_.append('(local '+name+' (ref $t'+str(i)+'))');steps.append('(local.set '+name+' '+expr+')');memo[key]=name
        return '(local.get '+name+')'
    root=build(target,tuple(path));access=root;current=target
    for p in path:
        t=types[current]
        if p=='e':
            access='(array.get $t%d %s (i32.const 0))'%(current,access);v=t['fields'][0]['value']
        else:access='(struct.get $t%d %d %s)'%(current,p,access);v=t['fields'][p]['value']
        current=v['ref']['index']
    body='\n'.join(steps)+'\n'+(root if return_root else '(i32.eqz (ref.is_null '+access+'))')
    stub_text='\n'.join('(func $stub%d (type $t%d) (unreachable))'%(i,i) for i in sorted(stubs))
    elems='(elem declare func '+' '.join('$stub%d'%i for i in sorted(stubs))+')' if stubs else ''
    result='(ref $t%d)'%target if return_root else 'i32'
    wat='(module\n'+type_text(model)+'\n'+stub_text+'\n'+elems+'\n(func (export "run") (result '+result+') '+' '.join(locals_)+'\n'+body+'))'
    return dict(wat=wat,target=target,path=list(path),mode=mode,nodes=calls,allocations=allocations,locals=len(locals_),milliseconds=(time.perf_counter_ns()-start)/1e6)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--target',type=int,required=True);ap.add_argument('--path',default='[]');ap.add_argument('--mode',choices=['tree','memo','worklist'],default='worklist');ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    try:
        r=generate(read(a.input),a.target,json.loads(a.path),a.mode);a.output.write_text(r.pop('wat'));print(json.dumps(dict(status='generated',**r)))
    except (Unsupported,Empty,Budget) as e:print(json.dumps(dict(status=type(e).__name__,reason=str(e))));raise SystemExit(2)
