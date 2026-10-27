# profile別テーブル表現の合成 — Iの見直し2

2026-10-24。**動作する限定生成器を作ったが、主特許候補への昇格は保留**。元の部分strict化に対し、命令列を維持して事前のデータ表現を変える案を試した。初期計画は[こちら](compensation-plan.md)。

## 構成とアルゴリズム

対象は256byteのlookup tableを16個のvectorへ分け、swizzleの結果をXORする既存XNNPACK型の骨格である。input byteの下位4bitごとに独立した16要素の列を考える。各profile Rとstrict化mask hにおける計算をGF(2)行列A(R,h)で表す。逆行列E(R,h)を事前表現とすれば、A E T=Tになる。

```text
for each allowed swizzle profile R:
    A := evaluate fixed lookup schedule on 16 basis columns
    E := Gaussian elimination to solve A E = I
    reject if singular; verify product and every byte-index class
emit init():
    R := public constant-input probe in this execution environment
    encoded_table := E[R] * original_table using vector XOR
emit run(N):
    reject invalid N before any write
    preload encoded vectors from fixed addresses
    process input/output sequentially with the same lookup schedule
```

実装は[compensate.py](compensate.py)。任意binaryを解釈する変換器ではなく、固定骨格と4種maskから実Wasmを作る生成器である。profile0は恒等表現、profile1の未変更maskは既存XNNPACKの差分表現と一致した。混合maskに対しても表現を再合成できたが、Gaussian eliminationや可逆表現を新しく発明したわけではない。

表はinit後に変更しない。1個の固定4page memoryで、元表[0,256)、encoded[512,768)、入力[1024,66560)、出力[131072,196608)を使う。Nは0..65536の16の倍数。shared memory、並行更新、任意alias、別の緩和演算、可変table寸法は非対応。profileを別runtimeへ持ち出して使うことも前提外。

## セキュリティ上の範囲

候補となる性質は、両profileでlookup結果を一致させ、入力indexによるlinear-memory table loadを処理loopから除くことである。表内容とindexは秘密にでき、Nと実行profileは公開とする。出力値は本処理が許す観測であり、値そのものを隠さない。

生成骨格の表loadは固定offset、入力と出力は公開counter、分岐はN・ready・公開profileのみ。実際のWasm address traceも検査した。ただしJITが作るnative命令、cache、時間、投機実行まで含むconstant-time証明ではない。正式なCT-Wasm型検査や検証済みcompilerを置き換えるものではない。

## 正当性

- [生成](../../results/profile-repair/compensation-v1/results.json): 4mask及び3対照×native/明示R0/明示R1、raw・O3・traceの63binary。生成約1.706秒。
- [Nodeと別byte式](../../results/profile-repair/compensation-audit-v1/results.json): 30式UNSAT、276table、15,792呼出し、61,498,752byte照合、不一致0。未初期化・不正長420trapでmemory不変。initのencoded外、runのoutput外のmemoryも照合。
- [Wasmtime50.0.1](../../results/profile-repair/compensation-cross-v1/results.json): default/実DET option、1,008呼出し、22,111,488byte照合、不一致0、42境界trap。DET時はprobe0を実際に観測。同CPUでありAArch64実機ではない。
- 256byte処理のtraceはadaptive/strictで48イベント、scalarで768イベント。4種の秘密内容変更でadaptiveは同一trace、scalarとR0の既存dispatch fallbackは異なった。これはWasm-levelの検査である。

## 性能と対照

[5 fresh process、各15標本](../../results/profile-repair/compensation-performance-v1/results.json)。Node --no-liftoff、O3済みbinary、同process内で方式とsizeをshuffle、2warmup。標本あたり1MiB、initは別に5000call×15標本。CPUはIntel i9-11900K。

|処理byte数|補償 ns/byte|全strict|既存型dispatch|scalar|対応processの補償/strict比の中央値|
|---:|---:|---:|---:|---:|---:|
|16|1.1224|1.2283|1.1519|1.0878|0.9250|
|256|0.4059|0.5352|0.4157|0.3305|0.7584|
|4096|0.3675|0.4868|0.3675|0.2719|0.7457|
|65536|0.3633|0.4836|0.3620|0.2671|0.7572|

全strict比の大batch約24–25%短縮は、既存のprofile1差分lookupと同じ効果である。scalarはさらに速いが入力依存の表addressを使う。明示R0では補償/strictは65536byteで1.0022、速度差なし。同一binary別instanceの比の中央値は16byteで1.0650、65536byteで0.9926なので、小batchの差を強い結果としない。

init中央値は補償18.86ns、strict15.58ns、既存型dispatch17.94ns。O3後sizeはそれぞれ1516/1016/1915byte、scalar524byte。4page memoryは固定で、追加encoded表は256byte、物理memoryの節約ではない。process RSSは約47.4–47.6MBで、単一方式の追加memoryとは分離していない。

## 先行技術と請求項たたき台

最も近い実装はXNNPACKのprofile probeと差分表、およびArm astc-encoderのarchitecture別vtable_prepareである。[先行比較](novelty-analysis.md)を参照。Swizzle Inventorはmappingの合成、US7739319B2は複数registerを使うSIMD lookup、CT-Wasmは型による情報流・時間漏洩対策を扱う。それらの一般原理を当研究の新規点へ含めない。

**I4（技術構成の記録）**: 複数の許容実行profileを持つlookup命令列について、各profileにおける入力表から出力への係数写像を生成し、所定のlookup結果を与えるprofile別の事前表現を求め、実行環境で得た公開profileに対応する事前表現を初期化時に選択し、入力indexによらないmemory address列で前記命令列を実行するWasm生成方法。

**I5（従属案）**: 一部の演算を厳密化した命令列について前記係数写像を再計算し、再計算した事前表現と当該命令列の積が所定の写像に一致する場合のみ生成を受理する方法。

|要素|既知部分|残る差分候補|
|---|---|---|
|共通profileとprobe|Wasm仕様、XNNPACK|なし|
|SIMD lookupと差分表|XNNPACK、astc-encoder、Intel特許|なし|
|係数抽出と逆行列|一般的な線形表現・合成|固定Wasm骨格への具体化に限定|
|複数profile・混合strict maskで同時に補償表を生成|今回実装した組合せ|既知の合成に条件を加えただけという反証が強い|
|固定addressを確認|既存情報流解析・CT-Wasm|今回のtrace検査はそれらより弱い|

新たな一般原理、既存dispatchを超える速度、権利化可能性は未確認。通常profileで既存表と同じものが出たことを隠さず、出願用の主案に昇格しない。特許family・審査履歴・日本の請求項調査は未完了。
