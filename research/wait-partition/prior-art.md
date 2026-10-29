# 先行資料との比較

確認日2026-10-22。以下は実際に開いた一次資料と今回読んだ範囲。検索結果の表示日を原刊行年として扱わない。

| 資料 | 種別・読んだ範囲 | 今回との関係 |
|---|---|---|
| WebAssembly Community Group, [Threading proposal for WebAssembly](https://raw.githubusercontent.com/WebAssembly/threads/main/proposals/threads/Overview.md) | 公式提案文書。wait32/64、notifyとコード例。査読論文ではない | 期待値比較、同一アドレスの通知、戻り値、spurious wakeupを許さない仕様を確認。これらは新しい機構ではない |
| LLVM Project, [AtomicExpandPass.cpp](https://raw.githubusercontent.com/llvm/llvm-project/main/llvm/lib/CodeGen/AtomicExpandPass.cpp) | 公式実装。冒頭、performMaskedAtomicOp/widenPartwordAtomicRMW、insertRMWCmpXchgLoop周辺。固定リリースを網羅的に比較していない | 部分wordの更新を広いwordへ持ち上げ、CAS loopを使うことは既存。今回の64bit CAS化を独立した発明としない |
| Tigress, [Encode Data](https://tigress.wtf/encodeData.html) | 公式ツール資料。概要、codec一覧、automaticの選択規則。査読論文ではない | 使用演算に合う符号化を選ぶ一般的方針は既存。wait footprintから選ぶというだけで一般原理の新規性を主張しない |
| Sebastian Burckhardt, *Memory Model Sensitive Analysis of Concurrent Data Types*, 2007, University of Pennsylvania, [博士論文](https://acg.cis.upenn.edu/milom/papers/sebastian_burckhardt_phd.pdf) | 表紙と§7.2.5 Packed Words（印刷pp.102–103）。会議査読論文ではない。全実験章は読了していない | 複数fieldのwordへのpackingと、個別fieldではなくword全体へアクセスする並行意味上の注意は既存。今回のpackingの着想自体に新規性はない |

今回切り出した技術差分候補は「native waitの観測射影を保つ因子分解条件を使って、許可するcross-field shearを選び、同じqueueと命令幅を維持する」手順である。上の資料の読了範囲で同じ手順を確認したわけではないが、そのことは初出の証明ではない。一般の表現独立性・商への因子分解として自然に導けるため、独立した新規性は弱いと判断する。

反証検索として `WebAssembly obfuscation "wait32" encoding`、`"data encoding" "futex" obfuscation`、`"atomic wait" "encoding" "obfuscation"`、`"obfuscation" "futex" patent` 等を実行した。同じ構成を直接確認できる一次資料は今回の検索範囲では得られなかった。検索漏れ、別名での実装、特許分類による調査は未解決であり、網羅的な特許調査を完了したとはしない。

最も強い棄却理由は、既知のatomic loweringと可逆符号化を正しく組み合わせた限定的実装条件にとどまり、今回の保護目標が4回の選択書込みで回復する点である。正当性の拡張は成果として記録するが、強い難読化アルゴリズムの新規性を裏付ける主発明には採用しない。
