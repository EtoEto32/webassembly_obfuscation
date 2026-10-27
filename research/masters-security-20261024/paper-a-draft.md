# WebAssemblyコンポーネントの実引数から生成する権限依存検査と、その適用限界

研究草稿、2026-10-24。既知技術に対する強い新規性を確立した投稿稿ではない。Aの実装・反証をまとめ、先のB草稿と区別する。

本稿の第1設計で見つかった契約と実行の不一致を受け、[第2設計の追補](effect-plan-design.md)を作成した。単一処理計画から依存と実行を導く実装・288条件・15 process測定・改訂請求項を含む。以下の第1設計の結果と同一の件数として合算しない。

## Abstract

WebAssemblyコンポーネントがhostへ処理を要求した後、実効果の受付までに権限やresourceの寿命が変化し得る。入口のみの認可は古い要求を許可し、全体世代による保守的な検査は無関係な変更でも要求を拒否する。本稿は、限定WITと明示した権限契約から、実際の選択枝のresource依存を生成する試作を検討する。host内の一回限りの要求に実体・slot・操作別世代を記録し、同期の効果受付で再検査する。実Componentの2,178判定、ローカルファイル操作288条件、終了処理60条件が独立oracleと一致した。別schemaを使うと旧生成器にfield名とnested optionの不備が見つかり、修正後336呼出しが一致した。20独立processの測定では、正しい手書き方式に対する時間比は約0.96–1.08だった。世代検査・依存追跡・WIT shim生成は先行するため、本稿は限定実装の成立条件と失敗例を報告する。特許に必要な技術的差分は未確立である。

## Introduction

認可の検査時点と実効果の受付時点が離れると、検査済みという事実だけでは現在の許可を表せない。Wasmの型付き境界はresourceの位置を明確にするが、どの業務権限が必要かまでは定義しない。また、borrow値の有効期間を越えて生のwrapperを保管できるとは限らない。

修士研究と両立する範囲で、この境界の生成処理とhost台帳を実装し、厳密に同じ依存を手書きした対照と比較する。目的は既知のepoch検査を新原理と名付けることではなく、どこまで生成でき、何を外部契約として残す必要があるかを測ることである。

## Related Work

