# 有限精度の観測閉包：生成規則と解除条件

2026-10-23。動作する限定試作であり、有効な新難読化・特許性は未確立。

## 対象と生成

R=Z/(2^32)、private状態x、更新x'=F(x)+u、観測h(x)=x²。reset(s)、peek()、step(u)を持つ、単一状態・次数2–4のcanonicalな実Wasmを受理する。式はadd/sub/mul、整数wrapだけ。import、memory、table、浮動小数点、除算、trap、非同期・並行・再入を受理しない。元のdebug/custom sectionの保存も対象外。変換はprivate mutable globalsを使い、旧stateを参照して全localを計算した後にglobalへ書く。

z_j=2^e_j x^jを生成する。未採用のjはe_j=32とみなす。初期e_2=0。full対照だけe_1=0も強制する。

```
repeat
  for each active j:
    expand (F(X)+U)^j modulo 2^32
    for each nonconstant-in-X term c X^k U^l:
      requirement = min(32, e[j] + v2(c))
      e[k] = min(e[k], requirement)
until e is unchanged

for each active j:
  expand 2^e[j] (F(X)+U)^j
  replace c X^k U^l by (c / 2^e[k]) z[k] U^l
  keep terms k=0 as public input polynomials
emit simultaneous updates, reset coordinates, and output z[2]
```

係数はまずmod2^32の非負代表にする。割算は割切れを検査した整数除算であり、偶数の逆元は取らない。係数0の項は削除する。次数64、各座標の精度変更32回を上限とし、閉じなければ未対応として拒否する。一般の多項式で閉包が小さくなる保証はない。

各更新は定義通り `z'_j=2^e_j (F(x)+u)^j`。resetでも同じ不変式を構成するため、呼出し列に関する帰納法で出力を保存する。worklistが求めるのは**形式係数の割切れに基づく単項式族内**の必要精度。零多項式による関数同値や座標間の非線形関係を使っていないので、最小の観測状態・最小メモリとは主張しない。試作の検査はcompiler全体の形式証明ではない。

実例quadraticの座標は `{1:1, 2:0, 3:9, 4:16, 5:25}`。xそのものは保存しないが、2xからx mod2^31を得られる。全3例ではxとx+2^31の観測状態が同じで、z_1=2xによりそれ以外の合同類は区別できる。消えた情報はこの意味で1bitであり、5–6wordの物理状態が削減されたわけではない。

## 方式既知の回復

攻撃者は配布Wasmの任意実行と新しいinstanceの作成を行える。元F、e、変換manifest、元のstate値は与えない。公開生成profile（次数≤4、加算入力、二乗出力）は既知。query.cjsはWasm exportだけを呼び、内部globalや命令・係数を読まない。

reset(s)後のstep(0),step(1)を別々に測ると、t=F(s)について

`(t+1)² - t² - 1 = 2t (mod 2^32)`。

差の非負代表を2で割り、F(s) mod2^31を得る。s=0..4の5点、10step・10resetから得た値を、階乗の2進付値と奇数部を分けた既知のfalling-factorial補間へ渡す。これによりFと関数として同じmod2^31の多項式Gを生成する。旧係数の一意回復ではない。

回復コードは `r←G(r)+u; return r²`。x≡r mod2^31なら、整数多項式はこの合同を保存し、x²≡r² mod2^32。従って、reset直後から任意長の入力列で同じ観測となる。有限クエリだけで任意binaryの意味を保証するわけではなく、公開profileの仮定が必要。実験では元FとGの差のNewton係数が全て0 mod2^31であることを別監査し、関数等価性を証明する。

## resetを削った追試

主実験後の適応的追試では、比較する全variantからreset/peekのexportを削る。これは異なるAPI profileの試験であり、元の3export APIと同一と主張しない。既知の初期状態0で、新instanceのstep(0)と別instanceのstep(1)からa=F(0) mod2^31を得る。さらに新instanceの第一入力をs-aにすれば、更新後状態はs mod2^31になる。その次に0と1を入れてF(s)を取り出す。合計12instance・22step、reset/peekは0回。raw/O3のコアからexportだけを削ったバイナリを試験した。削除後の再O3は実施していない。

この攻撃に秘密情報・暗号鍵・総当たりは不要。API名の削除では入力による状態制御を失わせられないことが失敗原因である。新instance不可、入力が任意でない、出力が二乗でない等にはそのまま適用できないが、その制約だけで新しい保護方式が成立するとも主張しない。

## 独創性の限界

過去のtorsion-stateは線形元更新、symmetric-stateは既知の対称式を使う手選択の商。本試作は非線形元更新から有限精度の単項式集合と精度を自動生成する点が異なる。しかしKoopman/Carleman型の持上げ、observable realization、有限環の係数縮約、単調worklistを超える独立した原理は確認できていない。Wasmの定義済みwrapは意味保存に有用だが、他の固定幅整数形式でも成立する。最も大きいReject理由は、既知原理への狭い適用で、しかも公開入出力から容易に同等コードへ戻せること。
