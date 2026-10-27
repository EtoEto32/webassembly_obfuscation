# 実測結果と判定

2026-10-26。Windows、Intel Core i9-11900K、Node24.15.0/V8 13.6.233.17、Python3.9.0、Z3 4.13.3、Wasmtime Python50.0.1、SpiderMonkey150.0.1、WABT1.0.42、Binaryen133。全て同じx86_64機上。独立CPU architectureの比較ではない。

## 正当性とモデルの範囲

16個の自作例をraw/O3の32実binaryへ生成。lane選択9例、swizzle3例、NaN3例、混合1例。各16入力（境界8＋固定seedの乱数8）を実行した。

|設定|呼出し|compile失敗/trap|修正後の具体値モデルで説明不能|
|---|---:|---:|---:|
|Node|512|0/0|0|
|Wasmtime通常|512|0/0|0|
|Wasmtime relaxed決定設定|512|0/0|0|
|SpiderMonkey|512|0/0|0|

`screen-v2`のSMT照合1,536件は全てSAT。`independent-v2`は全2,048実行を別の具体値計算で検査し、SpiderMonkey512件を修正SMTでも照合した。independent-v2はscreen-v1のbinaryを参照するが、auditでscreen-v2の32本とのbyte一致を確認した。

初期二択解釈でのSpiderMonkey120件の不一致は[既知byte選択の調査](model-revision.md)により再分類した。現状、新規engine bug、脆弱性、未知の最適化不正の発見は0。モデルと規範文書の完全な整合は未証明で、SATはモデルによる説明可能性を意味する。元とO3の全入力同値を証明していない。

## 検査感度

独立した具体値計算で許容性を決めた1,280組を4方式で照合した。659組はモデル内、621組はモデル外。正しい値を1bit変えた640組のうち19組は依然モデル内だったため、故障として数えていない。

|方式|モデル外621組の見逃し|モデル内659組の誤拒否|unknown|
|---|---:|---:|---:|
|joint（全出力の同時制約）|0|0|0|
|pointwise（出力ごとの所属）|57|0|0|
|independent-site|0|0|0|
|enumerated（共通profile列挙）|0|0|0|

このmutation集合は主として値のcopy関係を壊し、siteごとのprofile分離に対する検出差は生まれなかった。別途11手作業対照を実行し、site-profile-mixだけはjoint/enumeratedが拒否、independent-siteが受理することを確認した。独立NaN生成の異なる合法payload/signは受理できた。意図した反例を検出できたことを、実際のcompiler不具合の発見率と取り違えない。

## 費用

修正後`performance-v2`は4方式×3 fresh process。各processで同じ16caseを2batch warmup後、7batch測定。表示は1case当たりの時間、各process中央値の中央値。順序は固定seedでシャッフル。CPU固定・信頼区間推定はしていない。

|方式|ms/case|3 processの中央値範囲|query/16case|
|---|---:|---:|---:|
|joint|10.866|10.611–11.120|16|
|pointwise|14.059|14.004–14.098|108|
|independent-site|10.809|10.481–10.880|16|
|enumerated|11.315|10.946–11.332|29|

joint/enumerated比は約0.960。ただし範囲が重なり、わずかな差で一般的優位を主張しない。ここにはPython式生成とZ3検査を含む。実Wasm計算そのものや、他のfuzzerの速度との比較ではない。初期performance-v1は他の検査と時間帯が重なった探索的測定で、主比較には用いない。

検査processのpeak working setは約45.1–46.5 MB（10進）。Python/Z3全体の値で、提案固有の増分memoryではない。Node実行processのpeak RSSは36,984KiB。moduleはmemoryを宣言しないが、runtimeのstack/heap使用量が0という意味ではない。

rawサイズ69–179byte、O3は64–175byte。16本の生成＋validation時間中央値19.869ms、O3＋validation中央値24.374ms。外部ツールのprocess起動を含む。oracleは観測対象binaryへ計装を追加しない。

## 再現監査

`audit-v1/report.json`：7manifestの191file hash、一次source11件、42WAT再変換、32生成器text照合、raw/O3の32binaryのv1/v2 byte照合、32中央値再計算で不一致0。新しい意味モデルを数学的に証明した監査ではなく、保存物の整合・再生成検査である。既存paper/main.texとpaper/README.mdのhashは着手前の値を維持した。

## 厳格な研究判定

点ごとの弱い対照に対する効果は示した。しかし強い列挙対照と同じ検出結果であり、一般記号実行の枠を超えたアルゴリズム上の差は未確立。公式の同値性テスト、C4、既存I案に近い。最も目立った実engine不一致も既知の仕様議論に対応した。

従って**新しい独立アルゴリズムとして修士主テーマにする判断は保留**。同じ結果の対照があるだけで、応用・実装・評価の研究新規性が全て否定されたわけではない。主題にするには、仕様解釈を独立に確立したうえで、より広いbinaryへの自動適用、既存fuzzer/公式testに追加できる検査範囲、代表的な既知修正または未知の実不具合への効果、実用的費用を示す必要がある。現段階の小例と意図的mutationだけでは足りない。
