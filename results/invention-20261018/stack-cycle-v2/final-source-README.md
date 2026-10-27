# 同一スタック型の分割点を使うWasm平坦化の実験

2026-10-18。**実装・実験は完了したが、新規で有効な難読化方式としては採用しない。** 最適化前のサイズ削減は確認できた。一方、最適化後の優位性は一貫せず、方式既知の解析費用は通常のlocal退避dispatcherと近い。復元成功そのものを不採用理由にはしていない。

## 実装と技術的差分

実際の入力`.wasm`をWABTで読み、命令境界の型付きoperand stackを計算する。同じ非空型列Sが繰り返される区間から、指定個数の断片を作る。保護区間長を最大化し、同長ならSが長い区間を選ぶ。内部の分割点は最大断片長を最小化する動的計画法で選ぶ。最後の同点は型列の辞書順で決定する。最大1024命令、分割数1–128。

各断片S→Sをmulti-value block/loopの引数・結果で接続する。stackの最上段に次stateを置き、`br_table`がそれを消費する。元からあるlocalは残すが、変換器が追加するlocalは0。比較用`locals`は**同じ区間、分割点、case配置、次state**で、stack値とstateをlocalへ退避する。4/8/16分割を測った。

WASMixerの§4.2.1 Algorithm 2/3との比較から着想したが、著者実装を実行したものではない。対照は「local退避dispatcherの自作実装」と呼ぶ。WASMixer全体に勝ったという主張はしない。Wasmの値付き分岐によるlocal削減と、一般の列分割DPは既知である。今回の組合せが独立した研究貢献になる根拠は得られていない。[検討記録・草稿](paper-note.md)

## 再現

リポジトリrootからPowerShellで実行する。Python 3.9.0、Node 24.15.0 / V8 13.6.233.17-node.48、WABT 1.0.42、Binaryen 133を使用。外部Pythonパッケージ不要。ツールは`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`。別配置には`WASM_TOOLS_ROOT`を使える。CPUはIntel Core i9-11900K、Windows。実際の環境情報は結果内のJSONに保存する。

```powershell
python research/stack-cycle/transform.py input.wasm output.wasm --mode payload --fragments 8
python research/stack-cycle/specialize.py output.wasm recovered.wasm
& research/stack-cycle/reproduce.ps1 results/invention-20261018/stack-cycle-new-run
```

出力先は新規ディレクトリにする。再現スクリプトは生成、O2/O3、復元、正当性、WABT interpreter、性能、追加の型テスト、監査まで実行する。`transform.py`のCLIは既存出力バイナリを上書きしない。共有のWABT呼出し・WAT parserは`../connectivity-elimination/prototype.py`を読み、監査時にそのソースも保存する。

対象は単一定義関数の直線scalar命令列、任意の1個の非共有32-bit memory/data/export。元のif/loop、import/call、global、memory.grow、SIMD、GC、例外命令、multi-memory、memory64は対象外。全scalar命令を網羅した実装ではなく、`effect()`に列挙した命令のみを扱う。繰り返す型列が不足する関数も拒否する。custom/debug metadataは保持対象外。一般のC/C++プログラムへの適用率は測っていない。

## 計測結果

主結果は[stack-cycle-v2](../../results/invention-20261018/stack-cycle-v2/summary.json)。4小カーネル×7方式（元、local/payloadの各4/8/16分割）×raw/O2/O3=84条件。これと復元後84本の合計168条件を独立JS oracleで検査した。

- 主検査：611,730呼出し。返り値、trapの有無、trap後を含む全exported memoryの不一致0。同一instanceの継続呼出しも含む。
- 補助検査：i64、f32/f64の符号反転とbit再解釈、multi-result、selectの30条件・30,990呼出し、不一致0。NaNの算術結果一般のbit一致は主張しない。
- 別エンジン：WABT interpreterで84条件×4=336呼出し、不一致0。memoryの全byte比較はNode側で実施。
- 分割点DP：200小例を全列挙oracleと比較し、不一致0。対象外5種を明示拒否。
- 誤った次stateへ飛ぶ型としては正しい対照：4,107入力のうち4,106で不一致を検出。
- 復元：84/84成功。未対応・クラッシュ・timeoutは主条件では0。rawの各カーネルで7方式すべてが同じ復元関数命令列になった（型節の余剰宣言等は除外）。

### trap理由の差を隠さない

初回[v1の検査](../../results/invention-20261018/stack-cycle-v1/correctness.json)はV8エラーメッセージからの理由分類も同値条件に含め、52件の不一致を出した。内訳はmemory16/locals16のO2・O3、その復元後の4条件×13入力。Binaryenが副作用を挟まないloadとdivの評価順を変え、ゼロ除算より範囲外アクセスを先にtrapさせた。生の変換では理由差0。

