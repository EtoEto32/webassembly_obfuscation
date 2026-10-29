# 状態の対応を重ねるNFA化：実装・反証・再現

2026-10-18。**動作するWasm変換器は得たが、特許・論文の主方式には採用しない。** 状態の対応を曖昧にしても、簡潔な等価処理を作る費用を十分に増やすとは限らなかった。新規で有効な難読化の確立は未達である。

[固定した仮説](plan.md) → [アルゴリズム・成立条件・失敗原因](analysis.md) → [先行技術・公報照合](prior-art.md) → [日本語草稿](paper-note.md)。研究全体の基準は[難読化の評価方針](../evaluation-policy.md)に従う。

## 実装

元DFAと全語を受理する補助NFAを積にし、元DFAを使って意味保存を確認した状態結合だけを採用する。各NFA状態が対応し得る元状態の数を得点にし、重なりを増やす結合を選ぶ。配布Wasmはi64 localに到達状態集合を保持して更新する。

- `prototype.py transform input.wasm output.wasm --mode overlap`：実バイナリを読み、検証済みテンプレートに一致する場合だけ変換する。`lift` は積のみ、`random` は安全な結合の無作為選択。
- `prototype.py recover input.wasm output.wasm --method subset`：バイナリのみからNFAを抽出し等価DFAへ回復する。`bisimulation` / `simulation` / `reverse` も利用可能。元DFAやseedを入力にしない。
- `model.py`：言語包含の証明用検査、結合、trim、決定化、既知の簡約対照。
- `run.py`：生成、最適化、回復、差分検査、別エンジン、負の対照、性能測定、ソース保存。
- `study.py`：7種類の元DFA・補助幅3/5・2seedによる70モデル条件と、簡約器の独立検査。

入力は最大16状態の二文字DFAを実行する指定のWasm scannerのみ。公開APIは `run(pointer:i32,length:i32)->i32` と固定1pageの `memory`。文字は各byteの下位bit。出力NFAは最大64状態。任意のC/C++や一般Wasm関数を変換できる実装ではない。import、追加export、memory growth、共有memory、任意の副作用は非対応。

## 主実験

主結果：[overlap-wasm-v3](../../results/invention-20261018/overlap-wasm-v3/)。3カーネル × 元/積/無作為/重なり選択 × raw/O2/O3 = 36条件、回復36本を加えて72本。

|検査|実測|
|---|---|
|WABT / Node validation|72本受理|
|Nodeの値・trap有無・全64KiB memory照合|148,680呼出し、不一致0。期待trap 19,728|
|入力内訳 / binary|境界42、seed固定random 1,000、長さ0–9の二進語全1,023|
|WABT interpreter|288呼出し、不一致0|
|方式既知の回復|36/36成功、4経路すべてで元DFAと全語の言語同値性を確認|
|主解析の未対応 / crash / timeout / state limit / 誤答|いずれも0|
|不正なアドレス・副作用・bit判定を持つ有効Wasm|3対照を回復器が拒否|
|誤った状態結合の実Wasm対照|入力000で元0、誤結合後1をWABTで確認|

差分試験が通過しても、任意Wasmの全入力・全実行環境の数学的同値性を証明したとはしない。trapメッセージの文字列一致、コンパイル時メモリ不足、fuel上限は対象外。

## 費用

V8の同一プロセス内で3,000回warmup後、1,000呼出し×11標本。64byte/call、Nodeを条件ごとに3回新規起動し、起動順をseed固定で混ぜた（計108 process）。表はプロセス内中央値を3つ集めた中央値。JS呼出しループを含み、compile/instantiateは含まない。CPU固定・周波数固定は行っていない。[全条件・ばらつき](../../results/invention-20261018/overlap-wasm-v3/summary.json)。

|raw条件|bytes|実行 ns/call|最速の解析経路 ms|
|---|---:|---:|---:|
|suffix010 元|119|61.9|0.0310|
|suffix010 積|262|168.3|0.0348|
|suffix010 無作為|181|99.0|0.0339|
|suffix010 重なり|181|98.8|0.0352|
|contains0110 元|120|61.2|0.0424|
|contains0110 積|516|387.5|0.1071|
|contains0110 無作為|245|171.2|0.0576|
|contains0110 重なり|245|157.0|0.0601|
|mod4 元|118|64.9|0.0271|
|mod4 積|589|408.5|0.0641|
|mod4 無作為|309|217.7|0.0368|
|mod4 重なり|309|217.7|0.0360|

