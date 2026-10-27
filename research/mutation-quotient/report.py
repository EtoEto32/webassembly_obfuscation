# -*- coding: utf-8 -*-
import json
import platform
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import prototype as p


def main(main_,model_,audit_,io_,runtime_,out_):
    main,model,audit,io,runtime,out=map(lambda s:Path(s).resolve(),(main_,model_,audit_,io_,runtime_,out_))
    out.mkdir(parents=True,exist_ok=False)
    load=lambda path:json.loads(path.read_text(encoding='utf-8'))
    checks=load(main/'checks.json');memory=load(audit/'memory-checks.json');proof=load(model/'model.json');a=load(audit/'audit.json');ioc=load(io/'checks.json');attacks=load(main/'attacks.json');ior=load(io/'attacks.json');perf=load(runtime/'summary.json');trans=load(main/'transformations.json')
    if checks['mismatches'] or memory['mismatches'] or ioc['mismatches']:raise AssertionError('incorrect output')
    if any(x['status']!='unsat' for x in proof['smt']):raise AssertionError('unproved closure')
    if len(attacks)!=36 or len(ior)!=54 or a['replayed']!=90:raise AssertionError('coverage')
    # The cheap representative does not obscure the executable update function.
    identities=[]
    for c in load(main/'cases.json'):
        for opt in ('raw','O3'):
            mods=[p.q.read(main/(c['name']+'-'+mode+'-'+opt+'.wasm')) for mode in ('plain','representative')]
            fs=[next(e for e in m[1:] if e[0]=='func') for m in mods]
            if fs[0]!=fs[1]:raise AssertionError('representative changed update code')
            identities.append(dict(name=c['name'],optimization=opt,identical_run_body=True))
    p.q.save(out/'code-identities.json',identities)
    environment=dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.q.w.tool('wat2wasm',['--version']).strip(),binaryen=p.q.w.tool('wasm-opt',['--version']).strip())
    p.q.save(out/'environment.json',environment)
    lines=['# 更新状態の情報消去：実測と採否','',
      '2026-10-23。新しい有効な主難読化方式としては不採用。変換の成立条件と、公開更新を使う回復を実装した。研究全体の完了・特許性の判断とはしない。','',
      '## 正当性と反証','',
      f"- 主：{checks['binaries']}本、{checks['calls']:,}呼出し、trap {checks['traps']:,}、不一致0。",
      f"- 診断：{memory['binaries']}本、{memory['calls']:,}呼出し、trap {memory['traps']:,}。全呼出しで内部状態の関係、trap時は全64KiB不変を確認。",
      f"- 公開I/O回復：{len(ior)}条件、問い合わせ合計{sum(r['queries'] for r in ior):,}（各n回、別途reset1回）。回復Wasmの{ ioc['calls']:,}呼出しで不一致0。",
      f"- コードからの回復：変換{len(attacks)}条件すべて成功。方式に特化した完全profile照合を含み、一般の逆コンパイラではない。",
      f"- 別WABT：{a['wabt_calls']}呼出し。byte再生成：{a['replayed']}本一致。3不正profileを拒否。過剰消去の実Wasmの出力は{a['negative_outputs']}で不一致を検出。",
      f"- 小幅モデル：{proof['closure_pairs']:,}状態対比較。6種類のkの32bit閉性をZ3でunsat確認。全Wasmの形式証明ではない。",'',
      '主・診断・回復は同じ系列と入力を再利用する。呼出しの合計を独立標本数にしない。3サイズ×3倍率は同じAPIの設定違いである。','',
      '## 性能','',
      'k=257、O3の更新1回あたりns。共通Wasm loopの入力生成・関数呼出し・checksumを含む。resetはbatch冒頭に1回含む。', '',
      '|n|plain|representative|canonical|recovered|canonical/plain|',
      '|---:|---:|---:|---:|---:|---:|']
    for n in (4,32,256):
        rs={r['mode']:r for r in perf['targets'] if r['n']==n};v=[rs[k]['median_ns'] for k in ('plain','representative','canonical','recovered')]
        lines.append('|%d|%s|%.3f|'%(n,'|'.join('%.3f'%x for x in v),v[2]/v[0]))
    lines+=['',f"{perf['processes']} fresh Node process、{perf['batches']} batch、10ms未満{perf['batches_under_10ms']}。各条件3process、各7batch。16,384 warmup、20msを目標に反復数を校正。process中央値の中央値を掲載し、個々の値・ばらつきはruntime/summary.jsonとraw.jsonに保存。測定順は固定seedでshuffle。CPU affinity・周波数未固定。",'',
      '代表版は原版と同じrun命令列であることをraw/O3の18条件で確認。小さい時間差を保護効果・高速化の証拠にしない。canonicalの余分な費用はanchor変更時の全差の修復と各accessの再構成による。性能のrecoveredは同じO3を適用してから共通wrapperを追加した。','',
      '|n|plain bytes|representative bytes|canonical bytes|recovered bytes|',
      '|---:|---:|---:|---:|---:|']
    for n in (4,32,256):
        rs={r['mode']:r for r in perf['targets'] if r['n']==n};lines.append('|%d|%s|'%(n,'|'.join(str(rs[k]['core_bytes']) for k in ('plain','representative','canonical','recovered'))))
    rss=[x for r in perf['targets'] for x in r['rss_kib']]
    lines+=['',f"全版のlinear memoryは65,536 byte。Node全processのmax RSSは{min(rss):,}〜{max(rss):,} KiB。変換器固有のpeak memoryは未測定。",'',
      f"変換18件の単回時間は{min(r['ms'] for r in trans):.3f}〜{max(r['ms'] for r in trans):.3f}ms。binary回復の代表再構成だけは{min(r['analysis_ms'] for r in attacks):.6f}〜{max(r['analysis_ms'] for r in attacks):.6f}msで、読取・profile照合・出力は別項目に記録。Pythonの短時間値を安定した性能比には使わない。",'',
      '## 判断と限界','',
      'kに応じた消去情報量を論証し、異なる初期状態から同じ配布binaryが生まれる例も確認した。しかし、public APIを維持する最小状態は各n回の応答から戻る。代表選択だけで同じ操作コードを利用できるので、複雑な内部表現を維持する必要もなかった。情報消去の成功は、アルゴリズム保護の成功を意味しない。','',
      '商・対称性による状態縮約、データ表現合成、合同算術という既知枠組みとの差が弱い。一般のWasm、既存難読化製品との同コスト比較、NotDec/StackSightによる評価、秘密schema、任意の副作用へは一般化しない。通常の最適化にcanonicalが残ることだけを保護成功にしない。','',
      '初回main-v1の中断はO3によるdata segment分割へのreader未対応。修正後のmain-v2を主結果とし、旧不完全runを成功件数へ加算しない。','',
      '先に検討したrelaxed laneselectの関係制約は全byte組で成立条件を検査したが、仕様が許す片側への固定が可能なため、独立した難読化原理には採用しなかった。','',
      '## 証拠と再現','',
      '元結果のパスとSHA-256はprovenance.json、使用ソースはsources/。READMEの順番で新しい出力先へ再実行する。外部公開・pushはしていない。', '']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    sources=list(p.HERE.glob('*.py'))+list(p.HERE.glob('*.cjs'))+list(p.HERE.glob('*.md'))+[p.HERE.parent/'isotope-swizzle/prototype.py',p.HERE.parent/'connectivity-elimination/prototype.py',p.HERE.parent/'span-mask/bench.cjs']
    for src in sources:
        dst=out/'sources'/src.relative_to(p.ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    evidence=[]
    for folder in (main,model,audit,io,runtime,out):
        for f in sorted(folder.rglob('*')):
            if f.is_file() and f.name!='provenance.json':evidence.append(dict(path=str(f),bytes=f.stat().st_size,sha256=p.q.digest(f)))
    for exe in ('wat2wasm','wasm2wat','wasm-validate','wasm-interp'):
        f=p.q.w.WABT/(exe+'.exe');evidence.append(dict(path=str(f),bytes=f.stat().st_size,sha256=p.q.digest(f)))
    f=p.q.w.BINARYEN/'wasm-opt.exe';evidence.append(dict(path=str(f),bytes=f.stat().st_size,sha256=p.q.digest(f)))
    p.q.save(out/'provenance.json',dict(files=evidence));print(json.dumps(dict(evidence_files=len(evidence),report=str(out/'report.md'))),flush=True)


if __name__=='__main__':main(*sys.argv[1:])
