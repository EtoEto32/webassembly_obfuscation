"""Position-dependent byte representation; nonshared, fixed Wasm memory only."""
import argparse,copy,importlib.util,json,random,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('br_common',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
MODES=('plain','decode-scalar','direct-scalar','direct-simd','bulk-scalar','bulk-simd')
def expr(s):return q.w.parse('(module '+s+')')[1]
def vc(xs):return q.w.emit(q.vc(xs if isinstance(xs,list) else [xs]*16))
def sw(t,x):return f'(i8x16.swizzle {vc(t)} {x})'
def configuration(seed):
    r=random.Random(seed);p=list(range(16));r.shuffle(p)
    return p,[r.randrange(256) for _ in range(16)]
def keys(k,a,vector=False):
    index=f'(i8x16.add (i8x16.splat {a}) {vc(list(range(16)))})' if vector else f'(i8x16.splat {a})'
    v=sw(k,f'(v128.and {index} {vc(15)})')
    return v if vector else f'(i8x16.extract_lane_u 0 {v})'
def permute(p,x,vector=False):
    v=x if vector else f'(i8x16.splat {x})'
    a=sw(p,f'(v128.and {v} {vc(15)})');b=sw(p,f'(i8x16.shr_u {v} (i32.const 4))')
    result=f'(v128.or {a} (i8x16.shl {b} (i32.const 4)))'
    return result if vector else f'(i8x16.extract_lane_u 0 {result})'
def decode_strings(ss):
    out=bytearray()
    for s in ss:
        i=1
        while i<len(s)-1:
            if s[i]!='\\':out.extend(s[i].encode('utf-8'));i+=1
            elif re.fullmatch('[0-9a-fA-F]{2}',s[i+1:i+3]):out.append(int(s[i+1:i+3],16));i+=3
            else:out.append({'t':9,'n':10,'r':13,'"':34,"'":39,'\\':92}[s[i+1]]);i+=2
    return bytes(out)
def string(bs):return '"'+''.join('\\'+format(b,'02x') for b in bs)+'"'
def profile(m):
    allowed={'type','func','memory','data','global','export','start'}
    if any(x[0] not in allowed for x in m[1:]):raise q.Unsupported('unsupported module field')
    mem=[x for x in m[1:] if x[0]=='memory']
    if len(mem)!=1 or mem[0] not in (['memory','1','1'],['memory','2','2']):raise q.Unsupported('fixed 1/2 page memory required')
    if any(x[0]=='export' and x[2][0]=='memory' for x in m[1:]):raise q.Unsupported('private memory required')
    fs=[x for x in m[1:] if x[0]=='func'];limit=int(mem[0][1])*65536
    for f in fs:
        for e in q.walk(f):
            op=e[0]
            if '.atomic.' in op or op.startswith('atomic.'):raise q.Unsupported('atomic operation')
            if op in ('i32.load8_u','i32.load8_s','i32.store8'):
                if any(isinstance(x,str) and x.startswith('offset=') and int(x[7:])!=0 for x in e[1:]):raise q.Unsupported('nonzero memory offset')
            elif 'load' in op or 'store' in op or op.startswith(('v128.','i8x16.','i16x8.','i32x4.','i64x2.')):raise q.Unsupported('unsupported memory or vector operation')
            elif op.startswith('memory.') and op not in ('memory.copy','memory.size'):raise q.Unsupported('unsupported bulk/grow')
            elif op in ('call_indirect','return_call_indirect','call_ref','return_call_ref','data.drop'):raise q.Unsupported('indirect or segment operation')
    data=[]
    for x in m[1:]:
        if x[0]!='data':continue
        if len(x)<3 or x[1][:1]!=['i32.const'] or any(not isinstance(s,str) or not s.startswith('"') for s in x[2:]):raise q.Unsupported('constant active data only')
        off=int(x[1][1],0)&0xffffffff;bs=decode_strings(x[2:])
        if off+len(bs)>limit:raise q.Unsupported('out-of-bounds initial data')
        data.append((off,bs))
    return fs,limit,data
def copy_body(mode,p,k,limit):
    # Params d,s,n; locals index=3, source-address=4, dest-address=5.
    setup=''
    if mode.startswith('bulk'):setup='(memory.copy (local.get 0) (local.get 1) (local.get 2))'
    else:
        bads=[f'(i64.gt_u (i64.add (i64.extend_i32_u (local.get {a})) (i64.extend_i32_u (local.get 2))) (i64.const {limit}))' for a in (0,1)]
        setup=f'(if (i32.or {bads[0]} {bads[1]}) (then (unreachable)))'
    def step(width,backward=False):
        vec=width==16;d='(local.get 5)';s='(local.get 4)'
        before=f'(local.set 3 (i32.sub (local.get 3) (i32.const {width})))' if backward else ''
        address=f'(local.set 4 (i32.add (local.get 1) (local.get 3))) (local.set 5 (i32.add (local.get 0) (local.get 3)))'
        val=f'({"v128.load align=1" if vec else "i32.load8_u"} {d if mode.startswith("bulk") else s})'
        if mode=='decode-scalar':
            val=permute(p,permute(q.inv(p),f'(i32.xor {val} {keys(k,s)})'))
            val=f'(i32.xor {val} {keys(k,d)})'
        elif vec:val=f'(v128.xor {val} (local.get 6))'
        else:
            op='v128.xor' if vec else 'i32.xor';val=f'({op} {val} ({op} {keys(k,s,vec)} {keys(k,d,vec)}))'
        after='' if backward else f'(local.set 3 (i32.add (local.get 3) (i32.const {width})))'
        return before+address+f'({"v128.store align=1" if vec else "i32.store8"} {d} {val})'+after
    def loops(back=False):
        text='(local.set 3 (local.get 2))' if back else '(local.set 3 (i32.const 0))'
        if mode.endswith('simd'):
            phase='(i32.and (local.get 2) (i32.const 15))' if back else '(i32.const 0)'
            sk=keys(k,f'(i32.add (local.get 1) {phase})',True);dk=keys(k,f'(i32.add (local.get 0) {phase})',True)
            text+=f'(local.set 6 (v128.xor {sk} {dk}))'
        for width in ([16,1] if mode.endswith('simd') else [1]):
            remain='(local.get 3)' if back else '(i32.sub (local.get 2) (local.get 3))'
            text+=f'(block (loop (br_if 1 (i32.lt_u {remain} (i32.const {width}))) {step(width,back)} (br 0)))'
        return text
    body=loops() if mode.startswith('bulk') else f'(if (i32.le_u (local.get 0) (local.get 1)) (then {loops()}) (else {loops(True)}))'
    return f'(func (param i32 i32 i32) (local i32 i32 i32) {"(local v128)" if mode.endswith("simd") else ""} {setup} {body})'
def transform(src,dst,mode='bulk-simd',seed=7):
    if mode not in MODES:raise q.Unsupported('mode')
    begin=time.perf_counter();m=q.read(src);fs,limit,data=profile(m);p,k=configuration(seed);base=len(fs)
    if mode=='plain':q.compile(q.w.emit(m),dst);return dict(mode=mode,seed=seed,ms=(time.perf_counter()-begin)*1000,encoding=None,mask=None)
    def visit(e):
        if not isinstance(e,list):return e
        children=[visit(x) for x in e[1:]];op=e[0]
        if op in ('i32.load8_u','i32.load8_s','i32.store8','memory.copy'):
            args=[x for x in children if isinstance(x,list)]
            which=base+(1 if op=='i32.store8' else 2 if op=='memory.copy' else 0)
            result=['call',str(which),*args]
            return ['i32.extend8_s',result] if op=='i32.load8_s' else result
        return [op,*children]
    original_start=next((int(x[1]) for x in m[1:] if x[0]=='start'),None)
    m=['module',*[visit(x) if x[0]=='func' else copy.deepcopy(x) for x in m[1:] if x[0] not in ('start','data')]]
    # Only initially-zero gaps need runtime encoding; active bytes are encoded
    # statically, in their original order, so overlapping segments remain correct.
    covered=bytearray(limit)
    for off,bs in data:
        enc=bytes(((p[b&15]|(p[b>>4]<<4))^k[(off+i)&15]) for i,b in enumerate(bs))
        m.append(['data',['i32.const',str(off)],string(enc)]);covered[off:off+len(bs)]=b'\1'*len(bs)
    gaps=[];start=None
    for i,hit in enumerate(covered+b'\1'):
        if not hit and start is None:start=i
        if hit and start is not None:gaps.append((start,i));start=None
    raw='(i32.xor (i32.load8_u (local.get 0)) '+keys(k,'(local.get 0)')+')'
    reader=f'(func (param i32) (result i32) {permute(q.inv(p),raw)})'
    encoded=f'(i32.xor {permute(p,"(local.get 1)")} {keys(k,"(local.get 0)")})'
    writer=f'(func (param i32 i32) (i32.store8 (local.get 0) {encoded}))'
    init=''
    for a,b in gaps:
        init+=f'(local.set 0 (i32.const {a})) (block (loop (br_if 1 (i32.ge_u (local.get 0) (i32.const {b}))) (i32.store8 (local.get 0) (i32.xor (i32.const {p[0]*17}) {keys(k,"(local.get 0)")})) (local.set 0 (i32.add (local.get 0) (i32.const 1))) (br 0)))'
    if original_start is not None:init+=f'(call {original_start})'
    m.extend([expr(reader),expr(writer),expr(copy_body(mode,p,k,limit)),expr(f'(func (local i32) {init})'),['start',str(base+3)]])
    q.compile(q.w.emit(m),dst)
    return dict(mode=mode,seed=seed,ms=(time.perf_counter()-begin)*1000,encoding=p,mask=k,memory_bytes=limit,gaps=len(gaps),source_functions=base)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=MODES,default='bulk-simd');ap.add_argument('--seed',type=int,default=7);a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode,a.seed)))
