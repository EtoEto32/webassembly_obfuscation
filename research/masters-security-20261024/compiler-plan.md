# Bのコンパイラ出力への適用範囲を調べる追試

2026-10-24、コンパイル・測定より前に記録。

手書きWATの成功だけでは実用性を主張できないため、Rustから生成したCore Wasmを対象に、現在の解析器が範囲を得られる割合と全コピーになる理由を調べる。

- 自作の小さいRust処理（固定field更新、入力依存位置、条件付き更新、metadata読取り、bounded loop、copy/fill、helper call）を使う。第三者の実アプリケーションとは数えない。
- 通常のRust最適化 `0 / 2 / s` と、必要に応じBinaryen O3の違いを保存する。未対応の命令・effectは全コピー、拒否、tool errorを区別する。
- 生のポインタを使うfixtureにはhost側で有効なbuffer内の引数だけを与える。Rustソースの未定義動作を含む入力の結果で正当性を主張しない。
- 実行前のbufferから独立に値を保存し、解析結果に従ったviewと比較する。解析器の要約だけをoracleにしない。
- まず現行解析器を固定してcoverageを測る。その結果を見てから拡張する場合、別version・同じfixture・追加の負例で比較する。成功した例だけを選んだcoverage値を報告しない。
- 範囲解析が得られても、一般のC/Rust、WASI、Canonical ABIの対応を意味しない。性能改善の証明とは分ける。
- 今回のRust targetライブラリは既存compilerのmanifestのURL/hashからworkspace内に取得し、既存toolchain設定を変更しない。
