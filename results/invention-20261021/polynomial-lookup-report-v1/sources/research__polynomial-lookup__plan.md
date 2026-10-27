# 静的リストの全体表現変換：事前の検証計画

2026-10-21。前turnは過去の採用済み候補の評価確認で、新候補開発としては
no progress。本turnは別原理の検査を進める。主目標は維持し、この小実験を
新規で有効な難読化の完成へ読み替えない。

## 候補の絞込み

1. ループをSchur補完で評価する案：方程式化・既知の残差/陰的表現との
   差が未設計。今回は実装対象にしない。
2. 直前アドレスを使う文脈依存pointer：XOR-linked list等が既知。
   任意graphでの合流処理も未解決。独創的な新候補に数えない。
3. 固定lookup全体の多項式化：局所decoderを抽出する攻撃から離れ、
   sourceのnode/nextを実行時から除く。ただし集合のroot多項式と補間は既知。
   具体的なWasm生成、全u32域の扱い、回復費用を検査する仮説として選ぶ。

## 仮説と比較

読み取り専用の固定連結リストをP(X)=prod(X-key)、値の補間式R(X)へ変える。
対象はprivateな1page memory、export lookup(i32)->i32だけの限定profile。
ptr/next/field offsetを持たない表現にすることで、全key/value回復に必要な
処理をlist走査から有限体の因数分解へ変えられるか調べる。
元配置の一意回復不能だけは成功条件にしない。等価辞書が得られれば回復成功。

体はp=2^32-5。i64積がoverflowしない範囲で剰余計算できる。
key>=pの5値は別経路で厳密に処理する。valueはv mod pとfloor(v/p)の
2多項式へ分ける。全u32値の境界を省略しない。重複keyは元リストの
first-matchを保存する。到達cycle、範囲外next、公開/可変memoryは拒否。

比較は未変換list、単純flat array、polynomial。arrayは構造削除だけの対照。
raw/O3の出力・boundary・random・hit/missを検査し、複数の元配置が同じ
多項式になることは別に報告する。NotDecは未構築であり失敗/耐性に数えない。

回復器の入力は配布binaryだけ。data segmentからP/Rを取り、方式既知の
Cantor–Zassenhaus型の線形因子分割で全rootを求め、Rで値を回復する。
元key、生成seed、manifest、公開lookup oracleを回復器へ渡さない。
source profileに専用の抽出器であり汎用decompilerと称さない。

性能はO3、Wasm内loop、hitとmissを分け、warmup、calibration、9batch、
3 fresh processの分布を保存。時間、サイズ、線形memory、process RSS、
変換時間を区別する。攻撃はreader込みと本体を別々に測る。
既知構成との差がなければ主発明には採用せず、保護費用だけを新規性へ転用しない。

## 先行資料（実装前）

- Freedman, Nissim, Pinkas, *Efficient Private Matching and Set Intersection*,
  EUROCRYPT 2004、LNCS3027 pp1–19。著者PDF §4.1、PDF p5のroot多項式構成を読んだ。
  https://www.pinkas.net/PAPERS/FNP04.pdf
  集合を多項式の根にすることは既知。論文の暗号化係数/二者通信は本案にない。
  著者実装・暗号的保証を今回の結果へ転用しない。
- NTL公式ZZ_pXFactoring文書のFindRoots/RootEDF/CanZass説明を読んだ。
  https://libntl.org/doc/ZZ_pXFactoring.cpp.html
  公開係数のroot回復は既知の計算課題であり、2^32総当たりしかないとはしない。
  今回は標準Pythonの小規模実装を用い、NTL自体の速度を評価したとはしない。
- Galbraith, Li, *Obfuscation of Evasive Algebraic Set Membership*, ePrint
  2022/1516（2024改訂、Advances in Mathematics of Communications掲載と記載）。
  https://eprint.iacr.org/2022/1516
  要旨/書誌のみ確認、PDF403で本文未読。入力秘匿の暗号学的構成との一致を
  題名だけから断定しない。未読の安全性証明を本案に帰属させない。

検索: `obfuscation polynomial lookup interpolation`、`obfuscation polynomial
dictionary`、`obfuscation set membership polynomial roots`、
`Freedman Nissim Pinkas 2004 efficient private matching polynomial roots pdf`。
検索に完全一致が見つからないことを新規性の証拠にしない。
