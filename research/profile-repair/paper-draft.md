# WebAssemblyの共通実行profileを考慮した部分決定化の検証

## Abstract

WebAssemblyの一部の緩和SIMD演算は、同じ実行環境に共通するparameterによって動作が決まる。本稿は部分厳密化が相関を壊す反例と、観測を決定profileへ揃える限定実装を報告する。25設計例では変更14/99対独立近似92/99、80生成例では197/320対220/320だった。後者の差は意図的相関系列に限られた。第三者datasetの非空219binaryには対象命令がなく、XNNPACK由来の縮小例では既存設計が既に正しかった。profile別テーブル補償も実装したが、通常profileの表と速度は既存方式と同等だった。一般合成を超える新規性は未確立である。

## Introduction

セキュリティ判断の再現性を求めるhostにとって、CPUが変わると判断が変わることは望ましくない。既存runtimeは全緩和演算を決定化できる。本稿は変更範囲を減らす際の正当性を扱う。数値全般、外部時刻、thread schedulerを含む完全決定実行を提供するものではない。

## Related Work

Wasm標準の共通parameter、WasmtimeのDET設定、SKETCHの有限program合成、property-driven fence insertionが近い。制約によるprogram解析・PBE性能合成の特許とも一般構成が重なる。[書誌と読了範囲](novelty-analysis.md)を参照。CEGIS自体を新しく発明したとはしない。

追加の最も近い実装はXNNPACKのprofile probeと差分表lookupである。表現補償への見直しでは、astc-encoderのarchitecture別前処理、Swizzle Inventorの合成、IntelのSIMD lookup特許も直接的な反証となった。

## Motivation

同じdataを範囲外index16と32で読む二つのrelaxed swizzleは、共通Rにより共に0又は共にdataを返す。XORは0である。片方のみstrictへ変更すると、R=1でdataが残る。変更集合を増やす操作に対し観測の安定性は単調ではない。

## Threat Model

合法なWasm実行環境の違いと任意のi32入力を対象にする。host/engineの侵害や仕様違反を想定せず、ポリシー自体の妥当性も判定しない。保護する観測は純粋runの戻り値である。認証サービスへの実攻撃を評価したものではない。

## Proposed Method

siteの変更変数hと共通profile RでF(h,x,R)を表す。全strict基準C(x)への一致を全入力で検査する。反例x*,R*からF(h,x*,R*)=C(x*)を追加し、正の節に制限せず相関を残す。必要条件を蓄積して費用最小化し、全入力queryがUNSATになった候補を採用する。[疑似コードと条件付き論証](algorithm.md)を示した。

## Implementation

Python/WABT/Z3で実binaryを読んで書く。2 i32→1 i32、直線i32式、splatからswizzleを経てlane0を得る形、最大16siteに制限する。独立したbyte-lane evaluatorを用意し、O3によるv128 local/local.teeにも対応した。unknownと未対応を成功へ変換しない。

## Evaluation

25例・836入力でNode313,500照合、Wasmtime native/DET合計627,000照合に不一致0。別モデルのraw/O3計200式はUNSAT。小例の全184変更集合でも費用最小値が一致した。変更数は共通profile14、独立site92、全site99。片方のstrict化が元の0を255に変える反例も実行した。

最初のJS境界測定は同binary間差のため参考値とし、Wasm内loopと同process順序shuffleへ修正した。7fresh process、15標本×200000callで全strictに対する時間比は約0.893–1.022。手簡約は多くで速い。99から14という変更数の差を速度差と取り違えない。[全ログと表](results.md)に環境・反復・制約を記録した。

## Discussion

相関を保ったモデルが過剰な変更を減らせる一方、同じモデルを使って関数全体を簡約すれば、より大きな改善が可能な例が多い。限定的なsite選択に強い実用優位があるかは未確認である。非単調性への対応も一般の有限program合成の枠内に入る。

追加80例は1,003,200値照合、O3後334,400照合、別モデル640UNSATを通ったが、改善は4系列中1系列だった。NoWaSetでは対象命令がなく効果を測れなかった。XNNPACK縮小転記では変更不要という負の結果を得た。検査回数の増加を実用例数や新規性の増加と混同しない。

見直し2は各profileのlookupを行列Aで表し、A E=Iとなる事前表現を生成する。[実装・結果](compensation.md)はNode61,498,752byte、Wasmtime22,111,488byteの照合、別モデル30UNSATを含む。大batchは全strictより約24–25%短時間だったが既存型dispatchも同じ速さで、速度改善を新発明の効果に帰属できない。両profileでWasm-level address列を入力indexから独立させたが、nativeのconstant-time証明ではない。

## Limitations

初期の多くは定数へ簡約可能で、追加生成例も実アプリの標本ではない。1種類の緩和命令、同CPU、有限モデル、共有toolchainに依存する。XNNPACKは全C buildではなく縮小転記であり、表現補償も固定lookup生成器である。AArch64実機、浮動小数NaN、複数family、一般loop/副作用、実費用での最適性、特許family全調査は未実施。

## Conclusion

部分厳密化の非単調な反例と、それを避ける共通profileを使った選択手順を、実装と実測として保存した。標準CEGISに対する新原理や特許性は確認できず、成果は検証可能な限定研究候補として位置付ける。
