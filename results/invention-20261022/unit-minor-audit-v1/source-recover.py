"""Known-kernel, binary-only determinant expansion; no source/seed/shear log."""
import argparse
import itertools
import json
import time
from pathlib import Path
import prototype as p


def shape(m):
    return [x for x in m if not isinstance(x,list) or x[0]!='data']


def templates(directory):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=False)
    f=directory/'kernel.raw.wasm'
    p.compile_wat(p.kernel(p.payload([[p.const(1),p.var(0)],[{},p.const(1)]])),f)
    g=directory/'kernel.O3.wasm'; p.tool('wasm-opt',[f,'-O3','-o',g])
    return [shape(p.read(x)) for x in (f,g)]


def unquote(s):
    if not s.startswith('"') or not s.endswith('"'): raise ValueError('bad WAT string')
    s=s[1:-1]; out=bytearray(); i=0
    while i<len(s):
        if s[i]!='\\': out.append(ord(s[i])); i+=1
        elif i+2<len(s) and all(c in '0123456789abcdefABCDEF' for c in s[i+1:i+3]):
            out.append(int(s[i+1:i+3],16)); i+=3
        else:
            out.append({'n':10,'r':13,'t':9,'\\':92,'"':34,"'":39}[s[i+1]]); i+=2
    return bytes(out)


def extract(src, accepted):
    begin=time.perf_counter(); m=p.read(src)
    if shape(m) not in accepted: raise ValueError('unsupported or modified determinant kernel')
    mem=bytearray(65536)
    for x in m[1:]:
        if x[0]!='data': continue
        if len(x)<3 or x[1][0]!='i32.const': raise ValueError('unsupported active data')
        at=int(x[1][1]); data=b''.join(unquote(s) for s in x[2:])
        if at<0 or at+len(data)>len(mem): raise ValueError('data outside coefficient page')
        mem[at:at+len(data)]=data
    count=int.from_bytes(mem[8:12],'little'); end=256+20*count
    if end>len(mem) or any(mem[end:]): raise ValueError('unexpected payload')
    matrix=p.decode(bytes(mem[:end]))
    # Any polynomial evaluated mod 2 depends only on input parity. All 8
    # evaluations certify the rank condition for every 32-bit input.
    for xyz in itertools.product(range(2),repeat=3):
        if parity_rank(matrix,xyz)<len(matrix)-1:
            raise ValueError('rank certificate fails; determinant kernel may trap')
    return matrix,(time.perf_counter()-begin)*1000


def parity_rank(matrix, xyz):
    rows=[sum((p.eval_poly(a,xyz,1)<<j) for j,a in enumerate(line)) for line in matrix]
    rank=0
    for col in range(len(matrix)):
        pivot=next((i for i in range(rank,len(rows)) if rows[i]&(1<<col)),None)
        if pivot is None: continue
        rows[rank],rows[pivot]=rows[pivot],rows[rank]
        for i in range(rank+1,len(rows)):
            if rows[i]&(1<<col): rows[i]^=rows[rank]
        rank+=1
    return rank


def determinant(m, timeout=60):
    start=time.perf_counter(); n=len(m); states=[{} for _ in range(1<<n)]; states[0]=p.const(1)
    peak=1; transitions=0
    for mask in range((1<<n)-1):
        row=bin(mask).count('1')
        if not states[mask]: continue
        for j in range(n):
            if mask&(1<<j) or not m[row][j]: continue
            product=p.mul(states[mask],m[row][j]); dst=mask|(1<<j)
            sign=-1 if bin(mask>>(j+1)).count('1')%2 else 1
            states[dst]=p.add(states[dst],product,sign)
            peak=max(peak,len(product),len(states[dst])); transitions+=1
            if peak>200000: raise OverflowError('polynomial term cap')
            if time.perf_counter()-start>timeout: raise TimeoutError('symbolic determinant budget')
    result=states[-1]
    return result,dict(symbolic_ms=(time.perf_counter()-start)*1000,dimension=n,
                       subset_states=1<<n,transitions=transitions,peak_polynomial_terms=peak,
                       result_terms=len(result),result_degree=p.degree(result),
                       algorithm='division-free subset determinant over Z/(2^32)')


def recover(src, dst, accepted):
    m,read_ms=extract(src,accepted); poly,stats=determinant(m)
    p.compile_wat(p.poly_wat(poly),dst)
    stats.update(read_validate_ms=read_ms,wasm_sha256=p.digest(dst),input_sha256=p.digest(src),
                 status='recovered',source_formula_supplied=False,shear_log_supplied=False,
                 parity_inputs_certified=8,rank_lower_bound=len(m)-1)
    return stats


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('output'); a=ap.parse_args()
    dst=Path(a.output); dst.parent.mkdir(parents=True,exist_ok=True)
    ts=templates(dst.parent/(dst.stem+'-kernel-templates'))
    print(json.dumps(recover(a.input,dst,ts)))
