"""Read-only bounded expression analysis for linear WABT WAT.

No module execution or rewriting. Straight-line local integer expressions only;
clear state at every unsupported instruction/control/call/memory boundary.
One input variable, bitwise subexpressions with no arithmetic children, modular
polynomial reduction with Boolean bit variables (b*b=b). This is a limited
algebraic analysis, not a general MBA simplifier or maliciousness classifier.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

LIMIT = 4096


def add(a, b, modulus, scale=1):
    out = dict(a)
    for key, value in b.items():
        out[key] = (out.get(key, 0)+scale*value) % modulus
        if not out[key]:
            del out[key]
    if len(out)>LIMIT:
        raise ValueError('polynomial term limit')
    return out


def mul(a, b, modulus):
    if len(a)*len(b)>LIMIT*4:
        raise ValueError('polynomial product limit')
    out = {}
    for ka, va in a.items():
        for kb, vb in b.items():
            key = tuple(sorted(set(ka)|set(kb)))
            out[key] = (out.get(key, 0)+va*vb) % modulus
    out = {k:v for k,v in out.items() if v}
    if len(out)>LIMIT:
        raise ValueError('polynomial term limit')
    return out


def variables(e):
    if e[0]=='var':
        return {e[1]}
    if e[0]=='const':
        return set()
    return variables(e[1])|variables(e[2])


def size(e):
    return 1 if e[0] in ['var', 'const'] else 1+size(e[1])+size(e[2])


def bit(e, index, modulus):
    op=e[0]
    if op=='var':
        return {(index,):1}
    if op=='const':
        return {():1} if (e[1]>>index)&1 else {}
    if op not in ['and', 'or', 'xor']:
        raise ValueError('arithmetic child of bitwise expression')
    a,b=bit(e[1], index, modulus),bit(e[2], index, modulus)
    if op=='and':
        return mul(a,b,modulus)
    return add(add(a,b,modulus),mul(a,b,modulus),modulus,-1 if op=='or' else -2)


def polynomial(e, bits):
    modulus=1<<bits
    op=e[0]
    if op=='const':
        return {():e[1]%modulus} if e[1]%modulus else {}
    if op in ['var', 'and', 'or', 'xor']:
        out={}
        for index in range(bits):
            out=add(out,bit(e,index,modulus),modulus,1<<index)
        return out
    if op=='shl':
        if e[2][0]!='const':
            raise ValueError('nonconstant shift')
        return {k:(v*(1<<(e[2][1]&(bits-1))))%modulus for k,v in polynomial(e[1],bits).items() if (v*(1<<(e[2][1]&(bits-1))))%modulus}
    a,b=polynomial(e[1],bits),polynomial(e[2],bits)
    if op in ['add','sub']:
        return add(a,b,modulus,1 if op=='add' else -1)
    if op=='mul':
        return mul(a,b,modulus)
    raise ValueError('unsupported expression')


def shift_identity(e, bits):
    if len(variables(e))!=1:
        raise ValueError('requires exactly one independent variable')
    value=polynomial(e,bits)
    for shift in range(1,bits):
        expected={(i,):(1<<(i+shift)) for i in range(bits-shift)}
        if value==expected:
            return shift
    return None


def extract(text, minimum_nodes=12):
    stack=[];locals_={};epoch=0;function=None;matches=[];counts=Counter()
    for number, raw in enumerate(text.splitlines(),1):
        header=re.match(r'^  \(func (\$\S+|\(;\d+;\))',raw)
        if header:
            function=header[1]
        line=raw.strip()
        if not function:
            continue
        constant=re.fullmatch(r'(i32|i64)\.const (-?\d+)',line)
        local=re.fullmatch(r'local\.(get|set|tee) (\$\S+|\d+)',line)
        operation=re.fullmatch(r'(i32|i64)\.(add|sub|mul|and|or|xor|shl)',line)
        if constant:
            stack.append((int(constant[1][1:]),('const',int(constant[2])),number))
            continue
        if local and local[1]=='get':
            stack.append(locals_.get(local[2],(None,('var',f'{epoch}:{local[2]}'),number)))
            continue
        if operation and len(stack)>=2:
            right,left=stack.pop(),stack.pop();bits=int(operation[1][1:])
            if left[0] not in [None,bits] or right[0] not in [None,bits]:
                stack=[];locals_={};epoch+=1;counts['type_barrier']+=1
                continue
            e=(operation[2],left[1],right[1])
            if size(e)>80:
                # Keep an opaque dependency, rather than expanding without bounds.
                stack.append((bits,('var',f'opaque:{number}'),number));counts['node_limit']+=1
            else:
                stack.append((bits,e,min(left[2],right[2])))
            continue
        if local and local[1] in ['set','tee'] and stack:
            value=stack[-1] if local[1]=='tee' else stack.pop()
            locals_[local[2]]=value
            bits,e,start=value
            if bits and size(e)>=minimum_nodes:
                counts['candidates']+=1
                try:
                    shift=shift_identity(e,bits)
                except ValueError as exc:
                    counts[str(exc)]+=1
                else:
                    counts['supported_polynomials']+=1
                    if shift is not None:
                        matches.append(dict(function=function,first_line=start,last_line=number,
                                            output_local=local[2],bits=bits,nodes=size(e),shift=shift,
                                            expression=e,identity=f'x << {shift} modulo 2^{bits}'))
            continue
        if line=='nop':
            continue
        # No propagation over branches, memory, calls, trapping operators or
        # unsupported syntax. Function-local facts must not cross these barriers.
        stack=[];locals_={};epoch+=1;counts['barriers']+=1
        if raw.startswith('  (') and not header:
            function=None
    return matches,dict(counts)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    matches,counts=extract(args.input.read_text(encoding='utf-8'))
    args.output.write_text(json.dumps(dict(matches=matches,counts=counts,code_rewritten=False,runtime_executed=False),indent=2),encoding='utf-8')
    print(json.dumps(dict(matches=len(matches),counts=counts)))


if __name__=='__main__':
    main()
