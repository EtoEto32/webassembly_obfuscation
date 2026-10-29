# -*- coding: utf-8 -*-
import json,platform,shutil,sys
from pathlib import Path
import prototype as p
def read(f):return json.loads(Path(f).read_text(encoding='utf-8'))
def bounds(xs,key):return [min(v[key] for v in xs),max(v[key] for v in xs)]
def main(main_dir,follow_dir,audit_dir,runtime_dir,dest):
    main_dir,follow_dir,audit_dir,runtime_dir,out=map(lambda s:Path(s).resolve(),(main_dir,follow_dir,audit_dir,runtime_dir,dest));out.mkdir(parents=True,exist_ok=False)
    checks=read(main_dir/'checks.json');follow=read(follow_dir/'checks.json');audit=read(audit_dir/'audit.json');runtime=read(runtime_dir/'summary.json');attacks=read(main_dir/'attacks.json');rep=read(follow_dir/'attacks.json');trans=read(main_dir/'transforms.json')
    assert checks['mismatches']==checks['traps']==follow['mismatches']==follow['traps']==0
    assert all(v['identical_to_full_recovery'] for v in rep) and all(v['byte_identical'] for v in audit['replays'])
    rows=[]
    for name in ('round1','round3','round8'):
        plain=next(v for v in runtime['rows'] if v['name']==name and v['mode']=='plain')
        for n in (4,8):
            by={v['mode']:v for v in runtime['rows'] if v['name']==name and v['n']==n}
            fix=next(v for v in attacks if v['file']=='%s-n%d-fixed-O3.wasm'%(name,n));full=next(v for v in attacks if v['file']=='%s-n%d-sync-O3.wasm'%(name,n));representative=next(v for v in rep if v['file']==full['file'])
            by['plain']=plain
            rows.append({'name':name,'n':n,'runtime_ns':{m:r['median_ns'] for m,r in by.items()},'core_bytes':{m:r['core_bytes'] for m,r in by.items()},'sync_over_plain':by['sync']['median_ns']/plain['median_ns'],'sync_over_fixed':by['sync']['median_ns']/by['fixed']['median_ns'],
              'analysis_ms':{'fixed':fix['analysis_ms'],'all_states':full['analysis_ms'],'representative':representative['analysis_ms']},'analysis_steps':{k:sum(c['interpreter_steps'] for c in v['certificates']) for k,v in [('fixed',fix),('all_states',full),('representative',representative)]}})
    stats={'main_conditions':len(checks['positive']),'main_calls':checks['calls'],'negative_conditions':len(checks['negative']),'main_recoveries':len(attacks),'representative_conditions':len(follow['positive']),'representative_calls':follow['calls'],'representative_recoveries':len(rep),'gate_certificates':audit['gate_certificates'],'nonpotential_witnesses':audit['nonpotential_witnesses'],'small_width_pairs':audit['small_width_pairs'],'wabt_calls':audit['wabt_calls'],'byte_identical_replays':len(audit['replays']),
      'rows':rows,'processes':runtime['processes'],'batches':runtime['batches'],'under_10ms':runtime['under_10ms'],'transform_ms':bounds([v for v in trans if v['mode']!='bad'],'transform_ms'),'full_attack_ms':bounds(attacks,'total_ms'),'representative_attack_ms':bounds(rep,'total_ms'),'decision':'not adopted as main invention: known weighted synchronization and inexpensive representative specialization','goal_completed':False}
    p.q.save(out/'summary.json',stats)
    env={'python':sys.version,'os':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),'node':checks['node'],'v8':checks['v8'],'wabt':p.q.w.tool('wat2wasm',['--version']).strip(),'binaryen':p.q.w.tool('wasm-opt',['--version']).strip(),'runtime_flags':['--no-liftoff','--no-wasm-lazy-compilation'],'warmup':16384,'calibration_ms':20,'processes_per_variant':3,'batches_per_process':7,'affinity':False,'memory':'fixed/sync: 65536 bytes, plain/recovered: 0 bytes; RSS refers to whole Node process'}
    p.q.save(out/'environment.json',env)
    lines=['# 同期する解釈状態：実測と採否','','2026-10-23。主たる難読化発明には不採用。未知の入口状態から同じ計算へ収束させる原始操作は動作したが、代表状態一つの解釈で同等コードを得られた。重み付き同期という原理にも先行研究がある。',
      '', '主54条件62,208呼出しと代表回復12条件13,824呼出しは不一致・trapとも0。負対照12条件には全て反例があった。96gateの係数一致と加算potentialでは説明できない自己loop対、縮小幅9,216組、WABT54条件324呼出しを確認。回復器の範囲判定を厳密化した後、全24回復を再生成してbyte一致を確認した。これらは同じ3人工kernelの異なる検査であり、実アプリ66件に成功したという意味ではない。',
      '', '|case|状態数|元 ns|fixed ns|sync ns|回復 ns|sync/元|','|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        v=r['runtime_ns'];lines.append('|%s|%d|%.4f|%.4f|%.4f|%.4f|%.3f|'%(r['name'],r['n'],v['plain'],v['fixed'],v['sync'],v['sync-recovered'],r['sync_over_plain']))
    lines += ['', '値は各processの7batch中央値を3process間で再び中央値にした。63 fresh process・441batch、10ms未満なし。入力を変えながら共通Wasm loopでrunを呼び、結果をchecksumに反映する。coreはO3後にwrapperを追加。回復coreへ追加O3は行っていない。CPU affinity・外乱制御はなく、process/batchの範囲はruntime/summary.jsonと生値に保存した。',
      '', '|case|状態数|固定入口 解析ms|全入口検証 解析ms|代表候補 解析ms|代表/fixedの解釈step比|','|---|---:|---:|---:|---:|---:|']
    for r in rows:
        a=r['analysis_ms'];s=r['analysis_steps'];lines.append('|%s|%d|%.4f|%.4f|%.4f|%.4f|'%(r['name'],r['n'],a['fixed'],a['all_states'],a['representative'],s['representative']/s['fixed']))
    lines += ['', '解析msはWABTによる読取り後、binary内のhelperをaffine値で解釈する区間の単回測定である。統計的に精密な速度差の証明ではない。step数は独自interpreterのdispatch回数であり、人間の理解時間でも汎用decompilerの実測でもない。全状態の検証と、同期の約束を利用して候補を取り出す課題を区別した。代表解析の12出力は全状態解析の出力とbyte一致し、独立の差分試験にも通過した。元sourceや生成seedを回復器へ渡していない。',
      '', '|case|状態数|元 / fixed / sync / 回復 core bytes|','|---|---:|---|']
    for r in rows:lines.append('|%s|%d|%s|'%(r['name'],r['n'],' / '.join(str(r['core_bytes'][m]) for m in ('plain','fixed','sync','sync-recovered'))))
    lines += ['', 'fixed/syncは非公開linear memory65536byte、元/回復は0。RSSはNode全processを含む。変換時間 %.3f–%.3fms、全状態回復の全pipeline %.3f–%.3fms、代表回復 %.3f–%.3fms。各条件一回でprocess起動・WABT処理も含む。'%tuple(stats['transform_ms']+stats['full_attack_ms']+stats['representative_attack_ms']),
      '', '失敗分類：v1はO3がrem_uをandへ変えた形式を回復器が拒否し、未完了である。修正版v2が完了記録。full回復器は12個の誤重み対照を非一様な結果として拒否し、変換器はprofile外3入力を拒否した。追加のtrapする入口式も回復器が拒否することを確認した。未対応や実装不備を保護成功に数えない。',
      '', '限定の重要点：本実装は元のif構造を残し、helper入口の状態を引数から作る。任意CFGの各分岐から解釈状態を持ち回って合流させる実装までは作っていない。基本操作の段階で安い要約が成立したため、その方向の拡張には進まない。一般の非可逆な状態難読化の不可能性を証明したわけではない。',
      '', '先行性：Ivánのweighted synchronizationへpowerset semiringを通じて対応する。新しい数理原理との主張はできない。2026-10-21のVMSpec preprintも読み、context追跡・handler要約の評価観点を更新したが、その実装を実行した比較ではない。詳細は research/synchronizing-decoder/prior-art.md。',
      '', '主測定後に代表解析・拒否条件・ログ欄を追加した。sourcesには監査後のコードを保存し、主24回復binaryと同じ出力になることを再生成で確認した。v1の失敗と修正前ソースも収録する。数学的な係数検証と実装のテストを、任意Wasmに対する機械検証済み同値性と混同しない。']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    sources=[f for f in p.HERE.iterdir() if f.is_file()]+[p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py',p.ROOT/'research/span-mask/bench.cjs']
    for f in sources:
        t=out/'sources'/f.relative_to(p.ROOT);t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,t)
    folders=(main_dir,follow_dir,audit_dir,runtime_dir,main_dir.parent/'synchronizing-decoder-v1',main_dir.parent/'synchronizing-decoder-probe-v1',out)
    files=sorted({f for folder in folders for f in folder.rglob('*') if f.is_file() and f.name!='sha256.json' and '__pycache__' not in str(f)})
    p.q.save(out/'sha256.json',{f.relative_to(p.ROOT).as_posix():p.q.digest(f) for f in files});print(json.dumps({'hashes':len(files),'main_calls':checks['calls'],'followup_calls':follow['calls'],'goal_completed':False}))
if __name__=='__main__':main(*sys.argv[1:])
