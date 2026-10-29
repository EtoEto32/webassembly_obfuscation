# 区間上書きによる比較の実装と早期評価

2026-10-18。**実Wasmで動作・回復・費用を測定したが、新しい主方式には採用しない。** 領域共有は実行費用を下げる一方、最後の上書きを追う解析も安い。近い公開先行例を確認したため、メモリ経由の比較という一般発想を発明とはしない。

[事前計画](plan.md)、[先行技術](prior-art.md)、[日本語草稿](paper-note.md)。この早期ゲートの完了と、研究全体の新規で有効な方式の確立を区別する。

## 候補の規則

byte値a,bについて、次のメモリ更新は `[a<b]` を返す。

```
fill(private[base : base+256], 0)
fill(private[base : base+b], 1)
return load8(private[base+a])
```

Wasmの標準bulk memoryとmulti-memoryを使う。元の公開memoryを変更せず、非exportの第2memoryに一時状態を置く。解析者には第2memoryも見えると仮定する。

共有版の生成手順は、比較式の右辺パラメータbで比較をまとめ、異なるbごとに256byteのslotを割り当てる。関数の先頭で各slotを構築し、各比較をそのslotからのloadへ置き換える。副作用のない領域なので構築の前倒しが可能である。個別版は比較ごとに同じ256byteを初期化する。対照として、64KiBの二次元表 `T[a*256+b]=[a<b]` から読む版も生成する。これらは原理の異なる3発明として数えない。

意味保存は、初期化後の全iについて `M[base+i]=[i<b]` が成立することによる。slotは交差せず、a,bは0..255、最大64パラメータなので書込み・loadは1ページ以内に収まる。毎回初期化するため過去の呼出しに依存しない。正常なインスタンス化と資源確保を前提とし、追加memoryによる資源枯渇、時間、fuelを含む同値性は主張しない。

## 対象範囲

入力は実 `.wasm`。1〜64個のi32引数を持つ単一関数 `run` と、固定1ページの公開memoryだけを持つ。対象の式は `(arg_i & 255) <_u (arg_j & 255)`、0/1定数、and/or/xorによるBoolean結合。sourceのlocal、任意算術、loop、load/store、import、data、追加export等は拒否する。任意のC/Rust出力を変換するツールではない。

変換器はWABTでvalidate/WAT化し、型・module項目・式文法を検査する。WABTの型検査を回避したり、意図的trapや未定義動作を利用したりしない。custom/debug/linking情報の完全保存は保証対象外。保護課題は、バイナリから等価な比較・Boolean式と通常Wasmを回復する費用である。

## 方式を知る解析

[回復器](prototype.py)はバイナリのみを受け取り、sourceのモデルを受け取らない。localとoperand stackを記号評価し、private fillの領域と長さを記録する。load位置を覆う最後の部分上書きと、その前の256byte初期化を検査すると、元の比較へ戻せる。交差slot、不明な境界、初期化の欠落、未対応演算は拒否する。

これは一般の配列解析ではなく、今回の生成族とBinaryen O2/O3出力に対応した限定解析である。ただし、未対応を保護の成功とせず、対応後に費用を測った。二次元表の対照は全65,536byteが既知の比較関係と一致することを検査して回復する。

復元式とsource式について、各比較を独立Boolean変数として扱う代数標準形（ANF）の一致も検査した。この十分条件が成立すれば、比較間の依存関係によらずBoolean式は等価である。これは抽出した式同士の等価性であり、Wasmエンジンや変換器全体の形式検証ではない。

## 検査結果

主データは [interval-write-v3](../../results/invention-20261018/interval-write-v3/comparison.md)。pair2（1比較）、range4（2比較）、fanout8（同じ右辺を持つ7比較）、mixed8（5比較）の4合成例。元/table/individual/sharedの4方式×raw/O2/O3の48本と回復48本を検査した。

|項目|結果|
|---|---|
|WABT/Node validation|主96本が成功|
|Nodeによる値と公開memory比較|1,975,680呼出し、不一致0|
|WABT interpreterでの独立実行|384呼出し、不一致0|
|方式既知の式・Wasm回復|48/48成功、式のANFも一致|
|主解析の未対応・クラッシュ・時間上限・解析失敗|各0|
|v1とv3の主バイナリ|96/96で集合・SHA-256一致|

pair2では全65,536個のbyte対、各例で100境界組と4,096固定seedの32bit入力を使用した。pair2は69,732呼出し/本、他の3例は4,196呼出し/本。上位bitを含む32bit引数も検査し、毎呼出し後に公開memoryの65,536byte全体を比較した。件数は呼出し回数であり、重複のない独立標本数とはしない。主プログラムには資源枯渇以外のtrapを起こす操作はなく、観測上もtrapはなかった。WABTは各本に4つの固定入力wrapperを追加して実行した。

[負の対照](../../results/invention-20261018/interval-write-v3/negative-analysis.json)：上書き長をb+1へ変えたWasmは69,732呼出し中296件で誤り、回復器も拒否した。初期化を削除したWasmは連続2呼出し中1件で誤り、過去の呼出し依存を理由に拒否した。sourceへの公開memory書込み、Boolean式として扱えないnumeric OR、境界外になり得るload offsetも拒否した。最後の3種は受理条件の対照で、主性能測定には混ぜない。

