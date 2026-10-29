# メモリ表現候補を評価するための接続回復対照

2026-10-18。**新規難読化方式ではなく、次の候補の採用判断に使う攻撃側の基盤と対照実験。** NotDec、Howard、DSIの再実装でもない。新候補の数には加算しない。

## 検証した仮説

> 論理ノードを一つずつ巡回する構造が残れば、ノード内の配置変更やポインタ符号化を解除しなくても、実効アドレス列から訪問した接続を回復できる場合がある。

型名・固定offset・ポインタの生値を消したことだけで保護成功としないための比較。独立した一般的な新攻撃の主張ではなく、次の難読化案が超えるべき具体的な解析を実装した。

## 対照と観測契約

48要素の非循環列、96要素の循環列、128要素の非循環列を生成。各ノードは16バイトに整列した別領域にあり、nextとpayloadは各32bit。数値payloadの約1/3にポインタと同じ数値を意図的に含め、値の範囲だけでポインタを判定すると偽陽性が生じる条件を設けた。

3つの表現は自作の既知原理の対照であり、先行ツールの再現ではない。

1. `fixed`: nextがoffset 0、payloadがoffset 4。
2. `per-node`: ノードアドレスのbit 4によって二つの配置を選択。
3. `encoded`: 2に加え、nextを `next XOR (address * 0x9e3779b1 mod 2^32)` で格納。

公開`run(start_index, limit)`は、範囲外indexなら`unreachable`、それ以外は`limit & 255`回まで巡回し、`acc = rotl32(acc,5) XOR payload`を計算する。末尾0で終了する。循環列も必ず終了する。全32bit引数について契約を定義する。

メモリは非共有・非公開・固定64KiBで、実行中は読み取り専用。各対照の物理メモリ内容は異なる。等しいと検証したのは返り値とtrapであり、公開メモリの同値性ではない。専用の比較用プログラムであり、任意のWasmを難読化するパスではない。

## バイナリの計測

`instrument.py`は実際の入力.wasmを読み、WABTで名前を正規化してから、既存関数内のi32 loadをhelperへ置換する。元のアドレス式、loadの幅・符号拡張・即値offsetを保持し、loadの前後に記録用callbackを置く。元の関数参照を名前で保つため、import追加によるfunction indexの移動で呼出し先が変わらない。

callbackが引数を変更せず、対象プログラムから観測可能な副作用を起こさない条件では、元loadと同じ値を返す。loadがtrapするとafter記録は発生しない。記録には`unsigned(base)+unsigned(offset)`を使い、load自体の即値をi32のwrap加算へ置換しない。時間・資源・stack traceは保存対象外。全Wasm機能の形式的な保証ではない。

入力はdefined memory32が一つ、非共有、元importなし、読み取り専用のi32 scalar loadのプロファイルに限定。64bit/float/SIMD load、store、bulk memory、memory.grow、atomicを含むものを拒否する。WABTの正規WATを読む簡易パーサであり、debug/custom sectionの完全保存は保証しない。

`attack.cjs`に渡すのは記録と、**既知の16バイト整列仮定**のみ。ソースのnext配列、乱数seed、表現名、対応表は渡さない。アドレスを16バイト単位の領域へ写し、連続する同じ領域をまとめ、その後の領域への遷移を接続とする。正解グラフは攻撃が出力した後の採点にだけ使う。このコード上の分離はOSによる隔離ではない。

一般の型・shape推論器ではない。全要素を通る公開入力で得たtraceを使用し、未訪問の辺、nullへの終端辺、即時self-loopは回復対象外。ノードが同じ領域を共有する場合、無関係の領域も読む場合、整列単位が未知の場合には成功を保証しない。

## 実行結果

`results/invention-20261018/memory-trace-v1/`に入力・最適化済み・計測済みWasm、trace、参照データ、原コードsnapshot、hash、結果を保存。

- 3構造×3表現×raw/O2/O3 = 27条件。元と計測後の計54バイナリをWABT validate済み。
- 各条件336入力、元と計測後を独立JS参照計算へ照合。計18,144実行、不一致0。範囲外indexとwrap境界の引数を含む。
- WABT interpreterでは各未計測バイナリ4入力、計108実行を別のPython参照計算へ照合し、不一致0。計測importをWABT上で検証した結果ではない。
- 全27条件で対象の非null接続を偽陽性・見逃しなく回復。合計2,430辺。複数条件に同じ元グラフを使っており、2,430個の独立した未知構造を解いた意味ではない。
- 空trace、一ノードのみ、即時self-loopを回復したと誤認しない3対照を確認。

|表現（各9条件）|正解辺数|アドレス列からの正解／偽陽性|load値をポインタ候補とする正解／偽陽性|
|---|---:|---:|---:|
|fixed|810|810 / 0|810 / 267|
|per-node|810|810 / 0|810 / 267|
|encoded|810|810 / 0|6 / 267|

