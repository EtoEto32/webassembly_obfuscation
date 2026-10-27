"""Closed core-Wasm logical reset prototype. Not a patentability claim."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('reset_wat', ROOT/'research/connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
NUM = {'i32', 'i64', 'f32', 'f64'}
DECL = {'type', 'param', 'result', 'local'}
CONTROL = {'block','loop','if','then','else','br','br_if','br_table','return','nop','unreachable','drop','select',
           'call','local.get','local.set','local.tee','global.get','global.set','ref.null','ref.func','ref.is_null'}
SUFFIX = {'const','eqz','eq','ne','lt_s','lt_u','gt_s','gt_u','le_s','le_u','ge_s','ge_u','lt','gt','le','ge',
          'clz','ctz','popcnt','add','sub','mul','div_s','div_u','rem_s','rem_u','and','or','xor','shl','shr_s','shr_u','rotl','rotr',
          'abs','neg','ceil','floor','trunc','nearest','sqrt','div','min','max','copysign','wrap_i64','extend_i32_s','extend_i32_u',
          'extend8_s','extend16_s','extend32_s','demote_f64','promote_f32','reinterpret_i32','reinterpret_i64','reinterpret_f32','reinterpret_f64'}
SUFFIX |= {f'{a}_{b}_{c}' for a in ('trunc','trunc_sat','convert') for b in NUM for c in ('s','u')}

def tool(name, args):
    base=w.BINARYEN if name=='wasm-opt' else w.WABT
    p=subprocess.run([str(base/(name+'.exe')),*map(str,args)],capture_output=True,text=True,encoding='utf-8',timeout=60)
    if p.returncode: raise RuntimeError(json.dumps({'tool':name,'args':list(map(str,args)),'stderr':p.stderr}))
    return p.stdout

def compile_wat(text,path):
    path=Path(path)
    if path.exists(): raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.with_suffix('.wat').write_text(text,encoding='utf-8')
    tool('wat2wasm',[path.with_suffix('.wat'),'-o',path])
    tool('wasm-validate',[path])

def read(path):
    tool('wasm-validate',[path])
    return w.parse(tool('wasm2wat',[path,'--fold-exprs','--no-debug-names']))

def literal_length(s):
    # WABT escapes non-printable bytes as two hex digits. No Python unicode decoding.
    body=s[1:-1]; i=0; n=0
    while i<len(body):
        if body[i]=='\\':
            if i+2<len(body) and re.fullmatch('[0-9a-fA-F]{2}',body[i+1:i+3]): i+=3
            else: i+=2
            n+=1
        else:
            n+=len(body[i].encode('utf-8')); i+=1
    return n

def section(m,k): return [x for x in m[1:] if x[0]==k]
def expr(text): return w.parse('(module '+text+')')[1]

class Reset:
    def __init__(self,mod,mode):
        self.m=copy.deepcopy(mod); self.mode=mode; self.helpers={}; self.extra=[]; self.reset=[]
        if mode not in ('full','plain','no-bounds','no-drop'): raise ValueError('mode')
        allowed={'type','func','memory','table','global','data','elem','export'}
        if any(x[0] not in allowed for x in self.m[1:]): raise ValueError('Closed core module only; imports/start/features unsupported')
        ms=section(self.m,'memory'); ts=section(self.m,'table')
        if len(ms)!=1 or len(ms[0])!=3: raise ValueError('One bounded private memory32 required')
        self.mn,self.mx=map(int,ms[0][1:])
        if not 0<=self.mn<=self.mx<=256: raise ValueError('memory maximum <=256 pages')
        if len(ts)>1: raise ValueError('At most one private table')
        self.tn=self.tx=0
        if ts:
            if len(ts[0])!=4 or ts[0][-1]!='funcref': raise ValueError('Bounded funcref table only')
            self.tn,self.tx=map(int,ts[0][1:3])
            if not 0<=self.tn<=self.tx<=4096: raise ValueError('table maximum <=4096')
        for e in section(self.m,'export'):
            if e[2][0]!='func' or e[1].startswith('"__lr_'): raise ValueError('Only numeric function exports; reserved prefix')
        for t in section(self.m,'type'):
            if len(t)!=2 or t[1][0]!='func': raise ValueError('Function types only')
            for d in t[1][1:]:
                if d[0] not in ('param','result') or any(x not in NUM for x in d[1:]): raise ValueError('Numeric signatures only')
        for i,g in enumerate(section(self.m,'global')):
            gt=g[1][1] if isinstance(g[1],list) and g[1][0]=='mut' else g[1]
            if gt not in NUM or len(g)!=3 or g[2][0]!=gt+'.const': raise ValueError('Numeric constant global initializer only')
            if isinstance(g[1],list): self.reset.append(f'(global.set {i} {w.emit(g[2])})')
        self.g('$lr_m',self.mn)
        self.reset.insert(0,f'(memory.fill (i32.const 0) (i32.const 0) (i32.const {self.mn*65536}))')
        self.reset.append(f'(global.set $lr_m (i32.const {self.mn}))')
        if ts:
            self.g('$lr_t',self.tn)
            self.reset.append(f'(table.fill 0 (i32.const 0) (ref.null func) (i32.const {self.tn}))')
            self.reset.append(f'(global.set $lr_t (i32.const {self.tn}))')
        self.datas=self.segments('data')
        self.elems=self.segments('elem')
        self.has_table=bool(ts)

    def g(self,name,value): self.extra.append(expr(f'(global {name} (mut i32) (i32.const {value}))'))

    def segments(self,kind):
        out=[]
        for i,s in enumerate(section(self.m,kind)):
            xs=s[1:]; active=bool(xs and isinstance(xs[0],list) and xs[0][0]=='i32.const')
            declarative=bool(xs and xs[0]=='declare')
            if active:
                offset=int(xs[0][1]); xs=xs[1:]
            elif declarative: xs=xs[1:]
            if kind=='data':
                if any(not isinstance(t,str) or not t.startswith('"') for t in xs): raise ValueError('constant memory0 data only')
                n=sum(map(literal_length,xs))
            else:
                if not xs or xs[0]!='func' or any(not isinstance(t,str) or not t.isdigit() for t in xs[1:]):
                    raise ValueError('function-index element segments only')
                n=len(xs)-1
            live=not active and not declarative
            glob=f'$lr_{kind}_{i}'
            self.g(glob,n if live else 0)
            self.reset.append(f'(global.set {glob} (i32.const {n if live else 0}))')
            if active:
                name=f'$lr_shadow_{kind}_{i}'
                self.extra.append([kind,name,*xs])
                op='memory.init' if kind=='data' else 'table.init'
                self.reset.append(f'({op} {name} (i32.const {offset}) (i32.const 0) (i32.const {n}))')
            out.append({'n':n,'active':active,'declarative':declarative,'global':glob})
        return out

    def helper(self,name,text):
        self.helpers.setdefault(name,expr('(func '+name+' '+text+')'))
        return name

    def bound(self,addr,length,capacity):
        if self.mode=='no-bounds': return ''
        return f'(if (i64.gt_u (i64.add (i64.extend_i32_u {addr}) {length}) {capacity}) (then unreachable))'

    def memcap(self):return '(i64.shl (i64.extend_i32_u (global.get $lr_m)) (i64.const 16))'
    def tabcap(self):return '(i64.extend_i32_u (global.get $lr_t))'

    def access(self,x):
        op=x[0]; isstore='.store' in op; typ=op.split('.')[0]
        match=re.fullmatch(r'(i32|i64|f32|f64)\.(load|store)(8|16|32)?(_[su])?',op)
        if not match:return None
        width=int(match[3] or typ[1:])//8
        imms=[y for y in x[1:] if isinstance(y,str)]
        args=[y for y in x[1:] if isinstance(y,list)]
        if len(args)!=(2 if isstore else 1) or any(not y.startswith(('offset=','align=')) for y in imms): raise ValueError('Unfolded/multi-memory access unsupported')
        off=next((int(y[7:]) for y in imms if y.startswith('offset=')),0)
        name='$lr_'+op.replace('.','_')+'_'+str(off)+'_'+('_'.join(imms).replace('=','_'))
        check=self.bound('(local.get 0)',f'(i64.const {off+width})',self.memcap())
        params=f'(param i32 {typ})' if isstore else f'(param i32) (result {typ})'
        body=f'({op} {" ".join(imms)} (local.get 0)'+(' (local.get 1)' if isstore else '')+')'
        self.helper(name,params+check+body)
        return ['call',name,*[self.walk(a) for a in args]]

    def walk(self,x):
        if not isinstance(x,list):return x
        op=x[0]
        if op in DECL:
            if op!='type' and any(y not in NUM|{'funcref'} for y in x[1:]): raise ValueError('Local/block type unsupported')
            return x
        a=self.access(x)
        if a is not None:return a
        if op in ('memory.size','table.size'):
            return ['global.get','$lr_m' if op=='memory.size' else '$lr_t']
        if op in ('data.drop','elem.drop'):
            if self.mode=='no-drop':return x
            k='data' if op=='data.drop' else 'elem'
            return ['global.set',f'$lr_{k}_{int(x[1])}',['i32.const','0']]
        if op=='call_indirect':
            # Check the final evaluated table index after all call arguments.
            args=[z for z in x[1:] if isinstance(z,list) and z[0]!='type']
            if not args:raise ValueError('Unfolded indirect call')
            name='$lr_index'
            self.helper(name,'(param i32) (result i32)'+self.bound('(local.get 0)','(i64.const 1)',self.tabcap())+'(local.get 0)')
            out=[self.walk(z) for z in x]
            out[-1]=['call',name,out[-1]]
            return out
        if op in ('memory.grow','table.grow'):
            table=op.startswith('table'); name='$lr_tgrow' if table else '$lr_mgrow'
            args=[self.walk(z) for z in x[1:] if isinstance(z,list)]
            if len(args)!=(2 if table else 1):raise ValueError('Unfolded grow')
            glob='$lr_t' if table else '$lr_m'; maximum=self.tx if table else self.mx
            delta='1' if table else '0'; old='2' if table else '1'; new='3' if table else '2'; physical='4' if table else '3'
            params='(param funcref i32)' if table else '(param i32)'
            size='(table.size 0)' if table else '(memory.size)'
            grow=f'(table.grow 0 (ref.null func) (i32.sub (local.get {new}) (local.get {physical})))' if table else f'(memory.grow (i32.sub (local.get {new}) (local.get {physical})))'
            init=f'(table.fill 0 (local.get {old}) (local.get 0) (local.get {delta}))' if table else f'(memory.fill (i32.shl (local.get {old}) (i32.const 16)) (i32.const 0) (i32.shl (local.get {delta}) (i32.const 16)))'
            text=f'''{params} (result i32) (local i32 i32 i32)
            (local.set {old} (global.get {glob}))
            (if (i64.gt_u (i64.add (i64.extend_i32_u (local.get {old})) (i64.extend_i32_u (local.get {delta}))) (i64.const {maximum})) (then (return (i32.const -1))))
            (local.set {new} (i32.add (local.get {old}) (local.get {delta})))
            (local.set {physical} {size})
            (if (i32.gt_u (local.get {new}) (local.get {physical})) (then
              (if (i32.eq {grow} (i32.const -1)) (then (return (i32.const -1))))))
            {init} (global.set {glob} (local.get {new})) (local.get {old})'''
            self.helper(name,text)
            return ['call',name,*args]
        if op in ('memory.copy','memory.fill','memory.init','table.copy','table.fill','table.init','table.get','table.set'):
            table=op.startswith('table'); cap=self.tabcap() if table else self.memcap()
            args=[self.walk(z) for z in x[1:] if isinstance(z,list)]
            imms=[z for z in x[1:] if isinstance(z,str)]
            need=1 if op=='table.get' else 2 if op=='table.set' else 3
            if len(args)!=need:raise ValueError('Unfolded bulk/table access')
            name='$lr_'+op.replace('.','_')+'_'+'_'.join(imms)
            params=['i32']*need
            if op in ('table.set','table.fill'):params[1]='funcref'
            ret='(result funcref)' if op=='table.get' else ''
            length='(i64.const 1)' if need<3 else '(i64.extend_i32_u (local.get 2))'
            checks=self.bound('(local.get 0)',length,cap)
            if op.endswith('copy'):checks+=self.bound('(local.get 1)',length,cap)
            if op.endswith('init'):
                seg=int(imms[-1]); kind='elem' if table else 'data'
                # Segment-length check remains in no-bounds ablation: it tests memory/table capacity separately.
                checks+=f'(if (i64.gt_u (i64.add (i64.extend_i32_u (local.get 1)) {length}) (i64.extend_i32_u (global.get $lr_{kind}_{seg}))) (then unreachable))'
            body=f'({op} {" ".join(imms)} '+ ' '.join(f'(local.get {i})' for i in range(need))+')'
            self.helper(name,f'(param {" ".join(params)}) {ret} {checks} {body}')
            return ['call',name,*args]
        if op not in CONTROL and not ('.' in op and op.split('.',1)[0] in NUM and op.split('.',1)[1] in SUFFIX):
            raise ValueError('Unsupported opcode: '+str(op))
        return [self.walk(y) for y in x]

    def output(self):
        funcs=section(self.m,'func')
        # Even the plain ablation is checked against the same accepted syntax.
        transformed=[['func',*[self.walk(z) for z in f[1:]]] for f in funcs]
        if self.mode!='plain':
            it=iter(transformed)
            self.m=['module',*[next(it) if x[0]=='func' else x for x in self.m[1:]]]
        else:self.helpers={}
        self.m.extend(self.extra)
        self.m.extend(self.helpers.values())
        self.m.append(expr('(func $lr_reset (export "__lr_reset") '+' '.join(self.reset)+')'))
        return self.m

def transform(src,dst,mode='full'):
    start=time.perf_counter(); mod=read(src); reset=Reset(mod,mode); out=reset.output()
    compile_wat(w.emit(out),dst)
    return {'mode':mode,'sourceBytes':Path(src).stat().st_size,'bytes':Path(dst).stat().st_size,
            'milliseconds':(time.perf_counter()-start)*1000,'helpers':len(reset.helpers),
            'memoryPages':[reset.mn,reset.mx],'tableElements':[reset.tn,reset.tx],
            'dataSegments':len(reset.datas),'elementSegments':len(reset.elems)}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--mode',choices=['full','plain','no-bounds','no-drop'],default='full');a=ap.parse_args()
    print(json.dumps(transform(a.input,a.output,a.mode)))
