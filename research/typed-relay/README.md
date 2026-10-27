# 型付き共有relay：実装と反証

2026-10-18。**新しい難読化としては不採用。** 共有relayを深くすると固定長call-string解析に必要な文脈長は増えたが、引数位置の要約は安く構成できた。さらに通常のBinaryen O2/O3が追加の関数呼出しをすべて除去した。CPS・common prototype・call routingとの独立した差も弱い。[先行研究の確認範囲](prior-art.md)

この実験は「Wasmの型付き関数参照へ移せば新規で強い方式になる」という次案を避けるための対照であり、LuのCPS実装の再現・解除でも、論文や特許に使える主方式の完成でもない。難読化として解除不能性は要求していない。[評価方針](../evaluation-policy.md)

## 何を実装したか

実入力 `.wasm` のtrapしない二項i32演算を、同じsignatureの演算関数へ抽出する。非nullなtyped function referenceを直接呼ぶ版と、共有relayを1/4/8段通す版を生成する。relayは通常callまたはtail callを使う。sourceのloop、分岐、load/storeの順序はそのまま残す。[事前計画と疑似コード](plan.md)

保護目標は、各呼出し箇所で実行される元の演算とそのオペランド関係の回復である。loopの構造そのものを隠す変換ではない。解析者は全バイナリと方式を知り、元sourceや生成manifestを使わない。回復器はhelperの純粋性・引数対応を検証し、summaryをmemoizeする。副作用を落としたり、オペランド評価順を変えたりし得るhelperは拒否する。

対象は1つのexport `run` と固定1pageのexport `memory` を持つmodule。import/global/table/data segment、既存call、memory.grow、複数関数は入力非対応。folded WATで左右の子式が得られない算術命令も拒否する。バイナリ読み書き・validationはWABTを使う。原プログラムの副作用を持つ演算の移動や、任意プログラム全体への同値性証明は行わない。追加呼出しのstack等の資源は十分にあると仮定する。

## 実験結果

主記録：[typed-relay-v2](../../results/invention-20261018/typed-relay-v2/)。途中失敗は削除せず保存した。smoke-v1はBinaryen feature flagの不足、smoke-v2はWABT timeout、主v1は実行器間の値の相違を検出して中断。v2ではそれらを別集計し、第三の実行器を追加した。

[別出力先での再実行と監査](../../results/invention-20261018/typed-relay-replay-v3/verification.json)も完走し、108主バイナリのSHA-256が一致した。正当性・回復・最適化による消去・WABTの不一致分類も再現した。性能には実行ごとのばらつきがあり、上の主記録と混ぜて標本数を増やさない。

- 3つのbyte処理loop × 6方式 × raw/O2/O3 = **54主条件**。回復後54本を加え108バイナリ。
- Node24.15.0 / V8 13.6.233.17-node.48で**123,120呼出し、不一致0**。うち34,452は期待したmemory trap。各回で全65,536byteを比較し、途中のstore後にtrapする例も含む。
- 各binaryは140境界入力＋1,000ランダム入力。別実装のJavaScript参照計算と比較した。無限・巨大lengthを全列挙した試験ではない。
- Binaryen133のinterpreterは108本×4入力、**432呼出しでassertion成功**。零初期memoryで3正常入力と1境界trapの限定チェック。
- WABT1.0.42のinterpreterは108件中、**99一致、6値不一致、3 timeout（2秒）**。成功件数へ混ぜない。[最小再現](../../results/invention-20261018/typed-relay-engine-v2/results.json)では、callerに値が残るtail-ref呼出しを含む足し算で、Node/Binaryenが117、WABTが21を返した。原因箇所の修正や上流報告は未実施で、実行器側の問題を疑う根拠として保存した。
- バイナリのみのsummary回復は**54/54成功**。未対応・クラッシュ・timeoutはこの回復器では0。raw18条件は、回復した関数ASTが元のASTと厳密一致。
- 最適化後36条件（元6、変換30）では関数数1、call/call_ref/return_call/return_call_refすべて0。通常最適化だけで追加機構が除去された。
- helperの引数入替え、store追加、循環化という3つのvalid Wasm対照を回復器が拒否した。循環対照は実行せず、回復器の検査だけを行った。

