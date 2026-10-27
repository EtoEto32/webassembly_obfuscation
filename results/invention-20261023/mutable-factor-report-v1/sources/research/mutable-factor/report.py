# -*- coding: utf-8 -*-
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import prototype as p


def main(main_,model_,audit_,runtime_,out_):
    main,model,audit,runtime,out=map(lambda s:Path(s).resolve(),(main_,model_,audit_,runtime_,out_));out.mkdir(parents=True,exist_ok=False)
    load=lambda f:json.loads(f.read_text(encoding='utf-8'))
    ck=load(main/'checks.json');md=load(model/'model.json');ad=load(audit/'audit.json');pf=load(runtime/'summary.json')
    ids=load(main/'identities.json');attacks=load(main/'attacks.json');trans=load(main/'transformations.json')
    if ck['mismatches'] or ck['calls']!=202080 or len(ids)!=24 or not all(r['same_source_bytes'] for r in ids):raise AssertionError('main coverage')
    if len(ck['negative'])!=6 or not all(r['mismatches'] for r in ck['negative']):raise AssertionError('negative controls')
    if ad['interpreter_calls']!=240 or md['word32_one_update']!='unsat' or pf['processes']!=108 or pf['under_10ms']:raise AssertionError('audit/timing')
    env=dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),node=subprocess.check_output(['node','--version'],text=True).strip(),v8=subprocess.check_output(['node','-p','process.versions.v8'],text=True).strip(),wabt=p.q.w.tool('wat2wasm',['--version']).strip(),binaryen=p.q.w.tool('wasm-opt',['--version']).strip())
    p.q.save(out/'environment.json',env)
    lines=['# 可変二表による接続表現：実装と反証','',
      '2026-10-23。主特許候補には不採用。更新ごとの中間対応変更は実装できたが、方式既知の解析は二表を合成した論理接続を抽象状態に選べる。変更履歴を展開せず、全条件で元とbyte一致するWasmへ戻した。独立した新規性と保護優位を確立した結果ではない。','',
      '## 正当性と回復','',
      '- 4/16/128ノード×2seed。plain/fixed/moving、raw/O3、factorからの回復を合わせた主60本は126,300呼出し、期待trap720件、不一致0。',
      '- 診断用36本は75,780呼出し、期待trap432件、不一致0。毎回、合成した全接続と全payloadを照合し、trapでは全64KiBの物理memoryが不変であることも検査した。診断memoryを解除に渡していない。',
      '- 合計202,080呼出し・期待trap1,152件。独立JS参照、同一instanceの連続更新、reset、同じindex同士の交換、unsigned境界、stepsのoverflowを含む。有限実行検査は全入力の実装同値証明ではない。',
      f"- 小モデルはn=1..4の全A置換・全B・全u/v/wについて{md['origin_checks']:,}個の接続を照合し、不一致0。",
      '- 32bit index/valueの配列モデルでは、一更新の関係に反例がないことをZ3 4.13.3で確認（UNSAT）。必要な単射条件を外すとSAT。有限の小モデルと一般の一更新式の検査を区別する。',
      '- 誤store順の実Wasm負例6個は全て不一致を検出。負例の呼出しは上記の正対象件数に含めない。',
      '- WABT interpreterの主60本×4呼出し＝240比較も一致。source6本のbyte再現、公開memoryと誤store順の2profile拒否を確認。',
      '- fixed/movingのraw/O3、計24/24条件を回復。回復binaryは全24で元rawとbyte一致。元ソース・seed・正解manifestを回復器へ渡していない。',
      f"- 変換12件の単回時間は{min(x['ms'] for x in trans):.3f}–{max(x['ms'] for x in trans):.3f}ms。回復24件は{min(x['ms'] for x in attacks):.3f}–{max(x['ms'] for x in attacks):.3f}ms。いずれもWABT起動・読取・profile再生成・コンパイルを含む。",'',
      '回復器はまずfixedのprofileを試してからmovingを試すため、後者の時間には余分な再生成が入る。この実装上の差を保護効果の倍率に使わない。初期二表の合成はO(n)、一更新の抽象要約は履歴長に依存しない。未知方式の発見時間、汎用shape解析、人間の理解時間は未測定。','',
      '## 性能','',
      'O3後のcoreに共通Wasm wrapperを追加した。wrapperは各batchで一度resetし、LCG入力生成・run呼出し・checksumを繰り返す。V8は固定stepsを含めて最適化できる。steps=0は更新のみの対照。3サイズのv0だけを測り、v1へ一般化しない。','',
      '|ノード数|巡回回数|plain ns|fixed ns|moving ns|recovered ns|moving/plain|',
      '|---:|---:|---:|---:|---:|---:|---:|']
    for n in (4,16,128):
        for steps in (0,8,64):
            rs={r['mode']:r for r in pf['rows'] if r['n']==n and r['steps']==steps}
            v=[rs[k]['median_ns'] for k in ('plain','fixed','moving','recovered')]
            lines.append('|%d|%d|%s|%.3f|'%(n,steps,'|'.join('%.3f'%x for x in v),v[2]/v[0]))
    lines+=['','36条件×3 fresh Node process×7batch＝108process/756batch。warmup16,384回、20msを目標に校正、最大67,108,864回。全batch10ms以上。表は各条件21batchの中央値で、process中央値・最小最大・生データはsummary.json/raw.json。eager optimizing compilationを指定し、CPU affinity・周波数は未固定。', '',
      'wrapperの0/1/2/31/1024反復、3サイズ×3巡回回数×4版の180呼出しが一致。resetをtimed batchの先頭に含む。準備時間を一回当たりへ償却する小kernel測定で、実製品の速度予測ではない。','',
      '|ノード数|版|O3 core bytes|線形memory bytes|', '|---:|---|---:|---:|']
    for r in pf['rows']:
        if r['steps']==0:lines.append('|%d|%s|%d|%d|'%(r['n'],r['mode'],r['core_bytes'],r['memory_bytes']))
    raw=load(runtime/'raw.json');rss=[r['measurement']['max_rss_kib'] for r in raw]
    lines+=['',f"Node process peak RSSは{min(rss):,}–{max(rss):,}KiB。Wasmだけの実メモリ量ではない。確保された線形memoryは全版65,536byte、使用する初期配列はplainの8n byteからfactorの12n byteへ増える。Python変換器のpeak RAMは未測定。",'',
      '## 先行性と採否','',
      'Data location obfuscation（US9117094B2）の実行中配置変更・pointer scrambling、Drapeのdata refinementに近い。今回の四store更新は具体的だが、それだけで独立した新規性を認定できない。詳しい読了範囲はresearch/mutable-factor/prior-art.md。法的な特許性・権利侵害・権利の有効性は判定していない。','',
      'Aが変化しても、B∘Aという小さい観測関係は変わらない。この関係は巡回コードそのものに現れ、更新もこの関係の上で閉じる。固定表から可変表へ変更することで支払う実行費用に対し、追加の保護優位は確認できなかった。seedや交換回数だけを増やす次案は採らない。','',
      'NotDec/StackSightの実行、一般のallocatorやポインタ算術、外部観測・共有memory、実アプリ全体は未検証。既存ツールの未対応を強度として数えていない。これは次候補を絞る初期反証であり、研究全体は継続中。','',
      '再現はresearch/mutable-factor/README.md。sources/にソースsnapshot、provenance.jsonに全根拠・ツールのhashを保存。外部公開・push・課金はしていない。','']
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
    p.q.save(out/'provenance.json',dict(files=files));print(json.dumps(dict(pins=len(files),report=str(out/'report.md'))))


if __name__=='__main__':main(*sys.argv[1:])
