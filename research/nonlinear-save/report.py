# -*- coding: utf-8 -*-
"""Freeze measured results, producer sources and hashes; do not rerun experiments."""
import json, platform, shutil, sys
from pathlib import Path
import prototype as p

def read(f):return json.loads(Path(f).read_text(encoding='utf-8'))
def span(rows,key):return [min(r[key] for r in rows),max(r[key] for r in rows)]
def main(screen_dir,main_dir,audit_dir,held_dir,runtime_dir,dest):
    screen_dir,main_dir,audit_dir,held_dir,runtime_dir,out=map(lambda s:Path(s).resolve(),(screen_dir,main_dir,audit_dir,held_dir,runtime_dir,dest))
    out.mkdir(parents=True,exist_ok=False)
    screen=read(screen_dir/'screen.json');check=read(main_dir/'checks.json');held=read(held_dir/'checks.json');audit=read(audit_dir/'audit.json');runtime=read(runtime_dir/'summary.json')
    trans=read(main_dir/'transforms.json');attacks=read(main_dir/'attacks.json');held_attacks=read(held_dir/'attacks.json');raw=read(runtime_dir/'raw.json')
    assert check['mismatches']==held['mismatches']==0
    assert all(r['mismatches']>0 for r in check['negative']+held['negative'])
    assert len(attacks)==18 and len(held_attacks)==6
    assert all(a['status']=='finite_profile_candidate' for a in attacks+held_attacks)
    summary={'discovery_cases':screen['cases'],'discovery_gains':sum(r['color_bits']<r['linear_bits'] for r in screen['rows']),
      'heldout_cases':audit['holdout_cases'],'heldout_gains':audit['holdout_strict_gain'],'small_width_permutations':audit['permutations'],'small_width_gains':audit['strict_gain_exhaustive'],
      'main':{**{k:v for k,v in check.items() if k not in ('positive','negative')},'positive_conditions':len(check['positive']),'negative_conditions':len(check['negative']),'recoveries':len(attacks)},
      'holdout':{**{k:v for k,v in held.items() if k not in ('positive','negative')},'positive_conditions':len(held['positive']),'negative_conditions':len(held['negative']),'recoveries':len(held_attacks)},
      'wabt_conditions':len(audit['wabt']),'wabt_runs':audit['wabt_runs'],'wabt_expected_traps':audit['wabt_expected_traps'],'profile_rejections':audit['rejected'],
      'transform_ms':span([r for r in trans if r['mode']!='bad'],'transform_ms'),'main_attack_ms':span(attacks,'total_ms'),'holdout_attack_ms':span(held_attacks,'total_ms'),
      'processes':runtime['processes'],'batches':runtime['batches'],'under_10ms':runtime['under_10ms'],'rows':runtime['rows'],
      'goal_completed':False,'decision':'retain as small finite-state repair optimization; not adopted as main obfuscation invention'}
    p.q.save(out/'summary.json',summary)
    env={'python':sys.version,'os':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),
      'node':raw[0]['measurement']['node'],'v8':raw[0]['measurement']['v8'],'wabt':p.q.w.tool('wat2wasm',['--version']).strip(),'binaryen':p.q.w.tool('wasm-opt',['--version']).strip(),
      'flags':['--no-liftoff','--no-wasm-lazy-compilation'],'warmup':16384,'calibration_ms':20,'fresh_processes_per_variant':3,'batches_per_process':7,'affinity':False,
      'memory_metric':'fixed 65536-byte linear memory; maxRSS is whole Node process, not Wasm-only peak','measured_path':'reset + normal run + peek + common loop, with changing state each iteration'}
    p.q.save(out/'environment.json',env)
    lines=['# 非線形共有退避の実測結果','','2026-10-23。有限状態のrepair表生成として保存する。独立した強い難読化原理・特許性の確立には至っていない。',
      '', '探索600例中1例、独立holdout600例中1例で、最良の線形保存2bitに対して非線形保存1bitとなった。主ベンチマークの改善例は探索結果から選んだもので、平均的な効果ではない。3bit・固定copy列の全8!置換40,320例では改善は0件。',
      '', '主42条件40,362 API呼出し（16,128run、4,032reset、20,202peek）と追試14条件12,614呼出し（5,040run、1,260reset、6,314peek）は一致。期待trapは主9,828、追試3,024。負対照8条件は全て反例を検出。WABT別実行器の42条件420run・420peek、期待trap294件も一致した。',
      '', '回復器は元encoding・copy列・生成manifestを受け取らず、公開APIを使って全24変換条件の同等遷移表を生成した。2copyでは150 API呼出し、3copyでは200。全状態・全失敗位置を含む試験で一致したが、未知の隠れ状態を持つ任意Wasmの同値性を有限観測だけから保証したわけではない。元ソースの一意な回復という評価でもない。',
      '', '|case|full / linear / color 保存bit|同じ順のrepair表byte|同じ順の全表byte|', '|---|---|---|---|']
    for name in ('copy0','copy1','copy2'):
        rs={r['mode']:r for r in trans if r['name']==name}
        vals=[' / '.join(str(rs[m][key]) for m in ('full','linear','color')) for key in ('saved_bits','repair_table_bytes','all_table_bytes')]
        lines.append('|'+name+'|'+'|'.join(vals)+'|')
    lines += ['', '全方式の保存localはi32一つ、temporaryはi32一つ。保存bitの減少はlocal数・実メモリの減少を意味しない。全表byteにはencoding、inverse、save mapを含む。各prefixのrepair表には未使用組合せの領域もある。表のlayout自体を最小化した値ではない。',
      '', '|case|元 ns|full ns|linear ns|color ns|回復 ns|color/元|','|---|---:|---:|---:|---:|---:|---:|']
    for name in ('copy0','copy1','copy2'):
        rs={r['mode']:r for r in runtime['rows'] if r['name']==name};v=[rs[m]['median_ns'] for m in ('plain','full','linear','color','color-recovered')]
        lines.append('|%s|%.4f|%.4f|%.4f|%.4f|%.4f|%.3f|'%(tuple([name]+v+[v[3]/v[0]])))
    lines += ['', '各processの7batch中央値を3process間で再び中央値にした。45process・315batch、10ms未満のbatchなし。全て同じWasm内loopでreset/run/peekし、入力stateをLCGで変え、出力をchecksumへ反映する。coreはO3後にwrapperを付加し、回復coreには追加O3なし。V8によるinlineを含む。trap経路の速度は未測定。linear/colorの速度差は小さく、安定した高速化とは主張しない。',
      '', '|case|元 / full / linear / color / 回復 O3 core byte|','|---|---|']
    for name in ('copy0','copy1','copy2'):
        rs={r['mode']:r for r in runtime['rows'] if r['name']==name}
        lines.append('|%s|%s|'%(name,' / '.join(str(rs[m]['core_bytes']) for m in ('plain','full','linear','color','color-recovered'))))
    lines += ['', '改善例copy1ではlinear649→color606byteで43byte（約6.6%）減少。holdoutの改善例もlinear651→color595byte。ただしfull/linear/colorは共通lookup emitterであり、それぞれに最適化した手書き実装との比較ではない。全条件のlinear memoryは65536byte。RSSはwhole-processで、生値とばらつきはruntime/summary.jsonとraw.jsonを参照。',
      '', '変換 %.3f–%.3fms、主回復 %.3f–%.3fms、holdout回復 %.3f–%.3fms。各条件1回でprocess起動やWABT呼出しを含む。反復した実行時間測定と混同しない。'%tuple(summary['transform_ms']+summary['main_attack_ms']+summary['holdout_attack_ms']),
      '', '失敗分類：今回の正条件にvalidation失敗・実行器クラッシュ・timeoutはなかった。profile外のmemory export、extra global、wrong peekの3入力は意図して拒否。audit-v1は正常voidのログparser不備により未完了で、修正後v2を正結果に用いた。未対応やログ不備を保護成功に数えない。',
      '', '脅威モデルの限界：4個のbinary byteだけで全状態は16。公開reset/peekが全状態学習を容易にする。一般byte・任意heap、実アプリ、実デコンパイラ評価は未実施。既知のfunctional index codingとcographとの差が弱いため、表削減という工学的な結果を強い特許候補や新しい解析耐性と呼ばない。',
      '', '入力・出力・実測・証明書・別実行器ログ・未完了audit-v1をsha256.jsonで固定。sourcesに集計時のコードと共通helperを保存した。model.pyに後から追加したXOR線形性assertは出力を変更しない検査であり、holdout実行時にも通過した。']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    sourcefiles=[f for f in p.HERE.iterdir() if f.is_file()]+[p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py',p.ROOT/'research/span-mask/bench.cjs']
    for f in sourcefiles:
        t=out/'sources'/f.relative_to(p.ROOT);t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,t)
    folders=(screen_dir,main_dir,audit_dir,held_dir,runtime_dir,main_dir.parent/'nonlinear-save-audit-v1',out)
    files=sorted({f for folder in folders for f in folder.rglob('*') if f.is_file() and f.name!='sha256.json' and '__pycache__' not in str(f)})
    p.q.save(out/'sha256.json',{f.relative_to(p.ROOT).as_posix():p.q.digest(f) for f in files})
    print(json.dumps({'hashes':len(files),'main_calls':check['total_calls'],'holdout_calls':held['total_calls'],'recoveries':len(attacks)+len(held_attacks),'goal_completed':False}))
if __name__=='__main__':main(*sys.argv[1:])