Binaryen 133の[effects.h](https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/src/ir/effects.h)はtrap理由の違いを区別せず、他の観測可能な副作用を跨がないtrap同士の並替えを認めている。Wasm JS APIはtrapをRuntimeErrorへ写すが、これらの具体的なmessageを契約にしていない。[仕様](https://www.w3.org/TR/wasm-js-api-2/#exported-functions)

v2では**値またはtrapと全memory**を主観測とし、理由差52件を別の列に残した。memory不一致0を独立に確認した。JSのエラーメッセージ一致まで含む強い契約では、この最適化経路は一致していない。最初から全項目が一致したとは書かない。バイナリ変換規則を直して差を消したものでもない。

### 費用と解析

8分割、O3。時間は3個の独立Node processそれぞれの中央値の中央値。単位ns/呼出し、JSループ・引数展開を含む。解析時間はPythonのモデル構築・部分評価・WAT生成のみ、1 warmup後9反復の中央値。WABTの起動、逆アセンブル、WAT parse/compileはこの解析時間に含めない。

|カーネル|元 bytes / ns|local bytes / ns|payload bytes / ns|解析ms 元 / local / payload|
|---|---:|---:|---:|---:|
|xorshift16|421 / 36.4|528 / 33.3|519 / 35.5|0.5002 / 0.6209 / 0.6550|
|mixed4|243 / 35.0|350 / 40.8|387 / 38.0|0.2850 / 0.4186 / 0.4787|
|crc32word|715 / 47.1|822 / 48.8|811 / 52.0|0.8570 / 1.0349 / 1.0176|
|memory16|370 / 52.8|459 / 50.6|466 / 53.4|0.3039 / 0.4278 / 0.4629|

時間の全標本・process中央値・範囲は[比較表](../../results/invention-20261018/stack-cycle-v2/comparison.md)と[performance.json](../../results/invention-20261018/stack-cycle-v2/performance.json)を参照。例としてcrc32word/local8のprocess中央値は40.8, 48.8, 69.0nsで、payload8は47.3, 52.0, 52.6ns。数nsの差を性能優位と判定しない。

各binaryを3 processで測定、全252 process。各processは10,000回warmup、30,000回×9batch。順番を固定seedでshuffleし、測定processは逐次実行。CPU affinity、周波数固定、JIT tierの追跡はしていない。短いカーネルとJS呼出し費用のため、速度差の一般化はできない。最適化後の全24保護条件にdispatcherのloopとbr_tableが残ったが、機械語での残存は調べていない。

追加の線形memoryは0（memory16だけ元から65,536B）。process maxRSSは41,564–44,412KiBでV8・JS等を含む。Wasm値のレジスタ/ネイティブstack使用量は測っていない。24変換の時間は58.8–77.5msで、WABT子processの起動を含む。

未最適化8分割のlocal→payloadサイズはxorshift16 552→504B、mixed4 492→336B、crc32word 844→790B、memory16 499→451B。一方mixed4のO3では350→387Bへ逆転した。非引数local数もlocal側6→1、payload側1→9へ変わった。従って「追加local 0」は変換器の出力に限る性質で、最適化器やエンジンの内部コストを保証しない。

## 判定と残る課題

解析者はバイナリ・仕様・変換方式を知り、元のsource、分割点、seed、付属JSONを受け取らない。定数のstateだけ部分評価し、データ演算とload/store/divを順に残す通常のspecializerで、直線の等価処理を復元した。入力依存の元分岐を扱う解析器ではなく、その機能が必要なsourceも今回の変換対象外である。未知分岐は未対応として拒否する。

payload方式の解析費用は元より増えたが、O3/8分割では約1.19–1.68倍、0.46–1.02msに留まる。通常のlocal方式と同程度の増加であり、新規構成の保護上の上積みは確認できない。人間の解析時間や解析器開発費用は未計測。最適化で残ったことだけを耐性とは呼ばない。

不採用の理由は、(1)省サイズ化の核が標準機能の既知の利点、(2)最適化後の優位性が不安定、(3)定数stateの通常の追跡に対して局所退避方式と同程度の費用、(4)適用範囲が直線の小カーネルに限られること。一般CFGへの拡張、底部の不変stack値の除外、最適化器の癖に合わせた調整だけで新発明になったとは扱わない。新しい解析課題への具体的な差分が必要である。

[事前計画](plan.md)、[日本語草稿](paper-note.md)、[監査](../../results/invention-20261018/stack-cycle-v2/audit.json)、[別出力先での再現](../../results/invention-20261018/stack-cycle-replay-v1/audit.json)。有限テストを全入力の形式証明とはしていない。研究全体の「独自で有効な新方式」の確立は引き続き未達。
