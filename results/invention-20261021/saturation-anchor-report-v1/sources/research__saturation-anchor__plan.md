# 飽和カウンタへの適用計画

2026-10-21、測定前に固定。zero-anchorの適用が単位bitに狭かった問題を検査する。別の新発明として数えず、改良候補の適用限界を調べる。

仮説：E(15)=0を満たす4bit置換では、x,y∈0..15に対して strict_swizzle(E,x+y)=E(min(x+y,15))。合流する範囲外値は複数でも、その所望の論理結果は15一つなので成立する。relaxedへの変更は一般には不正。通常minを除いた利益がstrict命令の費用で相殺される可能性がある。

実装対象：二つのprivateなpacked 4bitカウンタ列。各256/4096個。初期化、加算merge、半減decay、get/set、checksumを備える限定Wasm moduleを変換する。TinyLFU等に存在する飽和・半減という処理を参考に自作するが、キャッシュ製品全体の実装・比較とはしない。2カウンタ/byte、memory1page、import/shared memory/growなし。

比較：plain、補数符号化、自由置換＋min、同じ零制約＋min、零制約＋strict表引き、零制約＋既存の飽和加算列、自由置換＋16行融合表。置換seed7/29。raw/O3双方の正しさとサイズを確認。保護強度が異なる補数版を同等の保護と扱わない。

正当性：独立scalar oracleとの全256値対、乱数の操作列、初期化前の状態、境界index・bankによるtrapと全memory副作用。実メモリを観測する診断用cloneはmemoryのexportだけを追加。実験上の定数表を用いて復号する検査とは別に、方式既知の解析者が16個の選択入力で符号化を回復できるか測る。

性能：全配列merge、merge+decayをWasm内部loopで反復。warmup100回、9batch×500回、条件ごと5 fresh process。順序seed211001。初期化と最後のchecksumは計時外。mergeのみは飽和後の定常状態が大半、merge+decayは状態更新が続く点を明記。CPU一組で中央値・process範囲、binary bytes、RSS、変換時間、memory使用量を保存。

先行性の注意：Hamburg, Accelerating AES with Vector Permute Instructions (CHES2009) §2.1/2.4/2.5に命令の零出力と特別値表現・表生成の対応が既にある。今回の式を新しい数学原理とはしない。費用改善が残るか、一般的な符号化生成との差が具体化できるかを別に判断する。
