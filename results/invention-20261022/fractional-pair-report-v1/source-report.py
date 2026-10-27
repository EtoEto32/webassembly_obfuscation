import argparse,json,shutil
from pathlib import Path
import prototype as p
def run(main,runtime,audit,output):
    main,runtime,audit,out=map(lambda x:Path(x).resolve(),(main,runtime,audit,output));out.mkdir(parents=True,exist_ok=False)
    paths=[main/'manifest.json',main/'checks.json',main/'analysis.json',main/'model.json',runtime/'summary.json',runtime/'runtime.json',audit/'audit.json']
    manifest,checks,analysis,model,perf,runs,auditdata=[json.loads(f.read_text()) for f in paths]
    assert checks['positiveMismatches']==0 and checks['negativeDetected']==6
    assert len(analysis)==12 and all(x['status']=='recovered' for x in analysis)
    ratios=[r['modes']['fraction']['median']/r['modes']['qsub']['median'] for r in perf['rows']]
    rss=[r['measurement']['maxRssKiB'] for r in runs]
    short=sum(b['ns']<10000000 for r in runs for b in r['measurement']['batches'])
    equality=[]
    for name in ('pair','chain','euclid'):
        bs={r['mode']:r['sha256'] for r in perf['binaries'] if r['name']==name}
        equality.append(dict(name=name,recovered_plain_equal=bs['recovered']==bs['plain']))
    report=dict(positive_calls=checks['positiveCalls'],positive_traps=checks['positiveTraps'],positive_mismatches=0,negative_detected=6,recovered=12,
        model_comparisons=model['comparisons'],wide_model_comparisons=model['wide_comparisons'],interpreter_calls=auditdata['interpreter_calls'],replayed=auditdata['replay_count'],controls=len(auditdata['controls']),
        rows=perf['rows'],binaries=perf['binaries'],fraction_qsub_ratio_range=[min(ratios),max(ratios)],
        processes=len(runs),batches=sum(len(r['measurement']['batches']) for r in runs),batches_below_10ms=short,max_rss_kib_range=[min(rss),max(rss)],
        read_ms_single_range=[min(r['read_ms'] for r in analysis),max(r['read_ms'] for r in analysis)],rewrite_ms_single_range=[min(r['rewrite_ms'] for r in analysis),max(r['rewrite_ms'] for r in analysis)],recovered_binary_equality=equality)
    p.q.save(out/'report.json',report);p.q.save(out/'input-pins.json',{str(f):p.q.digest(f) for f in paths})
    lines=['# 可変除数に合わせた小数部融合：実測比較','','主結果 main-v2 / runtime-v1 / audit-v1。3合成consumer、同じdiv/rem変換。時間は入力更新とchecksumを含むns/call、各processの9 batch中央値を3 fresh process間で中央値にした。','','| consumer | divisor入力 | plain | qsub | zero | fraction | recovered | fraction/qsub |','|---|---|---:|---:|---:|---:|---:|---:|']
    for r in perf['rows']:
        ms=r['modes'];vals=[ms[m]['median'] for m in ('plain','qsub','zero','fraction','recovered')]
        lines.append('| '+r['name']+' | '+r['distribution']+' | '+' | '.join(f'{x:.3f}' for x in vals)+f' | {vals[3]/vals[1]:.3f} |')
    lines+=['','fullの除数は1..2^31、smallは1..1024。chainでは後続除数を内部更新する。性能測定は除数0を含まない。CPU affinity/frequency未固定。',
        'plainは通常のdiv+rem。qsubはq=div、r=x-q*dという既知の対照。zeroは摂動なし、fractionは除数依存の許容摂動あり。回復版にはO3を追加適用し、全版とも共通bench wrapperを後付けして以降は最適化しない。',
        f"正36条件 {checks['positiveCalls']:,} 呼出し、うちtrap {checks['positiveTraps']:,}、不一致0。誤変換6条件すべて反例あり。縮小幅 {model['comparisons']:,} 比較、32bit {model['wide_comparisons']:,} 比較、別WABT実行 {auditdata['interpreter_calls']} 呼出しが一致。",
        '公開binaryだけを使う方式既知の回復はraw/O3の12/12条件。O3後も6変換条件にi64.div_uが残るが、閉じた算術式と一時localの非漏出を検査して通常div/remへ戻せた。解析器の未対応を耐性に加算していない。',
        f"回復の読取は単回{report['read_ms_single_range'][0]:.2f}–{report['read_ms_single_range'][1]:.2f}ms、書換え本体は{report['rewrite_ms_single_range'][0]:.3f}–{report['rewrite_ms_single_range'][1]:.3f}ms。統計的な攻撃費用や人的開発費用ではない。",
        f"実行はqsub対照の{min(ratios):.2f}–{max(ratios):.2f}倍。正しい構成と通常最適化後の残存は確認できたが、追加の保護効果と性能優位は支持されない。",
        f"{len(runs)} fresh process、{report['batches']} batch、うち{short} batchは10ms未満。全Node process最大RSSは{min(rss)}–{max(rss)}KiB、linear memoryは全版0。変換器固有のpeak memoryは未測定。",
        '42本のbyte再生成、6拒否対照を保存。各consumerは同じ入力を版間で反復し、独立標本数として足さない。全2^64入力の列挙・汎用Wasmの形式証明・実アプリでの優位性は主張しない。',
        '初回main-v1は負例の値をANDで小さくしたため誤りを発火せず失敗。main-v2でB+1を直接与え、数学モデルで構成した境界入力も追加した。主結果へv1の呼出し数を加算しない。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');shutil.copy2(__file__,out/'source-report.py')
    print(json.dumps({k:report[k] for k in ('positive_calls','positive_traps','recovered','fraction_qsub_ratio_range','batches_below_10ms','max_rss_kib_range')}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();[ap.add_argument(n) for n in ('main','runtime','audit','output')];a=ap.parse_args();run(a.main,a.runtime,a.audit,a.output)
