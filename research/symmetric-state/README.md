# 対称状態縮約：設計、実装、反証

2026-10-18。**本候補を保護方式として採用しない。** 可変table方式とは別に、具体的な内部状態を捨て、対称式だけで計算する方式を実装した。3種類の多項式更新則と1つの32bit係数対照条件で、元の更新則をすべて復元できた。新規で有効な方式の確立を報告するものではない。

## 原理と最近接研究

元の反復は (x,y)←(f(x,y),f(y,x))、外部出力は x+y+7xy とする。変換後は s=x+y,p=xy だけを保持し、基本対称式へ変換した S(s,p),P(s,p) で更新する。元のx,yに戻す処理はない。

意味保存条件は α∘F=F♯∘α、h=H∘α。整数多項式の恒等式を確認してからWasmのmod 2^32演算へ落とす。multi-valueの2結果を使って同時更新する。privateなstepと規定形driverのみ受理し、外部からの途中状態観測、import、memory、trap、副作用、非対称出力などは対象外。任意Wasm用の変換器ではない。

[事前設計と文献の確認範囲](design.md)。数学的な対称式への変換、抽象解釈、データ表現による難読化は既知。PEPM 2012のGiacobazzi/Jones/Mastroeniによるデータ型難読化が近接研究である。今回の差は元データを復号せず最終観測だけを保存する具体規則だが、その差が新規な難読化原理であることは確認できていない。Wasmの整数意味論と多値返却を利用するものの、他の形式にも実装できるためWasm固有性も弱い。

## 攻撃と実測結果

攻撃は公開されたS,Pから z²−S(x+y,xy)z+P(x+y,xy) を作る。整数への持上げが元の式に一致すれば、これは恒等的に (z−f(x,y))(z−f(y,x)) であり、因数から更新則を得られる。原バイナリや生成時manifestは攻撃入力にしない。事後監査でだけ元の更新則と照合する。交換までの復元を成功とすることを事前に固定した。

大きい係数では32bit wrapにより整数因数分解が失敗した。この失敗を保護成功にせず、f=x²+ay+cという族に対し、Sの係数からaと2cを取り出し、cの2候補をPとの剰余恒等式で検査した。この限定的なmodular攻撃でも更新則が戻った。任意の高次数・大係数多項式に対する完全な解除算法ではない。

確定結果は [再現実験ディレクトリ](../../results/invention-20261018/symmetric-state-reproduction-v1/manifest.json)。

|検証|結果|
|---|---|
|条件|4 kernel設定 × raw/O2/O3。wideはquadraticの係数対照で、4つの独立アプリではない|
|バイナリ|元12、変換12、各変換から直接解除12、計36|
|正当性|各1312入力（境界288＋乱数1024）、計47,232入力条件。不一致0、予期しないtrap 0|
|validation|WABT validator、Node WebAssembly.validateとも通過|
|更新則の復元|12/12。小係数9条件は整数因数分解、wide 3条件はmodular係数復元|
|攻撃構築時の実行問い合わせ|0。解除後の差分試験は別|
|事後の式検証|元と復元の更新則を交換までmod 2^32で照合し12/12一致|
|範囲外の拒否|非交換同変step、元の非対称出力、step外部公開、変換後の出力変更の4件を拒否|
|再現|別の完全ビルドで36本のhash一致、47,232入力条件で再び不一致0|

全入力に対するバイナリ同値性をテストだけで証明したとはしない。変換の多項式恒等式、driverの限定的認識、有限差分テストをそれぞれ区別する。解除器も特定のループ構造と入口・出口を検査する実験用実装で、任意の最適化済みWasmに完全対応するものではない。

## 非一意性だけでは保護を説明できない

[audit.json](../../results/invention-20261018/symmetric-state-reproduction-v1/audit.json) に小さい語幅の全状態列挙を保存。8bitでは65,536状態が22,016個の(s,p)へ写り、一つの(s,p)に最大16状態が対応した。

32bitでも x=65536k,y=−x、0≤k<65536 はすべて(s,p)=(0,0)となる。この65,536通りを直接検査した。単なるx,yの交換以上の曖昧さがあるが、上記の更新則復元は成功した。状態snapshotの曖昧さを、公開コードと公開入力を持つ解析者に対するアルゴリズム秘匿と同一視してはいけない。

## 費用

[全36条件の比較表](../../results/invention-20261018/symmetric-state-reproduction-v1/comparison.md) と [全反復値](../../results/invention-20261018/symmetric-state-reproduction-v1/performance.json)。Node 24.15.0 / V8 13.6.233.17-node.48、Windows、Core i9-11900K。各条件を別プロセスで実行し、81,920呼出しのウォームアップ後に7×16,384呼出しを測定。呼出し境界のJS費用を含む。条件順を固定seedでシャッフルした。

O3の変換版は元に対しバイナリサイズ約1.37–1.62倍、時間中央値比約1.23–1.32だった。ただし各条件1プロセスの短時間測定であり、強い統計的結論や他の環境への一般化はしない。RSSはNode全体のprocess peakであり、Wasmだけのメモリ費用とは区別する。線形memoryなしをメモリ費用0とは呼ばない。変換・解除時間はツール入出力を含む単発診断値。

## 再現方法

Python 3.9、SymPy 1.13.3（.tools/nonbijective-residual-cas）、WABT 1.0.42（.tools/wabt-1.0.42/bin）、Binaryen 133（.tools/binaryen-version_133/bin）、Node 24.15.0。既存の共通WAT parserは research/observation-synthesis/transform.py。依存SymPyの別配置は現在のスクリプトを調整するか通常のPython環境へ同版を導入する。WasmツールrootはWASM_TOOLS_ROOTで変更可能。

リポジトリrootから未使用の出力先を指定する：

```powershell
python research/symmetric-state/probe.py build results/symmetric-new
& 'C:/Program Files/nodejs/node.exe' research/symmetric-state/check.cjs results/symmetric-new
python research/symmetric-state/audit.py results/symmetric-new
& 'C:/Program Files/nodejs/node.exe' research/symmetric-state/measure.cjs results/symmetric-new
python research/symmetric-state/report.py results/symmetric-new results/invention-20261018/symmetric-state-v4
```

単独CLI：`probe.py encode INPUT.wasm OUTPUT.wasm`、`probe.py attack INPUT.wasm OUTPUT.wasm`。生成物とログは新規保存のみ。report.pyは今回固定した36本の再現専用の比較器である。

v1は最適化後のstack形式未対応、v2はその対応、v3は入口・出口検査とwide条件追加、v4は出口式の交換則への対応。いずれも同じ変換原理であり、異なる候補や設計上の成功例には数えない。最終的な再現実験が本文数値の根拠。v4の初期性能ログはXOR集約が反復数の偶奇で零となる弱い消費方法だったため、引用する性能値はrolling checksumへ修正した再現実験のものだけを使う。

## 残る課題

新規性も有効な保護効果も成立していない。大係数・高次数へ範囲を広げるだけでは、既知の多項式符号化との差を作れない。次に進むには、snapshotの非一意性ではなく、公開された更新則を含む解析タスクでの差を示す機構が必要。研究全体は未完了であり、この反証を新方式の完成に置き換えない。
