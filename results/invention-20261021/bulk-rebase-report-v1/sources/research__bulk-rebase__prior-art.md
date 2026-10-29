# 近い先行技術と差分の範囲

検索・部分読解：2026-10-21。次は技術比較であり、法的な権利範囲・存続・侵害・特許性の判断ではない。

| 資料 | 読んだ範囲 | 関連する構成 |
|---|---|---|
| *Data Randomization*, MSR-TR-2008-120、2008年9月。技術報告。[機関ページ](https://www.microsoft.com/en-us/research/publication/data-randomization/)・[PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2008/09/tr-2008-120.pdf) | PDF表題・要旨、§4.3、§5、§6.1の一部。PDF著者はCristian Cadar、Periklis Akritidis、Manuel Costa、Jean-Philippe Martin、Miguel Castro。機関メタデータは後3名のみのため相違を記録 | maskによる読書きの変換、byteアドレスに応じたmask位置選択、library wrapperと初期化が先行する。著者報告の平均時間増11%は本試作との比較値ではない。攻撃者にmaskが未知という脅威モデルも異なる |
| Augustin J. Farrugia、Mathieu Ciet、Benoit Chevallier-Mames、*Obfuscating transformations on data array content and addresses*、[US8667301B2](https://patents.google.com/patent/US8667301B2/en)、2014-03-04公開 | 書誌、説明の位置依存mask、請求項1–18。先行公開US20110246787A1の2011-10-06は同ページの書誌で確認。関連[US20140189366A1](https://patents.google.com/patent/US20140189366A1/en)は検索の長文抽出のみ、直接open失敗・請求項未読 | アドレスまたは添字の剰余からmaskを作り可逆結合する構成は既知。B2請求項1にはprimary addressのpage番号からsecurity parameterを作る要件もあり、全位置符号化一般と同一視しない |
| Henri Han Van Riel、Michael Tsirkin、*Re-duplication of de-duplicated encrypted memory*、[US11354420B2](https://patents.google.com/patent/US11354420B2/en)、2022-06-07公開 | 書誌、指定description、請求項1–20。A1公開2019-01-24は同ページの書誌確認 | hypervisorの重複排除済みpageを位置非依存の暗号入力へ変え、copy後に位置依存の入力へ変える。請求項10はin-place処理。秘密の暗号入力・page管理を使い、本案の公開mask、重複するbyte区間、Wasm trap保存とは異なる |
| WebAssembly CG, [memory.copy実行規則](https://webassembly.github.io/spec/core/exec/instructions.html#exec-memory-copy)、live仕様 | 範囲検査、零長、重複方向の規則 | 書込み前の範囲検査とmemmove相当の動作を利用する根拠。査読論文や独自アルゴリズムではない |

主な検索語は `data randomization byte mask wrapper`、`obfuscating transformations data array content addresses`、`encrypted memory copy location dependent re-duplication`。分類・family・引用関係を網羅した特許調査ではない。読めていない公報の請求項を推測しない。

広い位置依存符号化、復号を省く符号化間変換、コピー前後の表現修復は、上の既知構成と重なる。今回の狭い差分候補は、Wasmのcopyを先に行い、移動先だけを固定方向に補正することで、重複処理・失敗時の書込み禁止を標準命令に委ねる生成規則である。同一規則が未発見であることを独立した新規性の証明にしない。

実測では、直接SIMD対照よりコードは小さくなったが時間は改善しなかった。位置表現に対する解析も同じ31問い合わせで成立した。一般のmemmoveとXOR補正から導ける具体化という反論を覆す根拠は得ておらず、今回は主発明として採用しない。