[Omerの修士論文](https://kth.diva-portal.org/smash/get/diva2%3A2046977/FULLTEXT01.pdf)のWacky/Shimmerは、WITに基づくアクセス制御shimの配置と雛形生成を扱う。従ってWITからのセキュリティwrapper生成自体は新規性の根拠にしない。[root-scoped quiescence](https://arxiv.org/abs/2609.21284)は、非同期処理で権限依存と効果受付を扱う近接するpreprintである。

[EP3493461A1](https://patents.google.com/patent/EP3493461A1/en)には能力の版と失効情報による利用可否の扱いがある。[US11736525B1](https://patents.google.com/patent/US11736525B1/en)は静的解析から操作を認可actionへ対応させ、policyを生成する。Aの入力はWITと明示した権限契約であり、一般のアプリケーションコードから必要policyを推測する方式とは異なるが、自動生成という一般形は先行する。

受付済み効果と取消しを区別する[個人Internet-Draft](https://datatracker.ietf.org/doc/draft-watts-agent-clockout-profile/00/)も公表されている。これはIETF標準や実装評価ではない。各資料の実読範囲は[調査記録](prior-art.md)に示す。

## Motivation

copy(source,destination)が待ち行列へ入った後、destinationのwrite権限が失効したなら受付を止める必要がある。一方sourceのwrite権限だけの失効は、このcopyがsourceをreadするという契約では依存しない。同一実体を二つのhandleが指すaliasと、handle slotを別実体に再利用する場合も区別する。

正しい手書き実装でもこの判定はできる。生成の評価には、global epochという弱い精度の対照だけでなく、この手書き方式が不可欠である。

## Threat Model

guestは検証を通る任意のComponentであり、要求順序、variant、list、resourceのdropやtrapを操作できる。host、WIT parser、権限契約、resource実体へのresolver、同期executor、Jco/engineは信頼する。各instanceに別のhost台帳を割り当てる。

すべての対象効果が台帳を通り、失効と受付が一つのJS threadで直列化される場合に限定する。別workerの変更、外部サービス側の受付、隠れた認可依存、任意の非同期executor、engineの脆弱性を扱わない。性能実験では実体は二つのみである。

## Proposed Method

型と契約から、record、選択variant、list、optionをたどる抽出器を生成する。実引数から得た各resourceを有効なborrow期間中にhost台帳へ解決し、slot世代と操作権限世代を記録する。権限は実体単位へ集約する一方、slot寿命は各参照について保持する。

効果の内容をhost内へ固定し、一回限りのticketを作る。受付ではticketを消費し、slot生存・世代・実体と操作別許可・世代を照合する。一致した場合だけ同期executorを呼ぶ。finallyでticketの予約を返す。shutdownはpending ticketとinstance所有slotを無効にする。実FDのcloseはbackend ownerが別途実行する。

型構造に沿った射影の正しさと、射影が業務効果に対して完全であることは別である。後者は信頼する契約に依存する。[条件付きの論証](fence-soundness.md)を示すが、実装全体の形式証明は行っていない。

## Implementation

Pythonの限定WIT readerとJS生成器、Node 24.15.0、Jco 1.27.0を使用する。公式JcoでWITを検証し、実Componentをparse/opt/transpileして動かした。1 interface、1 prepare関数、u32、resource borrow、record、variant、list、optionが対象であり、一般WIT parserではない。

Jcoのoption none表現とfield名変換を明示的に扱う。nested optionはJSのundefined表現とtagged表現が交互になる。別schemaの試験前はこの対応が不完全だった。旧版・失敗ログ・修正版を全て保存する。

## Evaluation

|試験|対象・条件|観測|
|---|---|---|
|生成器模型|2,076要求、20,760イベント判定|独立oracleとの不一致0|
|実Component|raw/最適化後、計2,178受付|不一致0。drop・reuse・alias・個別slot変更を含む|
|ローカルI/O|288条件、別の制御失敗6例|内容・戻り値が一致。拒否64。read44回、write312回|
|instance teardown|60条件、うち例外36|ticket/論理参照0、FD180件の閉鎖を確認|
|異なるbinding shape|336実Component呼出し|旧版の2種不備を確認し、修正版で不一致0|
|性能|4方式×5独立process|生成operation/手書きoperation時間比約0.960–1.081|

これらは固定シナリオの件数であり、現実の障害発生率ではない。改修前後の同一条件を独立サンプルとして足し合わせない。depth 1–4のJS表現14例も確認したが、nested optionの実ABI試験はdepth 2だけである。

性能は100回warmup後、200回×9 batchをprocess内で測定した。各processの中央値から5 processの中央値とIQRを報告する。準備・Component呼出し・JS継続・受付・releaseを含み、OS I/Oは含まない。単純な高速化の結論は出さない。54失効シナリオで生成／手書きoperationは誤判定0、objectの不要拒否11、global31で、不正受付はいずれも0だった。

I/O失敗では、先に行われた書込みが残った。shutdownで論理参照が0になったことは、外部資源の処理が全て終わった証拠ではない。初回shape runnerのdirectory作成EPERMはtool実行失敗として別記し、解析失敗や拒否成功に数えない。

## Discussion

実Componentの所有権境界と、hostの受付点を接続できた点は実装上の到達点である。一方、WITが正しくてもbindingの表現対応で失敗し、適切な手書き方式に精度や速度で勝つ新原理は得られていない。生成器の価値を主張するには、既知のIDL生成器へ同等の規則を実装した対照や、実adapterでの設定漏れの評価が必要である。

手書きの意図的な誤実装を用意して本方式が勝つだけでは、現実に漏れが減る証拠にならない。型由来のpath完全性、binding適合性、業務契約の完全性を分けて評価する必要がある。

この区別を調べる負例では、型上は妥当でもcopy先のwriteをreadと誤注釈すると、write失効後の書込みを止められなかった。送信先を後から読み直すexecutorも依存集合を迂回した。awaitを含むexecutorでは、host内ログと実OS呼出しの時点が離れた。raw/optの6負例と6修正対照を保存した。生成器が信頼する契約やexecutorの誤りを自動で修復するとは主張しない。

## Limitations

単一runtime、限定schema、少数resource、同期host executor、自作fixtureに依存する。Rust/Wasmtimeのnative Component統合や本番WASI hostへの導入は未実施。I/Oはworkspace内の新規ファイルのみで、分散原子性や取消しを評価しない。メモリ測定のRSSはruntime込みのprocess値であり、台帳の厳密なpeak量ではない。特許の先行技術調査にも未取得資料が残る。

## Conclusion

型付き境界から具体的な認可依存を生成し、hostの受付と寿命管理へつなぐ限定試作を実装した。実験は狭い前提での動作を支持する。既知の世代検査とWIT shim生成を超える新しい安全原理、実アプリケーション上の設定漏れ低減、特許につながる非自明な差分は、現在の結果から主張できない。
