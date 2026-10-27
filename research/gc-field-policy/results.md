# Oの初期結果と新規性の留保

2026-10-26。18個の人工consumerと、private値だけが異なる2個のlibraryを作成した。Node 24.15.0/V8 13.6とWasmtime Python 50.0.1で各36組を実行し、返値・trap・owner側のstruct/array値の変化が全行一致した。[probe-v3](../../results/gc-field-policy/probe-v3/summary.json)。v3は独立した期待返値との照合も加えた。検査なしの実行は挙動確認用であり、受理loaderを迂回した脆弱性攻撃の実施ではない。

|検査方式|受理数 / 36|禁止操作を含む入力の誤受理 / 24|この試験では安全な入力の拒否 / 12|
|---|---:|---:|---:|
|検査なし|36|24|0|
|module-local型index一致|32|20|0|
|canonical型の完全一致|28|16|0|
|型の継承関係も閉じるclosure|10|0|2|
|全aggregate操作拒否|4|0|8|

型番号変更・同値型の複製を含め、parent型を介したfield access、consumer新規subtypeの生成、constant expression内の生成、array.copyのsource read / destination writeが重要だった。closureは今回の禁止操作を受理しなかったが、同じparent型の安全な新規objectを読む2条件も拒否した。18個のsourceを多数の独立実アプリとして数えない。

追加したNode loaderは同じbyte列を検査してからinstantiateし、10条件を実行、26条件をconsumer instantiation前に拒否した。検査なしで動くことと、実際に受理を止めたことを分けている。返値だけでなく、秘密fieldが77へ書き換わる制御例も2engineで確認した。

## この段階で支持されること

構造的な型同値性と明示的subtypingを使えば、runtime命令を追加しない保守的なfield policy checkerを作れる。単なる型indexやcanonical完全一致だけの対照には不足がある。これはこの試作の事実であり、既存製品に同じ不具合があるという報告ではない。

一方、型canonicalizationはwasmparserの既存実装、継承関係へのpermission伝播は既知のアクセス制御の原理である。**現状を「新しい型安全性アルゴリズム」として修士の主テーマに決定するには弱い。** 受理の制約・合成条件・精度の新しい知見に発展する可能性はあるが、まだ仮説である。

## 最も近い先行技術

[Wasm Type Imports and Exports提案のPrivate Types節](https://github.com/WebAssembly/proposal-type-imports/blob/main/proposals/type-imports/Overview.md)は、clientによるcastからの内容露出と逆方向の値偽造を明示している。従ってOの問題自体を新発見とはしない。private type提案は型/実行モデルを拡張する方向、Oは既存engineに渡すmoduleを制限する方向で、前提が違う。

[GC issue #215](https://github.com/WebAssembly/gc/issues/215)は2021年のstrong encapsulationの議論。査読論文ではない。[SecWasm](https://doi.org/10.1007/978-3-031-22308-2_5)はSAS 2022のhybrid IFC。Oは情報流全般を保証せず、SecWasmの代替ではない。JVM access checkingやproof-carrying codeとの原理的重なりを解消したわけでもない。

関連する実際の設計問題として、[Binaryen issue #8754](https://github.com/WebAssembly/binaryen/issues/8754)では、`--closed-world`時に外部で生成されたpublic型の値が入ってくる可能性と最適化仮定が議論されている。本文を読んだが、closed-world最適化に対してこのcheckerが十分な保証を与えることは未実証。現在のpolicyはfuncrefの生成・呼出しを制限しないので、そのまま`--closed-world`の全条件を証明する用途には使えない。

次は(1) private field enforcementのより近い先行研究、(2)実際のGC compiler/moduleでの必要例、(3)安全なconsumerを拒否しすぎない条件、(4)未対応命令・継承・再帰型に対する独立検査、(5)検査費用を調べる。受理できた人工例だけで主テーマへ昇格しない。

## 境界検査の追加

[boundary-v1](../../results/gc-field-policy/boundary-v1/summary.json)は9組を2engineで照合し、不一致0。recursive group全体の一致/不一致、packed fieldのsigned/unsigned読出し、array.new_default/new_data/init_data、空policyを検査した。未対応feature4件・不正policy3件は通常の拒否として区別した。同型arrayを別ownerが独立に使う安全な例も拒否したため、型だけでownerを区別できない限界は実例で確認された。

## 部分公開データ処理での反証

[workload-v2](../../results/gc-field-policy/workload-v2/summary.json)：5方式×3行数×2アクセス順×2pass数×2engine×3process = **360 process**。12warmup、11測定、固定seedの順序shuffle。各返値をPythonの独立計算と照合して全て一致。これは人工の単一処理系を条件変更した実験で、360個のアプリではない。

65536行、連続scan、1passの中央値（ms）：

|方式|Node|Wasmtime|
|---|---:|---:|
|shared + O|0.0565|0.4828|
|Wasm accessor関数|0.2518|0.8493|
|毎回public部分をcopy|0.3145|8.5239|
|producerでpublic/privateを分離|0.0529|0.4788|
|元layoutを維持しpublic viewを増分同期|0.0567|0.4903|

最初のv1は全件copyという弱い対照だったため、v2で既知の増分viewを追加した。**sharedは強い単純対照に対して明確なruntime優位を示さなかった。** sharedは元layoutを保ちpublic viewの追加を省けるが、cached-projectも元layoutを変えずに使える。差は補助viewのメモリと更新箇所管理の条件へ狭まる。

同条件のwhole-process peak RSSはsharedがNode44.35/Wasmtime30.20 MiB、cached-projectが47.70/32.21 MiB、splitが42.93/29.05 MiB。GC object単体の正確なサイズではない。バイナリはlib/client各数百byte。checker内部時間（validationを含む5比較mode全部）は4方式のv1診断で0.62–0.81ms、CLI往復8.45–9.75ms。これは1回の小入力診断でありscalabilityや安定した統計値ではない。run測定は受理後で、setupには別途検査・compile費用がある。

[workload-contract-v2](../../results/gc-field-policy/workload-contract-v2/summary.json)では、5方式×3行数×3private値=45組/engine、495計測API返値/engine、1965private値/engineを照合。秘密値を変えても公開集計が一致し、private値が保持された。これは有限差分検査で一般的noninterferenceではない。private値を返す関数を直接importする変種はGC checker単体では受理され、**別のimport allowlist**で両engineとも拒否した。機構の保証を混同しない。

[link-v3](../../results/gc-field-policy/link-v3/summary.json)は既存Binaryen 133のmerge/O3も追加。24process、全返値一致。65536行1passのmerge+O3はNode0.0709/Wasmtime0.6212msだった。raw accessorより速いがsharedと同一性能にはならなかった。静的link可能という追加前提があり、全hostを対象とした代替ではない。初回の未対応feature出力と2回目のdriver errorは別記録に残し、主測定から除外した。

## 更新した採否

[近接先行技術](prior-art.md)を加味し、**新しいアクセス制御アルゴリズムを主張する修士主題には現時点で推奨しない**。PCC/JVM/RichWasmとの原理的重なりが強く、通常のデータ分離や増分viewにも勝てていない。Wasm GC上でのpolicy合成の健全性・精度の限界を体系化する実装/評価研究としては残せるが、自然な既存compiler/pluginでの必要性と新しい知見が未実証である。

これ以上、同じ人工例だけを増やして主題確立扱いにはしない。型canonicalization・継承アクセス制御・incremental view maintenanceを新発明に数えず、次の原理を検討する。