解析時間は抽出後モデルについて11回測った中央値の、4経路中の最小。前処理・DFA最小化を含む。WABT起動・parse/validation（単回26.65–31.60ms）と、再生成による全プログラム照合（単回56.75–235.28ms）は別計上する。これらI/O・検査器の固定費を保護強度として数えない。専用解析器の開発費用は測定していない。

O3でも重なり版の集合更新は残り、suffix010 / contains0110 / mod4はそれぞれ155 / 230 / 299bytes、90.8 / 154.7 / 232.6ns/callだった。通常最適化に残ることと、方式既知の解析に費用を課すことは別である。

全条件の公開線形memoryは65,536byte、追加線形memoryは0。最大プロセスRSSは40,316–40,732KiB（V8など全体を含む）。変換は112.80–272.89msの単回観測。解析ごとのPython heap peakは`analysis.json`へ保存（別実行のtracemalloc、nativeや外部processのメモリは含まない）。Python解析msとV8実行nsを直接割って保護効率としない。

## 拡張モデルと結論

[overlap-study-v1](../../results/invention-20261018/overlap-study-v1/)は7 source × 2guard幅 ×（積1seed + 無作為2seed + 重なり2seed）の70条件。NFA最大146状態。4経路×70すべてが等価DFAへ回復し、通常subsetで訪問した集合は最大92、全経路中は最大274だった。1..6状態の任意NFA 120例でも、追加したsimulation簡約の前後を独立の決定化・言語比較で検査し不一致0。これは一般実装の形式証明ではない。

重なり得点を上げても、簡約後の集合数が減る例があった。例えば `contains0110, k5, seed20261018` で無作為→重なりの得点は47増えたが、四経路の最少訪問集合数は21→16。集合数は時間の代用ではなく、この例は「得点増加が必ず回復探索量を増やす」という仮定への反例である。拡張モデルの時間は単回で、Wasm主実験と一部同時実行されたため、厳密な性能比較には用いない。

mod4/mod8では異なる元状態の右言語が互いに素なので、意味保存・trimの条件の下で重なりを作れない。この必要条件を証明し、全条件で得点0となることを確認した。

元に比べた解析費用の小さな増加は存在する。一方、重なりを優先する追加規則が無作為対照より一貫して費用を増やすとは確認できず、既知NFA構成から独立した保護効果も未確認。回復成功だけを棄却理由にせず、この限定案を主方式から外す。

## 再現

リポジトリrootでPowerShellから実行。Python 3.9.0（標準libraryのみ）、Node 24.15.0 / V8 13.6.233.17、WABT 1.0.42、Binaryen 133。`.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin` に既存のWindows実行ファイルを使用する。`WASM_TOOLS_ROOT`でルートを変更可能。新規ダウンロード・課金・pushは不要。

```powershell
python research/overlap-automata/run.py results/invention-20261018/overlap-local-replay
python research/overlap-automata/study.py results/invention-20261018/overlap-local-model-study
python research/overlap-automata/prototype.py transform results/invention-20261018/overlap-wasm-v3/contains0110.plain.raw.wasm results/invention-20261018/overlap-custom.wasm --mode overlap
python research/overlap-automata/prototype.py recover results/invention-20261018/overlap-custom.wasm results/invention-20261018/overlap-custom-recovered.wasm --method simulation
```

出力先は未使用名を指定する。既存ファイルを上書きしない。バイナリからの復元器は隣のJSONを参照しない。参照先の `suffix-transport/prototype.py` と `connectivity-elimination/prototype.py` を含むソースのコピー・SHA256は結果内`environment.json`と`sources/`へ保存する。

追加のi64境界検査は `python research/overlap-automata/edge_checks.py results/invention-20261018/overlap-local-edges` で再現する。bit 0/31/32/63、負数表記のi64定数、初期bit63を含む6本で12,390呼出し・不一致0。[境界結果](../../results/invention-20261018/overlap-edge-v1/checks.json)は主実験の72本に合算しない。既存の保存結果の監査は `python research/overlap-automata/audit.py results/invention-20261018/overlap-local-audit.json`。

一括再実行は[overlap-wasm-replay-v4](../../results/invention-20261018/overlap-wasm-replay-v4/)へ保存し、v3とのバイナリ一致を検査する。計測値自体は同一を要求しない。

過去のログも保持：screen-v1はdead stateで得点が水増しされたため無効、screen-v2は修正後。wasm-v1は4件がeqz未対応、wasm-v2は同4件がlow-bit出力表現未対応。これらは解析器の実装範囲の問題であり保護効果ではない。v3で対応を追加。v1の性能はモデルstudyと同時実行されたため主結果にしない。
