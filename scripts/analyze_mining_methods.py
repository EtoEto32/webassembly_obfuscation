"""Static method-level mining-program comparisons; no execution of samples."""
import collections
import csv
import hashlib
import json
import statistics
from pathlib import Path
csv.field_size_limit(20_000_000)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/mining-methods'
PAIR=ROOT/'results/provenance/cryptic-bytes-parent-evidence.json'
FEATURE=ROOT/'results/corpus/module-features.csv'
METRICS=['bytes','instruction_count','defined_functions','code_section_bytes',
         'data_section_bytes','custom_payload_bytes','br_table_count',
         'br_table_in_loop_count','call_count','call_indirect_count','loop_count',
         'nop_count','memory_load_count','memory_store_count']


def write(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        w.writeheader();w.writerows(rows)


def quantile(a,p):
    a=sorted(a); z=(len(a)-1)*p; i=int(z)
    return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(z-i)


def load():
    evidence=json.loads(PAIR.read_text(encoding='utf-8'))
    selected={p:r for p,r in evidence.items() if r['program_category']=='miners'}
    required={r[k] for r in selected.values() for k in ('sha256','comparison_baseline_sha256')}
    features={}
    with FEATURE.open(encoding='utf-8',newline='') as h:
        for r in csv.DictReader(h):
            if r['sha256'] not in required:continue
            ops=json.loads(r['opcodes_json'] or '{}')
            f={m:float(r[m]) if r.get(m) else 0 for m in METRICS if m not in ('memory_load_count','memory_store_count')}
            f.update(status=r['status'],name_section=r['name_section'],object=r['object'],
                     memory_load_count=sum(v for k,v in ops.items() if '.load' in k),
                     memory_store_count=sum(v for k,v in ops.items() if '.store' in k))
            features[r['sha256']]=f
    assert required<=features.keys()
    return selected,features


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    selected,features=load(); pairs=[];manifest=[];excluded=[]
    for path,r in selected.items():
        a,b=features[r['comparison_baseline_sha256']],features[r['sha256']]
        raw=r['declared_transformation']
        method='wasm-mutate/iteration-series' if raw.startswith('wasm-mutate/') else raw
        meta=dict(path=path,program=r['program'],release=r['release_variant'],method=method,
            declared_transformation=raw,sha256=r['sha256'],baseline_sha256=r['comparison_baseline_sha256'])
        manifest.append(dict(**meta,object=b['object'],baseline_object=a['object'],
            source_commit=r.get('source_commit'),source_directory=r.get('source_directory'),
            pairing_basis=r.get('parent_basis'),build_condition='author-distributed release; not rebuilt here'))
        if a['status']!='ok' or b['status']!='ok':
            excluded.append(dict(**meta,baseline_status=a['status'],variant_status=b['status']));continue
        row=dict(**meta,name_before=a['name_section'],name_after=b['name_section'])
        for m in METRICS:
            row[m+'_before']=a[m];row[m+'_after']=b[m];row[m+'_delta']=b[m]-a[m]
            row[m+'_ratio']=b[m]/a[m] if a[m]!=0 else None
        pairs.append(row)
    groups=collections.defaultdict(list)
    for r in pairs:groups[(r['release'],r['method'],r['program'])].append(r)
    program=[]
    for (release,method,name),rs in sorted(groups.items()):
        row=dict(release=release,method=method,program=name,variant_count=len(rs))
        for m in METRICS:
            for stat in ('delta','ratio'):
                values=[r[m+'_'+stat] for r in rs if r[m+'_'+stat] is not None]
                row[m+'_'+stat]=statistics.median(values) if values else None
        program.append(row)
    aggregate=collections.defaultdict(list)
    for r in program:aggregate[(r['release'],r['method'])].append(r)
    summary=[]
    for (release,method),rs in sorted(aggregate.items()):
        for m in METRICS:
            for stat in ('delta','ratio'):
                vals=[r[m+'_'+stat] for r in rs if r[m+'_'+stat] is not None]
                summary.append(dict(release=release,method=method,metric=m,statistic=stat,
                    source_programs=len(rs),defined_values=len(vals),
                    minimum=min(vals) if vals else None,q1=quantile(vals,.25) if vals else None,
                    median=statistics.median(vals) if vals else None,q3=quantile(vals,.75) if vals else None,
                    maximum=max(vals) if vals else None,
                    decrease=sum(v<(1 if stat=='ratio' else 0) for v in vals),
                    unchanged=sum(v==(1 if stat=='ratio' else 0) for v in vals),
                    increase=sum(v>(1 if stat=='ratio' else 0) for v in vals)))
    # Verify identity baselines and independently reproduce prior ratio columns.
    baseline=[r for r in pairs if r['method']=='unobfuscated']
    assert len(baseline)==20
    assert all(r[m+'_delta']==0 for r in baseline for m in METRICS)
    old={r['path']:r for r in csv.DictReader((ROOT/'results/provenance/cryptic-bytes-feature-pairs.csv').open()) if r['program_category']=='miners'}
    for r in pairs:
        for m in ('bytes','instruction_count'):
            assert abs(r[m+'_ratio']-float(old[r['path']][m+'_ratio']))<1e-12
    write('pair-metrics.csv',pairs);write('input-manifest.csv',manifest)
    write('program-method-metrics.csv',program);write('method-summary.csv',summary)
    report=dict(input_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (PAIR,FEATURE)},
        selected=len(selected),analyzed=len(pairs),excluded=excluded,programs=sorted({r['program'] for r in pairs}),
        methods=sorted({r['method'] for r in pairs}),
        tests=['20 identity baselines have zero deltas','all paired size/instruction ratios reproduce existing pair table'],
        aggregation='median within each source program and method; across-program min, linear Q1, median, linear Q3, max',
        limits=['ten author-program labels are related CryptoNight variants, not ten independent malware families',
                'methods are declared settings, not independently confirmed per-file mechanisms',
                'wasm-mutate is an iteration series with mixed mutations, not a single isolated technique',
                'zero denominators are undefined ratios; deltas retained',
                'load/store totals count opcodes, not accessed bytes or dynamic frequencies',
                'no runtime or detector evaluation'])
    (OUT/'analysis-log.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
