# 同じ初期条件を作る一般SMT対照と費用

2026-10-24。[比較計画](guard-import-generic-plan.md)、[一般SMT実装](guard-import-generic.py)、[費用計画](guard-import-cost-plan.md)。具体storeの到達可能性だけを比べていた以前のCHC試験から進め、任意API列が一致する初期条件そのものを両方式に生成させた。

## 判定能力

等式lattice/copy写像を使わず、Store/Selectによる別意味論、一般的なWP、ForAll、Z3の量化消去と式の等価性検査を使う対照を自作した。[256契約](../../results/state-witness/guard-import-generic-v1/results.json)の全てでKと同じ初期条件を生成した。timeout・unknown・不一致は0だった。**「Kだけが条件を出せる」という能力上の優位は棄却する。** Whisk/PSyCO/WasmVerifierの著者実装を実行した比較ではない。

追加の[private table chain](../../results/state-witness/guard-import-chain-v1/manifest.json)も8条件で一致した。長さ1/8/32/96のcopy chainから公開tableへ値を送り、importが値を読んでから共通値へ上書きする。readありでは差が2/9/33/97 API後に出る。readなしでは最後の共通上書きで観測差が消える。Node/Wasmtime各564 API・548 import・16状態準備callでこの対照を再現した。pure reference tag呼出しは各290。人工的な遅延例で、独立したアプリや不具合の件数ではない。

chain scriptの初回起動は依存pathの誤りでdirectory作成前に停止した。`__file__`基準へ修正して実行した。algorithmの反例や性能測定には数えない。

## 費用

各方式3独立process、2 warmup＋5測定反復を逐次実行し、worker失敗・timeoutは0。[raw値と比較表](../../results/state-witness/guard-import-cost-v1/results.json)。以下はprocess中央値の中央値、共有WABT読取り/parseを除く条件合成時間で、遷移準備と出力用summary作成を含む。

|chain長|host read|K ms|一般SMT ms|K / 一般SMT|
|---|---|---:|---:|---:|
|1|あり|0.511|17.443|0.0293|
|8|あり|3.821|116.619|0.0328|
|32|あり|36.725|960.623|0.0382|
|96|あり|290.763|7,214.389|0.0403|
|1|なし|0.231|10.248|0.0226|
|8|なし|0.273|23.802|0.0115|
|32|なし|0.397|67.167|0.0059|
|96|なし|0.717|184.468|0.0039|

readありの人工例では、この一般SMT実装に対し約25–34倍速かった。これは既知の等式処理への特化の効果であり、新しい一般理論の根拠ではない。一般SMT側のSCC分解・incremental solver・式共有等を最適化し尽くした比較でもない。過去の具体BFSが有利だった単一storeの結果を撤回するものではなく、比較する出力課題が違う。

Windowsのprocess累積PeakWorkingSetは、記録されたcase境界でK側約22.55–26.50 MiB、一般SMT側約44.23–49.83 MiBだった。case順はseed付きshuffleで、peakをcase単体のメモリ量と解釈しない。共通harnessのため両方がZ3をloadしており、Kを単独配布したときの必要メモリでもない。Python3.9・単一Windows hostの結果で、第三者最適実装への優位を保証しない。

## 新規性への影響

### 一般対照を改善した追加比較

[計画](guard-import-cached-plan.md)を固定してから、一般SMTに式supportだけの置換、WP/QE cache、構文一致の早期判定、incremental solverを追加した。[256契約](../../results/state-witness/guard-import-cached-v1/results.json)と[8 chain](../../results/state-witness/guard-import-cached-chain-v1/results.json)は全て同じ条件、unknown/timeout/不一致0だった。Kの等式表現や正解条件をsolverに渡す変更ではない。

[同じ反復設計で再測定](../../results/state-witness/guard-import-cached-cost-v1/results.json)した6 workerも失敗0。readありについて、process中央値の中央値は以下となった。

|chain長|K ms|改善した一般SMT ms|一般SMT / K|
|---|---:|---:|---:|
|1|0.506|11.732|23.18|
|8|3.885|56.411|14.52|
|32|36.609|355.491|9.71|
|96|290.612|2,264.033|7.79|

速度差は約8–23倍へ縮んだ。先の25–34倍を一般的な方式差として引用しない。まだ自作の一般対照で、最適な式共有・SCC処理・変数表現まで比較したものではない。readなしは両者ともtrueを生成するが、一般SMT側の遷移準備費用が大きい。この差も新しい判定能力の証拠にはしない。

再現は上記cost commandへ `--baseline generic-cached` を加える。旧測定時のsourceは各結果directoryへ保存済みであり、改善前の結果を現sourceの結果へすり替えていない。

残せるのは、限定Wasm profileの等式条件へ特化することで、今回の自作一般SMT対照より小さい費用で同じ条件を得た、という実装上の結果である。既知のWP、等式抽象、量化消去の特殊化は独立した新原理ではない。修士研究としての対象差・説明可能な診断・効果を検討する材料にはなるが、自然な用途を示せていない[corpus結果](coverage-results.md)は別の弱点として残る。

## 再現

```powershell
python research/state-witness/guard-import-generic.py results/state-witness/guard-import-controls-v1 results/state-witness/local-import-generic
python research/state-witness/guard-import-chain.py results/state-witness/local-import-chain
python research/state-witness/guard-import-cost.py results/state-witness/local-import-chain results/state-witness/local-import-cost
```

[sourceのみの小artifact](../../artifacts/state-witness-import-v1.zip)にも一般対照と2engine実行を含めた。28 source/設定file、archive68,538 bytes、SHA256 `5c1e27faab6ac827dcd149899bf9a7e2654cdbd7774661e1c759cf4aaaa82dab`。[新directoryでの再現](../../results/state-witness/import-bundle-replay-v1/results.json)で39 binaryを同一bytesで再生成し、全チェックを通過した。反復性能測定、外部復元器、実アプリcorpusはこの小packageに含まない。
