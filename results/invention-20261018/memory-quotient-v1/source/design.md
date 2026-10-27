# アドレス領域を考慮したメモリ射影：探索仮説

2026-10-18、実験前の固定。仮説は、読み取り専用の私有メモリを各consumerが必要とする射影値だけへ置き換えることで、元のフィールドを配布物から除ける、というもの。可逆な配置変更とは異なる。ただし部分評価・データ表現合成に近く、独立した新規性は未確認。以下の限定規則を実装して、一般方式へ進める根拠があるかを先に検査する。

## 最小の規則と意味保存

入力は定義済み1ページの非公開memory32、import/start/global/tableなし、単一の `i32 -> i32` export。bodyは同じアドレス式を使う2個の `i32.load8_u` のXORだけ。アドレスは `x << s`、sは0から15、即値offsetはともに1ページ内。active dataは定数位置にある。store/grow/共有・export/importメモリは対象外。

`M` を初期メモリ、`S=2^s`、offsetをa,bとすると、到達可能なbaseはSの倍数である。`L=65536-1-max(a,b)`。正常領域の各baseについて `T[base/S]=M[base+a] XOR M[base+b]` を事前計算し、元memoryをTへ置換する。bodyはbaseを一度計算し、base<=LならTをload、そうでなければ意図した範囲外loadで同じmemory trapを発生させる。

アドレス式自体のi32 wrapと、memarg offsetの非wrap加算を区別する。元の2loadには副作用がないため、どちらでtrapしたかをホストから区別しない契約でtrap種別を保存できる。時間・stack trace・資源不足は対象外。メモリを外部へ公開する場合には適用しない。

## 全体の曖昧さを測る必要

1個の `u XOR v` は非単射でも、重なる窓をすべて保存すると、未知メモリに対する連立方程式は一意解を持ち得る。既知の零領域をanchorとするbyte間のXOR制約グラフを作り、anchorに接続しない成分数cを数える。前提のメモリ族の中で自由度は8c bit。候補選択では局所式の非単射性だけを指標にしない。

比較するのは、offset=(0,1)でs=0（全byte開始位置）とs=1（2byteごとの開始位置）。未知の先頭N byteと、それ以外は零という公開schemaを使う。N=32,128,512。これは小さい設計検査であり、実製品の秘密情報保護を代表するベンチマークとはしない。

## 攻撃と成功条件

解析者は方式、schema NとS、offset=(0,1)を知り、公開関数を呼べる。未知byte値と生成seedは与えない。必要なindexで得た返り値から制約グラフを解き、(1)元データが一意か、(2)同じ挙動の代表データを復元できるか、を別々に判定する。攻撃関数へ渡すのは問い合わせ結果と公開schemaのみ。採点器は後で正解と比較する。

正常・境界・wrap・trapを元/射影/代表再構成の実Wasmで比較する。raw/O2/O3を含める。変換時間、サイズ、1ページの論理memory、fresh Node processのpeak RSS、warmup後の反復時間を記録する。通常最適化での残存や、元データが一意に分からないことだけを保護成功にしない。

採用条件は、表現の消去に加えて、同じ意味を持つ簡潔なフィールドアクセス式の再構成費用が増すこと。代表データを線形時間で得て元と同じ2load+XORへ戻せるなら、アルゴリズム保護としては棄却する。次数を上げる等の修正へ自動的に進めない。

## 先行性の反証先

- Hawkins, Aiken, Fisher, Rinard, Sagiv, *Data Representation Synthesis*, PLDI 2011, pp.38–49, DOI10.1145/1993498.1993504。査読論文。[著者PDF](https://people.csail.mit.edu/rinard/paper/pldi11.synthesis.pdf)。書誌・要旨を確認。関係と関数従属性から具象表現を合成する一般原理が先行する。評価の独立再現は未実施。
- Giacobazzi, Jones, Mastroeni, *Obfuscation by Partial Evaluation of Distorted Interpreters*, PEPM 2012, DOI10.1145/2103746.2103761。査読論文。[著者PDF](https://profs.sci.univr.it/~giaco/download/pepm12-giacobazzi.pdf)。過去の本文照合は `../symmetric-state/design.md`。今回の直接取得は失敗、検索の要旨だけで新しい細部を推測しない。
- [Wasmのmemory命令規則](https://webassembly.github.io/spec/core/exec/instructions.html#memory-instructions)を確認。alignment指定に反する非整列アクセスも許容される。従ってCの型付きレコードだけを仮定して到達可能なbyte位置を削れない。今回のload8では全byte窓と明示的strideの違いを検査し、多byte load一般への実装はしていない。

射影・部分評価・XOR連立方程式・ランク計算を新発明とはしない。一般のconsumer射影と到達アドレス領域の共同選択は未実装で、具体的な選択則が既存方式にないとの確認も未完了。
