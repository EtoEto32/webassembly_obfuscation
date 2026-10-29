# Hの先行性と請求項たたき台

2026-10-24。**新規性・進歩性の確立は未達**。既存仕様から直接導ける部分を除いて評価する。

|一次資料|実際に読んだ範囲|Hとの関係|
|---|---|---|
|[ECMAScript現行draft](https://tc39.es/ecma262/multipage/structured-data.html#sec-atomics.waitasync)|25.4.3.5 GetWaiterList、25.4.3.12–14、25.4.10 notify、25.4.16 waitAsync|block+offsetのqueue、登録と通知件数の根拠。既存標準の通常用途を利用する。ページは2027 draft表示、確認日は上記日付。初出年はこのページから推定しない|
|[ECMAScript Shared Memory and Atomics提案](https://tc39.es/proposal-ecmascript-sharedmem/shmem.html)|§6.3.2.5 GetWaiterListとwake関連。全文精読ではない|blockとoffsetに対応するagent共通queueは先行。Hが発明した概念ではない|
|[Using WebAssembly threads from C, C++ and Rust](https://web.dev/articles/webassembly-threads)|shared memory、workerへの送信、atomicsの説明|WebAssembly.Memoryをworker間で共有することは通常機能。clone後の共有を新発見とはしない|
|[US8392661B1 Managing cache coherence](https://patents.google.com/patent/US8392661B1/en)|書誌、請求項1–11、検索で得たfutex周辺|Christopher D. Metcalf、優先2009-09-21、公開2013-03-05。主請求はcore間のcache配置とmigration。読了請求項でHの全構成は確認せず。ただし関連family全体と抵触の判断は未実施|
|[US8327187B1 Low-overhead operating systems](https://patents.google.com/patent/US8327187B1/en)|書誌と請求項1–14。全44項の精読ではない|Metcalf、優先2009-09-21、公開2012-12-04。読了項はOS taskの無効化要求と他processへの影響による許可。futex/alias記載の検索一致だけでHと同一請求とはしない。familyと残りの項は未精査|
|[TC39 meeting notes, 2021-12-14](https://github.com/tc39/notes/blob/main/meetings/2021-12/dec-14.md)|SharedArrayBufferのidentityに関する議論|別wrapperでも実体を共有する問題意識自体が先行する|
|[US8799914B1 Managing shared resource in an operating system by distributing reference to object and setting protection levels](https://patents.google.com/patent/US8799914B1/en)|書誌、請求項1–32、multiple aliasingの説明|Metcalf、優先2009-09-21、公開2014-08-05。参照配布・OS protection levelによる資源許可を請求し、説明中では仮想address aliasを考慮する排他を扱う。読了項にHのwaiter cohortによる観測分割全体は確認しなかったが、family全体・進歩性・抵触の判定ではない|

検索語は`SharedArrayBuffer identity waitAsync`、`same backing Atomics.notify`、`futex aliasing patent`、`memory identity wait notify`等。全文・全family調査ではなく、該当結果が出ないことを新規性の証明としない。論文として直接同じ分割アルゴリズムを提案する資料は現検索では特定できていないが、未発見であるだけである。

最も強い反証は仕様そのもの。二つのwrapperのqueueが同一かを見る一対一の方法は直接導ける。全waiterを先に登録し、通知で同値類を回収する改良が、通常のbatch化以上の進歩性を持つかは不明。Wasmへの適用だけを差分にはしない。

## 技術請求項案

**H1**: WebAssemblyへの共有メモリの結合を検査する方法であって、複数の共有メモリオブジェクトを捕捉し、前記各オブジェクトの同一offsetに内容を変更せず識別可能な非同期待機を登録し、未分類の一つのオブジェクトに通知を発行して、通知が返す件数と解決した待機の集合を照合し、前記集合に同じ共有実体識別子を割り当てる処理を繰り返し、得られた共有実体関係により前記捕捉したオブジェクトの非alias結合条件を判定する方法。

**H2**: H1において、通知処理の完了数を満たす前に次の集合へ進まず、deadlineによる未完了を非aliasと判定せず受付を保留又は拒否する方法。

**H3**: H1において、入力の通常propertyを介さず組込みgetterで実bufferを取得し、判定に用いた同じオブジェクト配列を後段のmodule結合に使用する方法。

**H4**: H1において、当該offsetの外部待機・通知・変更がない期間に検査を行い、n個の対象についてn個の待機登録と共有実体数k個の分類通知で分割を得る方法。

H1–4は技術構成の記録であり、権利化可能との結論ではない。最大のReject理由は「仕様既知のqueue同一性検査を一括化しただけ」である。正しいhost ID registryが既にある環境では必要性もない。

外部干渉の追加実験では、通知件数と完了件数が一致しても別実体を同一に誤分類した。H2の照合だけでH4の排他を検証できるとは主張しない。現段階で主特許候補へ格上げしない。

## 改良後の追加構成案と反論

**H5（検討案）**: H1において、結合対象の共有memoryへアクセスする管理下guestの実binaryを検査し、待機・通知操作と未検査host呼出し経路を拒否するとともに、保守的な書込み範囲の外にある共通offsetを選定し、検査済みの同一binaryを使用する実行domain内で前記分割を行う方法。

H5の限定実装では1種類のwriter、閉じたopcode集合、定数base/未知baseの単純な範囲解析を使う。900/900分割は成功したが、opcode制限・書込み範囲解析・queueの標準semanticsの組合せで説明できる。最大のReject理由は変わらない。全actorを管理できるhostが信頼できるregistryを維持する方が簡単という反論も残る。未書込みoffsetがない一般コードへの解決策ではない。

**H6（H1と異なる通知順序の独立構成案）**: 複数の共有memoryに対し、同一agentの同一job中に識別可能な非同期待機とその完了reactionを登録し、各memoryへの通知で得た正の通知件数を順に記録し、一回の完了待合せ後のreaction識別子列を前記件数により区切って実体同値類を復元し、捕捉済みmemoryへの結合条件を判定する方法。前提として当該位置に対する外部待機・通知を排除する。

H6は通常のPromise順序保証と既知queueを利用する。n=k=64でsingle-deadline版の0.161705msから0.054230msへ短縮したが、これはbatch化の性能効果であり進歩性の証明ではない。k=1では遅く、正しいregistryにも全条件で劣る。[順序の根拠と反例](algorithm.md)を公開条件として記録する。初期版からの主要改良は有限再試行、未書込み位置、順序利用の3回とし、ここでHの主設計探索を区切る。H6を別原理の新案数へ追加しない。
