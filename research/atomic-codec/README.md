# アトミック命令に両立する表現変換：実装と限界

2026-10-21。共有memoryの値を符号化し、一つの元RMWを一つのnative RMWへ写す生成器を実装した。正当性とCAS対照からの限定的な高速化は確認したが、**独立した主難読化方式としては不採用**。既存の有限環残差方式の構成的提案は保持する。

[事前計画](plan.md)、[アルゴリズム・制限の証明](algorithm.md)、[一次資料との比較](prior-art.md)、[論文ノート](paper-note.md)を参照。

## 得られたもの

演算集合に応じ、加減算中心なら奇数係数affine、bitwise RMWもあるなら全bit反転を選ぶ実Wasmパスを作った。load/store/cmpxchgも同じ表現へ写す。アドレスの即値offset、自然整列、旧値の返却を保持する。

全加算を固定ADD/SUB一命令、全ANDを固定AND/OR一命令で実行できる全単射word表現は、恒等か全bit反転に限られる。この限定条件を導出し、2～6bitの2,728候補、173,922組の検査と棄却反例で監査した。数学的な初出や、CAS・複数word表現まで排除する不可能性は主張しない。

対象は固定1pageの共有memory importを使う32bit atomic profile。hostはworker起動前に各wordを一度符号化し、全参加者は変換後APIを使う。従来表現のmemoryを直接操作する任意hostへのdrop-in置換ではない。混合幅・非atomic access・growth・data/start・wait/notify等は非対応。CAS対照には競合下の個別threadの終了保証がない。

## 保存した実測

|検査|結果・範囲|
|---|---|
|主raw/O3|18正条件、16,470呼出し、期待trap6,946。返値と全memory一致|
|追加の評価順・成功CAS・trap前副作用|10条件、元と変換の計4,000呼出し（2,000比較）、trap2,400呼出し。一致|
|実worker|10正条件の4worker ticket試験327,680更新。旧値が連番の置換、最終値も一致|
|混合履歴|8条件×16履歴×6更新=768更新。各履歴にthread順序を満たす逐次一貫な順序が存在|
|負例|誤ANDのraw/O3を検出。非原子的分割の4workerは32,768更新に対し最終値19,746 / 18,480となった|
|別実行器|WABT 18条件×9probe=162照合（36trap含む）、一致。並列WABT実験ではない|
|再現・拒否|主22本のbyte一致、非対応4例と不適合affine 1例の拒否|
|自動選択|2入力profileで、対応する検査済みnative版とbyte一致|
|方式既知の回復|符号化14/14条件で2回の選択storeから係数を求め、全memoryを回復。plain4条件をこの14へ含めない|

主プログラムは同じAPIのfull/counter部分集合で、18の独立アプリではない。境界・固定seed入力を用いる有限試験であり、全プログラムの意味保存を機械証明したものではない。実行間の開始・終了時刻まで記録したlinearizability検査でもない。負例のraceはscheduler依存で、再現時に取りこぼしが発生しなければno-witnessとして扱う。

競合なしfetch-add loopのO3、3 fresh process×9 batchでは、plain約7.13ns、反転native約7.12ns、反転CAS約7.56ns、affine native約7.13ns、affine CAS約8.31ns。同じcodecのCAS版から約5.76% / 14.16%短縮した。[生値と比較表](../../results/invention-20261021/atomic-codec-report-v2/comparison.md)。全条件の線形memoryは64KiB、process最大RSSは約37–38MiB。変換は主条件で約36–40ms（WABT読取・compile/validate含む各1回）。競合下性能や実製品の倍率は未測定。

## 判断

Tigressの公式資料には、実際の演算に適合するcodecを選ぶautomatic規則が既にある。De Morgan則、affine、一般更新をCAS loopにするloweringも既存。本案の差は、Wasm atomicの一命令条件を明示した限定構成と制限の導出にあるが、主発明としての独立性は弱い。

回復できることだけを不採用理由にはしない。同じ選択store攻撃が全符号化条件に2回で通り、追加の保護費用が確認できないこと、速度改善が既知の単純codecへ制限してCASを省くことで得られていることを判断根拠とする。一般の型・構造復元を評価した成果ではない。

## 再現

Python 3.9標準ライブラリ、Node 24.15.0/V8 13.6、WABT 1.0.42、Binaryen 133。Windows、16 logical processors。詳細は[環境](../../results/invention-20261021/atomic-codec-report-v2/environment.json)。依存readerはresearch/isotope-swizzleとconnectivity-eliminationのprototype.py。新package・課金なし。

rootから未作成の出力先を指定する。各コマンドは既存結果の上書きを拒否する。

```powershell
python research/atomic-codec/model.py results/atomic-new/model/model.json
python research/atomic-codec/run.py results/atomic-new/main
node research/atomic-codec/concurrency.cjs results/atomic-new/main
python research/atomic-codec/extra.py results/atomic-new/extra
python research/atomic-codec/audit.py results/atomic-new/main results/atomic-new/audit
python research/atomic-codec/choose_codec.py results/atomic-new/main results/atomic-new/selection
python research/atomic-codec/performance.py results/atomic-new/main results/atomic-new/runtime
python research/atomic-codec/report.py results/atomic-new/main results/atomic-new/runtime results/atomic-new/extra results/atomic-new/audit results/atomic-new/model results/atomic-new/selection results/atomic-new/report

# 個別の実バイナリ変換
python research/atomic-codec/prototype.py results/atomic-new/main/full-source.wasm results/atomic-new/example.wasm --mode auto
```

計測時は重い処理を並列実行しない。性能はCPU固定なし、128×128 warmup、batchを8ms目標で調整、9標本の中央値、3 processの中央値。実worker起動・初期化と性能測定を混ぜない。攻撃識別時間はcompile/instantiate込み各1回約0.23–0.48msの診断値であり反復した解析費用分布ではない。

保存先はresults/invention-20261021のatomic-codec-{main,model,extra,audit,selection,runtime}-v1とatomic-codec-report-v2。reportにはソースsnapshotとhash pinsがある。report-v1はselect.pyがPython標準moduleを隠した集計エラーで中断し、choose_codec.pyへ改名して修正した。実験値は変えていない。外部公開、push、出願をしていない。
