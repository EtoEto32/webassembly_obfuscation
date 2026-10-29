# Relaxed SIMD の選択を内部表現へ運ぶ仮説（2026-10-19、実験前）

状態複製とは異なる原理として、仕様で許された実装依存の値を、単一の Boolean mask として計算領域全体へ運ぶ。ただし XOR masking 自体は既知であり、暗号化、乱数生成、安全な side-channel masking を提案しない。

保護対象は限定された純粋 i32 計算の短い等価式への回復。攻撃者はバイナリ・方式・ツールを知り、コード変更もできる。元ソースは渡さない。成功は回復不能ではなく、通常の入力依存 mask より適応的回復の費用が増え、実行費用に対する増分が説明できること。単なる命令数増加・ツール未対応は成功に数えない。

E_m(x)=x XOR m。全 byte が 16..31 の index と全 255 の table に relaxed_swizzle を適用し、先頭 i32 を m にする。0/255 以外の mask でも意味保存する代数を使う。AND は (z AND w) XOR ((z XOR w) AND m)、OR は (z OR w) XOR ((z XOR w) AND m)、XOR は z XOR w XOR m。定数 shift/rotate L は L(z) XOR L(m) XOR m。入力・初期値・出力で符号化/復号する。

重要な反証：strict swizzle は合法な選択肢であり、全 index >=16 なら m=0 に精密化できる。元計算がすべての選択に対して同じなら、攻撃者はこの精密化を選べる。これは任意の relaxed SIMD プログラムの結果集合を保存する変換ではない。既知の生成規則と上記の独立性を根拠に、等価実装回復として評価する。

実験：3 kernel × plain/zero/dynamic/relaxed/ones/pattern × raw/O3、境界値と固定 seed ランダム入力。zero は変換のアブレーション、dynamic は既知の入力依存 mask 対照、ones/pattern は意味保存の対照。方式既知の純粋命令・範囲検査付き簡約を raw/O3 に実行する。誤った AND、範囲外でない index、副作用を含む入力を負の対照にする。実行時間は serial fresh process 3回、各10000 warmup、11反復×3000回。サイズ・変換/解析時間・RSS・local数も記録する。性能に対する解析費用の増分がなければ主案にしない。

対象：1個の exported run、3個の i32 引数、i32 戻り値、純粋な直線式と local.set。memory/import/call/div/float/branch は拒否。入力バイナリに検証と再出力を適用する。全入力の機械証明とは区別し、代数の帰納的説明と差分実験を保存する。
