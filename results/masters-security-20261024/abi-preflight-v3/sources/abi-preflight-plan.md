# Aの境界補助案：展開前の費用検査

2026-10-24、実行前の仮説。A2の生成器が受け取る値は既にhostへlift済みであり、recipeの操作数制限はその前の割当を制限しない。これは新発見の脆弱性という主張ではない。WasmtimeのGHSA-852m-cvvp-9p4w、GHSA-jqpg-j7w6-42pr、Cap'n Protoのtraversal limitが直接の先行対策である。

補助案は、固定した非再帰のlist型のCanonical ABI descriptorを先に読み、同じ(type, pointer, length)の計算を一呼出し内でmemoizeしつつ、出現回数を費用に加える。省略するのは再走査であって、共有部分の費用ではない。費用はleaf byte数＋非leaf listの要素数＋全list数。実RSSやWasmtime fuelと同じ単位ではない。

- この試験はAの適用境界を調べる追加模型で、新しい第4の主候補には数えない。
- 実Componentのlist<list<list<u8>>>を、Jco 1.27.0で展開する。自己作成した有界fixtureのみを使う。
- 比較はlift後の検査、非memoの展開前検査、memo付き展開前検査。非memo方式も同じ予算を守る正しい対照である。
- 入力は共有descriptorと分離descriptor。最大の論理payloadを1 MiB以下に制限する。実用サービスや他人の処理を対象にしない。
- 正当な予算内入力の戻り値、予算超過の拒否、host本体の呼出し回数を比較する。内部trampolineへの固定位置挿入は、汎用component変換器ではない。
- メモリは非共有で、事前検査とliftの間にguest実行・callback・awaitを挟まない。memoは呼出し間で持ち越さない。違反時の反例も単体で記録する。
- 一般のmemoizationや事前サイズ検査を新しいアルゴリズム原理とは呼ばない。memoなしの正しい上限方式を超える効果が狭ければ、主請求項へ追加しない。
