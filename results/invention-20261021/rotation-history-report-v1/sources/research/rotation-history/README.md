# 回転で観測位置を変える履歴型変換の検証

2026-10-21。固定回転の隠れた状態を出力履歴に置換する実Wasm変換器を作った。
**正当性の限定検証は成立したが、保護上の追加利得と独立した新規性が弱く、主発明には採用しない。**
入力依存回転への拡張については、一定長の実際の入出力履歴だけでは足りない条件と、必要な追加情報量を整理した。

[計画](plan.md)、[生成規則・意味保存・制限の論証](algorithm.md)、[先行研究との対応](prior-art.md)。
以前の[有限環残差フィードバックの構成的提案](../repository-assessment-20261021.md)は保持する。
本結果を研究全体の完了や、新しい主発明の成功に置き換えない。

## 実装範囲

sourceは`y'=rotl32(y,k) xor u`を入力wordごとに計算し、`y&M`を返す。
公開APIは`run(seed:i32,pointer:i32,length:i32)->i32`と固定1page memory。
history版は元のyを保持せず、回転した観測maskを追跡して生成した入出力履歴で実行する。
Wasmの固定幅rotate・wrap・bitwise演算とlocalを使うが、同じ意味を持つ他形式にも実装できる。

変換器は実際の`.wasm`をWABTで読み、全moduleが規定scan profileと一致することを確認して変換する。
任意のC/C++、任意のloop、非線形な状態更新、可変回転、外部call、追加の副作用には対応しない。
load順序、アドレスwrap、trap、公開memory不変を保持する。追加linear memoryは使わないが、履歴localの費用は増える。

保護目標は回転・観測規則の回復。解析者は方式と公開APIを知り、元ソース・生成manifest・係数表を受け取らない。
元から任意seedを受け取るこのAPIが、短い問い合わせによる復元を可能にしている。
固定seedしか受け取れないアプリへ、そのまま64回という回数を一般化しない。

## 正当性・回復・反例

4設定は `(k,M)=(1,0x7fffffff),(5,0xff),(16,0xffff),(1,1)`、履歴長は2/6/2/32。
同じ小さなscanの設定違いであり、4つの実アプリではない。

- source/history × 4設定 × raw/O3の16本と、historyから回復した8本、計24本。
- 各1,104入力、計26,496呼出しで値・trap・全64KiB memoryが一致。期待trapは7,776件、不一致0。
  境界560件、乱数512件、bit基底32件。WABTとNodeでvalidationを通過。
- 方式既知の回復はsource8/8・history8/8で成功。各64問い合わせで同じk/Mを得た。
  historyから生成した8本は元のraw binaryとbyte一致。元状態を消しても短い同等実装が戻った。
- 幅1..4の全回転・非零mask・seed・2入力列を計256,904列検査し、32bitの任意mask・64入力の512列も一致。
  これはPythonモデルであり、同数のWasm試験ではない。
- 24本のbyte再生成一致。別エンジンWABT interpreterの192 probeも一致。
- 有効なWasmである動的回転版とmemory上限変更版の2件を変換器が拒否。
- 入力依存回転はH=1/2/8/32/128/1024、raw/O3の計12対で、同じ過去出力・同じ末尾入力から次出力0/1へ分かれることを確認。
  追加のmask幅5/16/24/31では、隠れた各bitについてraw/O3の計104対でも確認した。

全Hに対する制限は実行数からの推測ではなく、[構成による論証](algorithm.md)による。
直近H個の実際の入出力以外に最低32-m bit相当の情報を保持する必要がある条件を示している。
任意の符号化状態を持つ変換まで不可能とはしない。全バイナリ・全入力の形式的同値証明も未実施。

## 費用

O3、128 word/call。各条件3 fresh Node process、各processの9 batch中央値をさらに3processで中央値化した。
1,024呼出しwarmup、5msを目安に最大2^18呼出しまで校正。JS呼出しloop・checksumを含み、compile/instantiateは含めない。
条件順はseed21102196で混ぜ、入力wordは固定seed21102195、呼出しごとに初期seedを変更した。

| 設定 | 履歴長 | source ns/call | history ns/call | source/history bytes |
|---|---:|---:|---:|---:|
| wide | 2 | 65.77 | 146.03 | 103 / 159 |
| byte | 6 | 63.74 | 339.19 | 100 / 274 |
| half | 2 | 64.19 | 88.09 | 101 / 141 |
| bit | 32 | 66.47 | 1979.86 | 99 / 947 |

履歴化は約1.37–29.78倍の実行時間。特にbyte設定のprocess中央値は321.89–457.09nsとばらつく。
性能の小差や他環境への一般化はしない。公開memoryは全条件65,536 bytes。
24 processの最大RSSは40,640–41,308KiBで、Node/JITも含む。変換は76.51–79.13msの単回記録で、
WABT入出力とprofileの再構築確認を含む。O3の処理時間は含まない。

回復本体はsource約0.166–0.299ms、history約0.175–0.345ms。
各binary1回の診断値であり、統計的な遅延差を主張しない。ファイル読取・compile/instantiateは別に約0.41–0.63ms。
公開問い合わせは両者とも64回で、履歴の増加に対応する問い合わせ増加は生じなかった。

## 結論の範囲

固定回転では局所状態を消した動作する変換が得られた。しかし、既知の可観測性・状態実現との技術的な近さがあり、
実行コストに見合う保護効果も示していない。入力依存回転で難しくする拡張には、単なる履歴長増加では解決しない正当性上の障害がある。
生成器・回復器・この成立条件を保存し、主方式には採用しない。新しい原理の発明が完成したという報告ではない。

## 再現

Python3.9標準library、Node24.15、WABT1.0.42、Binaryen133、Windowsを使用。
Node flagsは`--no-liftoff --no-wasm-lazy-compilation`。CPU固定・周波数固定なし。
WABTを`.tools/wabt-1.0.42/bin`、Binaryenを`.tools/binaryen-version_133/bin`へ置き、repo rootから実行する。
共有readerとしてisotope-swizzle/prototype.pyとconnectivity-elimination/prototype.pyへ依存する。
出力先は毎回新規directoryを指定する。

```powershell
python research/rotation-history/run.py results/rotation-new
python research/rotation-history/model.py results/rotation-model-new
python research/rotation-history/audit.py results/rotation-new results/rotation-audit-new
python research/rotation-history/performance.py results/rotation-new results/rotation-runtime-new
python research/rotation-history/prototype.py results/rotation-new/byte-source-raw.wasm results/rotation-custom.wasm
node research/rotation-history/inspect.cjs results/rotation-custom.wasm
```

生データは`results/invention-20261021/rotation-history-v1`、`rotation-history-model-v1`、
`rotation-history-audit-v1`、`rotation-history-runtime-v1`に保存。
[統合集計](../../results/invention-20261021/rotation-history-report-v1/summary.json)とsource snapshot・hash一覧も保存する。
初回snapshotの拒否対照名`changed-mask`は実際にはmemory上限変更であり、現行scriptでは名称を訂正した。