### 文脈長と要約は別の費用

rolling例の4種類の演算を共有すると、0-call-stringは一つの間接呼出しに4候補を集める。深さ1はk=1、深さ4はk=4、深さ8はk=8で候補が各1個になる。深さ8では状態context数がk=0の13からk=8の69へ増えた。[全270解析条件](../../results/invention-20261018/typed-relay-v2/reference-flow.json)

これは形式引数のref集合に限定した保守的解析であり、一般Wasmのpoints-to解析ではない。最悪計算量を証明した値でもない。方式既知のsummaryは深さ8でも12～13個のhelperを一度ずつ調べれば足りる。必要なcall-string長の増加を、そのまま最良の解除方法の費用増加としない。

### 性能

以下はrawの64byte処理1呼出し。nsは3 fresh processの各中央値の中央値。解析はWABT処理を除くPython summary構成・書換えの中央値。両者の時間を直接割って保護強度と呼ばない。

|例|方式|bytes|実行ns|解析ms|
|---|---|---:|---:|---:|
|rolling|元|121|73.5|0.0513|
|rolling|typed ref直接|206|111.4|0.0906|
|rolling|tail深さ1|218|164.0|0.0989|
|rolling|tail深さ4|254|163.4|0.1126|
|rolling|tail深さ8|302|619.8|0.1248|
|rolling|通常call深さ4|254|162.9|0.1148|
|dual|元|131|48.1|0.0597|
|dual|tail深さ8|328|803.8|0.1313|
|update|元|146|46.2|0.1075|
|update|tail深さ8|347|699.0|0.1397|

深さ8のrawは実行8.43～16.71倍、今回のsummary処理は1.30～2.43倍。元の解析も同じmodule検査やAST再構築を含む。絶対値は小さく、この比を他の解析器や人間の費用へ一般化しない。O2/O3では変換部分が消えるため、それ以上の保護性能は主張できない。

総計162 fresh process。各processでwarmup3,000呼出し、その後11反復×1,000呼出し。JSからの呼出しloopを含む。compile/instantiateを除外。update例のmemoryは呼出し間にresetしないため、継続更新時の定常的な仕事量を測る。coldな書換え費用の指標ではない。CPUはi9-11900K、Windows、Python3.9.0。[中央値・四分位・各process値](../../results/invention-20261018/typed-relay-v2/verification.json)

全条件の公開linear memoryは65,536B、追加linear memoryは0。Node全processのpeak RSSは40,136～41,276KiB。これはWasm単独のheap/stack使用量ではない。変換は53.71～62.99ms（各1観測）、WABT validation/disassemblyは26.34～30.61ms。解析器のpeak memoryと開発工数は未測定。[生データと全比較](../../results/invention-20261018/typed-relay-v2/comparison.md)

## 再現

Windows、Python3.9以上、Node24.15.0、repoの `.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin`。追加Python packageは不要。別配置は環境変数 `WASM_TOOLS_ROOT` でtoolsの親を指定する。外部公開・ネットワーク・課金は必要ない。必ず新しい出力先を指定する。

```powershell
python research/typed-relay/run.py results/typed-relay-new
python research/typed-relay/audit.py results/typed-relay-new
python research/typed-relay/engine_probe.py results/typed-relay-engine-new
```

変換・回復を個別に行うCLI：

```powershell
python research/typed-relay/prototype.py transform input.wasm protected.wasm --mode tail4
python research/typed-relay/prototype.py recover protected.wasm recovered.wasm
```

`--mode` は `ref`, `tail1`, `tail4`, `tail8`, `call4`。一般的なWasm入力を扱う実用製品ではない。今回の第三者向け再現を可能にする研究用CLIである。

## 判断

call-stringに対する効果は観測できた。しかし共通signatureと固定の引数転送は、コンパイラにも解析者にも対応を示している。通常最適化で消えること、より安いsummary回復があること、既知方式との独立した差が弱いことを合わせて不採用とする。これだけでCPS難読化一般が無効とは結論しない。特許に向けた独自で有効な主方式は未確立。
