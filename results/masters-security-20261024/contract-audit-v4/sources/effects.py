"""Acyclic path-sensitive write effects for normalized, validated Core Wasm.

This is a restricted abstract interpreter, not a new static analysis principle.
Unknown *values* are safe; unknown write addresses or lengths force full copy.
Control transfers carry their own local environment. Loops, recursion, host
effects and unsupported instructions force full copy. No unknown op is skipped.
"""
def summary(mod, export='"callback"'):
    memory=[x for x in mod[1:] if x[0]=='memory']
    allimports=[x for x in mod[1:] if x[0]=='import']
    if any(x[3][0]=='memory' for x in allimports) or len(memory)!=1:
        return {'kind':'reject','reason':'one defined memory, no imported memory required'}
    if any(a in ('shared','i64') for a in memory[0][1:] if isinstance(a,str)):
        return {'kind':'reject','reason':'memory32 nonshared required'}
    imports=[x for x in allimports if x[3][0]=='func']
    funcs=[x for x in mod[1:] if x[0]=='func']
    exports={x[1]:x[2] for x in mod[1:] if x[0]=='export'}
    if exports.get(export,[''])[0]!='func' or exports.get('"memory"')!=['memory','0']:
        return {'kind':'reject','reason':'entry or memory export missing'}
    writes=[];visited=set();fuel=[20000]

    def spend():
        fuel[0]-=1
        if fuel[0]<0: raise ValueError('acyclic path budget exceeded')

    def children(x, allowed=()):
        attrs=[a for a in x[1:] if isinstance(a,str)]
        if any(not a.startswith(allowed) for a in attrs): raise ValueError('unsupported attributes')
        return [a for a in x[1:] if isinstance(a,list)], attrs

    def value(x, env):
        spend()
        if not isinstance(x,list) or not x: raise ValueError('malformed expression')
        op=x[0]
        if op=='i32.const' and len(x)==2: return ['const',int(x[1])&0xffffffff]
        if op=='local.get' and len(x)==2: return env[int(x[1])]
        if op=='local.tee' and len(x)==3:
            v=value(x[2],env);env[int(x[1])]=v;return v
        if op=='global.get' and len(x)==2: return None
        if op in ('i32.add','i32.sub','i32.and') and len(x)==3:
            a=value(x[1],env);b=value(x[2],env)
            return None if a is None or b is None else [op[4:],a,b]
        if op in ('i32.eq','i32.ne','i32.lt_u','i32.lt_s','i32.le_u','i32.le_s',
                  'i32.gt_u','i32.gt_s','i32.ge_u','i32.ge_s') and len(x)==3:
            value(x[1],env);value(x[2],env);return None
        if op=='i32.eqz' and len(x)==2: value(x[1],env);return None
        if op in ('i32.load','i32.load8_u','i32.load8_s','i32.load16_u','i32.load16_s'):
            args,attrs=children(x,('offset=','align='))
            if len(args)!=1: raise ValueError('load shape unsupported')
            value(args[0],env);return None
        if op=='select' and len(x)==4:
            a=value(x[1],env);b=value(x[2],env);value(x[3],env)
            return a if a==b else None
        raise ValueError('unsupported value: '+op)

    # A flow is (target, locals). None=fallthrough, integer=branch depth,
    # 'return'=function return. Each branch owns a separate mutable env list.
    def seq(xs, env, stack):
        flows=[(None,env)]
        for x in xs:
            nextflows=[]
            for dest, state in flows:
                if dest is None: nextflows.extend(statement(x,state,stack))
                else: nextflows.append((dest,state))
            flows=nextflows
            if len(flows)>256: raise ValueError('acyclic path count exceeded')
        return flows

    def statement(x, env, stack):
        spend()
        if not isinstance(x,list) or not x: raise ValueError('statement shape unsupported')
        op=x[0]
        if op in ('i32.store8','i32.store16','i32.store'):
            args,attrs=children(x,('offset=','align='))
            if len(args)!=2: raise ValueError('store shape unsupported')
            addr=value(args[0],env);value(args[1],env)
            if addr is None: raise ValueError('unknown store address')
            writes.append({'addr':addr,'offset':next((int(a.split('=')[1]) for a in attrs if a.startswith('offset=')),0),
                           'length':['const',{'i32.store8':1,'i32.store16':2,'i32.store':4}[op]]})
        elif op in ('memory.fill','memory.copy') and len(x)==4:
            addr=value(x[1],env);value(x[2],env);length=value(x[3],env)
            if addr is None or length is None: raise ValueError('unknown bulk address/length')
            writes.append({'addr':addr,'offset':0,'length':length})
        elif op=='local.set' and len(x)==3: env[int(x[1])]=value(x[2],env)
        elif op=='drop' and len(x)==2: value(x[1],env)
        elif op=='call':
            args=[value(a,env) for a in x[2:]];function(int(x[1]),args,stack)
        elif op=='block':
            if any(not isinstance(a,list) or a[0] in ('result','type','param') for a in x[1:]):
                raise ValueError('block value/label unsupported')
            flows=seq(x[1:],env,stack)
            return [(None if d==0 else d-1 if isinstance(d,int) else d,s) for d,s in flows]
        elif op=='if':
            value(x[1],env)
            branches=x[2:]
            if not 1<=len(branches)<=2 or branches[0][0]!='then' or (len(branches)==2 and branches[1][0]!='else'):
                raise ValueError('if shape unsupported')
            flows=seq(branches[0][1:],env.copy(),stack)
            flows+=seq(branches[1][1:] if len(branches)==2 else [],env.copy(),stack)
            # Each if introduces a branch label, just as block does.
            return [(None if d==0 else d-1 if isinstance(d,int) else d,s) for d,s in flows]
        elif op=='br_if' and len(x)==3:
            value(x[2],env);return [(None,env.copy()),(int(x[1]),env.copy())]
        elif op=='br' and len(x)==2: return [(int(x[1]),env)]
        elif op=='return' and len(x)==1: return [('return',env)]
        elif op=='unreachable' and len(x)==1: return []
        elif op=='nop' and len(x)==1: pass
        else: raise ValueError('unsupported statement: '+op)
        return [(None,env)]

    def function(index, arguments, stack):
        spend()
        if index<len(imports): raise ValueError('reachable host import')
        if index in stack: raise ValueError('recursive call unsupported')
        f=funcs[index-len(imports)]
        if any(isinstance(x,str) for x in f[1:]): raise ValueError('named function unsupported')
        params=[a for x in f[1:] if x[0]=='param' for a in x[1:]]
        locals_=[a for x in f[1:] if x[0]=='local' for a in x[1:]]
        if params!=['i32']*len(arguments) or any(t!='i32' for t in locals_) or any(x[0]=='result' for x in f[1:]):
            raise ValueError('only i32 params/locals and void functions supported')
        visited.add(index)
        env=arguments.copy()+[['const',0] for _ in locals_]
        body=[x for x in f[1:] if x[0] not in ('type','param','local')]
        flows=seq(body,env,stack+(index,))
        if any(d not in (None,'return',0) for d,s in flows): raise ValueError('unresolved branch target')

    try:
        function(int(exports[export][1]),[['arg',i] for i in range(3)],())
        # Paths may produce identical effects; exact expression deduplication
        # does not remove any reachable write.
        unique=[]
        for w in writes:
            if w not in unique: unique.append(w)
        return {'kind':'ranges','writes':unique,'visitedFunctions':sorted(visited),'analyzer':'acyclic-v1'}
    except (ValueError,IndexError,KeyError,TypeError) as e:
        return {'kind':'full','reason':str(e),'analyzer':'acyclic-v1'}
