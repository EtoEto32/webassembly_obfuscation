# 丸めを保存する符号表現と零符号の遅延修復

2026-10-21。暗号鍵を仮定しない、限定したWasmプログラム変換の候補。[実装](prototype.py)、[固定計画](plan.md)、[先行技術](prior-art.md)。既知の符号代数を新しい数学とはしない。

## 対象と観測契約

入力は検証可能な実`.wasm`。閉じた2関数moduleで、1関数は1–16個のf32引数、f32結果、512node以内の非循環add/sub/mul計算。localへの代入・共有を認める。もう1関数はi32引数のbit列をf32へreinterpretし、結果NaNを0x7fc00000へ正規化してi32で返す、明示的な公開`run`である。このwrapperが元からあることをparserが検査する。

f64、div、min/max、比較を利用する計算、途中のbit観測、import、メモリ、global、ループ、複数exportは未対応。元のNaN payloadを観測できるAPIへ適用して後からcanonical化する変換ではない。入力のNaN、∞、subnormal、±0を排除しない。Wasmの固定した丸め、符号付き零、bit reinterpretを用いるが、同じ意味を持つ他の形式への応用も可能である。

## 数値の計算

元nodeの値をx_i、変換後をv_i、生成時の公開可能な符号phaseをp_i∈{0,1}とする。N_p(x)はp=1の時だけf32.negする。各nodeは元と同じ精度で一度丸める。

```text
input j:  v_i = N_(p_i)(argument_j)
add a,b:  v_i = f32.add(N_(p_a xor p_i)(v_a),
                         N_(p_b xor p_i)(v_b))
sub a,b:  v_i = f32.add(N_(p_a xor p_i)(v_a),
                         N_(p_b xor p_i xor 1)(v_b))
mul a,b:  v_i = f32.mul(N_(p_a xor p_b xor p_i)(v_a), v_b)
```

保持する関係は、NaN同士、零同士、または非零について`v_i=N_(p_i)(x_i)`である。零の符号だけは途中で一致を要求しない。NaN以外では絶対値と零判定が一致する。加減乗算の丸めを別々に残し、再結合やFMA化をしない。

## 論理符号の計算

最終v_rootが非零ならphaseを外して返す。NaNは外側の既存APIで正規化する。零なら、全nodeの元の論理符号σ_iを依存順に計算する。Z(v)はf32での零判定、S(v)はbit31。

```text
input j: σ_i = S(argument_j)
nonzero node: σ_i = S(v_i) xor p_i
zero mul a,b: σ_i = σ_a xor σ_b
zero add a,b: σ_i = Z(v_a) and Z(v_b) and σ_a and σ_b
zero sub a,b: σ_i = Z(v_a) and Z(v_b) and σ_a and (σ_b xor 1)

if Z(v_root): return reinterpret_f32(σ_root << 31)
else:         return N_(p_root)(v_root)
```

`eager`対照はadd/subごとに零符号を修復する。`deferred`は上の補助計算を出力が零の時だけ実行する。`uncorrected`は零修復を除いた負例。phase数の増加を別発明とは数えない。

## 意味保存の論拠と限界

1. RNEの対称性から非零の加減乗算は同時符号反転と整合する。零符号が違っても、add/sub/mulだけでは零か否か・非零の大きさを変えない。∞との乗算で零がNaNになる場合も両方でNaNになる。
2. 有限binary32値は2^-149の整数倍であり、加減算の非零の厳密結果がその半分未満へなることはない。従って加減算の零結果は、同符号の零を合わせる場合を除き相殺による+0で、上の式で元の符号が決まる。
3. 乗算がunderflowして零へ丸められる場合も、符号は元の両入力の符号のxorである。これは数値graphの誤った零符号からでなくσから求める。
4. NaNは対象の三演算を通じて伝播する。rootが零ならrootに寄与する祖先にNaNはなく、意味の定まらないNaN符号は零修復に影響しない。
5. 上記をDAG順に帰納すると、rootの修復と既存のNaN正規化により公開i32結果が一致する。

これは定義した変換についての数学的議論であり、parser・Wasm生成器・JITを含めた機械検証ではない。途中に除算やbit観測を足すと、零符号の一時的な相違が非零の値や分岐へ影響し得るため、対象を自動拡張しない。独立整数oracleによる有限検査は別の証拠である。

## 解析者と解除

解析者は全Wasm、方式の説明、実行環境、任意入力を持つ。生成前DAG、phase表、seedを専用回復器へ渡さない。保護目標は、元の数値計算に対応する簡潔な計算を取り出す負担を増やすこと。

回復器は浮動式を「符号を外したnode、符号phase」に分けて伝播し、非零側からadd/sub/mul graphを抽出する。この候補は零符号を保存しない場合があり、全域同値な最適化器とは呼ばない。適応版は候補の結果が零の時に元の公開関数を呼び、それ以外を候補で返す。元の全コードを残す部分簡約であり、完全解除ではない。

回復器は真正な生成物という前提を置き、零補正や分岐と結果の関係を独立に証明しない。任意Wasmへ適用して安全とする認証器ではない。通常O3で分岐や零補正が残ることも、方式既知のこの部分簡約への耐性を意味しない。
