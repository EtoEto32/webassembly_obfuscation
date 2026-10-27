# 再開点：型回復のアクセス経路

2026-10-21。本区間はprogress。公開Retypdをworkspace内venvで動かし、Wasmの
型制約抽出・既知変換の対照・適応shape回復・実測・再現を作成した。

- 前区間のstatus再確認はno progressだったため、実解析器を用意して進めた。
- NotDec本体はLLVM14開発環境がないため未実行。今回のRetypd実験をNotDec結果と呼ばない。
- regular/forced計40 Wasm、70,440 calls（3,600 trap含む）一致。40 byte再生成一致。
- full solverの経路列挙には大幅な増加があるが、7-node shapeは残る。
- 実Wasm由来の76 solver成功、1 timeout、3未実行。abstract pilotは別集計。
- 既存shape統合を使うfield回復は40/40、0.185–1.412ms（読取別）。
- 単なるloop peelingは主発明にしない。n拡大・時間上限拡大だけで再開しない。
- 生成規則とshape回復の双方へ影響する新しい差分が必要。強い難読化、世界初、
  特許取得、元研究の完了は主張しない。有限環残差方式の限定採用は取り消さない。

コード・環境・制約・メトリクス・再現はREADME参照。起動した実験processは全て終了。
