# 広い飽和レーンによる商表現：実測比較

主結果はmain v2 / runtime v2 / audit v1。3合成関数、8レーン、12/48/128更新。CPU affinity/frequency未固定。入力更新・loop・checksumを含むns/call。各processの9 batch中央値を3 fresh process間で再び中央値にした。

| fixture | plain | native8 | canonical | zero | bucket | recovered | bucket/native8 |
|---|---:|---:|---:|---:|---:|---:|---:|
| small12 | 8.209 | 6.318 | 9.753 | 8.715 | 8.382 | 8.426 | 1.327 |
| mixed48 | 31.133 | 21.730 | 32.855 | 24.337 | 24.382 | 8.722 | 1.122 |
| byte128 | 72.701 | 46.651 | 74.638 | 60.299 | 59.858 | 8.432 | 1.283 |

canonicalは飽和加算後だけ下位bitを消す比較。減算後の不要な正規化は入れない。zeroは初期余り0、bucketは入力由来の余りを持つ。native8は通常の8bit SIMDで同じ論理処理をする対照であり、既存難読化ツールの再現ではない。
bucket/canonicalは約0.74–0.86、bucket/plainは約0.78–1.02。一方、bucket/native8は約1.12–1.33で、今回の全例でnative8が速い。正規化削減の利益を、最良の通常表現に対する優位と読み替えない。
正60条件、3,962,880呼出しの不一致0。各条件はbyte対65536個を全レーンへbroadcastした入力と512個の独立packed入力。2^128入力を全列挙したものではない。負6条件は全て不一致を検出。
方式既知の公開I/O学習は30/30で等価候補を生成し、上の差分検査が一致。fixtureごとに2528/2556/2558問い合わせのいずれかで、全mode・raw/O3が同じ問い合わせ数・同じ回復binaryとなった。元の更新列は復元していない。
学習の単回時間はNodeのpack/unpack・query記録を含み、compile/instantiateとWasm生成を除く。静的逆コンパイルの時間や、人間の解析器開発費用ではない。
66本のbyte再生成一致。別WABT実行480呼出し一致。4対象外sourceを拒否。縮小幅の代数検査29,344比較、16bit境界・乱数33,056比較は一致。
未変換・変換のlinear memoryは0。学習版は係数表24,576bytesを固定65,536byteのprivate memoryに保存する。recoveredは追加O3なし。他版はO3後、全て同じbench wrapperを後付けする。回復版の速度向上には表引きへの置換とmemory追加を伴う。
54 fresh process、486 batch。10ms未満は17件。Node全processの最大RSS範囲は36348–36764 KiB。Python変換・学習器固有のpeak memoryは測定していない。
一般のlane依存があるプログラムではbroadcast学習は不十分。byte rotationがbroadcastではidentityに見え、入力1で256と1に分かれる負例をauditへ保存。学習器を汎用同値検証器とは扱わない。
