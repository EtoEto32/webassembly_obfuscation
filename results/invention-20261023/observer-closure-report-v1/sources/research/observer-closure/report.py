# -*- coding: utf-8 -*-
import json, platform, shutil, subprocess, sys
from pathlib import Path
import prototype as p

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def main(main_dir,audit_dir,runtime_dir,fresh_dir,dest):
    main_dir,audit_dir,runtime_dir,fresh_dir,out=map(lambda x:Path(x).resolve(),(main_dir,audit_dir,runtime_dir,fresh_dir,dest));out.mkdir(parents=True,exist_ok=False)
    checks=read(main_dir/'checks.json');audit=read(audit_dir/'audit.json');runtime=read(runtime_dir/'summary.json');fresh=read(fresh_dir/'checks.json');trans=read(main_dir/'transforms.json');attacks=read(main_dir/'attacks.json');follow=read(fresh_dir/'attacks.json')
    assert checks['mismatches']==checks['traps']==fresh['mismatches']==fresh['traps']==0
    assert len(attacks)==len(audit['polynomial_certificates'])==len(follow)==12
    rows=[]
    for name in ('quadratic','cubic','mixed4'):
        rs={r['mode']:r for r in runtime['rows'] if r['name']==name}
        rows.append({'name':name,**{mode:rs[mode]['median_ns'] for mode in rs},'quotient_over_plain':rs['quotient']['median_ns']/rs['plain']['median_ns'],'quotient_over_full':rs['quotient']['median_ns']/rs['full']['median_ns'],'bytes':{mode:rs[mode]['core_bytes'] for mode in rs},'state_bytes':{mode:rs[mode]['global_state_bytes'] for mode in rs}})
    stats={'main_positive_conditions':len(checks['positive']),'main_calls':checks['total_calls'],'main_steps':checks['steps'],'negative_conditions':len(checks['negative']),'main_recoveries':len(attacks),'fresh_conditions':fresh['conditions'],'fresh_steps':fresh['step_calls'],'fresh_recoveries':len(follow),'small_width_pairs':audit['state_input_pairs'],'small_width_closures':audit['closures'],'wabt_steps':audit['wabt_step_calls'],'wabt_observations':audit['wabt_observations'],'runtime':rows,'processes':runtime['processes'],'batches':runtime['batches'],'under_10ms':runtime['under_10ms'],'transform_ms_range':[min(x['transform_ms'] for x in trans if x['mode']!='bad'),max(x['transform_ms'] for x in trans if x['mode']!='bad')],'reset_attack_ms_range':[min(x['total_ms'] for x in attacks),max(x['total_ms'] for x in attacks)],'fresh_attack_ms_range':[min(x['total_ms'] for x in follow),max(x['total_ms'] for x in follow)],'goal_completed':False,'decision':'not adopted as main patent candidate'}
    p.q.save(out/'summary.json',stats)
    env={'python':sys.version,'os':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),'node':checks['node'],'v8':checks['v8'],'wabt':p.q.w.tool('wat2wasm',['--version']).strip(),'binaryen':p.q.w.tool('wasm-opt',['--version']).strip(),'runtime_flags':['--no-liftoff','--no-wasm-lazy-compilation'],'warmup':16384,'calibration_ms':20,'fresh_processes_per_variant':3,'batches_per_process':7,'affinity':False,'memory_metric':'no linear memory; nominal i32 global bytes separately; maxRSS is whole Node process, not Wasm heap peak'}
    p.q.save(out/'environment.json',env)
    lines=['# 観測閉包の実測結果','', '2026-10-23。主案には不採用。自動閉包の生成自体は動作したが、公開APIから小さい更新を回復できた。', '', '|case|元 ns|full ns|quotient ns|回復 ns|quotient/元|', '|---|---:|---:|---:|---:|---:|']
    for r in rows:lines.append('|%s|%.4f|%.4f|%.4f|%.4f|%.3f|'%(r['name'],r['plain'],r['full'],r['quotient'],r['quotient-recovered'],r['quotient_over_plain']))
    lines += ['', '中央値は各processの7batch中央値を3processで再び中央値にしたもの。coreをO3後、同じWasm loopを追加。回復coreへ追加O3は行わず、V8条件は共通。毎回入力を変え、出力をchecksumへ反映。初期resetは1batchに1回。短い元コードのinlineを含む現実の実装差であり、命令単独のレイテンシではない。', '', '主30条件780,090 API呼出しは全一致。負対照6条件は全て誤答。回復12条件は10step+10reset、追加12条件はresetなし22step・12instance。追試491,520stepは全一致。mainとfreshは同じ3人工kernelであり独立コーパスとして足さない。', '', '小幅42閉包・524,256状態入力対は一致。回復は主・追試それぞれ12件でmod2^31の関数差をNewton係数で証明。WABTの独立実行器は360step・90最終観測で一致。負対照や未対応を保護成功へ数えていない。', '', '|case|元/full/quotient/回復のcore bytes|同じ順のglobal state bytes|', '|---|---|---|']
    for r in rows:lines.append('|%s|%s|%s|'%(r['name'],' / '.join(str(r['bytes'][m]) for m in ('plain','full','quotient','quotient-recovered')),' / '.join(str(r['state_bytes'][m]) for m in ('plain','full','quotient','quotient-recovered'))))
    lines += ['', 'linear memoryは全条件0。global state bytesは宣言したi32の論理的な4byte換算であり、実エンジンのallocationを測った値ではない。whole-process RSSはruntime/raw.json参照。変換・攻撃は条件ごと1回のwall timeで、process起動・WABT処理を含む。中央値の反復測定と混同しない。', '', '変換時間範囲 %.3f–%.3fms、reset攻撃 %.3f–%.3fms、fresh攻撃 %.3f–%.3fms。'%(tuple(stats['transform_ms_range']+stats['reset_attack_ms_range']+stats['fresh_attack_ms_range'])), '', '精度を削ったquotientとfullの差は小さく、process間・batch間ばらつきが重なる。統計的な速度優位を主張しない。主比較で元より約5.18–10.05倍の実行費用を払っても同じquery攻撃で戻せた。', '', '原理の先行性は research/observer-closure/prior-art.md、成立証明と限界はalgorithm.md。有限環の観測閉包という狭い差分だけから新規性・進歩性を断定しない。公開先行技術の法的な網羅調査、任意Wasmの保護、実アプリでの効果、他のdecompilerの評価は今回未実施。', '', '入力、バイナリ、差分結果、単回時間、性能生値、別実行器ログを参照元に保持し、sha256.jsonに相対パスとhashを固定。sourcesには本集計時のbranchコードと共通helperの複製を収録する。主実験のfresh追加前のソースはmain/sources-pre-freshに保持した。']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    sourcefiles=[f for f in p.HERE.iterdir() if f.is_file()]+[p.ROOT/'research/dyadic-difference/prototype.py',p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py',p.ROOT/'research/span-mask/bench.cjs']
    for f in sourcefiles:
        target=out/'sources'/f.relative_to(p.ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
    files=[]
    for folder in (main_dir,audit_dir,runtime_dir,fresh_dir,out):files += [f for f in folder.rglob('*') if f.is_file() and f.name!='sha256.json' and '__pycache__' not in str(f)]
    p.q.save(out/'sha256.json',{str(f.relative_to(p.ROOT)).replace('\\','/'):p.q.digest(f) for f in sorted(set(files))})
    print(json.dumps({'hashes':len(set(files)),**stats}))
if __name__=='__main__':main(*sys.argv[1:])
