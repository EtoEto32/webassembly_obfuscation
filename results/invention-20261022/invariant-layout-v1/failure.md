# 初回実行の中断

2026-10-22。fixed版を最適化する際、Binaryenに`--enable-simd`を渡していなかったため入力validationが失敗した。元版とfixed rawはWABTで生成済み。実行結果や解析耐性として数えない。run.pyの最適化呼出しへflagを追加し、別の出力先v2へ再実行する。
