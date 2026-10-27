# A第2設計：生成器の独立照合

2026-10-24。固定した6種類のrecipeだけの成功を、生成器一般の安全性としない。異なる型と処理を生成し、Pythonの小さい直接実行器と生成JSを比較する。

- resourceを数値IDで表す生成器単体試験。実Component試験とは別集計。
- recordの名前変換、list内のread結果、option内のスコープ、listのlist、同一実体のalias、複数のread/write順序を含む。
- Python参照実行器はrecipeを直接解釈し、read時点のbyteを保存してwriteする。生成器の中間表現・権限policy・register番号はoracleに流用しない。
- JSは生成された計画を既存createFileExecutorで実ファイルへ適用する。値はUTF-8のvalid/invalid byte、空、NUL、最大16 KiBを含む。返却文字列は検査対象外とし、read回数・write回数・最終byteを比較する。
- 空list、optionなしとあり、aliasの組合せを含む固定seedの入力。上限超過と未定義read参照は別の拒否試験。
- 期待結果は不一致0。失敗を隠して入力を除外しない。試験を通っても全recipeの健全性証明、WASI APIとの同等性、特許新規性とは主張しない。
