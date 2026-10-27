# ビット依存フィードバック：実装と不採用の判断

2026-10-18。**主方式には採用しない。** ビットの閉路検査から残差フィードバックのマスクと有限更新回数を生成する手順を実装した。正当性は支持されたが、元と同じBoolean DAGへ自動回復でき、実行費用に見合う保護効果を確認できなかった。独自で有効な難読化発明の確立、特許性の判断は未達である。

## 構成と意味保存

[事前仕様](plan.md)に従い、純粋なi32 SSA計算 v=F(v,x) に対して後方の語の残差を前方の語に加えた。

    H_i(v,x) = F_i(v,x) XOR XOR_{j>i} (((v_j XOR F_j(v,x)) << k_ij) & m_ij)

元の命令のビット依存関係を保守的に展開し、追加辺が閉路を作るビットをマスクから除く。最長路の予算は元の深さ+16。候補をseed 17/29で順序付けし、最大min(12,節点数)個のshift-and-maskを選ぶ。部分マスクを許すmaskedと、全ビットを受理できない候補を捨てるuniformを比較する。seedを別の発明と数えない。

固定点の残差rはr=Grを満たす。Gは厳密上三角だからr=0。ビットDAGの深さ1の値は1更新後、深さdの値はd更新後に確定するため、最大深さD回で元の計算へ収束する。残差内のF_jの依存は、元のjへの辺とjからの追加辺の合成で覆われる。この説明は対応演算の依存モデルが正しい場合の条件付き論証であり、実装全体の機械検証ではない。

Wasmのi32剰余演算・shift仕様に従うが、原理は他の語演算にも適用可能。Wasm固有の新原理とは主張しない。

## 対応範囲と回復タスク

単一関数、i32引数、結果一つ、直線コード、local、定数、add/sub/mul/and/or/xor、定数shift/rotate、1–32演算節点。memory・import・call・global・ソース制御フロー・trap演算・浮動小数点は拒否する。副作用とtrap順序を扱う一般変換器ではない。

攻撃者は方式とバイナリを知る。元ソース、seed、生成レポートは回復器に渡さない。ループ1回分を記号実行して更新式を抽出し、ビットの固定点方程式を依存順に解いてXOR等を正規化する。減算カウンタを抽出し、出力の確定に必要な更新回数も検査する。任意のループの逆コンパイラではない。

保護目標は元と同じBoolean DAGを得るための費用増加。元の変数名の回復、一般プログラムの理解時間、実製品全体の保護効果をこの小例で代用しない。

## 結果

主データ：[bit-feedback-v3](../../results/invention-20261018/bit-feedback-v3/)。[比較表](../../results/invention-20261018/bit-feedback-v3/comparison.md)、[実行時間](../../results/invention-20261018/bit-feedback-v3/runtime.json)、[解析時間](../../results/invention-20261018/bit-feedback-v3/analysis-timing.json)、[監査](../../results/invention-20261018/bit-feedback-v3/audit.json)。

3カーネル（arx、blend、carry）×8表現（plain、同期更新のみ、uniformの2seed、maskedの2seed、maskedと同じ回数の無feedback対照2つ）×raw/O2/O3 = 72条件。

|検査|結果|
|---|---|
|主72本と回復72本、各2,244入力|基準と対象の呼出しを合計646,272回、不一致0|
|別エンジンWABT interpreter|72条件×4入力=288回、不一致0|
|非zero初期状態2値、raw/O3、基準込み27条件|121,176呼出し、不一致0|
|2/3/4bitの3節点例、全入力と全初期状態|209,664組、不一致0|
|更新数を1にした誤バイナリ|2,244入力すべてで差を検出。回復器も上界不足を拒否|
|非対応4種類|明示的に拒否|
|Boolean DAG回復|72/72成功、元と同じ出力digest。未対応・解析失敗・クラッシュ・タイムアウト発生0|

全入力の実装同値性を実行検査で証明したとは主張しない。回復後Wasmもvalidationと実行照合を行った。

実行時間は216 fresh Node process。各10,000回warmup、9反復×10,000呼出し、各バイナリ3 process、固定seedで順序をshuffle。JS呼出し・入力取得費用を含む。CPU固定・JIT tier固定はしておらず、process中央値のばらつきを表に併記する。小さな時間差を優位性と断定しない。

