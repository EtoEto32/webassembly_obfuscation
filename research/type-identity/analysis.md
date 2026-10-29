# 型identityの追加機構が寄与したか

2026-10-19。主結果はv3、性能はperformance-v2、別engineはverify-v2。古い測定を加えて標本数を増やさない。

## 原因の確認

raw binaryにはG×(N+D)個のstruct型宣言が実在する。Binaryen readerは同値groupを統合するため、disassemblyではN+D個になる。O3出力binaryもN+D個である。D個の兄弟型は残るが、実際の状態tokenは元の状態と同じ有限集合に属する。型定義と参照検査の対応を読めば、この集合へ整数ラベルを付けられる。

その後の解除はGC allocationを型ラベルへ、`ref.test`をラベルの等値比較へ変える。この操作に元の遷移表や生成seedは不要で、型同値の曖昧さを探索する必要もない。主GC系30条件すべてでこれを実行し、回復したWasmを実行検証した。原型の名前や元packed-table命令列まで復元したとは主張しない。

group系24条件のうち22は、通常GC対照を解除したbinaryとbyte一致する。残るrandom16/O3の兄弟型32の2条件では、O3が未使用globalを消した後も残る型検査の整数定数が異なる。差分で確認した定数はいずれもallocationされた型ラベルの集合外であり、type numberingの違いである。これらも差分検査は通る。byte非一致を解除失敗や保護成功にしない。

## 費用の解釈

[比較表](../../results/invention-20261019/type-identity-report-v1/comparison.md)は42条件それぞれ3個のfresh processを含む。各processはcompile/instantiateを別計測し、10,000回warmup後に10,000呼出し×9回測る。順序はseed固定でshuffle。入力は同じLCG列、n=31。ホストloopとchecksumを含み、Wasm本体だけの命令時間ではない。全条件のchecksumをカーネルごとに照合した。

group数8・兄弟型32の通常GC対照比（3kernel×raw/O3の6組）：実行0.956–1.040、reader込み0.905–1.047、Python後処理1.090–1.245。後処理に小さい費用増があることは否定しない。ただし型定義を読む量が増えた効果を含み、reader込み時間は外部ツールの起動が支配的である。既存の正規化を越える解析課題の増加を実証していない。解析器の初回開発工数、人の理解時間、NotDec本体の性能は測っていない。

binaryサイズは同じ比較で1.126–3.410倍。全targetのlinear memoryは0。GC tokenは宣言上N個、余分な兄弟型のinstanceを作るわけではない。O3が消すglobalもある。Node全processのpeak RSS中央値は39,704–40,376KiB。GC objectの物理サイズだけを独立測定した値ではない。変換時間は105.3–132.1msの単回観測で、source検査・一時的な再構成・外部ツール起動を含む。compile/instantiate値は比較表と生値に保存した。

最大group数・兄弟型数を増やした追加12条件は正当性・対応範囲の検査であり、性能測定対象に加えていない。うち4条件は単一状態の定数関数なので、非定数8条件と分けた。

## 実装の不備と修正

- probe-v1：source検査で、expression専用の既存readerをloop入りscannerへ使い`br_if`を未対応として止まった。通常のmodule parseと全体照合へ修正。
- main-v1：O3がglobal/localの型を具体的な非null型や`struct`へ狭めた際、解除器が未対応として停止。型を整数へ写す規則を拡張しv2で完走。
- null-v1：allocationを持たない別fixtureは既存の対応範囲チェックで拒否された。次に、空struct globalを含むnullable local fixtureを用いたnull-v2で、元は1、解除後は0となる反例を得た。i32 localの既定値0をnullの表現−1へ初期化していなかったためである。明示初期化を加えnull-v3は1/1。主fixtureでは必ず先に代入するのでv2には不一致が出なかったが、修正後に主v3・別engine・性能を再実行した。
- 初回のshellによる小probe作成は引用符の構成を誤って実行できなかった。独立したPythonファイルへ切り替えた。Wasmの性能・耐性の結果ではない。

これらは自身のツールの非対応・誤りであり、保護機構が解析に勝った事例ではない。v2以前の結果・source snapshot・反例は残した。最終監査では、現在の実行コード、replay snapshot、42 targetと42回復のhashを照合した。

## 採否

型同値性に関する整合が必要なことは実験で確認できた。しかし仕様上の標準的な型正規化で追加構造の多くが消え、残りは有限の型ラベルへ射影できる。形の同じ型が多いこと、同じ型が複数の番号で現れることは、それ自体で追加の意味解析課題にならなかった。

最大のReject理由は、既知の型ラベル化・state表現の移植からの技術差が弱く、追加解析費用もmetadataの増量と区別できない点である。原理の異なる探索枝としては実装・評価を終えたが、新しい主発明とはしない。次は「標準readerがすでに計算する同値類」をそのまま保護の根拠にする案を避ける。未知の機能・tool非対応だけを狙う方向へは進めない。
