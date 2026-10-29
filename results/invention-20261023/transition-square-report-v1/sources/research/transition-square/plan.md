# 遷移を合成した双模倣評価の仮説

2026-10-23。新規性未確認の実験仮説。元の回路を実行する代わりに、ラベル付き有限Markov graphの2状態が確率的双模倣関係にあるかを計算する。回路からgraphへの変換はChen / van Breugel / Worrell 2012の既知構成を基礎にする。これ自体を発明と数えない。

今回調べる核は、自己遷移を加えたL=(I+P)/2を二乗しQ=L^2だけを配布し、同じラベルと出力対で評価すること。2段先へのshortcutと元のedgeを混ぜ、gate境界の回復に追加の問題を作る仮説である。Wasmは整数重みとprivate linear memoryによる完全に決定的なpartition refinementを実行する。乱数sampling、暗号化、外部の秘密を使わない。Wasm固有の新原理とはまだ言えない。

対象は副作用なしの単一i32入力/出力のBoolean式。入力bit抽出、AND/OR、literal否定だけ。全word入力を許す。元のtrapやmemory副作用がある関数は拒否する。3つの大きさ、元/P/Q、raw/O3、2つのstate番号置換で比較する。

正当性はラベルpartitionのblock-constant subspaceがP不変であることとQ不変であることの同値を使う。生成graphはleafの自己loop以外DAGでPの固有値は0/1。Lの固有値は1/2と1なので主平方根を一意に戻せる。この事実は意味保存の根拠であると同時に解除方法になり得る。公開graphからtopological orderと三角行列の平方根を求め、Pを戻してBoolean式を回復する攻撃を**最初から**実装する。

成功条件は単にQが動くことではなく、P対照より回復に増えた費用が実行費用増に見合い、既知の行列関数・lumpability・回路還元だけに還元されない生成上の差を示すこと。全例を簡単に戻せる場合は主案へ採用しない。P-completenessを保護強度の証明に使わない。元source・seed・正解graphは攻撃器へ渡さない。

最も近い一次資料は [FoSSaCS 2012著者版§2](https://www.cs.ox.ac.uk/james.worrell/prob-bisim2.pdf)、[書誌とDOI](https://ora.ox.ac.uk/objects/uuid%3A9d0aa28e-8894-4a5f-b280-383d8d100d3a)。本文§2のmatching lemmaと回路還元、要旨を読んだ。後半のpseudometricアルゴリズムの実験再現ではない。行列平方根やlumpabilityに関する追加資料も検索し、新規性判断へ反映する。