## 性能と効果の分離

v3のO3、fanout8。単位ns/callはJSからの引数展開・呼出しを含むため、Wasm命令だけの実行時間ではない。

|方式|binary bytes|実行ns/call|解析ms|
|---|---:|---:|---:|
|元|132|46.15|0.0540|
|二次元表|65,737|48.08|0.5963|
|個別上書き|277|119.91|0.0823|
|共有上書き|159|64.41|0.0550|

共有によって個別版より実行費用とサイズが減った。この改善は事実だが、解析時間も減り、同例では元と近かった。4例の共有版の実行倍率は元の1.31〜2.26倍、解析倍率は今回の実装で1.02〜1.58倍。回復成功だけで効果ゼロとは扱わないが、独立した保護上の利点を示す結果は弱い。表版に対するサイズ削減はある一方、表版はこの測定では元と近い実行時間だった。[全O3表とばらつき](../../results/invention-20261018/interval-write-v3/comparison.md)

各主条件を3 fresh Node process、2,000回warmup、9反復×10,000呼出し、計144process。固定seedの1,024入力を循環し、実験順序を固定seedでシャッフル。CPU affinity・JIT tierを固定していない。短時間の差はprocess間のばらつきを伴う。v1/v2/v3の再実行件数を独立標本として合算しない。

実行時間は関数呼出し部分であり、moduleのコンパイル・インスタンス化・active dataの初期化は含めない。

全方式の公開memoryは65,536byte。変換版はさらに固定65,536byteを割り当てる。実際に使う範囲は個別版256byte、共有版256〜1,024byte、表版65,536byteだが、範囲が小さいことを割当memory削減と表現しない。Node全体の最大RSSは41,828〜42,444KiBで、差からWasm単体の費用を分離しない。

変換時間は各条件1回で、表版69.58〜71.93ms、個別53.83〜56.91ms、共有54.30〜57.52ms。WABT起動・入力検査・出力生成・validationを含む。回復解析は1warmup後9回、WABT起動/WAT化/parseの25.85〜54.26msを除く。回復Wasmの生成・validationと解析器の開発時間も含めない。解析器のピークmemoryは未測定。

v1/v2の表解析は、毎回Pythonで既知表を再生成し文字列を逐次decodeしたため約15msだった。v3は固定の比較表を一度用意し、全byteのdecode/照合を高速化して約0.6msへ短縮した。古い遅い値を対照方式の保護強度には使わない。これも最適な解析時間の下界ではない。

## 再現と環境

未使用の出力ディレクトリを指定する。全生成・最適化・回復・正当性・性能・hash比較を実行する。

```powershell
python research/interval-write/run.py results/invention-20261018/interval-write-repro --compare results/invention-20261018/interval-write-v3
```

単独CLI：

```powershell
python research/interval-write/prototype.py shared results/invention-20261018/interval-write-v3/fanout8.plain.raw.wasm results/invention-20261018/interval-demo/protected.wasm
python research/interval-write/prototype.py recover results/invention-20261018/interval-demo/protected.wasm results/invention-20261018/interval-demo/recovered.wasm
```

Python 3.9.0、Node v24.15.0 / V8 13.6.233.17-node.48、WABT 1.0.42、Binaryen 133。OSのPython報告値はWindows-10-10.0.26100-SP0、CPUはi9-11900K 3.50GHz。NodeはPATH上、WABTは `.tools/wabt-1.0.42/bin`、Binaryenは `.tools/binaryen-version_133/bin`。Python追加packageは不要。[共通パーサ](../connectivity-elimination/prototype.py)をimportする。必要なツールは公式 [WABT](https://github.com/WebAssembly/wabt/releases)、[Binaryen](https://github.com/WebAssembly/binaryen/releases)、[Node.js](https://nodejs.org/en/download/archive) の対応版を用意する。

結果の `sources/` と `audit.json` は実行時ソースとhash。snapshotだけで動くpackageではなく、再現はリポジトリ内で行う。smoke-v1の廃止済みWABTフラグ、smoke-v2の最適化後stack/gt対応不足を主解析の保護成功に数えない。v2ではBoolean簡約と数値演算の適用条件を修正し、v3で対照の解析効率とoffsetの拒否検査を強化した。主96バイナリの意味・内容は同一である。

[audit.py](audit.py) による保存証拠の整合性監査も実行し、件数、全主バイナリとsource snapshotのhash、再現一致、負の対照を確認した。[監査結果](../../results/invention-20261018/interval-write-v3/verification.json)。これは追加の実行性能実験ではない。

## 判断

メモリ経由の比較、lookup、私有scratchという一般構成は既知であり、bulk命令への置換と共通構築の共有だけでは新しい発明を確定できない。領域共有の費用改善は、すでに回復しやすい比較表を効率的に作る効果でもあった。したがって主方式に採用せず、実アプリへの拡張・著者ツールとの比較・人間の解析時間評価は実施していない。

今回の反証は、入力依存の書込みを加えても、各loadの最後の定義が短い区間式なら局所回復できる、という限定したもの。すべてのメモリ難読化が無効という結論ではない。研究全体の目標と特許を目指す方針は継続する。
