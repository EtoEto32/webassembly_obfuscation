# 同期queueによる実体分割

入力はhostが管理するn個のshared WebAssembly.Memory、全memoryに存在する4B整列offset。保護目標は、異なるimportラッパーが同じbyteを共有しているのに「非alias」と受理する誤りを防ぐこと。

## 手順

```text
snapshot = 一度だけ読み取った入力memory配列
for each memory i:
    builtin Memory.buffer getterで実bufferを取得しbrandを検査
    offsetの現在値をatomic load
    waitAsyncを登録; async=trueを要求
labels = 未分類
for each 未分類の代表i:
    batchを作る
    count = notify-all(snapshot[i], offset)
    解決したwaiterの識別子を当該batchへ集める
    count個の通知完了と代表i自身の完了を確認
    完了した集合に同じlabelを与える
    deadline又は不整合なら判定不能として終了
return frozen(snapshot), frozen(labels)
```

成功時はn個の待機登録、k個のnotify、n個のPromise解決。JS全体の実行時間やengine内部queue探索が厳密にO(n)であるとの主張ではない。正常終了時に余分なcleanup通知はしない。異常終了時は未分類の自分のwaiterを通知で回収するため、静止前提が引き続き必要。

## 条件付きの正しさ

ECMAScriptのWaiterListはShared Data Blockとbyte offsetの組で決まる。同じoffsetへ各ラッパーから一度登録したwaiterは、同じ実体の場合だけ同じqueueに入る。外部のwait/notifyがなく、期待値の読取りから登録まで書込みがなければ全登録が成功する。代表のnotify-allは当該同値類の全waiterだけを解決する。返却件数と解決数の一致を確認してから次の代表へ移るため、非同期配送の遅れを非aliasと誤認しない。未分類の代表を順に選ぶ帰納法で全同値類を得る。

この論証は対象offsetの排他を仮定する。コードが排他を証明・取得するわけではない。異常の全種類を常に検出できるとは主張しない。deadlineは可用性上の制限であり、時間以内に応答しない相手を独立memoryと判定する用途には使わない。

実際に、Aの外部waiterとBへの外部notifyを組み合わせると、件数が一致したまま独立A/Bを誤結合した（[5試行](../../results/waiter-identity/interference-v1/results.json)）。件数照合は排他の代わりにならない。この前提を確保できない呼出し元へ安全な一般判定APIとして提供しない。

## 実装上の境界

bufferを普通のpropertyとして読む旧版は、own propertyで隠された場合に異なるmemoryを検査してしまった。修正版はbuiltin getterでbrandを確認する。検査済み配列を返し、検査後の入力配列変更との食い違いを避ける。これは標準的な境界実装であり発明の新要素ではない。

対象byteを変更しない一方、待機queueは変更する。対象に既存waiterがいればそれを起こす場合があり、無条件の非侵襲検査とは呼ばない。登録IDが信頼して得られるなら、この検査を省ける。実装上限n≤256、評価はn≤64のmemory32の小例。成功経路はNode/V8とSpiderMonkeyで比較した。

## 第二・第三設計: 並行更新への限定対応

`partition-concurrent.cjs`はloadとwaitAsyncの間の更新によるnot-equalを有限回再試行する。外部wait/notifyがなければ、登録成功後の通常のbyte更新はwaiterを解決しないので、成功した分割の条件付き論証は維持できる。ただし高頻度更新では登録成功が少なく、lock-free/wait-freeな進捗保証ではない。

`queue-free.py`はvalidation後の実binaryについて、単一共有memory import、数値run、閉じた命令許可集合に制限し、guestからwait/notifyやhost呼出しへ到達できないことを局所確認する。許可したstore/RMWは全て4byte。定数i32 baseはunsignedへ解釈し、memarg offsetを数学的整数で加える。動的baseは最初のpage全域へ拡大する。全書込み区間と交差しない4byte整列位置があれば、そこを登録に使う。offset加算をi32 wrapにしない。

hostは検査したbinaryの同一byte列をworkerへ渡す。証明対象はこのguestの操作だけである。未登録worker・別JSコード・後から渡すmemoryの扱いまで確認する仕組みではなく、全actorの管理を信頼しなければならない。単にサイドカーのhashを読んでもこの前提は成立しない。実装した評価domainは同じ1種類のwriter binaryを使う。

第三設計は「検査cellは書かれない」という元の前提を静的に具体化するもので、任意の競合を解決する新しい同期原理ではない。一般のdynamic-address writerでは候補なしとなる。

## 初期設計から三回目の改良: 一回の完了待合せ

`partition-ordinal.cjs`は同じagentの同じ同期jobで次を行う。

```
全wrapperにwaitAsyncを登録し、各Promiseへ識別子を到着列に加えるreactionを付ける
全wrapperへ順にnotify-allし、正の件数と代表indexを順に保存する
件数の総和がnと一致することを確認する
全Promiseの完了又はdeadlineを一度だけ待つ
到着列を保存した件数の長さごとに区切り、同じ区間へ同じlabelを付ける
各区間にその通知の代表が含まれることを確認し、捕捉配列とlabelを返す
```

外部wait/notifyがないなら、ある実体への最初のnotifyがその実体の全waiterを解決し、後続aliasへのnotifyは0を返す。同じagentの`NotifyWaiter`は直接Promiseをresolveする。事前登録したreactionは通知順にenqueueされ、`HostEnqueuePromiseJob`の順序保証により同じ実体の識別子が連続する。従って件数で区切った区間が実体の分割となる。n登録+n通知、一回のbarrier。群別版のn登録+k通知より通知は増える。

根拠は[ECMAScript §25.4.3.12](https://tc39.es/ecma262/multipage/structured-data.html#sec-notifywaiter)と[§9.5.5](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html#sec-hostenqueuepromisejob)。別agentへ送るgeneric jobには同じ順序保証を置けない。組込みを信頼し、登録・reaction設定・通知の途中でユーザーコードへ制御を渡さない範囲の論証である。

件数や代表所属だけで順序前提を検証できない。独立した4要素模型では、真の分割[0,0,1,1]に到着列[0,3,2,1]を人工的に与えると、代表検査を通って[0,1,1,0]と誤る。実エンジンでこの並替えを観測した結果ではない。順序保証を削って任意schedulerへ一般化できないことを示す。
