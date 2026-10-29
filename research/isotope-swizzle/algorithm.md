# アルゴリズムと成立範囲

## 入力と変換

3 個の i32 入力から i32 を返す純粋関数 `run`。各 byte の下位 4 bit を独立に add/sub/xor する小さな式 DAG に限定する。入力は既に SIMD 命令へ下ろした実 Wasm。`parse_source` が関数・ABI・命令・mask の形を検査する。一般の Wasm、scalar i32 加算、carry を伴う 32 bit 算術への自動適用ではない。import、memory、table、global、loop、call、trap、浮動小数点、外部副作用を扱わない。

各値 v に独立な置換 P_v: {0,…,15}→{0,…,15} を割り当てる。公開 seed は生成の再現用であり、秘密鍵ではない。演算 z=f(x,y) は

`T[b][a] = P_z(f(P_x^-1(a), P_y^-1(b)))`

という 256 byte の表へ変換する。16 個の行をそれぞれ v128.const として置き、`swizzle(row,a)` を全行で評価し、b と 1,…,15 の比較による bitselect で該当行を選ぶ。b=0 は既定行。初期入力だけを符号化し、最終結果だけを復号する。中間値は nibble の置換表現を保つ。入出力の全単射を合成する原理自体は既知。

```text
compile(value):
  if already compiled: return its local
  choose a 16-element permutation P[value]
  if input: result = swizzle(P[value], splat(input) & 15)
  else:
    a,b = compile(left), compile(right)
    T = compose(input inverses, original operation, output permutation)
    result = multiplex 16 swizzle rows using b
  store result in a fresh v128 local
  return local
return extract_lane0(swizzle(inverse(P[root]), compile(root)))
```

Wasm 命令は 16 lanes を計算するが、この ABI では i32x4.splat により 4 byte の組を複製し、最後に最初の 4 lanes を取り出す。16 個の独立データを処理した性能とは報告しない。線形メモリは追加しない。表は命令の定数としてコード領域を占有する。

意味保存は、各入力が P_v(v) であるという帰納的不変条件から従う。各演算後に mod 16 の mask を維持し、swizzle の範囲外ゼロ化を発生させない。sub の負値も 4 bit への剰余で一致する。インスタンス化・JIT の資源消費まで同一にする主張ではない。有限テストは emitter 全体の形式検証を代替しない。

## 方式既知の回復

Wasm の評価順を保って local.tee/local.set を単一代入形式へ移し、再利用された local 番号を区別する。全 16 行が揃った表の部分式を抽出する。入力が 0…15 に収まることを mask、定数、swizzle、代入関係から確認する。未証明なら拒否する。b≥16 の元の既定行動作や a≥16 のゼロ化に、群の式をそのまま当てはめると誤るためである。

T(a,b) と書き、C(a)=T(a,0)、R(b)=T(0,b)、e=T(0,0) とする。Latin square なら C,R は置換であり、

`G(u,v) = T(C^-1(u), R^-1(v))`

は e を単位元とする principal isotope となる。入力演算が加算なら、出力符号化を γ、入力 0 に対応する原座標の和を c として

`G(u,v) = γ(γ^-1(u) + γ^-1(v) - c)`。

従って `θ(u)=γ^-1(u)-c` が元の群への同型である。引算は右入力の符号反転を置換へ吸収できる。XOR も同じ可換群の議論になる。この既知の代数的構成を新定理とは呼ばない。

実装では未知の γ を使わず、全 4096 三つ組の結合律と可換性を検査する。位数 16 の元を見つければ巡回群 C16 の座標を生成し、全元の平方が e なら基底を増やして (C2)^4 の座標を生成する。他の群は未対応として拒否する。座標写像を φ とすると

`T(a,b)=φ^-1(φ(C(a)) op φ(R(b)))`。

全 256 対の一致を確かめて、3 個の swizzle と add/xor へ置換し、モジュール全体を出力する。元の置換や add/sub の元の表記を同定する必要はない。残った置換は小さな表現変更であり、元ソースそのものを完全に再現したとは報告しない。攻撃は生成 seed、元式、generation manifest を入力にしない。関数呼出し oracle も不要。

群の検証に O(16³)、表抽出と SSA に式サイズ相当の仕事を要する。小さな独立表を並べる今回の設計では、回復作業は表ごとに分割できる。暗号学的困難性や人の解析時間の下限は導けない。
