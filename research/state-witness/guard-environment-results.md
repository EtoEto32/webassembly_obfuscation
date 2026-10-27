# host書込みを許す契約の実測

2026-10-24。[事前計画](guard-environment-plan.md)、[アルゴリズム](guard-environment.py)、[限定論証](guard-environment-proof.md)。従来の「呼出し間に外部書込みなし」という契約を、公開resourceへの任意の共通書込みを許す契約へ広げた。

## 元exportだけの小例

[6 module・36契約](../../results/state-witness/guard-environment-controls-v1/manifest.json)で条件を比較した。元exportで観測できる32契約はNode/Wasmtimeで一致し、各engineのguest診断274回、状態準備272回、host cell書込み48回となった。private store全体の観測を要求する4契約は元exportでは検証できず、実行済みに数えていない。公開部分をmask前に修復する対照は、host書込み後も一致した。

さらに、初期条件への閉包だけでは不十分になる[2 module・4契約](../../results/state-witness/guard-environment-interleave-v1/manifest.json)を作った。公開table P、private tableのHとXを持つ。`arm` は両側でPをHへcopyし、segmentの寿命差によって片側だけ別segment Cをdropし、両側ともtrapする。`publish` はCが生きた側だけHをPへcopyしてtrapする。外部書込みなしなら、最初はCが両側とも生き、寿命が分かれる時にはH=Pが成立するので、全ての共通初期storeで公開観測が一致する。

ところが `arm → hostがPをnullへ変更 → publish` では、片側だけPがHへ戻る。自動合成した最短反例は3操作だった。修復版ではpublishの前にPをHへcopyし直し、差が消える。trap終端契約ではarmの後に続けられない。4契約のNode/Wasmtime実行は各12診断call・8準備call・4cell書込みで一致し、[別array式44義務](../../results/state-witness/guard-environment-interleave-check-v1/results.json)はUNSATだった。これは手書きの機構反例であり、実製品不具合ではない。

## 固定済み混合コーパス

以前生成した96 module・576契約・2,304初期storeを変更せず使った。[新条件と反例](../../results/state-witness/guard-environment-corpus-v1/manifest.json)で、外部書込み禁止時の結果を全件再現し、新条件が旧条件より弱くならないことを確認した。

|比較|初期store数|
|---|---:|
|旧契約も新契約も一致|1,507|
|旧契約では一致、新契約では反例あり|339|
|旧契約も新契約も反例あり|458|

新しい797反例のうち339列がhost書込みを1回含み、他458列はguestだけで区別できた。最大列長は3操作。旧契約で条件付きだった196契約のうち161は、新契約では満たす初期storeがなくなった。残る35契約はprivate cellの条件を持つ。元から無条件一致だった契約が崩れる例はこのコーパスにはなく、その境界は上記interleaveの追加例で別に示した。

[Node](../../results/state-witness/guard-environment-node-v1/results.json)と[Wasmtime](../../results/state-witness/guard-environment-cross-v1/results.json)で、それぞれ150,360 guest API呼出し・14,482 host cell書込みが整合した。共通trapで13,622列を終了した。Wasmtimeのtable照合では別途82,084回の純粋定数関数呼出しを使った。初期storeの生成区分は旧コーパスから継承しており、全て無作為入力とはしない。肯定例の有限実行を全入力証明とは扱わない。

[別array式と普遍量化による検査](../../results/state-witness/guard-environment-check-v1/results.json)は576契約、2,654義務がUNSAT、unknown0だった。host入力を整数変数で普遍量化し、copy写像の閉包実装をそのままoracleには使っていない。parserと限定profileは共有している。

## 汎用solverとの比較

[CHC/Spacer](../../results/state-witness/guard-environment-chc-v1/results.json)へ共通host入力の遷移を追加した。各契約の保存済みsample index2を1個ずつ選び、576 query中186 SAT・390 UNSAT、timeout/unknown/error0、Kと全件一致した。初期状態を固定する到達可能性判定であり、任意初期storeの条件合成とは出力が異なる。環境入力を加えても汎用solverでは解けないという優位は得られていない。全queryのSMTを保存した。時間値は単発の診断値で、正式な性能比較には使わない。

## 実復元器への適用

[追試計画](guard-environment-external-plan.md)。4 fixtureを8変換条件で検査した。1byte/4byteの非空data、先頭を修復する対照、長さ0のinit対照である。元/中断点追加/無移行変換で公開結果は一致した。

初回[v1](../../results/state-witness/guard-environment-external-v1/results.json)ではmigrate8復元・Weave16復元の全てが一致した。migrateは一つのpollだけを持ち、その位置からの再開でdropを再実行するため、この配置では寿命差が残らなかった。[Wasmtimeのv1](../../results/state-witness/guard-environment-external-cross-v1/results.json)も8復元・診断差0となった。

loopの後にもdropを置く別の元入力を作った[v2](../../results/state-witness/guard-environment-external-v2/results.json)では、両復元器とも16復元・未到達4、entry差0・診断前guest memory差0だった。migrateでstop1から復元しhost書込みを行う場合だけ、1byte/4byteの二つの診断が異なった。書込みなし、stop0、修復対照、長さ0対照は一致した。Weaveは16復元全て一致した。[Wasmtimeのv2](../../results/state-witness/guard-environment-external-cross-v2/results.json)も16復元・診断差2を再現した。

これは既知の寿命復元差に対する二つのサイズ対照であり、二つの新しい独立bugではない。診断は1回で終えるのでtrap後再入を使っていない。ただしmigrateの非entry API利用は実験adapterであり、作者による保証は未確認である。作者確認済み脆弱性としては数えない。観測したのは元guestの1page prefixで、Weaveのprivate suffixは含めない。

この非entryという限界に対し、後続の[entry内host import実験](guard-import-entry-results.md)を別入力として実施した。元entryだけで、host traceと最終trapが一致するのに公開memoryが異なる同じサイズ対照を確認した。ただしimportを含む後続入力は現行解析器の対象外であり、自動条件合成の受理例には数えない。

## 再現

出力先は未作成のdirectoryを使う。

```powershell
python research/state-witness/guard-environment-controls.py results/state-witness/local-env-controls
python research/state-witness/guard-environment-interleave.py results/state-witness/local-env-interleave
python research/state-witness/guard-environment-corpus.py results/state-witness/guard-holdout-v1 results/state-witness/local-env-corpus
node research/state-witness/guard-environment-replay.mjs results/state-witness/local-env-corpus results/state-witness/local-env-node
python research/state-witness/guard-environment-cross.py results/state-witness/local-env-corpus results/state-witness/local-env-node results/state-witness/local-env-cross
python research/state-witness/guard-environment-check.py results/state-witness/local-env-corpus results/state-witness/local-env-check
python research/state-witness/guard-environment-chc.py results/state-witness/local-env-corpus results/state-witness/local-env-chc
```

外部比較は固定済みの復元器実行ファイルを必要とする。[外部比較の環境](guard-external-results.md)を参照。

```powershell
python research/state-witness/guard-environment-external-inputs.py results/state-witness/local-env-external-inputs --tail-drop
node research/state-witness/guard-environment-external.mjs results/state-witness/local-env-external-inputs results/state-witness/local-env-external
python research/state-witness/guard-environment-external-cross.py results/state-witness/local-env-external-inputs results/state-witness/local-env-external results/state-witness/local-env-external-cross
```

成果は環境契約の限定拡張、初期条件だけでは不十分な反例、実測差の切分けである。普遍量化、環境遷移、関係固定点という一般原理の新規性は主張しない。
