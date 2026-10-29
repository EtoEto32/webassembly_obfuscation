# -*- coding: utf-8 -*-
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import prototype as p


def main(main_,model_,audit_,runtime_,out_):
    main,model,audit,runtime,out=map(lambda x:Path(x).resolve(),(main_,model_,audit_,runtime_,out_));out.mkdir(parents=True,exist_ok=False)
    load=lambda x:json.loads(x.read_text(encoding='utf-8'))
    check=load(main/'checks.json');a=load(audit/'audit.json');m=load(model/'model.json');perf=load(runtime/'summary.json');attacks=load(main/'attacks.json');trans=load(main/'transformations.json');identity=load(main/'identities.json')
    if check['binaries']!=36 or check['mismatches'] or len(identity)!=12 or not all(x['same_source_bytes'] for x in identity):raise AssertionError('coverage')
    if len(check['negative'])!=12 or not all(x['mismatches'] for x in check['negative']) or perf['batches_under_10ms'] or a['wabt_calls']!=144:raise AssertionError('controls/timing')
    env=dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),node=subprocess.check_output(['node','--version'],text=True).strip(),v8=subprocess.check_output(['node','-p','process.versions.v8'],text=True).strip(),wabt=p.q.w.tool('wat2wasm',['--version']).strip(),binaryen=p.q.w.tool('wasm-opt',['--version']).strip())
    p.q.save(out/'environment.json',env)
    lines=['# コピー結果を実体化しない変換：初期ゲートの結果','',
      '2026-10-23。既知のlazy copy/read forwardingに近く、方式既知の回復が容易なため、主特許候補には不採用。値の座標変換から離れる候補の初期検査であり、一般のWasmや実用的な保護対象へ適用した結果ではない。','',
      '## 正当性と解除','',
      f"- 2/4/8回copy×2parameter配置×raw/O3。未変換・変換・回復を合わせて{check['binaries']}本、{check['calls']:,}呼出し、{check['traps']:,}期待trap、不一致0。",
      '- 部分重なり、同一範囲、零長、memory末尾、uint32和のoverflow、不正query、失敗後の次の呼出しを含む。参照は独立JS copyWithin。privateな途中memoryの一致は要求しない。',
      f"- 2copyの全小モデル：memory長1..8、{m['symbolic_origin_checks']:,}個のorigin照合で一致。byte値ではなく出自indexを比較する。",
      f"- 別WABT interpreter：{a['wabt_calls']}呼出し一致。export memoryと範囲検査欠落の2不正profileを拒否。",
      '- 検査を省く版とcopy順序を誤る版の12個すべてで反例を検出。正対象の件数に含めない。',
      '- 方式既知の回復：12/12。元のparameter配置、source、seedを渡さず、条件式から抽出。回復Wasmは全12で元rawとbyte単位で同一。',
      f"- 回復の単回時間（WABT読取と完全profile照合を含む）{min(x['analysis_including_profile_ms'] for x in attacks):.3f}〜{max(x['analysis_including_profile_ms'] for x in attacks):.3f}ms。変換6件は{min(x['ms'] for x in trans):.3f}〜{max(x['ms'] for x in trans):.3f}ms。",'',
      '初版はO3がoperand stackへ古い値を残してlocalを再利用する形式に未対応だった。stackとlocal.teeを実行順に扱うよう修正すると回復できた。未対応を難読化成功として数えない。','',
      '## 性能の限定的な対照','',
      '各copyは16KiB、呼出しごとに原版が64KiB scratchを初期化し、最後に1byteだけ観測する人工的な負荷。疎な読出しに有利な設定であり、通常のアプリ全体の高速化を示すものではない。共通Wasm loopの入力生成・呼出し・checksumを含む。', '',
      '|copy数|未変換 ns|引戻し ns|回復後 ns|未変換/引戻し|',
      '|---:|---:|---:|---:|---:|']
    for n in (2,4,8):
        rs={x['mode']:x for x in perf['targets'] if x['copies']==n};v=[rs[k]['median_ns'] for k in ('plain','pullback','recovered')]
        lines.append('|%d|%s|%.2f|'%(n,'|'.join('%.3f'%x for x in v),v[0]/v[1]))
    lines+=['','27 fresh Node process、189batch、全batch10ms以上。各条件3process×7batch、warmup16,384、20msを目標に校正。process中央値の中央値を掲載し、全batchとprocess中央値はraw.json/summary.json。eager optimizing compilation指定、CPU affinity/周波数は未固定。', '',
      '最初のruntime-v1では高速な版が校正の上限へ達し、36batchが10ms未満だった。反復上限を引き上げたruntime-v2だけを確定値に使い、v1と標本を合算しない。','',
      '|copy数|版|O3 binary bytes|linear memory bytes|',
      '|---:|---|---:|---:|']
    for row in perf['targets']:lines.append('|%d|%s|%d|%d|'%(row['copies'],row['mode'],row['core_bytes'],row['memory_bytes']))
    rss=[v for x in perf['targets'] for v in x['rss_kib']]
    lines+=['',f"Node全process peak RSS {min(rss):,}〜{max(rss):,}KiB。変換器だけのpeak RAMは未測定。",'',
      '## 採否と次への条件','',
      'この負荷では計算を省く最適化として有利な値が得られた。しかし物理的なcopy列が範囲条件の列に移っただけで、その対応は公開binaryに残る。高速なこと、途中のmemoryが原版と異なること、copy命令が消えたことは、保護の根拠にならない。', '',
      'lazy memcpy/read forwardingは既知で、Wasmの正確なtrap保持は必要な実装条件である。今回の条件保存を独立した新発明と認定しない。この枝の係数・copy段数・データ量を増やす改良は主案にしない。次は、更新前後の作用を局所的な対応式として残さない生成規則が必要である。','',
      'NotDec/StackSightの実行、大規模実アプリ、共有memory、persistentな外部状態、途中のhost観測は未検証。数学的なcopyの意味保存論証と有限Wasmテストを区別する。','',
      'READMEに再現コマンド。根拠はmain-v2/model-v1/audit-v1/runtime-v2。sources/にコードのsnapshot、provenance.jsonに根拠と使用ツールのSHA-256。外部公開・pushは行っていない。', '']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    sources=list(p.HERE.glob('*.py'))+list(p.HERE.glob('*.cjs'))+list(p.HERE.glob('*.md'))+[p.HERE.parent/'mutation-quotient/prototype.py',p.HERE.parent/'isotope-swizzle/prototype.py',p.HERE.parent/'connectivity-elimination/prototype.py',p.HERE.parent/'span-mask/bench.cjs']
    for src in sources:
        dst=out/'sources'/src.relative_to(p.ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    files=[]
    for folder in (main,model,audit,runtime,out):
        for f in sorted(folder.rglob('*')):
            if f.is_file() and f.name!='provenance.json':files.append(dict(path=str(f),bytes=f.stat().st_size,sha256=p.q.digest(f)))
    for name in ('wat2wasm','wasm2wat','wasm-validate','wasm-interp','wasm-opt'):
        f=(p.q.w.BINARYEN if name=='wasm-opt' else p.q.w.WABT)/(name+'.exe');files.append(dict(path=str(f),bytes=f.stat().st_size,sha256=p.q.digest(f)))
    p.q.save(out/'provenance.json',dict(files=files));print(json.dumps(dict(evidence_files=len(files),report=str(out/'report.md'))))


if __name__=='__main__':main(*sys.argv[1:])
