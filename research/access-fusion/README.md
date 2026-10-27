# 隣接アクセスと消費演算の統合：限定規則の検証

2026-10-18。主研究の途中成果。**この2フィールド規則単独を新規難読化として採用しない。** 非公開の型情報を回復しづらくする仮説の、最小限の動作・反証試験である。

## 研究仮説と実際に実装した範囲

NotDecはアクセスの幅・オフセットから型制約を得る。そこで、複数の隣接フィールドを広いwordで読み、個々の元フィールドをi32の途中値へ戻さずに消費演算を計算すれば、型境界が弱まるという仮説を置いた。

全体構想は「副作用境界ごとの読み取り範囲を覆う集合と、出力から必要なビットへの射影を同時に選ぶ」もの。ただし、その集合選択器・一般の領域合成は未実装。ここで実装した規則は次だけであり、一般構想の完成とはしない。

```
op(load32(p, offset=a), load32(p, offset=a+4))
  -> v=load64(p, offset=a)
     wrap32(op64(v, v >>u 32))
op in {xor, add, sub}
```

比較はplain、wide-split（元の2つのi32を一度取り出す対照）、wide-fused（上記）。wide-splitも自作の限定対照でありLLVMや既存難読化ツールの再現ではない。どちらも8バイトを読むので、wide-splitとの差は元のscalar途中値を構築するかどうかである。

## 意味保存の根拠

little-endianの64ビット値をv=L+2^32 Hと書く。xor/add/subの下位32ビットは、LとHに同じ32ビット演算をした結果に等しい。上位へのcarry/borrowはwrap32に影響しない。乗算・比較・除算やsigned拡張にはこの規則を適用しない。

両loadのアドレスは同じlocal.getであり、副作用はない。即値offsetはaとa+4、元の要求範囲の和集合は連続した[p+a,p+a+8)。Wasmの有効アドレス計算を32ビット加算へ置換せず、offset即値を保持する。このため、元の2loadが両方成功する条件とload64が成功する条件は一致する。一方だけが成功する入力でも、途中に外部効果がないのでメモリ範囲外trapとその時点のメモリを保存する。元領域より前のstoreは移動しない。

非共有memory32一つ、importなし、通常load、アドレス式はlocal.getのみを対象とする。shared memory、途中のstore/call、任意アドレス式、別名の再評価、memory64は対象外。時間・trapのPC・スタックトレースは観測対象外。有限試験は全入力の証明とはしない。

## 実測結果

最新結果は `../../results/invention-20261018/access-fusion-v2/results.json`。

4入力プログラム（xor、加算、減算、大きい即値offsetによるtrap確認）、3変換×raw/O2/O3とraw解除2形式、計44バイナリ。各1,047入力（境界23、memory内512、全32bit乱数512）で**46,068照合、不一致0**。返り値、同一エンジンのtrapメッセージ、64KiB全memoryのbyte列を直接比較した。Node24.15.0 / V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。

全例に実行前のstoreがあり、trap後にもこの更新が保たれるかを比較する。非整列、メモリ末尾、32bit有効アドレスoverflowを含む。大offset例は全入力がtrapし、値の演算検証の成功数として解釈しない。

|raw条件|xor / add / sub bytes|大offset bytes|使用するload|
|---|---:|---:|---|
|plain|68|76|i32×2|
|wide-split|83|87|i64×1|
|wide-fused|82|86|i64×1|

適応的解除器はバイナリのhelperの型・演算を認識し、呼出し地点のload64を元のoffset間隔4の2loadへ戻す。元ソース・正解表・変換ログは渡さない。rawの8/8条件で1箇所ずつ回復し、その出力も上記の照合に含めた。unused helperを残すため解除後bytesは元と同じではない。元バイナリの完全再現率ではなく、対象アクセス式の復元を測った。

O2/O3後はhelperがinline化される例があり、解除器は未対応。これを防御成功とは数えない。最適化後のバイナリ・WATを保存したが、最適化後の適応的解除の成功率は未測定。NotDec/StackSight本体も今回実行していない。

全条件の線形memoryは65536bytes。変換時間はJSONに単発値として保存したが、性能・peak RSS・同等コスト比較は未実施。この早期棄却から性能優位を主張しない。

## 初回失敗と修正

v1は参照メモリを`Buffer.from(ArrayBuffer)`で保持し、snapshotをコピーしなかった。そのため後続入力で参照記録が変わり、未変換自身も不一致になった（46,024件）。これは難読化の意味保存違反ではなく検証器の誤りだった。

v1の結果・使用ソースを保存し、`Buffer.from(new Uint8Array(...))`で独立したコピーに修正して全条件をv2へ再実行した。v1を有効な失敗率へ加算せず、v2との入力重複も独立標本として数えない。

## 判断・先行研究

実行時に元のi32値を個別に生成しなくても、64bit値のビット射影で解析者は元の2値を回復できる。したがって「元フィールドの値をレジスタ上へ直接置かない」だけでは今回の保護目標を満たさない。

また、[LLVMのSLPベクトル化](https://llvm.org/docs/Vectorizers.html#the-slp-vectorizer)は既にscalarのまとめ上げを行う。今回のi64規則そのものを新しい原理としない。一般のアクセスcover最適化を進めるなら、通常のwideningと異なる規則と、ビット射影後にも残る復元課題が必要。単に対象幅やフィールド数を増やす実験には進まない。

## 再現CLI

```
node research/access-fusion/experiment.cjs experiment results/invention-20261018/access-fusion-reproduction
node research/access-fusion/experiment.cjs transform input.wasm output.wasm wide-fused
node research/access-fusion/experiment.cjs transform output.wasm recovered.wasm recover
```

出力先は新しいものを指定。依存はNode標準ライブラリと`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`。別配置は`WASM_TOOLS_ROOT`。入力バイナリを実際に読む変換器だが、一般Wasmの全機能に対応するとはしない。WABT生成WATを読む簡易パーサを使用。debug/custom sectionを完全には保存しない。
