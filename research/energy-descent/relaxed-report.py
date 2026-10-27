# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import shutil
import sys
import relaxed as r

def load(root,name):return json.loads((root/name).read_text(encoding='utf8'))
def pincheck(root):
    pins=load(root,'pins.json')
    for f,h in pins.items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,f
    return len(pins)

def uncapped_dependencies(record):
    I,n=record['inputs'],record['n'];rules={}
    for j in range(I,I+n):
        D={mask^(1<<j):c for mask,c in record['terms'] if mask>>j&1}
        support=sorted({k for mask in D for k in range(I+n) if mask>>k&1})
        if len(support)>20:raise ValueError('Support cap')
        truth=[]
        for a in range(1<<len(support)):
            state=sum(1<<k for q,k in enumerate(support) if a>>q&1);d=sum(c for mask,c in D.items() if state&mask==mask)
            if d==0:raise ValueError('Tie')
            truth.append(int(d<0))
        rules[j]=[support[q] for q in range(len(support)) if any(truth[a]!=truth[a^(1<<q)] for a in range(len(truth)) if not a>>q&1)]
    pending=set(rules);done=set(range(I))
    while True:
        ready=[j for j in pending if set(rules[j])<=done]
        if not ready:break
        pending.difference_update(ready);done.update(ready)
    return {'dependencies':rules,'topological_sort_remainder':sorted(pending),'cyclic':bool(pending)}

def main(base,dst):
    base=Path(base);root=Path(dst);root.mkdir(parents=True,exist_ok=False)
    names=['energy-relaxed-v1','energy-relaxed-coupled-v1','energy-relaxed-audit-v1','energy-relaxed-performance-v1'];pins={name:pincheck(base/name) for name in names}
    mains=[(base/name,load(base/name,'manifest.json')) for name in names[:2]]
    targets=[(path,t) for path,m in mains for t in m['targets']]
    checks=[x for path,m in mains for x in load(path,'checks.json')['rows']]
    initial=[x for path,m in mains for x in load(path,'all-initial-checks.json')['rows']]
    attacks=[x for path,m in mains for x in m['attacks']];old=[x for path,m in mains for x in m['old_attack']]
    audit=load(base/names[2],'audit.json');perf=load(base/names[3],'performance.json');pc=load(base/names[3],'checks.json')
    coupled=mains[-1][1];by_mode={t['mode']:t for t in coupled['transforms']};dependency=uncapped_dependencies(by_mode['synth']['record']);assert dependency['cyclic']
    assert all(x['mismatches']==0 and x['traps']==0 for x in checks)
    assert all(x['mismatches']==0 for x in initial)
    stats={x['mode']:x for x in perf['summary']}
    facts={'source_pin_counts':pins,'fixtures':sum(len(m['models']) for _,m in mains),'conditions':len(targets),
           'distinct_main_binaries':len({hashlib.sha256((path/t['file']).read_bytes()).hexdigest() for path,t in targets}),
           'normal_calls':sum(x['calls'] for x in checks),'all_initial_calls':sum(x['calls'] for x in initial),
           'recoveries':len(attacks),'old_attack_unsupported':sum(x['status']=='unsupported' for x in old),
           'old_attack_unsupported_reasons':[x['reason'] for x in old if x['status']=='unsupported'],
           'coupled_full_dependency_check':dependency,'coupled_weights':{k:v['weights'] for k,v in by_mode.items()},
           'coupled_strict_deviation':by_mode['synth']['deviation']['strict'],
           'recovery_total_ms_range':[min(x['milliseconds'] for x in attacks),max(x['milliseconds'] for x in attacks)],
           'recovery_core_median_ms_range':[min(x['median_ms'] for x in audit['core_timings']),max(x['median_ms'] for x in audit['core_timings'])],
           'coupled_core_timings':[x for x in audit['core_timings'] if 'coupled' in x['file']],
           'byte_replay':len(audit['byte_replay']),'wabt_calls':sum(x['calls'] for x in audit['wabt']),
           'minimizer_unsat_checks':sum(len(x['steps']) for x in audit['minimization_and_output_certificates']),
           'output_equivalence_unsat_checks':len(audit['minimization_and_output_certificates']),
           'no_false_minimum_unsat_checks':len(audit['fresh_no_false_minimum']),
           'negative_flat_minima':len(audit['flat_counterexamples']),
           'performance':perf['summary'],'processes':len(perf['rows']),'batches':sum(len(x['samples']) for x in perf['rows']),
           'short_batches':sum(s['milliseconds']<10 for x in perf['rows'] for s in x['samples']),
           'synth_plain_time_ratio':stats['synth']['ns']/stats['plain']['ns'],
           'synth_recovered_time_ratio':stats['synth']['ns']/stats['synth-recovered']['ns'],
           'synth_dag_time_ratio':stats['synth']['ns']/stats['dag']['ns'],
           'maxRSSKiB_range':[min(x['maxRSSKiB'] for x in perf['rows']),max(x['maxRSSKiB'] for x in perf['rows'])],
           'performance_run_checks':sum(x['run_calls'] for x in pc['rows']),
           'performance_wrapper_checks':sum(x['wrapper_checks'] for x in pc['rows']),'cpu':pc['cpu']}
    assert (facts['fixtures'],facts['conditions'],facts['normal_calls'],facts['recoveries'])==(7,70,180420,28)
    assert facts['all_initial_calls']==2922496 and facts['old_attack_unsupported']==2 and facts['minimizer_unsat_checks']==248
    (root/'facts.json').write_text(json.dumps(facts,indent=2),encoding='utf8')
    table=['# Energy改良の実測比較','', '対象はordered-guardsの小合成回路一つ。O3、共通Wasm内部loop。','',
           '|版|ns/call中央値|process中央値範囲ns|最適化後byte|宣言線形memory B|','|---|---:|---:|---:|---:|']
    for t in perf['summary']:table.append(f'|{t["mode"]}|{t["ns"]:.3f}|{t["range_ns"][0]:.3f}–{t["range_ns"][1]:.3f}|{t["optimized_bytes"]}|{t["linear_memory_bytes"]}|')
    table+=['',f'合成版/元版 {facts["synth_plain_time_ratio"]:.3f}、合成版/回復版 {facts["synth_recovered_time_ratio"]:.3f}、合成版/優越版 {facts["synth_dag_time_ratio"]:.4f}。',
            '15 fresh process、各7batch、warmup 16384、20ms calibration目標、10ms未満batch 0。CPU affinity/周波数は固定していない。',
            '優越版も合成版も変化がなくなるまでsweepする。同じ停止規則の比較で、旧固定n回実装との性能比較ではない。',
            '約1.9%の中央値差にはprocess範囲の重なりがあり、安定した性能改善と結論しない。',
            'maxRSSはNode process全体の指標。保護方式単独のheap量ではない。',
            '',f'主70条件はbyte異なる{facts["distinct_main_binaries"]}本。180420通常呼出し、別の初期値公開probeで2922496呼出しが一致。両コーパスの重複は除外していない。',
            '28回復すべて成功。旧解析の未対応2条件は5入力lookup制限が直接の理由。制限を外した依存検査でも循環があるが、最小化消去は回復できる。']
    (root/'comparison.md').write_text('\n'.join(table)+'\n',encoding='utf8');shutil.copyfile(Path(__file__),root/'source-relaxed-report.py')
    (root/'pins.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in facts.items() if not isinstance(v,(dict,list))},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
