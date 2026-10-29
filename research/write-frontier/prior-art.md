# 書込み被覆の先行技術照合

2026-10-18。ここでの新規性評価は技術的な比較であり、特許の権利範囲・有効性・実施自由の判断ではない。

## 実際に確認した資料

| 資料 | 著者・年・種別 | 確認範囲と関係 |
|---|---|---|
| [WebAssembly Core Specification: Memory Instructions](https://webassembly.github.io/spec/core/exec/instructions.html#memory-instructions) | WebAssembly Community Group、参照ページ表示3.0 / 2026-10-13、仕様 | store/storeNの実行規則を確認。範囲条件を満たさない場合のtrapはbyte更新より前。即値offsetとbaseの和をi32で折り返す説明ではない。 |
| [[PATCH][v5] GIMPLE store merging pass](https://gcc.gnu.org/legacy-ml/gcc-patches/2016-10/msg00572.html) | Kyrylo Tkachov、2016-10-10、GCC公開開発資料・ソース | 投稿本文、merge_overlapping、apply_stores、coalesceの該当コードを読んだ。重なりを含むstoreをプログラム順にbyte像へ適用し、広幅storeを作る一般構成は既知。査読論文とはしない。 |
| [Speculative Optimization Using Hardware-Monitored Guarded Regions for Java Virtual Machines](https://pharm.ece.wisc.edu/papers/vee10.pdf) | Lixin Su, Mikko H. Lipasti、VEE 2007、会議論文の著者版 | Abstract、§1–3の該当箇所、§5.2の条件を確認。例外を監視する領域で投機最適化し、失敗時に巻戻して保守的なコードを再実行する。上限実験で平均15.9%の性能改善と報告するが、評価時に例外・再実行は発生しない設定。全実験の再現はしていない。URLのvee10を発表年2010とは解釈しない。 |
| [US20190163475A1: System and method for store fusion](https://patents.google.com/patent/US20190163475) | John M. King、公開2019-05-30、公開特許公報 | 書誌、例外処理の本文、請求項1–20を確認。隣接する同幅store micro-operationを融合し、例外時は融合しない形で再実行する記載がある。審査経過・全図面・B2の請求項変更は未確認。 |

GCCリポジトリの直接openは取得エラーだったが、公式メーリングリストのパッチ本文を取得して確認した。検索結果だけで現行GCC全体の実装を精読したとはしない。上記コードをコピーせず、この試作の被覆・記号評価は独立して記述した。

## 差分候補と反証

| 今回の要素 | 既知要素との関係 | 今回残った差・限界 |
|---|---|---|
| store列の最終byte像を計算 | GCCのstore mergingが近い | byte像を計算するだけでは新規性にならない |
| trap後の可視memoryを保存 | 正確な例外、投機と再実行が既知 | この試作は共通baseと即値offsetに制限し、新しい最大右端で静的に分割。再実行用コードやhardware monitorを使わない |
| 重なる広幅storeで被覆 | store融合・分割・重なり処理が既知 | 動的計画法による引数境界横断の選好が差分候補。ただし区間被覆のDP自体は新しい原理ではない |
| フィールド境界を減らす | 型回復の手掛かりを減らす一般目標 | byte正規化と公開I/O回復で同値更新を得られた。最適化によって同一になる条件もある |

公報のhardware micro-operation方式と、今回のWasmソフトウェア変換が同じ請求項に該当すると判断したものではない。一方、「storeをまとめる際に例外の意味を保つ」という問題設定そのものを初出とは書けない。

今回の検索は `compiler store merging precise exceptions`、`WebAssembly store merging trap`、`obfuscation memory writes reordering`、`patent store fusion exception` 等から一次資料へ辿った限定調査である。この正確な被覆目的関数と同一の記載を確認できていないことは、先行技術が存在しない証拠ではない。

## 採否

既知のbyte像合成と例外制約に対する具体的な実装差はある。しかし同store数の対照に対する増分は一部の処理費用に限られ、公開I/O回復に必要な問い合わせ数は増えなかった。今回の対象範囲では、出願の核とする新規性・保護効果の根拠が不足している。これは特許を得られないという法的結論ではなく、この研究候補の採否である。
