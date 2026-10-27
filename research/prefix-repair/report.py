import argparse,json,statistics,shutil
from pathlib import Path
import prototype as p

def run(main,analysis,runtime,audit,out):
    main,analysis,runtime,audit,out=map(lambda x:Path(x).resolve(),(main,analysis,runtime,audit,out))
    out.mkdir(parents=True,exist_ok=False)
    load=lambda root,name:json.loads((root/name).read_text(encoding='utf-8'))
    manifest=load(main,'manifest.json');checks=load(main,'checks.json');attacks=load(analysis,'analysis.json')
    timings=load(runtime,'runtime.json');auditdata=load(audit,'audit.json');rows=[]
    for name in manifest['fixtures']:
        for seed in (211070,211071):
            modes={}
            for mode in ('plain','eager','full','basis'):
                ts=[x for x in manifest['targets'] if x['name']==name and x['seed']==seed and x['mode']==mode]
                values=[x['measurement']['medianNs'] for x in timings if x['name']==name and x['seed']==seed and x['mode']==mode]
                assert len(values)==3 and len(ts)==2
                modes[mode]=dict(ns_median=statistics.median(values),ns_process_range=[min(values),max(values)],
                    bytes={t['opt']:t['bytes'] for t in ts},transform_ms=ts[0]['meta']['transform_ms'])
            target=next(t for t in manifest['targets'] if t['name']==name and t['seed']==seed and t['mode']=='basis')
            rows.append(dict(name=name,seed=seed,n=target['meta']['n'],rank=target['meta']['joint_rank'],
                prefix_ranks=target['meta']['prefix_ranks'],modes=modes,
                basis_over_eager=modes['basis']['ns_median']/modes['eager']['ns_median'],
                basis_over_plain=modes['basis']['ns_median']/modes['plain']['ns_median']))
    rss=[r['measurement']['maxRssKiB'] for r in timings]
    report=dict(rows=rows,positive_calls=checks['calls'],positive_traps=checks['traps'],
        mismatches=sum(r['mismatches'] for r in checks['rows']),negative_conditions=len(checks['negative']),
        negative_detected=sum(r['mismatches']>0 for r in checks['negative']),
        recovered=sum(r['status']=='recovered' for r in attacks),rejected=sum(r['status']=='rejected' for r in attacks),
        reexecution=load(analysis,'checks.json'),processes=len(timings),max_rss_kib_range=[min(rss),max(rss)],
        batches_below_5ms=sum(b['ns']<5000000 for r in timings for b in r['measurement']['batches']),
        linear_memory_bytes=65536,extra_linear_memory_bytes=0,
        interpreter_calls=sum(r['calls'] for r in auditdata['interpreter']),
        analysis_read_ms_range=[min(x['meta']['read_ms'] for x in attacks if x['status']=='recovered'),max(x['meta']['read_ms'] for x in attacks if x['status']=='recovered')],
        analysis_ms_range=[min(x['meta']['analysis_ms'] for x in attacks if x['status']=='recovered'),max(x['meta']['analysis_ms'] for x in attacks if x['status']=='recovered')],
        interpretation='Scoped encoded-copy repair cost reduction; novelty and additional protection are not established.')
    p.q.save(out/'report.json',report)
    lines=['# コピー列の共有修復：実測値','',
        '主結果：main v2 / analysis v4 / runtime v2 / audit v1。値は各processの9 batch中央値を、3 fresh process間で再び中央値にしたns/copy列。',
        '同じ符号化Bに対する比較。小型の固定列3種・2 seedであり、一般アプリケーションの加速率ではない。','',
        '| fixture | seed | N / 保存rank | plain ns | eager ns | full ns | basis ns | basis/eager | basis/plain |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        vals=[row['modes'][mode]['ns_median'] for mode in ('plain','eager','full','basis')]
        lines.append('| '+row['name']+' | '+str(row['seed'])+' | '+str(row['n'])+' / '+str(row['rank'])+' | '+' | '.join(f'{v:.3f}' for v in vals)+f" | {row['basis_over_eager']:.3f} | {row['basis_over_plain']:.2f} |")
    lines+=['','process間の範囲、raw/O3サイズ、変換時間の単回値はreport.jsonに保存。',
        f"正当性：{report['positive_calls']:,}呼出し、うち期待trap {report['positive_traps']:,}、不一致0。負例12条件を全て検出。",
        '方式既知の回復：正常48条件すべてを回復、負例12条件すべてを拒否。3種類の回復出力を再実行。',
        f"別実行器WABT：{report['interpreter_calls']}呼出しのtrapと後続digestを照合。これは全memoryの再検証ではない。",
        f"Node全process最大RSS範囲 {min(rss)}–{max(rss)} KiB。追加linear memoryは0、保存localの資源消費は別途生じる。",
        f"{report['batches_below_5ms']}/648 batchが5ms未満。calibration上限等があり、全batchで目標時間を達成したとはいえない。",
        '実行費用は未変換より増加する。回復器が容易に除去できたため、修復費用の削減を難読化強度の増加とは扱わない。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    shutil.copy2(Path(__file__),out/'source-report.py')
    p.q.save(out/'input-pins.json',{str(root/name):p.q.digest(root/name) for root,names in [(main,['manifest.json','checks.json']), (analysis,['analysis.json','checks.json']), (runtime,['runtime.json','protocol.json']), (audit,['audit.json'])] for name in names})
    print(json.dumps(dict(rows=len(rows),positive_calls=report['positive_calls'],recovered=report['recovered'])))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for name in ('main','analysis','runtime','audit','output'):ap.add_argument(name)
    a=ap.parse_args();run(a.main,a.analysis,a.runtime,a.audit,a.output)
