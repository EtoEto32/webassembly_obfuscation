# 設計、条件、攻撃

## 保護目標と方式

公開ABIの入出力を維持し、純粋な整数計算の短い等価実装への回復費用を増やせるかを調べる。攻撃者は変換規則、配布バイナリ、仕様、最適化器、実行器を利用でき、バイナリを書き換えられる。元ソース・内部seed・実験manifestは回復器へ渡さない。秘密鍵も外部秘密も存在しない。

32bit値 x の内部表現を E_m(x)=x XOR m とする。mは関数入口で一度だけ設定し、関数内では一定。relaxed版は全byteが255のtableと、`(splat(param0) AND 0x0f...) OR 0x10...` のindexで `i8x16.relaxed_swizzle` を実行し、先頭32bitを取り出す。各indexは16..31。合法な結果の組合せや同一環境内の整合性に依存しないよう、任意の32bit mで正しい変換を使う。

擬似コード：

```
validate restricted source module
m := choose_mask(mode, original parameters)
encoded_parameter[i] := parameter[i] XOR m
encoded_zero_local[i] := m
for each source assignment in order:
    encoded_destination := lower(source_expression)
return lower(source_result) XOR m

lower(x AND y) := (z AND w) XOR ((z XOR w) AND m)
lower(x OR  y) := (z OR  w) XOR ((z XOR w) AND m)
lower(x XOR y) := z XOR w XOR m
lower(L(x))   := L(z) XOR L(m) XOR m
where z=lower(x), w=lower(y), L=constant shift/rotate
```

各lower結果は新localへ格納するため、式を複製して指数的に大きくしない。sourceのparamへの再代入もencoded側へ写し、元のparamは入口mask計算にのみ使う。zero/ones/patternはm固定、dynamicは`param0 XOR rotl(param1,7)`。共通maskを使うことで原論文の独立乱数maskによるside-channel安全性は失われる。そこは保護対象に含めない。

## 意味保存の説明

各bitでm=0なら表現は恒等。m=1では値が補数になり、AND/ORはDe Morgan則で交換される。上記のcross termがこの交換を行う。XORは符号化を一回残す。定数shift/rotateはXORに関して線形なので、L(z) XOR L(m)=L(x)。したがって各localの表現関係を代入順に維持し、末尾の復号で元の値を得る。

これは変換規則についての帰納的な説明であり、Python実装・パーサ・ランタイム全体を証明支援器で検証した結果ではない。数値はi32のbitvectorとして扱い、shift量はmod32。memoryや整数除算を扱わないため、この対象範囲には元のメモリ副作用・算術trapがない。未対応機能を含むmoduleは拒否する。追加localに必要な実行資源が十分あることを前提とし、資源枯渇まで同一とは主張しない。

## 適応的回復

1. 範囲解析：pureな直線命令だけ受理し、既知0/1 bitを局所環境へ伝播する。全index byteについて既知1 bitだけで16以上と示せるなら、strict swizzleを選ぶと零になる。副作用を消さないよう、効果を持つ命令は拒否する。local.set/teeは順序通りに処理する。
2. 系列特化：生成方式とmask独立性を知る解析者は、dynamicまたはrelaxedのmask生成式を0へ置換する。消す式の内部にlocal.set/tee等がないことを確認する。両方式へ同じ探索器を使う。
3. 通常のBinaryen O3、さらにO3収束実行で不要演算を除去する。

範囲解析のstrict選択は、一般のrelaxedプログラムでは結果集合を狭める精密化であり、結果集合の同値変換ではない。生成系列では全mで元の計算が同じなので、どの選択でも等価出力になる。系列特化もこの前提を必要とする。回復器はmask独立性を任意入力に対して自動証明しない。直接maskを返す対照では結果が変わることを実際に確認した。

## 仮説の判定

仕様上の複数結果があるだけでは、この限定案の回復費用を継続的には増やせなかった。復元成功自体を失敗理由とはしない。共通の系列特化解析費用と回復後サイズがdynamic対照に近く、既知maskingに対する独立した技術差も弱いことを不採用の理由とする。一般のRelaxed SIMD難読化や非決定的難読化の不可能性を示したものではない。
