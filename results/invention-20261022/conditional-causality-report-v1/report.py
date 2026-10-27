# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import sys


def main(main_dir,perf_dir,audit_dir,out):
    main_dir,perf_dir,audit_dir,out=map(Path,(main_dir,perf_dir,audit_dir,out));out.mkdir(parents=True,exist_ok=False)
    m=json.loads((main_dir/'manifest.json').read_text(encoding='utf8'))
    pf=json.loads((perf_dir/'facts.json').read_text(encoding='utf8'))
    audit=json.loads((audit_dir/'facts.json').read_text(encoding='utf8'))
    checks=json.loads((main_dir/'checks.json').read_text(encoding='utf8'))
    data={'main_targets':len(m['targets']),'byte_distinct_main':len({hashlib.sha256((main_dir/t['file']).read_bytes()).hexdigest() for t in m['targets']}),'main_calls':checks['main_calls'],'probe_calls':checks['probe_calls'],'recoveries':len(m['recoveries']),'helper_smt':len(audit['helper_equivalence']),'composition_cases':sum(len(t['facts']) for t in audit['composition']),'wabt_calls':sum(t['calls'] for t in audit['interpreter']),'perf_processes':pf['processes'],'perf_batches':pf['batches'],'perf_short_batches':len(pf['short_batches']),'fixtures':[]}
    for name,f in m['fixtures'].items():
        ts={t['mode']:t for t in pf['targets'] if t['fixture']==name}
        cyclic=next(t['record'] for t in m['transforms'] if t['fixture']==name and t['mode']=='cyclic')
        core=perf_dir/ts['plain']['core']
        same={mode:core.read_bytes()==(perf_dir/ts[mode]['core']).read_bytes() for mode in ('ordered-recovered','cyclic-recovered')}
        if not all(same.values()):raise AssertionError('Recovered optimized implementation not byte-identical')
        # Kahn's algorithm on the union checks an actual cycle, not just backward labels.
        n=len(f['ops']);edges={(a,b) for order in f['orders'] for a,b in zip(order,order[1:])}
        pending=set(range(n));removed=[]
        while True:
            ready=sorted(j for j in pending if not any(a in pending and b==j for a,b in edges))
            if not ready:break
            pending.difference_update(ready);removed.extend(ready)
        if not pending:raise AssertionError('No static cycle')
        row={'fixture':name,'operators':n,'schedule_length':len(cyclic['schedule']),'union_has_cycle':True,'kahn_remaining_vertices':sorted(pending),'performance':ts,'cyclic_over_plain':ts['cyclic']['median_ns']/ts['plain']['median_ns'],'cyclic_over_ordered':ts['cyclic']['median_ns']/ts['ordered']['median_ns'],'optimized_recovered_equal_plain':same}
        data['fixtures'].append(row)
    data['recovery_timing']={mode:{key:{'min':min(vals),'median':statistics.median(vals),'max':max(vals)} for key in ('milliseconds','read_guard_ms','core_ms') for vals in [[r[key] for r in m['recoveries'] if r['mode']==mode]]} for mode in ('ordered','cyclic')}
    data['transform_ms']=[t['milliseconds'] for t in m['transforms']]
    data['max_rss_kib_range']=[min(t['rss_range_kib'][0] for t in pf['targets']),max(t['rss_range_kib'][1] for t in pf['targets'])]
    (out/'facts.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
    lines=['# 条件別の循環する共有演算：比較','', '時刻2026-10-22。時間はns/call、3 process中央値の中央値。1–5 ns付近の小差を速度優位と解釈しない。','', '|fixture|演算数/固定schedule長|plain|ordered VM|cyclic|cyclic回復|cyclic/plain|cyclic/ordered|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in data['fixtures']:
        t=r['performance'];lines.append(f'|{r["fixture"]}|{r["operators"]}/{r["schedule_length"]}|{t["plain"]["median_ns"]:.3f}|{t["ordered"]["median_ns"]:.3f}|{t["cyclic"]["median_ns"]:.3f}|{t["cyclic-recovered"]["median_ns"]:.3f}|{r["cyclic_over_plain"]:.3f}|{r["cyclic_over_ordered"]:.3f}|')
    lines+=['','|fixture|plain O3 bytes|ordered O3 bytes|cyclic O3 bytes|回復 O3 bytes|','|---|---:|---:|---:|---:|']
    for r in data['fixtures']:
        t=r['performance'];lines.append('|'+r['fixture']+'|'+'|'.join(str(t[k]['core_bytes']) for k in ('plain','ordered','cyclic','cyclic-recovered'))+'|')
    lines+=['','両VMはprivate linear memory 65,536 bytesとn個のtable entryを追加する。直接版・回復版のlinear memoryは0。回復O3の6本はそれぞれ対応するplain O3とbyte一致。プロセスRSSはNode全体の測定。','',f'主{data["main_targets"]}条件（異なるbinary {data["byte_distinct_main"]}本）、{data["main_calls"]}通常呼出し、{data["probe_calls"]}任意初期状態probe。回復{data["recoveries"]}条件、helper同値SMT {data["helper_smt"]}、記号合成順{data["composition_cases"]}条件、WABT {data["wabt_calls"]}呼出し。','', '通常VMからの追加費用は約33–59%。scheduleの共有による10–26 bytesの縮小はあるが、元版より大きく、保護費用上の優位は示されない。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    shutil.copyfile(__file__,out/'report.py')
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir()) if f.is_file()},indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in data.items() if k not in ('fixtures','recovery_timing','transform_ms')}))


if __name__=='__main__':main(*sys.argv[1:])
