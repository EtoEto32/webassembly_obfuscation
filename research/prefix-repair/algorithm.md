# 失敗prefixを含むコピー列の共有修復

2026-10-22。実験開始は10月21日。[事前計画](plan.md)の限定profileを実装した。

## 入出力と不変条件

N個のbyteからなる論理状態Xを、GF(2)の可逆N×N行列BでY=BXへ符号化する。
各byteの同じbit位置に同じBを作用させ、各行はbyteのXORとして実装する。
copyの行列Cは、重なりを含むmemmoveのsnapshot意味を持つ行選択行列である。
成功prefix jの合成はP_j=C_j…C_1、P_0=I。

入口状態をY_0とすると、符号化memoryへnative copy列を直接実行した直後はP_j Y_0。
論理copyを符号化した正しい状態はB P_j B^-1 Y_0なので、必要な修復は

```text
D_j = B P_j B^-1 XOR P_j
V = row_basis(stack(D_0, ..., D_K))
U_j V = D_j
```

と表せる。入口でz=VY_0を保存すれば、prefix jでmemoryへU_j zをXORするだけで整合する。
copyで失われた入口情報を後から読めると仮定していない。zはlocalに先に退避する。

```text
compile(source):
    validate closed profile
    choose invertible B; calculate D_j, V, U_j
    encode initial data with B
    replace digest's byte reads by B^-1 rows
    emit run(fail):
        z := V * current_memory
        for j = 0 .. K-1:
            if fail == j: current_memory ^= U_j * z
            native memory.copy(fail == j ? 65536 : dst[j], src[j], len[j])
        current_memory ^= U_K * z
```

最初のD_0は0なので最初の修復は省ける。正常途中に観測はない。
失敗copyは書込み前にtrapし、先行copyの効果は残るため、その直前でprefixの表現を修復する。
trap後のdigestと後続runも保つ。trap位置のPC、実行時間、fuel消費は観測同値の対象外。
host callback・共有memory・外部memory参照があると途中観測を排除できず、本実装では拒否する。

## 保存量の限定的な性質

入口から保存する線形値だけで全D_j Y_0を計算するなら、保存する行空間は全D_jの行空間を含む必要がある。
従ってrank(stack D_j)個のbyte値を保存するVは、この方式内で最小の線形保存次元を持つ。
現在memoryを補助情報にする方式、非線形符号化、実際のregister割当、XOR数や実行時間の最小性ではない。
実際にrotate32ではrank=Nで圧縮できず、full版がbasis版より速いseedもある。

## 適用範囲

実binaryをWABTで読み、再生成した未変換profileとASTが完全一致する場合だけ変換する。
private memory32、1page固定、初期dataは2..64byte、定数範囲の正長copyが1..16個。
exportはrun(i32)とdigest()->i32のみ。失敗位置は公開i32引数で指定し、範囲外は正常終了。
動的アドレス、任意のWasm、import、start、grow、shared、memory64には対応しない。
汎用変換器と称さない。Python整数行列とWABT/Binaryenを用い、外部Python packageは不要。

## 解析目標と解除

解析者は方式・binary・toolchainを知り、元source、seed、行列manifestは持たない。
目的は論理copy列と初期状態を回復し、同じAPI意味を持つ短い実装へ戻すこと。
digest中のXORを追うとB^-1の全行が見える。native copyと最適化による小幅load/storeから
元copy列を抽出し、失敗prefixごとのbit線形意味を照合してから未符号化版を生成できた。
raw/O3を含む正48条件すべてで、回復binaryは元sourceとbyte一致した。

回復器は元のfail引数が既定のguard以外へ流れないことも検査する。
その条件下で0..K-1とそれ以外の分割を網羅し、symbolic memory bitに対する写像を確認する。
これは限定言語の検証器であり、実装全体の機械証明ではない。
旧checkerの不十分なguard検査と反例は[修正履歴](revision.md)に保持した。

今回の失敗原因は、修復の統合によりcodecが変わらず、観測処理に全decoderが露出すること。
復号式を単に長くしたり行列を大きくしても、この解除原理を解消したことにはならない。
