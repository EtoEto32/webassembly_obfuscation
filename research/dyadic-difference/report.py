import argparse,json,shutil
from pathlib import Path
import prototype as p


def report(base,out):
    base,out=Path(base).resolve(),Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    names=['dyadic-difference-v1','dyadic-difference-performance-v1','dyadic-difference-audit-v1','dyadic-difference-guarded-v1','dyadic-difference-guarded-performance-v1','dyadic-difference-guarded-audit-v1','dyadic-difference-high-degree-v1']
    verified={}
    for name in names:
        pins=json.loads((base/name/'pins.json').read_text(encoding='utf-8'))
        for f,h in pins.items():assert p.q.digest(base/name/f)==h,f
        verified[name]=len(pins)
    def read(folder,file):return json.loads((base/folder/file).read_text(encoding='utf-8'))
    main=read(names[0],'checks.json');audit=read(names[2],'audit.json');guard=read(names[3],'checks.json');gaudit=read(names[5],'audit.json');perf=read(names[4],'runtime.json');high=read(names[6],'checks.json')
    analyses=read(names[3],'analysis.json');static=read(names[0],'analysis.json')
    facts=dict(verified_pins=verified,main_calls=main['calls'],main_positive=len(main['rows']),main_negative=len(main['negative']),main_unique_positive=audit['unique_positive_binaries'],static_recoveries=len(static),static_different_coefficients=sum(not r['source_coefficients_equal'] for r in static),guarded_calls=guard['calls'],guarded_positive=len(guard['rows']),guarded_unique_positive=gaudit['unique_positive_binaries'],public_recoveries=len(analyses),public_queries_each=34,public_queries_total=sum(a['query']['queries'] for a in analyses),helper_calls=audit['helper_checks']['calls'],wabt_calls_initial=audit['wabt_calls'],wabt_calls_guarded=gaudit['wabt_calls'],small_models=audit['models'],high_degree_calls=high['calls'],high_degree_recoveries=len(read(names[6],'analysis.json')),high_degree_queries=204,high_degree_wabt_calls=sum(r['calls'] for r in read(names[6],'wabt.json')),performance=perf['summary'],processes=perf['processes'],batches=perf['batches'],short_batches=perf['short_batches'],node_rss_kib=[min(r['max_rss_kib'] for r in perf['rows']),max(r['max_rss_kib'] for r in perf['rows'])])
    p.q.save(out/'facts.json',facts)
    lines=['# 差分評価の比較','', '同一候補の初版と修正版を分ける。再生成や計測反復を独立ケースに加算しない。','', '| 例 | plain ns | delta ns | guarded ns | 回復 ns | guarded/plain | guarded bytes |','|---|---:|---:|---:|---:|---:|---:|']
    for row in perf['summary']:
        lines.append('| '+row['name']+' | '+' | '.join(f"{row[m]['median_ns']:.3f}" for m in ['plain','delta','guarded','recovered'])+f" | {row['guarded_over_plain']:.3f} | {row['guarded']['bytes']} |")
    lines += ['', '各セルは3 fresh processの7batch中央値から算出。回復はO3入力から生成したHorner式（出力自体にBinaryenを再適用しない）。V8のフラグは同じ。LCG・checksum・import費用込み。','', '元/差分/修正版の公開問い合わせtranscriptは例ごとに一致した。全18条件が34問い合わせで回復。初版の静的回復は12条件成功、うち8条件は元と異なる係数だが同じ関数。修正版の静的回復6拒否を保護成功とはしない。','', '主発明には不採用。有限差分化、Newton補間、有限環多項式の既知構造との独立性は確立していない。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');shutil.copy2(__file__,out/'source-report.py')
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(facts))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('base');ap.add_argument('output');a=ap.parse_args();report(a.base,a.output)
