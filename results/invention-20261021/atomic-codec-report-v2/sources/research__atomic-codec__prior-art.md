# 最も近い先行構成と確認範囲

2026-10-21。公開一次資料を英語で検索し本文の指定箇所を読んだ。本候補のための新しい公報請求項の調査は行っていない。未発見を新規性の証明にしない。

| 資料 | 年・種別・URL | 読んだ内容と本案との関係 |
|---|---|---|
| Stephen Drape, Obfuscation of Abstract Data-Types | 2004、Oxford博士論文。[本文](https://www.cs.ox.ac.uk/files/2892/thesis.pdf) | §3.2–3.2.1の抽象化写像・可換条件・全単射時の共役構成を確認。表現から演算を導く原理は既存。今回この論文の性能実験を再現していない。 |
| Tigress, Encode Data | 開発者公式実装資料、現在ページの公開日未確認。[公式](https://tigress.wtf/encodeData.html) | 冒頭の奇数係数affine、Usageのautomatic/poly1を実読。automaticは実際に使う演算を符号化領域で処理できるcodecを選ぶと記載し、4.1.1からと明記する。**演算集合からcodecを選ぶという生成規則も既存**。このページにatomicの説明がないことを、全Tigress実装の未対応や本案の初出の証明にしない。実行比較はしていない。 |
| LLVM Project, AtomicExpandPass.cpp | 公式ソース、mainの参照時点版、学術論文ではない。[ソース](https://raw.githubusercontent.com/llvm/llvm-project/main/llvm/lib/CodeGen/AtomicExpandPass.cpp) | `insertRMWCmpXchgLoop` のコメント・処理、および `expandAtomicRMWToCmpXchg` を確認。load、候補更新、CAS、失敗時再試行という一般loweringが既存。今回LLVMを用いて生成したという意味ではない。 |
| WebAssembly Community Group, Threads proposal overview | 仕様提案資料。[公式](https://github.com/WebAssembly/threads/blob/main/proposals/threads/Overview.md) | Atomic Memory Accesses、RMW、Compare Exchange、Alignment、Initializing Memory Only Onceを確認。自然整列、旧値返却、SC、共有初期化の契約を実装へ反映した。提案の古いoverviewと最新版の全仕様の精査を混同しない。 |

差分として具体化したのは「Wasmの対象命令集合について単一native RMWへ閉じる条件を検査し、即値アドレス・trap・共有状態を保持して出力する」限定パスと制限の導出である。先行構成との一般枠組みの一致だけで個々の実装差を否定しないが、今回の実体は既知affine/NOTとCAS lowererであり、独立した主発明として強い差ではない。全bit反転とDe Morgan則自体を新発明とはしない。

最も大きいReject理由：高速経路を選ぶと符号化が既知の簡単な表現に制限され、演算適合による選択も既に文書化されている。さらに今回の保護対象は二つの選択書込みで戻る。CASを省く限定的性能改善だけで、新しい難読化の機構としての独立性・有用性を主張できない。

Rust AtomicU32のdoc URLは取得失敗、GitHub表示の検索では該当fetch_updateを確認できなかったため根拠に使わない。cppreferenceは補助的に開いたが、技術結論は上記一次資料と自分の導出・実験に限定した。検索に出た他の「atomic」を含む論文や公報の多くは並行RMWとは別の意味であり、読了先行研究として加算しない。
