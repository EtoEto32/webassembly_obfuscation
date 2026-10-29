# -*- coding: utf-8 -*-
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import shutil
import sys
import interactions as p

spec=importlib.util.spec_from_file_location('relaxed_audit',p.r.p.HERE/'relaxed-audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def selector_profile(record):
    I,n=record['inputs'],record['n'];rows=[]
    for j in range(I,I+n):
        D={m^(1<<j):c for m,c in record['terms'] if m>>j&1}
        coords=[k for k in range(I+n) if k!=j];values=[]
        for a in range(1<<len(coords)):
            state=sum(1<<k for q,k in enumerate(coords) if a>>q&1)
            values.append((state,sum(c for m,c in D.items() if state&m==m)))
        best=None
        for size in range(len(coords)+1):
            for subset in itertools.combinations(coords,size):
                forced={};okay=True
                for state,d in values:
                    if d==0:continue
                    key=sum((state>>k&1)<<q for q,k in enumerate(subset));want=int(d<0)
                    if key in forced and forced[key]!=want:okay=False;break
                    forced[key]=want
                if okay:best={'minimum_selector_arity':size,'args':subset};break
            if best is not None:break
        canonical=p.r.local_rule(dict(record['terms']),j,I+n)
        rows.append({'coordinate':j,'zero_tie_selector_arity':len(canonical['args']),
                     'ties':sum(d==0 for _,d in values),**best})
    return rows

def main(source,performance,dst):
    src=Path(source);perfroot=Path(performance);root=Path(dst);root.mkdir(parents=True,exist_ok=False)
    pin_counts={src.name:audit.pincheck(src),perfroot.name:audit.pincheck(perfroot)}
    m=json.loads((src/'manifest.json').read_text());perf=json.loads((perfroot/'performance.json').read_text());certificates=[];profiles=[];replay=[];wabt=[]
    for a in m['attacks']:
        record=p.r.p.rawdata(p.r.p.w.parse(p.r.p.w.tool('wasm2wat',[src/a['file'],'--fold-exprs'])))
        certificates.append({'file':a['file'],**audit.check_rules(record,a['model'],m['models'][a['name']]['gates'])})
        profiles.append({'file':a['file'],'coordinates':selector_profile(record)})
    for t in m['targets']:
        if t['mode']=='plain':model=m['models'][t['name']];text=p.r.p.plain(model['inputs'],model['gates'])
        elif t['mode'].endswith('-recovered'):
            a=next(a for a in m['attacks'] if Path(a['file']).stem+'-recovered.wasm'==t['file']);text=p.r.p.recovered_wat(a['model'])
        else:text=p.r.render(next(a['record'] for a in m['transforms'] if (a['name'],a['mode'])==(t['name'],t['mode'])))
        out=root/t['file']
        if t['stage']=='O3' and not t['mode'].endswith('-recovered'):
            raw=out.with_stem(out.stem+'-raw');p.r.p.save(text,raw);p.r.p.w.tool('wasm-opt',[raw,'-O3','-o',out])
        else:p.r.p.save(text,out)
        assert out.read_bytes()==(src/t['file']).read_bytes();replay.append(t['file'])
        mod=p.r.p.w.parse(p.r.p.w.tool('wasm2wat',[out,'--fold-exprs']));idx=int(next(x[2][1] for x in mod[1:] if x[:2]==['export','"run"']))
        inputs=[0,1,0xffffffff,0x80000000]
        extra=''.join(f'(func (export "p{i}") (result i32) (call {idx} (i32.const {x})))' for i,x in enumerate(inputs))
        probe=out.with_stem(out.stem+'-wabt');p.r.p.save(p.r.p.w.emit(mod)[:-1]+extra+')',probe);result=p.r.p.w.tool('wasm-interp',[probe,'--run-all-exports'])
        for i,x in enumerate(inputs):assert f'p{i}() => i32:{audit.old.logical(m["models"][t["name"]]["gates"],x)[-1]}' in result,result
        wabt.append({'file':t['file'],'calls':4,'stdout':result})
    checks=json.loads((src/'checks.json').read_text());initial=json.loads((src/'all-initial-checks.json').read_text())
    assert all(x['mismatches']==0 and x['traps']==0 for x in checks['rows'])
    assert all(x['mismatches']==0 for x in initial['rows'])
    ratios=[]
    for name in m['models']:
        s={x['mode']:x for x in perf['summary'] if x['name']==name}
        ratios.append({'name':name,'interaction_plain':s['interaction']['ns']/s['plain']['ns'],
                       'interaction_dag':s['interaction']['ns']/s['dag']['ns'],
                       'interaction_recovered':s['interaction']['ns']/s['interaction-recovered']['ns']})
    facts={'source_pins':pin_counts,'conditions':len(m['targets']),
           'distinct_main_binaries':len({hashlib.sha256((src/t['file']).read_bytes()).hexdigest() for t in m['targets']}),
           'normal_calls':sum(x['calls'] for x in checks['rows']),'all_initial_calls':sum(x['calls'] for x in initial['rows']),
           'recoveries':len(m['attacks']),'public_certificate_queries':sum(len(a['public_certificate']['checks']) for a in m['attacks']),
           'recovery_total_ms':[a['milliseconds'] for a in m['attacks']],
           'recovery_core_ms':[a['model']['milliseconds'] for a in m['attacks']],
           'public_certificate_ms':[a['public_certificate']['milliseconds'] for a in m['attacks']],
           'selector_profiles':profiles,'certificates':certificates,'byte_replay':replay,'wabt':wabt,
           'ablations':[{'name':a['name'],'checks':a['public_certificate']} for a in m['ablations']],
           'performance':perf['summary'],'ratios':ratios,'processes':len(perf['rows']),
           'batches':sum(len(x['samples']) for x in perf['rows']),
           'short_batches':sum(s['milliseconds']<10 for x in perf['rows'] for s in x['samples']),
           'maxRSSKiB_range':[min(x['maxRSSKiB'] for x in perf['rows']),max(x['maxRSSKiB'] for x in perf['rows'])]}
    (root/'facts.json').write_text(json.dumps(facts,indent=2),encoding='utf8')
    lines=['# Signed interaction revision: measurement','', '|fixture|mode|ns/call|process median range|optimized bytes|linear memory B|','|---|---|---:|---|---:|---:|']
    for t in perf['summary']:lines.append(f'|{t["name"]}|{t["mode"]}|{t["ns"]:.3f}|{t["range_ns"][0]:.3f}–{t["range_ns"][1]:.3f}|{t["optimized_bytes"]}|{t["linear_memory_bytes"]}|')
    lines+=['','These are tiny 2-input-bit kernels: only four meaningful external inputs each. This is a mechanism screen, not evidence of protection against I/O learning.',
            'The same dynamic stopping rule is used for dag and interaction. 45 fresh processes, seven batches each, warmup 16384, 20ms calibration target; CPU affinity/frequency not fixed.']
    (root/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    shutil.copyfile(Path(__file__),root/'source-interactions-audit.py');shutil.copyfile(p.r.p.HERE/'relaxed-audit.py',root/'source-relaxed-audit.py')
    (root/'pins.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'conditions':facts['conditions'],'distinct':facts['distinct_main_binaries'],'normal_calls':facts['normal_calls'],'initial_calls':facts['all_initial_calls'],'recoveries':facts['recoveries'],'wabt_calls':sum(x['calls'] for x in wabt),'ratios':ratios,
                      'interaction_selector_profiles':[x for x in profiles if 'interaction.wasm' in x['file']]},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
