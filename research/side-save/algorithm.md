# 全copy prefixの現状態を使う共有退避

2026-10-23。既存の符号化memory修復の費用を減らす生成アルゴリズム。coded side-informationという既知枠組みと近く、独立した新難読化原理を確立したとは扱わない。

## 問題

論理byte列xを可逆なGF(2)行列Bでy=Bxへ符号化する。同じ行列を各bit面へ適用する。native `memory.copy`のprefixをP_jとすると、修復前の現memoryはP_j y0。必要なのはB P_j B^-1 y0だから、差分D_j=B P_j B^-1+P_jを加える。

prefix-repairは全D_jの行空間を入口で保存する。loss-flagはBを制限し、現memoryだけでD_jを回復可能にする。今回は**Bを変更せず**、入口に保存するz=V y0と現memoryの両方を使う。

```
row(D_j) ⊆ row(P_j) + row(V)           (全prefix j)
R_j [P_j ; V] = D_j                   (生成後に検査)
repair: y_j ← y_j + R_j [y_j ; z]
```

copyが失った値を現memoryから復元できるとは仮定しない。足りない独立情報をVに入れる。線形な共有退避の次元を最小化することが今回の具体課題であり、総local数、register数、XOR数、実行時間の最小化ではない。

## 生成規則

P_{j+1}=C_{j+1}P_jなのでrow(P_{j+1})⊆row(P_j)。後のprefixほど少ない副情報を持つ。この順序を使う。

```
V = []
for j = K downto 0:
    for row d in D_j:
        if d is not in span(P_j rows + V):
            V.append(d)
for j = 0..K:
    solve R_j [P_j ; V] = D_j by binary elimination
    verify the matrix identity
    factor R_j into U_j W_j
emit:
    z = V * initial physical memory
    native copies, unchanged on successful paths
    before failure at prefix j, or normal exit:
        t = W_j [current physical memory ; z]  // 全て先に計算
        physical memory ^= U_j t
```

ここで行列加算はXOR。各repairは全temporaryを読み終わってからstoreし、重複copyのsnapshot意味も保つ。入口退避がr、最大temporaryがtなら、本emitterはr+t個のi32 localを宣言する。byte相当の独立情報一つも実装上はi32 localに格納しており、r byteのstackが測れたという意味ではない。

## 最小性の交換論証（限定された線形モデル）

side-information行空間S_j=row(P_j)が単調に縮むとする。後方greedyが既に選んだ空間をUとし、これを含む任意の実行可能な共有保存空間Wを考える。初めはU=0なので任意の最適解を選べる。

stage jでd∉S_j+Uなら、Wの実行可能性よりd=s+w（s∈S_j,w∈W）と書け、w∉U。Uの基底とwを含むWの基底を取り、wをdで置換してW'を作る。次元は増えない。未処理の早いstage i≤jではS_j⊆S_iだからW+S_i=W'+S_iで、要求の回復可能性を保つ。処理済みの遅いstageは既にUだけと自身の副情報で満たされ、Uは変更しない。従って、次元を増やさずU+dを含む実行可能な保存空間へ交換できる。

これを繰り返すと、任意の最適解はgreedyの全Vを含む同次元以下の解へ変形できる。V自身も全要求を満たすので、greedyはこのモデルで最小。一般の非線形・bit面間符号・非nested side-information・実CPU保存領域の最小性は主張しない。既知index codingの特殊構造への議論であり、新しい一般符号理論の発見とは扱わない。

検査では3byteの全168可逆B×単点copy2個の全36列、計6,048問題で全16subspaceの最小値と一致。各0/1初期状態・各prefixの145,152比較も一致した。別に4次元・任意線形要求の固定seed 1,000問題を全67subspaceと比較して一致。有限検査と上の手書き論証を区別し、Python実装の機械証明とは呼ばない。

## 意味保存と対象範囲

既存prefix-repairの実binary parserを使用する。private memory32固定1page、2..64byteの初期領域、1..16個の定数・正長copy、`run(fail:i32)`と`digest()->i32`。failがjならj番目のdstだけ65536にし、そのcopyは範囲検査で書込み前にtrapする。全ての既知の正常・trap出口直前で表現を修復し、trap後のdigestと次回runも保つ。各修復アクセスは既存の先頭Nbyteに収まる。

sourceをcanonical生成物とAST照合する限定profile。dynamic copy、grow、import、shared memory、memory64、任意の関数・分岐、外部観測・外部memory更新は未対応。診断用memory exportはcheckerだけに追加する。実時間・fuel・trap PC・資源枯渇の同一性は対象外。

## 解析者と限界

方式・binary・規則は公開。元source・seed・行列metadataを回復器には渡さない。既存prefix-repair回復器はdigestからB^-1を抽出し、全failure区分のsymbolic memory効果を検査する。回復器を変更せずbasis/side各12条件を元sourceとbyte一致するWasmへ戻した。保存量が減ったことを解析耐性の増加とは扱わない。一方、回復可能な難読化にも費用改善はあり得るため、工学的な生成部品として保持する。
