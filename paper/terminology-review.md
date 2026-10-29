> この文書は2026年10月7日の旧原稿に対する履歴である。題目、実測の有無、PDF・ページ数の記録は現在の原稿の状態を示さない。現状は `README.md` と `results/runtime-mining/cross-dataset/goal-requirements-audit.txt` を参照する。

# 用語の見直し

2026-10-07。main.texの本文・表と、図1の日本語ラベルをそろえた。タイトルから「公開」を削除し、「静的コード変化の分析」を「コード変化の静的解析」に変更した。数値、数式、引用キー、参照先、著者・所属・指導教員は保持した。

| 元の表現 | 修正後 | 確認した資料・判断 |
| --- | --- | --- |
| 別名解析 | エイリアス解析 | [大阪大学のプログラム解析研究紹介](https://sel.ist.osaka-u.ac.jp/research/slicing/index.html.ja)で使われる名称。異なる参照が同じメモリ領域を指すかを調べるという本文の説明を保持。 |
| 汚染解析 | テイント解析 | [名古屋工業大学の教員紹介](https://www.nitech.ac.jp/faculty/saito-shoichi.html)で使われる名称。データの流れを追う解析という説明を追加。 |
| 算術式符号化 | 算術式の複雑化 | [Tigress EncodeArithmetic公式説明](https://tigress.cs.arizona.edu/transformPage/docs/encodeArithmetic/index.html)の「整数の演算をより複雑な式に置き換える」という内容を日本語で説明したもの。定着した学術用語と断定せず、意味が伝わる説明として採用。設定名encodearithmeticは保持。 |
| リテラル符号化 | リテラルの難読化 | [Tigress EncodeLiterals公式説明](https://tigress.wtf/encodeLiterals.html)で数値・文字列を含む対象を確認。リテラルの説明を本文に追加。 |
| 仮想化 | 初出でコードの仮想化と説明 | [Tigress Virtualize公式説明](https://tigress.wtf/virtualize.html)では関数を専用の命令列を持つインタプリタへ変換する。[日本ソフトウェア科学会FOSE予稿集](https://sdl.ist.osaka-u.ac.jp/~shinsuke/tmp/fose-2022-proceedings.pdf)でも「コードの仮想化」が使われる。本文では説明後に「仮想化」と略記。 |
| 平坦化 | 初出で制御フロー平坦化と説明 | [情報処理学会第87回全国大会抄録](https://www.ipsj.or.jp/event/taikai/87/WEB/data/pdf/5ZD-04.html)で使われる名称。以降は平坦化と略記。 |
| 命令置換 | 保持 | [情報処理学会の論文](https://ipsj.ixsq.nii.ac.jp/records/220620)で使われる名称。LLVMの設定subobfとTigressのencodearithmeticは混同しない。 |
| 配布シード | 変換元として配布されたファイル | ファイルの役割をそのまま説明。 |
| 対応比較、反復系列、全数確認 | 比較、繰り返し変換したファイル、全ファイルでの確認 | 不要な名詞の連結を避けて説明。比較対象を対応付ける手順や基準版との自己比較の記述は保持。 |

「符号化」自体を誤訳とは判断していない。ここでは難読化ツールの設定名を読むために追加の知識が必要になる箇所を、処理内容が分かる説明に置き換えた。

定量結果は配布元の設定名に基づく比較であり、全ファイルについて難読化の仕組みを確認したという主張には変更していない。未評価の採掘性能、実行時負荷、検出回避能力についても元の文書に記載された制約を保持した。

確認結果として、yomiyasuの静的検査と差分検査を実行した。残った否定表現は、研究対象や確認範囲を限定するために必要なので保持した。pLaTeX・pBibTeX・dvipdfmxで9ページのPDFを生成し、全ページと図1を目視確認した。数値・数式・引用・参照を機械的に比較し、一致を確認した。
