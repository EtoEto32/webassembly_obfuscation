# E4の先行研究照合と、候補Fの型制約の予備実験

2026-10-12。独立研究の途中記録。新方式の採用・目標完了を示すものではない。

## E4：状態と例外を含む合成だけでは差分にならない

前回のE4は、メモリ更新やtrap時の状態も同値性の制約に入れた領域書き換えという仮説だった。今回、次の直接の関連記述を確認した。

- [Equality Saturation: A New Approach to Optimization, LMCS 2011](https://homes.cs.washington.edu/~ztatlock/pubs/eqsat-tate-lmcs11.pdf)：§6末尾のeffect tokenとFig.18、および§8のExceptions（PDF59頁）を確認。終了しない演算を消さないための効果表現、例外状態をheap summaryへまとめ、例外発生時の観測可能な状態を保存する説明がある。論文の全形式化や実装は今回検証していない。
- [Constantine, CCS 2021](https://download.vusec.net/papers/constantine_ccs21.pdf)：§2、§4.2.5、付録の正しさに関する段落を確認。実行する分岐とダミー分岐の状態を分け、ダミー側の除算などを安全に扱う。元プログラムがerror-freeであるという前提があり、任意のWasm trap保存と同じ保証だとは言わない。ソースを今回実行したわけではない。
- [Practical Data Location Obfuscation](https://www.microsoft.com/en-us/research/publication/practical-data-location-obfuscation/)：機関の要旨ページのみ確認。heapアクセスを間接化する関連資料だが、本文未確認なので方式の詳細や完全な重複は断定しない。

このため「副作用を考慮する」「両分岐を安全に実行する」という一般的な構成だけのE4は採用しない。前回のtrap後のmemory反例は検証条件として残すが、新しい難読化原理とは扱わない。

## 候補F：型を保つブロック分割・dispatcher配置

保護対象は制御の対応関係。非null参照を含む既存の計算を分割・並べ替える際、ブロック間の値受け渡しを一律のnullable localへ落とさず、型付きの境界引数で運ぶ方向を検討する。

これは前のGC dispatcher B2とは別の仮説である。B2は**制御状態の番号をGC型で表した**。Fでは制御状態は通常の整数のままでよく、**元プログラムが処理する参照値を、制御変換後もどの型で運ぶか**を問題にする。ただしこの違いだけで新規性は成立しない。

### 今回確かめた問題

非null参照localは、コード検証で初期化を確認できない地点では読めない。dispatcherの別周回で先に定義されるという実行時のstate不変条件だけでは、その検証条件を満たせない場合がある。

`probe.cjs`でアセンブラを通さず4本を直接生成し、Node 24.15.0 / V8 13.6.233.17-node.48に渡した。

|ケース|検証結果|実行結果|
|---|---|---|
|initialize-before-loop|受理|5境界入力で入力と出力が一致|
|flat-nonnullable|拒否|uninitialized non-defaultable local: 1 @+70|
|flat-nullable|受理|5境界入力で一致|
|typed-loop-payload|受理|5境界入力で一致|

flat-nonnullableはstate=0で参照を作り、次周回で使うが検証に失敗する。flat-nullableはlocal宣言だけをnullableにして受理される。typed-loop-payloadはループへ渡す非null参照を入り口でlocalへ束縛してから使う。

最後のケースは完全なdispatcherではなく、境界の型を運べることだけを示す。4例のサイズや5入力を比較して、難読化の強さ・速度・一般的な変換可能性を主張しない。新規性の証拠にも使わない。

### アセンブラによる修正を混同しない

Binaryen 133のwasm-disをflat-nonnullableへ適用すると、元の非null localをnullable localとref.as_non_nullで表したWATが出た。そのWATを再アセンブルしたバイナリはNodeで受理された。よってこの出力を、元バイナリの宣言をそのまま表す資料として使わない。

`*.binaryen-view.wat`はBinaryen経由の表現であり、直接生成した元バイナリとの同一性を保証しない。`*.roundtrip.wasm`と`roundtrip-hashes.json`はその確認記録。主たる検証結果は、直接生成した4本のSHA-256を含む`artifacts/results.json`に記録している。

## 最も近い既存方式と、確認すべき差分

- [WASMixer v1](https://arxiv.org/html/2308.03123v1)：§4.2 Stage I、Algorithm 2、Stage IIとAlgorithm 3を確認。分割前後のスタック値を新しいlocalsへ保存・復元し、ブロックを再構成する方式がある。今回確認した箇所からは、非null参照を含む型付き境界の計画は確認できない。ただし著者実装の最新版が非対応と断定する根拠にはしない。
- [Wasm function-references提案](https://github.com/WebAssembly/function-references/blob/main/proposals/function-references/Overview.md)：初期化追跡の説明とLocals/Instruction Sequencesを確認。提案資料には古い記述も残るため、今回の挙動の根拠は実行したバイナリとエンジン結果を併記する。
- [Tigress Flatten](https://tigress.wtf/flatten.html)：SplitBasicBlocks、dispatchの種類、call dispatchのグループ化を確認。分割、複数のdispatch方式、関数化自体は既知。著者実装の比較実験は未実施。
- [Bigloo/Wasm発表スライド](https://www.normalesup.org/~hgruniaux/projects/bigloo-wasm/slides.pdf)：検索抜粋のみでdispatcherとnon-nullable localの問題への言及を発見。全文・実装は未確認。今回発見した制約を新発見とは主張しない。

Wasm multi-valueによるphi値の受け渡し自体も既知である。前回のアフィン案と同様、それを使っただけでは採用しない。

## Fで必要な設計・実装

仮説の焦点は、**同じブロック分割・並べ替えの範囲を保ちながら、非null参照のnullable化や不要な保存・復元を減らせるか**である。単に難読化する範囲を減らして速くする比較では、この仮説を支持できない。

設計案（未実装）：

1. 入力ブロックごとに入り口・出口のスタック型、生存値、local初期化事実を求める。
2. 全辺を一律localへ運ぶ対照を作る。参照については検証可能なnullable化を行い、必要な型回復操作を明示する。
3. 同じ型付きpayloadを受け取れるブロック集合と、構造化したbr/loopで往来できる集合の両方を制約とし、dispatcher領域を選ぶ。
4. 値の位置の対応を各辺で明示し、型付き境界で受け渡す。単に型が同じという理由で異なる値を取り違えない。
5. 異なるpayloadをもつ循環や合流で計画が作れない場合は、そのケースを非対応または対照方式へのfallbackとして明示する。別の計算へ置き換えない。

これだけでは一般CFGの変換アルゴリズムは未定義である。最初の対象を単一入り口の構造化領域とし、循環・異なるlive signatureの扱い、nullable化を減らす計画の選択規則、最悪時の追加コストを定義する必要がある。CPS、SSA破壊、register coalescing、既存の部分的flatteningとの比較も未完了。

## 比較と棄却条件

- 通常版、localsを使う自作分割対照、F候補、型付き転送だけを無効にした版を同じ計算・分割点・並べ替えseedで比較する。自作対照をWASMixer著者実装とは呼ばない。
- 正しさは非線形算術、参照生成/読み出し、分岐、ループ、null処理・trapを含めて調べる。
- 解析者にはWasmのみを渡す。目的はブロック間の値と制御の対応の復元とし、元ソースの復元と区別する。
- 書き換え前の処理を復元する既存解析に対し少なくとも対照並みの効果があるかを確認したうえでコストを比べる。速くても同程度に制御を変換していないなら優位としない。
- 既存compiler loweringのそのままの移植に留まる、最適化後の差が消える、型情報の増加で復元が容易になる、同じ分割条件を維持できない、のいずれかなら新方式としての採用を見直す。

## 再現・現在の状態

```powershell
node probe.cjs
```

Node標準ライブラリのみ。乱数なし。直接バイナリ生成なのでWATの修正を経由しない。結果の再生成は`artifacts/results.json`と4本の元バイナリを上書きする。Binaryenの表示・roundtrip資料は予備確認時に別途作成し、元バイナリとして使わない。

E4の一般的な構成は重複が強く、採用を見送る。Fは型制約の確認と設計仮説までであり、採用未決定、変換器未完成、比較実験未実施。研究全体の目標は継続中。
