# 観測に影響しないsegment状態の除外

2026-10-24。[事前計画](guard-projection-plan.md)、[実装](guard-project.py)。既知の依存関係による状態削減をKへ適用した。独立した発明や新しい一般解析原理としては数えない。

## 変換の範囲

受理した元APIのinitが参照するsegmentだけを解析modelへ残し、それ以外へのdropを削除する。**元のWasm binaryは変更しない。** 現profileにはsegmentを読む他の命令がないため、非参照segmentの寿命はAPI結果・memory/table・関連segment状態へ影響しない。完全な内部segment一致を要求する契約にはこの削減を適用しない。

保持する参照は構文上の全initから決める保守的な集合であり、最小集合とは限らない。例えば絶対にtrapしない0長initでも参照を保持する。動的API、外部状態、無制限の特徴追加を可能にするものではない。

## 実験

[既存134module・964store](../../results/state-witness/guard-project-v1/results.json)で条件・分類・最短長が変わらず、反例列そのものの変更も0だった。公式67対の分類も不変だった。これは以前の実行結果との回帰照合であり、全964storeをこの修正後に再びengineで実行した件数ではない。

新しく、条件付きmasked-initへ0/2/4/6/8/10/11個の無関係なdrop APIを加えた。いずれも条件は`memory[0]=65`のままで、修正前の状態数2/8/32/128/512/上限超過/上限超過が、全て2状態になった。8個の対照では約29.549msから0.347msとなった一方、0個では0.029msから0.092msへ増えた。これは単一process、2 warmup/7反復、model読取りを除く中央値である。射影後は履歴構築も含み、人工対照を一般Wasmの速度へ外挿しない。

異なる初期寿命とdrop順序を与えた28条件・56初期storeについて、Node/Wasmtimeそれぞれ4,008 API呼出しを実行した。肯定例の一致と否定例のstore差が両engineで予測どおりだった。このstore差は追加observerで読むprivate memoryも含む。公開APIだけの不一致件数とは扱わない。

## 別の式による射影の検査

[検査器](guard-project-check.py)はsegment寿命を記号的Booleanとし、arrayのStore/Selectと条件式で元/射影後のAPIを実行する。任意の許された初期寿命と共通storeで、結果・全store・保持したsegment状態が同じかを照合した。[141module・307検証義務](../../results/state-witness/guard-project-check-v1/results.json)は全てUNSAT、solver unknownは0だった。

parserと受理profileは共有する。削除されたsegment状態の完全一致は検証義務に含めていない。公式Wasm意味論からの機械化証明ではなく、共有model内で、別の効果記述によって射影前後が対応することの検査である。

```powershell
python research/state-witness/guard-project-evaluate.py results/state-witness/guard-witness-v1 results/state-witness/guard-table-corpus-v1 results/state-witness/spec-v4 results/state-witness/local-guard-project
python research/state-witness/guard-project-check.py results/state-witness/guard-witness-v1 results/state-witness/local-guard-project results/state-witness/local-guard-project-check
```
