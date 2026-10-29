"""Check linear, zero-reset, bounded state promise from raw/O3 Wasm.

Independent of source coefficients/U/D. Never called by public-I/O recover().
"""
import json
import sys
import prototype as p


def certify(path,bound=8):
    p.w.tool('wasm-validate',[path]);m=p.w.parse(p.w.tool('wasm2wat',[path,'--fold-exprs']))
    if any(x[0] not in ('func','type','global','export') for x in m[1:]):raise ValueError('Unsupported section')
    gs=[x for x in m[1:] if x[0]=='global'];fs=[x for x in m[1:] if x[0]=='func'];n=len(gs)
    if not 1<=n<=bound or gs!=[['global',['mut','i32'],['i32.const','0']] for _ in range(n)]:raise ValueError('State bound/type/initialization')
    exports=[p.w.emit(x) for x in m[1:] if x[0]=='export']
    if sorted(exports)!=sorted(['(export "step" (func 0))','(export "reset" (func 1))']) or len(fs)!=2:raise ValueError('Export/function profile')
    def execute(f,reset=False):
        params=[v for x in f[1:] if isinstance(x,list) and x[0]=='param' for v in x[1:]]
        results=[v for x in f[1:] if isinstance(x,list) and x[0]=='result' for v in x[1:]]
        locals_=[v for x in f[1:] if isinstance(x,list) and x[0]=='local' for v in x[1:]]
        if params!=([] if reset else ['i32']) or results!=([] if reset else ['i32']) or any(x!='i32' for x in locals_):raise ValueError('Function types')
        zero=tuple([0]*(n+2))
        g=[tuple(int(k==i) for k in range(n+2)) for i in range(n)]
        loc=([tuple(int(k==n) for k in range(n+2))] if not reset else [])+[zero]*len(locals_)
        stack=[]
        def walk(x):
            op=x[0]
            for y in x[1:]:
                if isinstance(y,list):walk(y)
            if op=='i32.const':stack.append(tuple([0]*(n+1)+[int(x[1])&p.MASK]))
            elif op=='global.get':stack.append(g[int(x[1])])
            elif op=='local.get':stack.append(loc[int(x[1])])
            elif op=='global.set':g[int(x[1])]=stack.pop()
            elif op=='local.set':loc[int(x[1])]=stack.pop()
            elif op=='local.tee':loc[int(x[1])]=stack[-1]
            elif op in ('i32.add','i32.sub','i32.mul','i32.shl'):
                b=stack.pop();a=stack.pop()
                if op in ('i32.add','i32.sub'):
                    sign=1 if op=='i32.add' else -1;v=tuple((x+sign*y)&p.MASK for x,y in zip(a,b))
                elif op=='i32.mul':
                    if any(a[:-1]) and any(b[:-1]):raise ValueError('Nonlinear multiplication')
                    if any(a[:-1]):a,b=b,a
                    v=tuple((a[-1]*x)&p.MASK for x in b)
                else:
                    if any(b[:-1]):raise ValueError('Variable shift')
                    v=tuple((x<<(b[-1]&31))&p.MASK for x in a)
                stack.append(v)
            elif op=='drop':stack.pop()
            else:raise ValueError('Unsupported instruction '+op)
        for x in f[1:]:
            if isinstance(x,list) and x[0] not in ('type','param','result','local'):walk(x)
        if len(stack)!=(0 if reset else 1):raise ValueError('Stack result')
        return g,stack
    reset,stack=execute(fs[1],True)
    if any(any(row) for row in reset):raise ValueError('Nonzero reset')
    states,stack=execute(fs[0]);out=stack[0]
    if any(row[-1] for row in states) or out[-1]:raise ValueError('Affine bias')
    a=[list(row[:n]) for row in states];b=[row[n] for row in states]
    # Certify y=C*x_after: solve C*[A B]=[L D]. This excludes a general
    # independent direct feedthrough term, which could raise the order bound.
    equations=[list(col) for col in zip(*a)]+[b]
    solution=p.solve(equations,list(out[:n+1]),n)
    if solution is None:raise ValueError('Output not a post-state observation')
    return {'n':n,'bound':bound,'a':a,'b':b,'c':solution['solution'],
            'zero_initial':True,'zero_reset':True,'linear_time_invariant':True,'post_state_output':True}

if __name__=='__main__':print(json.dumps(certify(sys.argv[1]),indent=2))
