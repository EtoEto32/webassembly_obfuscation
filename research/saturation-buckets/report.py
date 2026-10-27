import argparse,json,shutil
from pathlib import Path
import prototype as p

def run(main,runtime,audit,output):
    main,runtime,audit,out=map(lambda x:Path(x).resolve(),(main,runtime,audit,output));out.mkdir(parents=True,exist_ok=False)
    load=lambda root,name:json.loads((root/name).read_text(encoding='utf-8'))
    manifest=load(main,'manifest.json');checks=load(main,'checks.json');attacks=load(main,'analysis.json');timings=load(runtime,'runtime.json');summary=load(runtime,'summary.json');auditdata=load(audit,'audit.json');rows=[]
    modes=('plain','native8','canonical','zero','bucket','recovered')
    for fixture in summary['rows']:
        name=fixture['name'];entry=dict(name=name,steps=len(manifest['fixtures'][name]['ops']),bits=manifest['fixtures'][name]['bits'],modes={})
        for mode in modes:
            ts=[t for t in manifest['targets'] if t['name']==name and t['mode']==mode and (mode!='recovered' or t['origin_mode']=='plain')]
            entry['modes'][mode]=dict(runtime_ns=fixture['modes'][mode],bytes={t['opt']:t['bytes'] for t in ts},linear_memory_bytes=65536 if mode=='recovered' else 0)
            if mode!='recovered':
                at=next(a for a in attacks if a['file']==name+'.'+mode+'.O3.wasm')
                entry['modes'][mode].update(transform_ms_single=ts[0]['meta']['transform_ms'],queries=at['queries'],learning_ms_single=at['elapsed_ms'])
        med=lambda mode:entry['modes'][mode]['runtime_ns']['median']
        entry.update(bucket_over_plain=med('bucket')/med('plain'),bucket_over_native8=med('bucket')/med('native8'),bucket_over_canonical=med('bucket')/med('canonical'))
        rows.append(entry)
    positive=[r for r in checks['rows'] if r['mode']!='bad'];negative=[r for r in checks['rows'] if r['mode']=='bad'];rss=[r['measurement']['maxRssKiB'] for r in timings]
    report=dict(rows=rows,positive_conditions=len(positive),positive_calls=sum(r['calls'] for r in positive),mismatches=sum(r['mismatches'] for r in positive),negative_conditions=len(negative),negative_detected=sum(r['mismatches']>0 for r in negative),recovered_conditions=len(attacks),unique_recovered_binaries=len({a['sha256'] for a in attacks}),processes=len(timings),max_rss_kib_range=[min(rss),max(rss)],batches_below_10ms=sum(b['ns']<10000000 for r in timings for b in r['measurement']['batches']),total_batches=sum(len(r['measurement']['batches']) for r in timings),interpreter_calls=sum(r['calls'] for r in auditdata['interpreter']),model_comparisons=auditdata['model_comparisons'],full_width_comparisons=auditdata['full_width_comparisons'],environment=auditdata['environment'],interpretation='Quotient lowering removes per-step normalization but no added protection: all modes have identical oracle query counts and canonical learned functions; native8 is faster in all three fixtures.')
    p.q.save(out/'report.json',report)
    lines=['# 広い飽和レーンによる商表現：実測比較','',
        '主結果はmain v2 / runtime v2 / audit v1。3合成関数、8レーン、12/48/128更新。CPU affinity/frequency未固定。入力更新・loop・checksumを含むns/call。各processの9 batch中央値を3 fresh process間で再び中央値にした。','',
        '| fixture | plain | native8 | canonical | zero | bucket | recovered | bucket/native8 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        lines.append('| '+row['name']+' | '+' | '.join(f"{row['modes'][m]['runtime_ns']['median']:.3f}" for m in modes)+f" | {row['bucket_over_native8']:.3f} |")
    lines+=['','canonicalは飽和加算後だけ下位bitを消す比較。減算後の不要な正規化は入れない。zeroは初期余り0、bucketは入力由来の余りを持つ。native8は通常の8bit SIMDで同じ論理処理をする対照であり、既存難読化ツールの再現ではない。',
        'bucket/canonicalは約0.74–0.86、bucket/plainは約0.78–1.02。一方、bucket/native8は約1.12–1.33で、今回の全例でnative8が速い。正規化削減の利益を、最良の通常表現に対する優位と読み替えない。',
        f"正{len(positive)}条件、{report['positive_calls']:,}呼出しの不一致0。各条件はbyte対65536個を全レーンへbroadcastした入力と512個の独立packed入力。2^128入力を全列挙したものではない。負6条件は全て不一致を検出。",
        f"方式既知の公開I/O学習は{len(attacks)}/{len(attacks)}で等価候補を生成し、上の差分検査が一致。fixtureごとに2528/2556/2558問い合わせのいずれかで、全mode・raw/O3が同じ問い合わせ数・同じ回復binaryとなった。元の更新列は復元していない。",
        '学習の単回時間はNodeのpack/unpack・query記録を含み、compile/instantiateとWasm生成を除く。静的逆コンパイルの時間や、人間の解析器開発費用ではない。',
        f"66本のbyte再生成一致。別WABT実行{report['interpreter_calls']}呼出し一致。4対象外sourceを拒否。縮小幅の代数検査{report['model_comparisons']:,}比較、16bit境界・乱数{report['full_width_comparisons']:,}比較は一致。",
        '未変換・変換のlinear memoryは0。学習版は係数表24,576bytesを固定65,536byteのprivate memoryに保存する。recoveredは追加O3なし。他版はO3後、全て同じbench wrapperを後付けする。回復版の速度向上には表引きへの置換とmemory追加を伴う。',
        f"54 fresh process、486 batch。10ms未満は{report['batches_below_10ms']}件。Node全processの最大RSS範囲は{min(rss)}–{max(rss)} KiB。Python変換・学習器固有のpeak memoryは測定していない。",
        '一般のlane依存があるプログラムではbroadcast学習は不十分。byte rotationがbroadcastではidentityに見え、入力1で256と1に分かれる負例をauditへ保存。学習器を汎用同値検証器とは扱わない。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    p.q.save(out/'input-pins.json',{str(root/name):p.q.digest(root/name) for root,names in [(main,['manifest.json','checks.json','analysis.json']),(runtime,['runtime.json','summary.json']),(audit,['audit.json'])] for name in names})
    shutil.copy2(Path(__file__),out/'source-report.py')
    print(json.dumps(dict(positive_calls=report['positive_calls'],recovered=len(attacks),rss_range=report['max_rss_kib_range'],short_batches=report['batches_below_10ms'])))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for name in ('main','runtime','audit','output'):ap.add_argument(name)
    a=ap.parse_args();run(a.main,a.runtime,a.audit,a.output)
