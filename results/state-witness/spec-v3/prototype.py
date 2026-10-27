"""Generate non-mutating observers for a restricted, closed core Wasm module.

The zero-length init semantics are specified by Wasm, not claimed as new.
Full observers are test-only and intentionally expose private state to the host.
Numeric observers omit function identity and host memory access for J comparison.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('logical_reset',ROOT/'research/logical-reset/prototype.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


def augment(module,numeric_only=False):
    m=copy.deepcopy(module)
    if any(x[0] not in {'type','func','memory','table','global','data','elem','export'} for x in m[1:]):
        raise ValueError('Closed module required; imports/start/other sections unsupported')
    if any(e[1].startswith('"__sw_') for e in p.section(m,'export')):
        raise ValueError('Reserved observer export prefix')
    memories=p.section(m,'memory');tables=p.section(m,'table');funcs=p.section(m,'func')
    if len(memories)>1 or len(tables)>4:raise ValueError('At most one memory and four tables')
    for item,kind,limit in [(memories,'memory',256),(tables,'table',4096)]:
        for entry in item:
            fields=entry[1:]
            if kind=='table':
                if fields[-1]!='funcref':raise ValueError('Only funcref tables')
                fields=fields[:-1]
            if not 1<=len(fields)<=2 or any(not isinstance(x,str) or not x.isdigit() for x in fields):
                raise ValueError('Nonshared memory32/table32 with numeric limits required')
            if any(int(x)>limit for x in fields):raise ValueError('Research size limit')
    for t in p.section(m,'type'):
        if len(t)!=2 or t[1][0]!='func':raise ValueError('Core function types required')
        for a in t[1][1:]:
            if a[0] not in ('param','result') or any(x not in p.NUM|{'funcref'} for x in a[1:]):
                raise ValueError('Numeric/funcref signatures only')
    manifest={'profile':'numeric' if numeric_only else 'full','memory':bool(memories),'table':bool(tables),'tableCount':len(tables),
              'functions':len(funcs),'globals':[],'segments':[],'originalExports':copy.deepcopy(p.section(m,'export'))}
    def add(name,body):m.append(p.expr('(func (export "__sw_'+name+'") '+body+')'))
    if memories:
        add('pages','(result i32) (memory.size)')
        add('byte','(param i32) (result i32) (i32.load8_u (local.get 0))')
        add('memory_end','(result i32) (i32.load8_u (i32.shl (memory.size) (i32.const 16)))')
        if not numeric_only:m.append(p.expr('(export "__sw_memory" (memory 0))'))
    if tables:
        for index in range(len(tables)):
            suffix='' if index==0 else '_'+str(index)
            add('length'+suffix,f'(result i32) (table.size {index})')
            add('null'+suffix,f'(param i32) (result i32) (ref.is_null (table.get {index} (local.get 0)))')
            add('table_end'+suffix,f'(result i32) (ref.is_null (table.get {index} (table.size {index})))')
            if not numeric_only:
                add('ref'+suffix,f'(param i32) (result funcref) (table.get {index} (local.get 0))')
                m.append(p.expr(f'(export "__sw_table{suffix}" (table {index}))'))
        if not numeric_only:
            # A closed module has only its own functions and null in a funcref table.
            for i in range(len(funcs)):m.append(p.expr(f'(export "__sw_func_{i}" (func {i}))'))
    for i,g in enumerate(p.section(module,'global')):
        typ=g[1][1] if isinstance(g[1],list) and g[1][0]=='mut' else g[1]
        if typ not in p.NUM:raise ValueError('Numeric globals only')
        result='i64' if typ in ('i64','f64') else 'i32'
        body=f'(global.get {i})'
        if typ.startswith('f'):body=f'({result}.reinterpret_{typ} {body})'
        add(f'global_{i}',f'(result {result}) '+body)
        manifest['globals'].append({'index':i,'type':typ,'result':result})
        if not numeric_only:m.append(p.expr(f'(export "__sw_global_host_{i}" (global {i}))'))
    for kind in ('data','elem'):
        for i,s in enumerate(p.section(module,kind)):
            fields=s[1:];mode='passive'
            if fields and isinstance(fields[0],list) and fields[0][0] in ('table','memory'):
                fields=fields[1:]
            if fields and isinstance(fields[0],list) and fields[0][0]=='i32.const':
                mode='active';fields=fields[1:]
            elif fields and fields[0]=='declare':mode='declarative';fields=fields[1:]
            if kind=='data':
                if any(not isinstance(x,str) or not x.startswith('"') for x in fields):
                    raise ValueError('Constant data in memory 0 only')
                n=sum(map(p.literal_length,fields))
            else:
                if not fields or fields[0]!='func' or any(not isinstance(x,str) or not x.isdigit() for x in fields[1:]):
                    raise ValueError('Function-index element segments only')
                n=len(fields)-1
            probe=None
            if (kind=='data' and memories) or (kind=='elem' and tables):
                probe=f'__sw_{kind}_{i}'
                op='memory.init' if kind=='data' else 'table.init'
                # Even a zero-page/zero-entry destination admits endpoint 0, length 0.
                add(f'{kind}_{i}',f'({op} {i} (i32.const 0) (i32.const 1) (i32.const 0))')
            manifest['segments'].append({'kind':kind,'index':i,'mode':mode,'bytesOrEntries':n,'probe':probe,
                'initialLive':mode=='passive' and n>0,'observable':bool(probe) and n>0})
    return m,manifest


def transform(source,destination,numeric_only=False):
    start=time.perf_counter();module=p.read(source);output,manifest=augment(module,numeric_only)
    p.compile_wat(p.w.emit(output),destination)
    manifest.update({'sourceSha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),
                     'outputSha256':hashlib.sha256(Path(destination).read_bytes()).hexdigest(),
                     'sourceBytes':Path(source).stat().st_size,'outputBytes':Path(destination).stat().st_size,
                     'transformSeconds':time.perf_counter()-start})
    Path(destination).with_suffix('.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    return manifest


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('destination',type=Path)
    a.add_argument('--numeric-only',action='store_true');v=a.parse_args()
    print(json.dumps(transform(v.source,v.destination,v.numeric_only)))
