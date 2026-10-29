# -*- coding: utf-8 -*-
import datetime
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import prototype as p


def main(main_,model_,audit_,runtime_,quartic_,out_):
    main,model,audit,runtime,quartic,out=map(lambda x:Path(x).resolve(),(main_,model_,audit_,runtime_,quartic_,out_))
    out.mkdir(parents=True,exist_ok=False);load=lambda x:json.loads(x.read_text(encoding='utf-8'))
    checks=load(main/'checks.json');memory=load(audit/'memory-checks.json');a=load(audit/'audit.json');proof=load(model/'summary.json');perf=load(runtime/'summary.json');attacks=load(main/'attacks.json');qc=load(quartic/'checks.json');qa=load(quartic/'attacks.json');transform=load(main/'transformations.json')
    if checks['binaries']!=120 or qc['binaries']!=28 or any(x['mismatches'] for x in (checks,memory,proof,qc)):raise AssertionError('correctness coverage')
    if len(attacks)!=54 or len(qa)!=12 or any(x['status']!='recovered' for x in attacks+qa):raise AssertionError('attack coverage')
    if a['replayed']!=66 or perf['processes']!=108 or perf['batches_under_10ms']:raise AssertionError('audit coverage')
    # Check that the supposedly recovered models are as small as their source.
    identities=[]
    for case in load(main/'cases.json'):
        src=p.q.read(main/(case['name']+'-plain-raw.wasm'))
        for row in load(main/'manifest.json'):
            if row['name']==case['name'] and row['mode'].endswith('-recovered'):
                recovered=p.q.read(main/row['file'])
                identities.append(dict(file=row['file'],identical_source_ast=recovered==src))
    p.q.save(out/'source-identities.json',identities)
    env=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=sys.version,platform=platform.platform(),processor=platform.processor(),node=subprocess.check_output(['node','--version'],text=True).strip(),v8=subprocess.check_output(['node','-p','process.versions.v8'],text=True).strip(),wabt=p.q.w.tool('wat2wasm',['--version']).strip(),binaryen=p.q.w.tool('wasm-opt',['--version']).strip())
    p.q.save(out/'environment.json',env)
    lines=['# 部分文字列をまたぐ文法変換：実測と採否','',
      '2026-10-23。主特許候補としては不採用。新しい保護効果を確認した結果ではなく、動作する変換と、任意の重みにも通用する解除条件を実装・検査した結果である。研究全体の成功・完了とは扱わない。','',
      '## 正当性・回復','',
      f"- 主：{checks['binaries']} Wasm、{checks['calls']:,}呼出し、{checks['traps']}期待trap、不一致0。3文法の0/1版と任意の奇数32bit重み版。",
      f"- 四次項の追加例：{qc['binaries']} Wasm、{qc['calls']:,}呼出し、{qc['traps']}期待trap、不一致0。α=65536ではα²=0となり四次が消える対照も実施。",
      f"- private memoryを診断用にexportした別binary：{memory['binaries']}本、{memory['calls']:,}呼出し、{memory['traps']}期待trap。不正入力のtrap前後で全memory不変を確認。",
      f"- 別実行系WABT interpreter：{a['wabt_calls']}呼出し一致。変換のbyte再生成{a['replayed']}本一致。2不正profileを拒否。",
      f"- 補正項を欠落させた実Wasmはlength={a['counterexample']['n']}, low={a['counterexample']['lo']}で出力{a['counterexample']['values']}となり誤りを検出。",
      f"- 方式既知の回復：主{len(attacks)}/{len(attacks)}、四次の追加{len(qa)}/{len(qa)}。攻撃入力は配布binaryと公開された方式区分だけ。元grammar/seed/shear値は渡さない。",
      f"- 主回復の{sum(x['identical_source_ast'] for x in identities)}/{len(identities)}は、raw元Wasmと同じASTまで回復。他も全係数の逆変換恒等式を確認した等価文法で、同じ入力で差分検査済み。",
      f"- 任意の重み・非単元係数を含む多項式系{proof['random_systems']}件、うち不定な合同類{proof['nonunique_congruences']}件で最小剰余による回復を確認。小幅算術{proof['finite_pairs']}対も一致。",'',
      '主・診断・再生成は入力を再利用する。総呼出し数を独立したランダム標本数にしない。主では273の非ゼロ参照入力、58の上位bitが立った参照入力を含む。全短入力、境界長、固定seed入力に対する検査であり、全Wasm入力の形式証明ではない。','',
      '## 実行時間','',
      'α=257、0/1文法、O3。単位µs/parse。Wasm内反復の入力選択とchecksumを含む。', '',
      '|文法|長さ|未変換|線形|非線形|回復後|非線形/未変換|',
      '|---|---:|---:|---:|---:|---:|---:|']
    ratios=[]
    for name in ('dyck','palindrome','expression'):
        for n in sorted({x['n'] for x in perf['targets'] if x['name']==name}):
            rs={x['mode']:x for x in perf['targets'] if x['name']==name and x['n']==n};v=[rs[k]['median_ns']/1000 for k in ('plain','linear','nonlinear','recovered')];ratio=v[2]/v[0];ratios.append(ratio)
            lines.append('|%s|%d|%s|%.3f|'%(name,n,'|'.join('%.3f'%x for x in v),ratio))
    lines+=['',f"108 fresh Node process、756 batch、10ms未満0。各条件3process×7batch、warmup32parse、校正は20ms目標。process中央値の中央値を掲載。`--no-liftoff --no-wasm-lazy-compilation`。順序はseed20261023でshuffle。CPU affinityと周波数は未固定。全process中央値とbatch値はruntimeのsummary.json/raw.jsonに保存。非線形/未変換は{min(ratios):.3f}〜{max(ratios):.3f}。",'',
      '同コストでの既存製品・既存論文実装との比較ではない。線形変換は近接する既知原理を自前で実装した対照。weighted版と四次の追加例の実行性能は未測定。小さい回復後/未変換の時間差に意味を持たせない。','',
      '|文法|版|O3 bytes|states|binary rules|linear memory bytes|chart bytes|',
      '|---|---|---:|---:|---:|---:|---:|']
    for name in ('dyck','palindrome','expression'):
        for mode in ('plain','linear','nonlinear','recovered'):
            row=next(x for x in perf['targets'] if x['name']==name and x['mode']==mode)
            lines.append('|%s|%s|%d|%d|%d|%d|%d|'%(name,mode,row['core_bytes'],row['states'],row['rules'],row['memory_bytes'],33*33*4*row['states']))
    rss=[v for x in perf['targets'] for v in x['rss_kib']]
    lines+=['',f"Node全process peak RSS {min(rss):,}〜{max(rss):,} KiB。変換器だけのpeak RAMは未測定。変換{len(transform)}件の単回時間{min(x['ms'] for x in transform):.3f}〜{max(x['ms'] for x in transform):.3f}ms。",'',
      f"主54回復の係数探索時間は{min(x['search_ms'] for x in attacks):.3f}〜{max(x['search_ms'] for x in attacks):.3f}ms。読取・profile照合は別に{min(x['read_ms'] for x in attacks):.3f}〜{max(x['read_ms'] for x in attacks):.3f}ms。これらは単回測定で、安定した解析速度比の推定には使わない。出力までのtotal_msもattacks.jsonに残した。",'',
      '## 何が分かったか','',
      'この案は同じセル内の線形混合から離れ、全分割点をまたぐ畳み込みで内部文法を変更する。補正項とpropernessから意味保存を説明でき、通常O3後にも余分な規則は残る。しかし単一二次shearが作る三次成分は、係数を隠すのではなく線形合同式として露出させる。任意の32bit重み・偶数係数でも、最小剰余の逆shearで簡潔な等価文法が得られることを論証した。','',
      'したがって、係数の桁数、非線形という名称、最適化後の規則数を増やすだけではこの案を救えない。単一shearのパラメータを増やす追試は終了する。既知の非線形変換、形式級数の代数系、文法の二項化との具体的な独立性も未確立で、主特許候補として採用しない。','',
      '一般Wasm変換・実用的な大規模parser・NotDec/StackSight・多段shear合成の評価には至っていない。元の規則を完全一致で特定できない場合でも、等価で小さいparserへ戻れば保護目標への攻撃成功とする。','',
      '## 再現情報','',
      'research/substring-shear/README.mdに全コマンド。main-v3、model-v2、audit-v1、runtime-v1、quartic-v2が本レポートの根拠。旧不完全runは個別INCOMPLETE.mdを残し、成功件数に含めない。source snapshotはsources/、全根拠のSHA-256はprovenance.json。', '']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    sources=list(p.HERE.glob('*.py'))+list(p.HERE.glob('*.cjs'))+list(p.HERE.glob('*.md'))+[p.HERE.parent/'mutation-quotient/prototype.py',p.HERE.parent/'isotope-swizzle/prototype.py',p.HERE.parent/'connectivity-elimination/prototype.py']
    for src in sources:
        dst=out/'sources'/src.relative_to(p.ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    files=[]
    for folder in (main,model,audit,runtime,quartic,out):
        for f in sorted(folder.rglob('*')):
            if f.is_file() and f.name!='provenance.json':files.append(dict(path=str(f),bytes=f.stat().st_size,sha256=p.q.digest(f)))
    for name in ('wat2wasm','wasm2wat','wasm-validate','wasm-interp','wasm-opt'):
        f=(p.q.w.BINARYEN if name=='wasm-opt' else p.q.w.WABT)/(name+'.exe');files.append(dict(path=str(f),bytes=f.stat().st_size,sha256=p.q.digest(f)))
    p.q.save(out/'provenance.json',dict(files=files));print(json.dumps(dict(evidence_files=len(files),identical_source_ast=sum(x['identical_source_ast'] for x in identities),report=str(out/'report.md'))))


if __name__=='__main__':main(*sys.argv[1:])
