# コピーと可換な混合表現の生成

## 対象と保護目標

private memory32の先頭N byte（2≤N≤32）、固定したcopy操作群、byte read/writeだけを持つ限定profileを入力とする。source binaryをWABTで検証・読取りし、再生成したcanonical moduleとのAST一致で対象範囲を確認する。sourceのcopyは全て領域内にあり、引数は定数である。read/writeの引数は任意i32で、領域外の通常memoryと範囲外trapも保持する。

目的は、元フィールドを複数の物理byteへ混ぜながら、元のcopyを保持してコピーごとの変換費用を省くこと。直接の比較対象は同じ行列Bの全復号・再符号化版。暗号鍵・秘密の生成ログ・未知の方式を安全性の前提にしない。攻撃者は全binary、実行、改変、memory export追加、公開read/write/copyを利用できる。時間、コード位置、stack traceは意味保存の観測から除く。

## 構成

byteの各bit面に対してGF(2)上の同じN×N行列を使う。コピー(d,s,l)を、行iが「コピー後のbyte iの元位置」を選ぶ行列Cで表す。重なるcopyでもコピー前の値を選ぶ写像にする。

```
extract data and all fixed copies from validated source
for every source copy C:
    add every scalar equation in B*C XOR C*B = 0
solve the homogeneous GF(2) system for a complete linear basis
sample 256 combinations with a fixed seed
keep invertible combinations; choose the one with most nonzero coefficients
if none was found: keep identity B
compute B_inverse
replace initial x by y = B*x
emit read(i) as row i of B_inverse applied to y, if i < N
emit write(i,v) as y ^= column i of B * (v XOR old_read(i)), if i < N
leave every copy function unchanged in native mode
keep accesses outside the encoded window as ordinary load8/store8
```

samplingは可逆解全ての探索でも最適化でもない。恒等行列が必ず解であるため、256回で非対角解を見つけなかったことを「混合不能の証明」としない。今回allcells8は解空間の次元1を求めたので、このbyte間線形混合族の可逆解がIだけと分かる。一般のbyte置換まで不存在と主張しない。非零係数数は構成選択の代理指標であり、保護強度ではない。

## 意味保存の理由

初期状態y=B xとする。readはBの逆行列で元byteを得る。writeの論理差分をδとすると、更新後は `y+B*e_i*δ = B*(x+e_i*δ)` であり、byteへの下位8bit格納も元store8と一致する。δの計算は全storeより前に完了させる。copyは `C*y=C*B*x=B*C*x` なので、全復号せずに元のcopy後状態を表せる。これらの操作列に対する帰納法で関係を保つ。

初期値はN byteのdataだけで、それ以降は元の零memory。変換は最初のN byteだけを変更し、read/writeの領域外分岐では元のload/storeをそのまま使う。符号なし比較により負のi32引数もこの分岐へ入り、範囲外store前に他の状態を変更しない。copyは対象領域内に限定しているため変換中の復号・再符号化を含めtrapしない。これは局所意味の説明であり、parser・emitter・runtimeまでの機械検証ではない。

任意Wasm、可変copy範囲、公開memoryへの外部書換え、共有memory、grow、memory64、imports、start、任意関数、副作用のあるアドレス式は非対応。関数を追加して適用範囲を黙って拡げない。領域サイズの増大では未知数N²と制約数が増え、各read/writeも密度に比例する。

## 対照と解除

plainは元profile、uniformは領域内の全byteへ同じXOR定数173を使う既知型の対照、conjugateはnativeと**同じB**で各copyの前後に全領域を復号・再符号化する。allcells8の恒等行列に対するconjugateの費用は無用な処理の費用であり、有用な保護の高速化として数えない。

方式既知の第一の回復は32 byteの公開上限を使い、各論理byteを1bitだけ変えた物理memory差分からBの列を得る。96 API呼出し（32 read、64 write）と、独立した128 writeのモデル照合を行う。有限照合だけでは任意binaryの線形性を証明しない。

さらにこの公開ABIなら、固定copy群をbinaryから読み、初期論理値を32 readで得るだけでplainの等価版を生成できる。原Bは不要である。O3がcopyを1/2/4/8-byteのload/storeへ下ろした形にも対応する。この安い攻撃の成功は、小さな公開read/write実験での保護目標の弱さを示す。private helperを持つ任意アプリを同じ32 queryで解除した結果ではない。
