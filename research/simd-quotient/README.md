# SIMDの非正規マスク：具体案の実装と回復

2026-10-18。**主難読化方式には不採用。** 比較結果を0/255に固定せず、偽を0、真を1..255で表し、飽和差・min/maxで条件判定を融合する実Wasm変換を実装した。各段階で正規化する対照より軽量だが、0か正数かという射影だけで元の条件式を回復できる。既知の順序に基づく論理表現から独立した新規性と、実用的な保護上の優位性は未確立である。

## 設計

[事前仕様と変換規則](plan.md)。Q(x)=[x>0]について、Q(min(a,b))=Q(a) AND Q(b)、Q(max(a,b))=Q(a) OR Q(b)、Q(sat_sub(1,a))=NOT Q(a)。unsignedのsat_sub(a,b)が正なのはa>bの場合だけである。これらを命令の対応関係として用い、Boolean cone内部のマスクを非正規値へ変える。結果をbitmaskへ変える直前にgt_u(x,0)で0/255へ戻す。WasmのSIMDを使うが、同じ飽和命令を持つ他の形式にも適用でき、Wasmだけの新原理ではない。

対応範囲は、純粋な単一関数、i32引数から構成するv128、i8x16のunsigned比較・eq/ne、v128 Boolean演算、i8x16.bitmaskのi32結果。memory、import、call、global、制御フロー、trap、副作用、浮動小数点は扱わない。localsは記号式へ展開し、出力ではDAG共有を戻す。元からSIMDであるコードを対象にし、scalarからの自動vector化の効果を混ぜない。

意味保存はQとの交換則を式の構造に沿って用いて説明できる。ただし実装全体の形式証明ではない。bitmaskは各byteのMSBを集める命令なので、非正規値を直接渡すとQとは一致しない。回復器・変換器は最終bitmaskの引数が0/255と証明できることを要求する。さらにQ(a AND 1)=Q(a)は任意のbyteには成り立たないため、aが0/255のmaskである場合だけ簡約する。

## 先行技術と差分

