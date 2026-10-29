import argparse, json, shutil, statistics
from pathlib import Path
import prototype as p


def run(main,runtime,audit,output):
    main,runtime,audit,out=map(lambda x:Path(x).resolve(),(main,runtime,audit,output))
    out.mkdir(parents=True,exist_ok=False)
    load=lambda root,name:json.loads((root/name).read_text(encoding='utf-8'))
    manifest=load(main,'manifest.json');checks=load(main,'checks.json');attacks=load(main,'analysis.json')
    timings=load(runtime,'runtime.json');runtime_summary=load(runtime,'summary.json');auditdata=load(audit,'audit.json')
    rows=[]
    for fixture in runtime_summary['rows']:
        entry=dict(name=fixture['name'],modes={})
        for mode,data in fixture['modes'].items():
            targets=[t for t in manifest['targets'] if t['name']==fixture['name'] and t['mode']==mode and (mode!='recovered' or t['origin_mode']=='plain')]
            attack=[a for a in attacks if a['file']==fixture['name']+'.'+mode+'.O3.wasm']
            entry['modes'][mode]=dict(ns=data,bytes={t['opt']:t['bytes'] for t in targets},linear_memory_bytes=0 if mode=='recovered' else 65536)
            if mode!='recovered':
                entry['modes'][mode]['transform_ms_single']=targets[0]['meta']['transform_ms']
                entry['modes'][mode]['analysis_single']=dict(read_ms=attack[0]['read_ms'],recovery_ms=attack[0]['recovery_ms'],candidate_tests=sum(g['candidates'] for g in attack[0]['groups']),full_signature_tests=sum(g['full_signatures'] for g in attack[0]['groups']))
        entry['mix_over_plain']=entry['modes']['mix']['ns']['median']/entry['modes']['plain']['ns']['median']
        entry['recovered_over_plain']=entry['modes']['recovered']['ns']['median']/entry['modes']['plain']['ns']['median']
        rows.append(entry)
    positive=[r for r in checks['rows'] if r['mode']!='bad'];negative=[r for r in checks['rows'] if r['mode']=='bad']
    rss=[r['measurement']['maxRssKiB'] for r in timings]
    report=dict(rows=rows,positive_calls=sum(r['calls'] for r in positive),positive_conditions=len(positive),mismatches=sum(r['mismatches'] for r in positive),negative_conditions=len(negative),negative_detected=sum(r['mismatches']>0 for r in negative),recovered_conditions=len(attacks),unique_recovered_binaries=len({a['sha256'] for a in attacks}),processes=len(timings),max_rss_kib_range=[min(rss),max(rss)],batches_below_10ms=sum(b['ns']<10000000 for r in timings for b in r['measurement']['batches']),total_batches=sum(len(r['measurement']['batches']) for r in timings),analysis_read_ms_range=[min(a['read_ms'] for a in attacks),max(a['read_ms'] for a in attacks)],analysis_ms_range=[min(a['recovery_ms'] for a in attacks),max(a['recovery_ms'] for a in attacks)],interpreter_calls=sum(r['calls'] for r in auditdata['interpreter']),environment=auditdata['environment'],interpretation='Exact finite-domain construction works; activation-cone prior art is close and binary-only canonicalization removes all tested encodings. Independent novelty and additional protection are not established.')
    p.q.save(out/'report.json',report)
    lines=['# 同符号群の係数混合：実測結果','',
        '主結果はmain v2 / runtime v1 / audit v1。3合成関数、各4 channel、1 encoding seed。raw/O3や変換条件を独立ベンチマークと数えない。','',
        '| fixture | plain ns | permutation ns | mix ns | recovered ns | mix/plain | O3 bytes plain/perm/mix/recovered |',
        '|---|---:|---:|---:|---:|---:|---|']
    for row in rows:
        modes=row['modes'];values=[modes[m]['ns']['median'] for m in ('plain','perm','mix','recovered')]
        sizes=[modes[m]['bytes']['O3'] for m in ('plain','perm','mix','recovered')]
        lines.append('| '+row['name']+' | '+' | '.join(f'{v:.3f}' for v in values)+f" | {row['mix_over_plain']:.3f} | "+'/'.join(map(str,sizes))+' |')
    lines += ['',
        '値は各processの9 batch中央値を、3 fresh process間で再び中央値にしたns/呼出し。入力更新・loop・checksumの共通費用を含む。recoveredはraw生成のまま追加O3なし。他3版はO3後。全版に同じbench wrapperを後付けし、追加最適化しない。',
        f"正36条件の{report['positive_calls']:,}呼出しは不一致0。各条件65536 reduced入力と512上位bit違い。混合条件を破る負6条件は全て反例あり。別WABTでは36本×8入力={report['interpreter_calls']}呼出し一致。全42本のbyte再生成一致、4対象外profile拒否。",
        '公開binaryだけを入力とする方式既知の回復は18/18成功。fixtureごとに元版・permutation・mixのraw/O3すべてが同一の短い等価binaryとなった。元の4係数列や混合行列を一意復元したという意味ではない。',
        f"回復本体単回値の範囲は{min(a['recovery_ms'] for a in attacks):.3f}–{max(a['recovery_ms'] for a in attacks):.3f} ms。読取・profile照合・出力compileの時間は別で、反復統計や人間の解析開発時間ではない。",
        f"Node全processの最大RSS範囲は{min(rss)}–{max(rss)} KiB。通常3版のWasm linear memoryは各65536 bytes、回復版はmemoryなし。Pythonの全列挙signatureや解析器のpeak memoryは測定していない。",
        f"{report['batches_below_10ms']}/{report['total_batches']} batchが10ms未満。calibration上限2^22に達した場合もあり、目標batch時間を全件満たしたという解釈はしない。CPU affinity/frequencyは未固定。",
        'この規模でmixとplainの時間は近いが、数%の差を確定した高速化とは扱わない。費用増大は小さい一方、対照より解析を難しくする機構は実証できなかった。',
        '近い既存技術は、有限データ上で同じactivation patternを持つ係数のconeとmerge。整数格子を全列挙する差分だけで独立した新規性があるとは結論しない。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    p.q.save(out/'input-pins.json',{str(root/name):p.q.digest(root/name) for root,names in [(main,['manifest.json','checks.json','analysis.json']),(runtime,['runtime.json','summary.json']),(audit,['audit.json'])] for name in names})
    shutil.copy2(Path(__file__),out/'source-report.py')
    print(json.dumps(dict(positive_calls=report['positive_calls'],recovered=report['recovered_conditions'],rss_range=report['max_rss_kib_range'],short_batches=report['batches_below_10ms'])))


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for name in ('main','runtime','audit','output'):ap.add_argument(name)
    a=ap.parse_args();run(a.main,a.runtime,a.audit,a.output)