解析時間は1回warmup＋9反復。WABT起動・disassembly・parseを除き、bit計算・停止上界の検査・DAG digestを含む。初回のparse込み時間はmanifestに別記録。linear memoryは0 byte。RSSはNode/V8全体の最大値であり、Wasmだけの追加量ではない。21回の変換時間・サイズも保存した。

部分マスクは一部の候補を残せるが、全3カーネルでuniformも生成できたため、一般的な適用範囲拡大は未実証。carry/seed17はuniformとmaskedが同一バイナリとなった。

## 失敗原因と先行技術

停止性のために残したビットの非巡回性は、解析者にも依存順の回復手順を与える。確定後の残差が相殺されるため、元と同じDAGが残った。語単位の循環やループ残存だけではこの回復を妨げない。実行側が毎回反復を支払うのに対し、解析側の追加費用は今回、元のbit展開費用に近かった。この費用関係と新規差分の弱さが不採用の理由であり、「回復できたから」ではない。mask密度・seedだけの変更を次の発明にはしない。

- Riedel/Bruck, *The Synthesis of Cyclic Combinational Circuits*, DAC2003, pp.163–168。[著者掲載ページ](https://mriedel.ece.umn.edu/wiki/index.php/File%3ARiedel_Bruck_The_Synthesis_of_Cyclic_Combinational_Circuits.pdf)の検索結果は確認したが、今回論文本文は取得できなかった。
- 関連する[US7249341B2](https://patents.google.com/patent/US7249341B2/en)の一次検索による本文・請求項1等の抽出には、非循環networkへのcycle導入とcombinational性判定の反復が記載される。全請求項の照合ではない。
- Kaveh Shamsi, Meng Li, Travis Meade, Zheng Zhao, David Z. Pan, Yier Jin, *Cyclic Obfuscation for Creating SAT-Unresolvable Circuits*, GLSVLSI2017, DOI [10.1145/3060403.3060458](https://doi.org/10.1145/3060403.3060458)。[著者PDF](https://personal.utdallas.edu/~kaveh.shamsi/publications/GLSVLSI17_Obfus.pdf)本文、Algorithm 1、評価を確認。査読会議論文。鍵付き経路やIC camouflagingの循環構造により既存SAT攻撃のDAG前提を外す。面積・遅延の改善を報告する一方、適応的攻撃と詳細な物理評価を課題とする。本案の公開ソフトウェア上のbit解析とは攻撃モデルが異なる。
- repo内の[固定点検査](../../tmp/fixed-point-source-audit/README.md)、[carry収束検査](../../tmp/settling-carry/README.md)も比較した。固定点難読化の初提案とは扱わない。

[特許調査台帳](../patent/README.md)には公開特許5件の確認範囲と構成対応を保存した。新規性・進歩性・権利侵害の有無は結論していない。

## 環境・再現

Python 3.9以上、Node 24.15.0、WABT 1.0.42、Binaryen 133、Windows x64。CPU等は[environment.json](../../results/invention-20261018/bit-feedback-v3/environment.json)。外部Pythonライブラリ不要。ツールは`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`、親は`WASM_TOOLS_ROOT`で変更できる。共通WAT parser・ツール呼出しに`research/connectivity-elimination/prototype.py`、命令平坦化に`research/stack-cycle/transform.py`を使う。リポジトリ全体を保存して実行する。

```powershell
powershell -NoProfile -File research/bit-feedback/reproduce.ps1 -Output results/invention-20261018/bit-feedback-reproduction
python research/bit-feedback/transform.py input.wasm output.wasm --mode masked --seed 17
python research/bit-feedback/recover.py output.wasm --output recovered.wasm
```

新しい出力先が必要で、既存バイナリ・実験ディレクトリは上書きしない。v1は混在したfolded/stack表記の読取エラーで途中停止。v2で修正し完走。v3は回復器に停止上界の検査を加えて再測定した。v2/v3の変換・回復バイナリ144本を比較して監査する。これらを独立した発明の成功数にしない。[日本語草稿](paper-note.md)。
