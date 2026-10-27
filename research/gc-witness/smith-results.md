# Rの強い対照と入力供給: 2026-10-27の採否

**現在のRを独立した新アルゴリズムとして修士研究の主テーマに昇格させる根拠は不足。** 小さな既存生成器修正で構築成功が増え、追加の入力深さ探索の効用は限定された。これは「研究として何も残らない」ことや、全ての用途で無効なことの証明ではない。生成器の盲点を具体的に確認する実装上の知見は得た。

## 既存生成器本体での比較

公式wasm-smith **0.262.0** crateを固定。archive SHA256は `d59ba1915172128cdc0ef870cae157e539882a9605e591ef36d0d2e9cbb73505`。別copyの`array.new_fixed`候補判定を、element operandがstackにない場合も長さ0で使えるよう変更した。差分は[smith-zero-seed.patch](smith-zero-seed.patch)。空array命令は既存仕様であり、新命令・新しい型理論を発明したものではない。

4型構成 × 64 seed × stock/zero = **512生成試行**。seedはPython `random.Random(seed)`から8,192 byte。型と`observe(ref null T)->i32`のABIをmodule_shapeで固定し、元の型を変更しない。max_functions=4、max_instructions=80、その他設定は保存したdriver sourceを参照。同じseedでも候補集合の変更により以後の命令分布が変わる。各出力の命令が一対一に対応する比較ではない。

関数本体の可変長array生成には長さ`&31`を両群で適用し、globalの定数式は既存設定`limit_arrays_in_const_exprs=true, const_expr_fuel=8`で制限した。前者は**意味を変える実験用変換**。上限を付けたプログラムでの結果であり、元の無制限プログラムの意味保存を主張しない。fuel=100,000、linear memory制限16MiB。後者はGC heap全体のメモリ使用量を意味しない。

主結果は`results/gc-witness/smith-v2/`。constructor/get/setの後にcounterを増やし、Wasmtime 50.0.1で`observe(null)`を呼んだ。constructorの成功は、その後trapやfuel超過になった実行にもあり得る。

|型|生成成功 stock / zero|構築が成功したseed stock / zero|対象get/setが成功したseed stock / zero|
|---|---:|---:|---:|
|nonnull自己参照array|62 / 62|0 / 24|0 / 0|
|nullable自己参照array|64 / 64|8 / 28|1 / 0|
|i32 array|64 / 64|10 / 27|0 / 0|
|nonnull自己参照struct（負の対照）|61 / 61|0 / 0|0 / 0|

各群の分母は64 seed。全体は生成成功502、生成エラー10。実行結果はreturned166、fuel171、trap165。compile/instantiation失敗は0。生成エラーは両群の同じ5条件で、制限された構成下の`Unstructured::choose`の空候補に関する失敗。エンジンの新規脆弱性とは数えない。

## 測定条件の訂正とbaseline確認

前版`smith-v1/`はglobal定数式を制限しておらず、12 instantiation失敗があった。allocation size too large / GC heap out of memoryを保存した。v2は設定を直した別試行で、v1を削除しない。

`smith-cap-controls-v1/`: array.new/new_defaultの長さ0,1,31,32,63,255,-1,INT_MINを検査。16条件で結果長`n&31`、成功constructor=1を確認。rawも実行したのは小さい非負12条件だけ。巨大なraw割り当てを実行していない。これは制限の校正であり意味保存テストではない。

`smith-baseline-v1/`: 無改変の公式crateを使う第三driverでstockを全256条件照合。251生成物はbyte一致、5生成失敗もstatus/reason一致。負の対照structではstock/zeroの61生成物が全てbyte一致した。これによりfeature-offを既存ツールの代理として使う範囲を確認した。

## 型付き参照を渡す追加試験

事前計画は[smith-input-plan.md](smith-input-plan.md)。同じ502 binaryの本体・計数器を再利用し、呼出し側だけ変更した。入力はnull、空array、element 0をたどる深さ1/2/4の鎖。scalar arrayには長さ1/2/4のゼロ値配列を用いる。構築不能structはnullのみ。

R生成器が非null値を返すprovider moduleを生成し、Wasmのimport/exportで型を保持して実対象に渡す。各呼出しでfresh instanceを使い、対象本体の成功操作だけを数える。provider自身の構築・読み出しは対象counterに入らない。これは固定深さの単純探索で、プログラムの要求を解析する新しい解法ではない。

`smith-input-v1/`: **2,022呼出し**。nullの502再実行は以前のstatus/constructor/accessと全て一致。別の手書きconsumerによる45校正条件は期待したtrap/成功access数と一致。

空arrayから深さ付き入力に変えて新たにaccessが成功した生成物は、**stockのnullable-array seed 50の1本だけ**。深さ1/2/4の全てで成功し、深さ2以上の追加効果は0。nonnull自己参照arrayは両群で依然0だった。手書きconsumerの成功は、ランダム生成器のcoverage改善に合算しない。

静的に対象get/setを含むarray生成物は380本中34本と少なく、失敗の原因は入力構造だけではない。診断例cycle-array seed 2 stockには大きい添字と無条件分岐の後のaccessがある。seed 50 stockは引数のarrayを読み、入力を非空にすると1回のaccessが成功した。これら数例だけから全失敗を分類済みとはしない。

## 新規性と有効性の判定

1. `worklist`自体の新規性・優位性は前回のmemo化DFS対照で示されていない。
2. 構築成功率の増加は既存生成器の局所的な候補条件修正でも得られる。R全体の独自効果とは数えない。
3. 入力を非null/非空にする効果は1本で確認できたが、単純な深さ1入力で足りた。アクセスpathの高度な計画が必要だったとはいえない。
4. 同一時間でのエンジンcoverage、既知bug回帰集合、実アプリGC型の適用率、複数エンジンでのこの追加試験、反復性能・GC heap実測は未評価。今回の単発generation時間を速度優位の根拠にしない。
5. 型に合う値を境界で使う一般構成にもWeaver等の先行研究がある。単なるWasm対応や部品の再命名を新規性にしない。一方、既知技法を使うだけで修士研究の応用・実証上の新規性まで否定するわけではない。

今後の候補を選ぶときは、値の存在から一歩進んだ、既存の単純対照で代替できない検証課題を先に定める。heapのalias/循環制約も候補だが、Koratやgeneralized symbolic executionとの重複を既に2026-10-24に指摘済みであり、調査なしに新案と呼ばない。

## 再現と監査

[smith-reproduction.md](smith-reproduction.md)を参照。全512条件の再生成、502 byte比較、502計数器再挿入、集計の再計算、upstream sourceのhashを`smith-audit.py`で確認する。監査値は`results/gc-witness/smith-audit-v1/report.json`。

監査は実行済み。502再生成、502計数器再挿入、8集計群、502 null再実行の保存値、公式crate内24file hashで不一致0。旧Rを含む`audit-v2/report.json`は16manifest・6,671file hash、965binary再生成、325 memo/worklist比較で不一致0。無関係なpaper/main.texについては、旧監査時点からのhash変更が検出された。今回の作業でそのファイルを編集しておらず、既存変更を保持した。研究dataの一致と無関係なファイルの状態を混同しない。

診断中、Binaryen133 wasm-disはnullable-array-50-stockに対し`invalid element segment index`でparseを拒否した。別validatorとWasmtimeでは受理されたが、原因の縮小・仕様確認はしておらず、独立したtool差異として扱う。未知bug発見の件数には入れない。
