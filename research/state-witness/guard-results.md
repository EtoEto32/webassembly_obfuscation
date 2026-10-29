# 記号的なメモリ条件合成の結果

2026-10-24。[事前計画](guard-plan.md)、[アルゴリズムの論証](guard-proof.md)。これはKの追加解析であり、別の新発明成立とは数えない。

本書はmemory版の結果である。後続の[table拡張](guard-table-results.md)は同じ公式67対で55対を受理し、[反例抽出](guard-witness-results.md)まで実装した。以下の未対応50対という値はmemory版の受理範囲を示す。

## 何が増えたか

従来の有限APIモデルは、再構成した具体的memoryでの同一観測を示した。新しい試作は、固定したsegment寿命差に対し、**任意の初期memoryと任意長の元API列を対象に、各API終了後の結果・memory一致を保つ条件**を等式連言として合成する。扱える命令は定数bulk memory列などに限定し、parserと受理範囲は[実装](guard-analysis.py)に明示した。

実測由来のcase 0では、二つのcheckpoint条件の双方で次の条件を生成した。

```
memory[7] = 2 AND memory[8] = 7 AND memory[9] = 1 AND memory[10] = 8
```

この条件があるため、片側でinitがtrapし、もう片側で同じbytesを書いてから別のinitでtrapしても、元APIのtrapとmemoryが一致する。条件以外のmemoryは、左右で同じなら任意のbytesでよい。測定したmemoryはこの条件を満たした。条件を破るmemoryでは実API列で差が現れた。変換器の再開metadataを含む一般復元証明ではなく、元programへ射影したstateの条件である。

## 実験

|対象|分類・確認|具体実行|
|---|---|---|
|[12自作control](../../results/state-witness/guard-controls-v1/results.json)|コピー元への条件伝播、overlap、0長、unsigned境界、drop、矛盾等を照合。固定点1–5反復|216初期memory、各engine 10,428 API呼出し。Node/Wasmtime一致|
|[既存18復元差](../../results/state-witness/guard-context-v1/results.json)|条件付き2、全memoryで一致7、満たすmemoryなし2、未対応7|[受理11条件](../../results/state-witness/guard-validation-v1/results.json)で測定memoryと摂動143例、各engine 2,176 API呼出し。Node/Wasmtime一致|
|[開発moduleを除いた67状態対](../../results/state-witness/guard-corpus-v1/results.json)|全memoryで一致11、満たすmemoryなし6、未対応50|この表のguardは静的適用結果。全67対の新しい具体実行は行っていない|

具体列の実行上限は深さ4。任意長の主張はこの有限実行件数から導くのでなく、限定profileの固定点と論証に基づく。測定由来11条件は独立した11不具合ではなく、同じ元moduleの複数中断を含む。

## 生成器とは別の式による検査

説明例の後に規則を固定した[生成例追試](guard-random-plan.md)も行った。[96 module・576 memory](../../results/state-witness/guard-random-v1/results.json)は条件付き44、全memoryで一致40、満たすmemoryなし12となった。両engineそれぞれ119,160 API呼出しを実行し、条件充足例の相違と深さ4内で未判定の条件違反例は0だった。これはprofile内で事前に決めた人工分布の検査で、一般Wasmの発見率とは扱わない。追加の[SMT検査](../../results/state-witness/guard-check-random-v1/results.json)は385義務がUNSAT、弱めた88対照がSATだった。合計は119証明条件・438義務・102弱化対照である。

[Z3 array検査器](guard-check.py)を追加し、copy/constantのprovenance写像とは別にStore/Selectでbulk操作を記述した。生成したstate条件が各APIについて結果一致・post-memory一致・後続条件を含意するかを確認した。[小例12](../../results/state-witness/guard-check-controls-v1/results.json)の31義務と[実測由来11](../../results/state-witness/guard-check-context-v1/results.json)の22義務、計53義務がUNSATだった。条件を除去する14対照は全てSATとなった。

SATは「弱めた条件では検証義務を満たさない」という意味であり、その一回のAPIだけで必ず外部相違が出るとは限らない。後続条件が壊れる反例も含む。元の具体列検査では必要に応じて後続APIを実行して差を確認した。

parser/profileは共有しており、完全に独立した実装ではない。Z3 4.13.3を信頼する。UNSATは生成された条件の十分性の検査であり、最弱性、checker自体の正当性、Wasm全機能への適用の機械証明ではない。

## 新規性について

新たに得たのは、Wasmの限定したAPI/segment状態対について、具体memoryの一例から条件を一般化する実装と結果である。predicate transformer、等式抽象、帰納的不変条件、register automataは既存研究にある。そのため一般アルゴリズムの発明は主張できない。修士研究の技術的な貢献候補としては、trap前副作用を残すこの契約での条件合成と、具体復元差への適用が残る。50/67未対応という狭さと、近い解析手法との直接比較が課題である。

## 再現

```powershell
python research/state-witness/guard-controls.py results/state-witness/local-guard-controls
python research/state-witness/guard-corpus.py results/state-witness/spec-v4 results/state-witness/disjoint-v1 results/state-witness/local-guard-corpus
python research/state-witness/guard-context.py results/state-witness/cut-inputs-v1 results/state-witness/context-inputs-v3 results/state-witness/cut-v1 results/state-witness/local-guard-context
python research/state-witness/guard-validate.py results/state-witness/cut-inputs-v1 results/state-witness/context-v3 results/state-witness/local-guard-context results/state-witness/local-guard-validation
python research/state-witness/guard-check.py results/state-witness/local-guard-controls results/state-witness/local-guard-check-controls
python research/state-witness/guard-check.py results/state-witness/local-guard-validation results/state-witness/local-guard-check-context
```

PythonがWasmtime/Z3を読む場所は既存の`.tools/import-alias-quotient-python`と`.tools/encoding-synthesis-python`。旧context分類器を書き換えて結果に適合させていない。