load値だけの検査ではencodedの見逃しが増える。しかし実効アドレス列には同じ巡回が残る。**この差を符号化の白箱保護効果として報告してはいけない。** XORの逆変換を知る攻撃でも解除できるが、今回の接続回復はその逆変換を必要としなかった。

回復処理のみの単発測定の中央値は表現別0.058–0.109ms。trace取得・Wasm実行・変換を含まず、反復性能比較でもない。命令数・サイズ・この時間から保護強度を導かない。完全な性能評価、RSS、NotDec本体との比較は未実施。

計測器の追加検査は`memory-trace-boundaries-v1/`。5種類のload、即値offset 0/65535/0xffffffff、非整列・メモリ末尾・全32bit境界の18入力を元と計測後で試した。30バイナリ、540実行、不一致0。範囲外loadの前記録が1回、後記録が0回になることも確認。既存helperへのcallも含む。有限検査であり、全入力の形式証明ではない。

環境: Windows x64、Node 24.15.0、V8 13.6.233.17-node.48、WABT 1.0.42、Binaryen 133、Python 3.9。CPUとコードhashはJSON参照。

## 先行研究と次の設計への制約

- Stephen Drape, *Obfuscation of Abstract Data-Types*, Oxford博士論文、2004。[本文](https://www.cs.ox.ac.uk/files/2892/thesis.pdf)の表紙、要旨、§7.2.1–7.2.2を追加確認。binary treeをternary treeへ写し、値の偶奇による位置選択とjunkを使う例がある。値依存の配置や非単射の表現を新原理とはしない。博士論文と査読会議論文を区別する。著者実装は未実行。
- Thomas Rupprecht, *Data Structure Identification from Executions of Pointer Programs*, University of Bamberg Press、2020、博士論文、[DOI 10.20378/irb-47325](https://doi.org/10.20378/irb-47325)、[本文](https://fis.uni-bamberg.de/bitstream/uniba/47325/3/fisba47325_A3a.pdf)。§15.1.2、§17.2.6を確認。naiveな型情報の組合せで隠れる例にも、memory chunkとpointer connectionを追うDSIrefが対応する。今回の規則はDSIrefの再現・改善ではない。著者のC/C++実験をWasmの結果へ転用しない。
- Anckaert, Jakubowski, Venkatesan, Saw, *Practical Data Location Obfuscation*, MSR-TR-2009-3、2009、技術報告。[機関ページ](https://www.microsoft.com/en-us/research/publication/practical-data-location-obfuscation/)の要旨を確認。heapの周期的再配置、localのheapへの移動、pointer scramblingを扱う。本文の全規則・評価値は今回未確認。
- Wangほか、*NotDec*, ICSE 2026、[本文](https://arxiv.org/html/2608.03286v1)。§3.2.1–3.2.2を再確認。固定offsetの減少やPNDiffの曖昧化だけでは、別の動的な接続回復も防げるとは言えない。2026-10-18に確認した[releases](https://github.com/NotDec/NotDec/releases)には配布物がなく、既存Docker daemonも起動していない状態だった。本体未実行。この環境事情を防御成功に数えない。

今回の設計判断は「配置変更の種類を増やして再試作しない」。ノードごとのアクセス遷移を残す案は、本解析を適用してから採否を判断する。巡回を変える場合にも、単なる全走査・ダミーアクセス・既存のoblivious accessを新規性の根拠にはしない。

**新しい変換規則自体はまだ確定していない。** この攻撃基盤や既知の3対照を、新規アルゴリズムの実装完了へ置き換えない。研究目標は未達成で継続中。

## 再現

リポジトリrootで、PythonとNodeがPATHにある場合。出力先は毎回新規にする。

```powershell
python research/memory-trace-audit/build.py results/invention-20261018/memory-trace-reproduction
node research/memory-trace-audit/check.cjs results/invention-20261018/memory-trace-reproduction
python research/memory-trace-audit/cross_engine.py results/invention-20261018/memory-trace-reproduction
node research/memory-trace-audit/check-boundaries.cjs results/invention-20261018/memory-trace-boundaries-reproduction
```

ツールは`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`。別配置は`WASM_TOOLS_ROOT`。`check-boundaries.cjs`の第2引数にはPython実行ファイルの絶対パスを指定できる。

対応プロファイルに対する計測CLI:

```powershell
python research/memory-trace-audit/instrument.py input.wasm observed.wasm
```

計測後には`audit.before(site,base,offset)->base`と`audit.after(site,base,offset,value)->value`を渡す。例は`check.cjs`参照。site情報は計測箇所の識別用で、元のフィールド名・next関係を含まない。
