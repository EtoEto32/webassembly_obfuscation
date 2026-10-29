# 実アプリreplayでの復元・observer合成結果

2026-10-24。[実行前計画](r3-weave-plan.md)。Wasm-R3-Benchのうち先の実験で正常完走した10本を使い、Weaveの公開default設定で比較した。upstreamコードは変更していない。

## 実測

[変換](../../results/state-witness/r3-weave-inputs-v1/results.json)はplain / directoryの20本とも成功し、WABT validationも通過した。[実行](../../results/state-witness/r3-weave-v1/results.json)は10本×2構成×通常/復元の40条件で、36比較完了・4中断未到達、timeout/実行失敗/状態差は0だった。

- 通常実行20条件は全て元APIの結果と公開memory prefixが一致した。
- 復元条件20のうち16が最初のpollへ到達し、別instanceへのrestore/resume後に一致した。
- factorialとjqkungfuは両構成とも中断点へ未到達だった。通常完了として比較はできたが、復元成功の16件に含めない。
- directory構成20条件では、元の論理memory全bytes/長さ、numeric global bits、table参照のindex集合、segment probe、境界probeも比較した。連続二回の観測で元guest state差はなかった。

plain構成のmemory検査は元の最終memory長に相当するprefixであり、論理容量・private stateの完全照合とは区別する。directory構成の参照対応にも[信頼境界](threat-model.md)がある。観測に失敗していないことは全変換の正しさの証明ではない。

## 資源と限界

Node 24.15/V8、Windows単一host、各条件60秒、物理memory最大512pages、JS old-space 512MiB。元binaryも同じ上限で再実行した。Weaveが付加するprivate領域は元memory比較から除き、directory observer側の論理memory上限は256pagesを維持した。poll_period=512、stack_pages=16で、先の小例poll_period=1とは設定が異なる。

一条件につき一実行でwarmupはない。時間とRSSは診断値であり、統計的性能差は主張しない。ここでのWeave追試はNodeのみ。元/observer付き元をWasmtimeで比較した先のR3実験を、Weaveの独立engine追試として数えない。

10本はwebアプリのrecord済み実行から作られたreplay binaryであり、元webアプリの全入力を代表しない。また対象にdata.drop/elem.dropがなく、寿命が変わる実アプリにおける誤復元を新たに発見したわけではない。Weaveがこの集合で正しく働いたという正常対照と、Kの合成範囲拡張として位置付ける。

## 再現

既存の固定source build `.tools/weave-build` に、[小さいdriver](weave-default.rs)を `src/bin/weave-default.rs` として配置し、`cargo build --release --offline --bin weave-default` でbuildする。公開libraryのdefault optionsだけを使用する。依存取得は[Weaveの既存手順](weave-results.md)を参照。

```powershell
python research/state-witness/r3-weave-generate.py results/state-witness/r3-normalized-v1 results/state-witness/r3-audit-v2 results/state-witness/local-r3-weave-inputs
python research/state-witness/r3-weave-run.py results/state-witness/local-r3-weave-inputs results/state-witness/local-r3-weave
```

出力は新しいdirectoryへ保存する。transform入力、driver、adapter、CLI hash、各実行のsource hash、途中段階、失敗分類を保存している。
