# 発明研究の保存結果

2026-10-18。新しい有効な保護方式の確立には至らなかった。主結果は[observation-suite-v2/comparison.md](observation-suite-v2/comparison.md)、解釈は[論文草稿](../../paper-draft.md)、再現は[実装README](../../research/observation-synthesis/README.md)。

|ディレクトリ|扱い|
|---|---|
|trap-carrier-v1/v2|trap依存の残存性と方式既知の解除。既知原理なので3案には数えない|
|access-fusion-v1|初回メモリsnapshotの不備を保持。主結論に使用しない|
|access-fusion-v2|修正した意味保存とrawアクセス復元の早期ゲート|
|observation-core-v1/v2|1式の候補生成、観測profile、0/1→0/1/2演算への強化|
|observation-binary-v1|実.wasmの限定変換・副作用差分試験|
|observation-suite-v1|非同期instantiateが完了せず出力が未完成。測定成功に数えない|
|observation-suite-v2|主実験75条件。Wasm、SHA、計画、観測値、復元、性能、生値、独立検証を保存|
|observation-reproduction-v1|一括スクリプトの新規出力先での再実行。主実験と独立に分母へ加算しない|

suite-v2の`transform-resources/`は冒頭が別エンジン検査と並行した診断測定。主表は後で単独実行した`transform-resources-sequential/`を使う。v2の`inventory.json`は集計時のファイル集合のハッシュで、後から付けた説明文を含む全リポジトリの署名ではない。

75条件のうち保護対象があるのは60条件、15条件は対象なし。54,600入力条件は方式間で同じ入力を使い、独立入力の総数ではない。返り値・probe・checkedの3呼出しが計163,800。過去の別ディレクトリの件数をこの数に合算しない。

書き直した実装で旧結果を上書きせず、source snapshotと失敗を残した。生データやsnapshot中の旧状態表現より、論文草稿・最終監査の解釈を優先する。