- Vasumathi Raman, Alexandre Donzé, Dorsa Sadigh, Richard M. Murray, Sanjit A. Seshia, **Reactive Synthesis from Signal Temporal Logic Specifications**, HSCC2015, pp.239–248, [DOI:10.1145/2728606.2728628](https://doi.org/10.1145/2728606.2728628)、査読会議論文。[著者PDF](https://people.eecs.berkeley.edu/~sseshia/pubdir/hscc15-mpcstl.pdf)の要旨・§2.2を確認した。実数値のrobustnessをmin/maxで合成し、正負からBoolean意味を得る既知の構成。論文全体の実験の再現・数値比較は行っていない。難読化を提案した論文として扱わない。
- [WebAssembly公式SIMD提案資料](https://github.com/WebAssembly/relaxed-simd/blob/main/proposals/simd/SIMD.md)のSaturating integer subtractionの定義を一次検索抜粋で確認。unsigned差は負なら0へclampする。これは既知の命令仕様であり新規の演算ではない。
- [WASMixer §4.2.2](https://arxiv.org/html/2308.03123v1)を再確認。callからcall_indirectへの変換とopaque predicateを使う先行方式であり、単なる間接呼出し化を新案にしない。
- [US8645930B2](https://patents.google.com/patent/US8645930B2/en)は共通prototype・関数統合を記載する。請求項1–17、概要を確認し、最初に検討した型統一・間接呼出しの方向から切り替えた。[特許追補](../patent/signature-and-simd.md)。

具体的な検査対象は、unsigned byteの飽和差を入力とする非正規maskをcone全体で維持する生成規則である。既知の構成要素を含むことだけで全体が同一とは結論しない一方、min/maxを論理へ写す簡単な商写像が残っているため、値の多様性を新たな保護効果とは扱わない。先行技術不存在・特許性・FTOは未判断。

## 実験と結果

主データ：[simd-quotient-v2](../../results/invention-20261018/simd-quotient-v2/)。[比較表](../../results/invention-20261018/simd-quotient-v2/comparison.md)、[manifest](../../results/invention-20261018/simd-quotient-v2/manifest.json)、[監査](../../results/invention-20261018/simd-quotient-v2/audit.json)。一括再現は[replay-v1](../../results/invention-20261018/simd-quotient-replay-v1/)、追加の誤演算対照はその[記録](../../results/invention-20261018/simd-quotient-replay-v1/wrong-arithmetic.json)。

3つの人工条件判定kernel、plain／各gate正規化／融合、raw／O2／O3の27本と、回復後27本を検査した。各入力は2つの128bit vectorを8個のi32で渡す。同一byteを全laneへ複製した全256²入力組と、laneごとに異なる乱数2,048組、計67,584入力を使う。JSの独立したscalar条件式を参照し、**54条件・3,649,536呼出しで不一致0**。全256bit入力の実行列挙ではない。

WABT interpreterでは27条件×4境界入力=108呼出しで一致。byte範囲の交換則は590,080比較で不一致0。非正規bitmaskを2つの入口で拒否し、誤ったAND-1簡約を防ぐparity例は元・回復の512呼出しで一致した。replayでは飽和減算を通常のwrap減算に変えた、validationを通る誤バイナリも用意して差を検出する。

方式既知の回復器は元ソース・生成reportを使わず、実バイナリから比較とBoolean結合を再構成する。各解析内で式をmemo化し、反復測定間ではcacheを共有しない。**27/27条件で元と同じ正規化条件式へ回復**した。主条件で未対応0、crash0、解析失敗0、timeout発生0。生成された回復Wasmもvalidate・実行した。

O3の測定例（実行はns、解析はms）：

|kernel|plain bytes/ns/ms|融合 bytes/ns/ms|各gate正規化 bytes/ns/ms|
|---|---|---|---|
|range|164 / 11.31 / 0.1019|232 / 11.77 / 0.1131|552 / 12.33 / 0.1775|
|pair|138 / 6.65 / 0.0966|232 / 9.13 / 0.1025|432 / 11.17 / 0.1452|
|filter|190 / 7.69 / 0.1540|316 / 9.44 / 0.1746|716 / 13.79 / 0.2693|

実行時間は81 fresh Node process（各条件3 process）。各20,000 warmup、9反復×20,000呼出し、固定seedでprocess順をshuffleし、process内中央値の中央値を報告。JS呼出しと8引数の取得を含む。CPU affinity・JIT tierを固定しておらず、例えばrangeのprocess中央値はplain 7.18–11.39 ns、融合7.72–12.19 nsとばらつく。小差を高速化の証明にしない。全反復はruntime.jsonに保存した。

解析は1 warmup＋9反復、WABT起動・parseを除くQの抽象評価時間。parse込み初回はmanifestに別保存。Python解析時間とV8実行時間の比を保護強度には使わない。linear memoryは0 byte、process RSSはNode/V8込み。変換6回の時間とバイナリサイズもmanifestに保存した。

## 採否と次の制約

融合の費用低下はあるが、融合により解析側の式も小さくなった。元の条件式への回復は0.1–0.2 ms程度の抽象評価で済み、元に比べた追加費用も小さい。これだけで未知の解析法すべてに弱いと証明したわけではないが、単純な方式既知の回復に対して新しい実用上の利点を確立できず、主方式には採用しない。単に「回復できたから」という判断ではない。

次は独立した各値に同じ二値射影を適用するだけで操作列へ戻せる構成を、実装前に検査する。広い値域、違う型、異なるlane配置だけではこの問題を解決しない。今回の案を既存の型統一・SIMD配置の案と合わせて「3つの新発明」と数えない。

## 再現

Python 3.9以上、Node 24.15.0、WABT 1.0.42、Binaryen 133。標準Pythonライブラリだけを使う。共通parserとツール起動は`research/connectivity-elimination/prototype.py`、ツールは`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`。親directoryは`WASM_TOOLS_ROOT`で変更可能。実環境は[environment.json](../../results/invention-20261018/simd-quotient-v2/environment.json)。

```powershell
python research/simd-quotient/reproduce.py results/simd-quotient-reproduction
python research/simd-quotient/prototype.py fused input.wasm output.wasm
python research/simd-quotient/prototype.py recover output.wasm recovered.wasm
```

出力先は未使用の名前を指定する。v1は主corpusでは正しかったが回復器に適用条件の漏れがあった。v2で非正規bitmaskの拒否、AND-1簡約の条件、解析ごとのmemoを追加した。v1/v2の主54本はbyte単位で同一。PowerShell版一括scriptは環境のAuthorizationManagerに拒否されたためPython版を用いた。replayは最終scriptによる別出力先での実行であり、新しいベンチマーク数に加算しない。[日本語草稿](paper-note.md)。
