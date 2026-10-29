# 修士研究向けWasmセキュリティ：3つの発明候補

2026-10-24。ユーザーの指定により、難読化からWasmセキュリティ全般へ検討を拡張した。**3案の具体的構成・請求項案・検証計画と、小規模な実Wasm試作を作成した。ただし3件の新規特許を確立したわけではない。**

|優先順位|案と原理|狙う技術的効果|現時点の新規性上の問題|
|---|---|---|---|
|1|[A: 実引数から権限依存フェンスを生成](candidate-a.md) — 認可依存の具体化|失効後の新規受付を防ぎ、無関係な権限変更による拒否を削減|依存権限・epoch・WIT shim生成は既知。限定生成から効果受付への接続が研究対象|
|2|[B: 再入の書込み上界から部分snapshotを生成](candidate-b.md) — メモリ効果の静的解析|検証時の値を保ちながら境界をまたぐ退避を削減|静的checkpoint・RLBoxに近い。第三者libraryではコピー削減を確認できなかった|
|3|[C: 非同期資源の返却義務を生成](candidate-c.md) — 予約の保存則|キャンセル連打による資源枠の早期再利用を防ぐ|基本方式は正しいセマフォと同一。複数寿命の生成・合成が未実装|

3案はそれぞれ認可・メモリ・資源量という異なる不変条件を守る。初期はBを優先したが、第三者libraryで効果を確認できなかったため追加実装はAを優先する。各案には週8–10時間・約8～12週間の単独計画を置き、3案を同時に完成させる予定にはしない。研究室の本来のテーマとの接続や締切は未指定のため、見積りは確約ではない。

## 資料

- [先行論文・特許・読了範囲](prior-art.md)
- [請求項の要素別監査と、新規性をまだ主張できない理由](claim-chart.md)
- [実験前に固定した仮説](plan.md)
- 各案のページに、構成図、手順、前提、独立請求項1＋従属3、比較対照、測定方法、最大のReject理由を記載。
- [実測一覧](../../results/masters-security-20261024/report-v1/report.md)
- [Bの研究草稿（日本語、正の結果と反証を併記）](paper-draft.md)
- [Aの研究草稿（実Component・I/O・寿命・bindingの結果）](paper-a-draft.md)、[Aの条件付き安全性](fence-soundness.md)
- [A第2設計と改訂請求項: 単一の処理計画から認可と実行を導く](effect-plan-design.md)
- [A第2設計の草稿：強い対照と適用限界を含む](paper-a-plan-draft.md)、[ShillDB・ACE・境界予算の追加先行調査](prior-art-followup.md)
- [原データ](../../results/masters-security-20261024/probe-v2/results.json)、[全binary一覧と範囲要約](../../results/masters-security-20261024/probe-v2/manifest.json)、[監査](../../results/masters-security-20261024/audit-v1/audit.json)

## 現在の実測

- A: raw/O3それぞれ216シナリオ。入口だけの検査では不正受付105、全体世代方式では不要拒否84、操作別依存方式はどちらも0。ただし依存抽出は手書きの最小実装。
- B: 18 binary、3,744入力、旧値viewの不一致0。466ケースはtrapを含む。範囲を解析できた16本で保持payloadの合計13,631,488→18,746 byte。総メモリ・総コピー・速度の同率改善を意味しない。
- C: 32条件。上限8に対して弱い返却方式では最大64、実解放方式では8。正しいセマフォ対照と同じであり、一般的な資源制御の新発明とは扱わない。
- 全22 binaryのvalidation、主出力60ファイルのhash、別有限モデル186,624照合、WABTのtrap副作用例を確認。
- B追試: Wasm→host→同じWasmへの実際の再入14本、1,498ケースの旧値viewが一致。到達する関数の要約と疎な読取り集合を追加。未知importとgrowは全コピー。別監査で42ファイルと7回帰例を確認。[追試原データ](../../results/masters-security-20261024/boundary-v1/results.json)。
- Rust追試: 自作8処理から48本を生成。同じ6,528入力で部分退避の適用12/48→28/48、不一致0。[改修前](../../results/masters-security-20261024/compiler-v1/results.json)／[改修後](../../results/masters-security-20261024/compiler-v2/results.json)。第三者実アプリケーションの評価ではない。
- 解析器追試: 128本・8,960入力・308 trapで観測した変更の上界漏れ0。[監査](../../results/masters-security-20261024/effects-audit-v1/audit.json)、[安全条件と論証範囲](soundness.md)。
- consumer比較: 20独立processで4方式を測定。区間読取りの全コピー時間比は例ごと約0.75–1.23、常に高速ではない。[性能原表](../../results/masters-security-20261024/consumer-v1/report.md)。保存payload削減と総メモリ削減を区別する。
- 強い対照: checksumを再入前に計算する方式が有力だった。[追加25 process](../../results/masters-security-20261024/consumer-v2/report.md)。この用途で部分snapshotの必要性は示せない。
- 用途を限定した追試: 再入後まで読取り位置が渡されないAPIでは、受理7例の全コピー時間比約0.41–0.73、未対応loop例約1.12。[20 processの実測](../../results/masters-security-20261024/query-v1/report.md)。自作microbenchmarkであり、強い新規性の根拠ではない。
- [契約監査](../../results/masters-security-20261024/contract-audit-v1/audit.json): 730 hash照合、176上界の再導出、別writer等の3反例、偽造上界の再解析不一致を確認。
- A生成追試: 限定WITをJcoで検証して抽出JSを生成。2,076要求・20,760イベント判定で手書きoracleと不一致0。3不正契約・6不正引数を拒否。[最新の再試験](../../results/masters-security-20261024/fence-v3/results.json)。
- A実Component追試: raw/最適化後の計2,178回で依存・受付判定が一致。実resource.drop・再利用・呼出し後の継続を含む。[最新の再試験](../../results/masters-security-20261024/component-fence-v3/results.json)。
- AのローカルI/O: 288条件の内容・戻り値が一致、64拒否。別の6失敗例に途中書込みが残る例を含む。[実測](../../results/masters-security-20261024/fence-file-v3/results.json)。受付はtransactionやrollbackではない。
- Aのteardown: 60条件でticket・論理参照を回収、試験FD180件の閉鎖を確認。[実測](../../results/masters-security-20261024/fence-teardown-v2/results.json)。instance専用の資源に限定し、共有backendや非同期I/Oの終了を意味しない。
- Aの別schema: field名とnested optionのbinding不備を旧版で検出。修正版は336実Component呼出しが一致。[実測](../../results/masters-security-20261024/fence-shapes-v2/results.json)。v1はdirectory作成のtool失敗で測定未実行。
- Aの契約負例: 誤注釈・mutable送信先・非同期executorによって前提が崩れる6負例と6修正対照を保存。[実測](../../results/masters-security-20261024/fence-negatives-v1/results.json)。生成器が業務認可を型だけから証明するわけではない。
- A第2設計: 限定recipeから固定計画を一つ生成し、同じopcode列から依存と実行を導く。288条件一致、不正recipe6種類・外部callbackを拒否。[実測](../../results/masters-security-20261024/effect-plan-v2/results.json)。同じfile executorを使う15 processの時間比は正しい手書き比約0.992～1.005。[原表](../../results/masters-security-20261024/effect-performance-v1/report.md)。capability DSL等に近く、特許新規性は未確認。
- B第三者library追試: hash-wasm 4.12.0の48条件・1,680入力は一致したが、46条件が全コピー。保存量147,000→147,000 byte、削減0。[比較表](../../results/masters-security-20261024/library-v1/report.md)。既存の小さなstate saveに対する優位性を確認できなかった。
- A性能: 改修後の20 process、生成操作別方式は手書き比約0.960～1.081の時間。54失効シナリオでは両方式とも誤判定0、実体方式の不要拒否11、全体方式31。[最新原表](../../results/masters-security-20261024/fence-performance-v2/report.md)。OS I/O費用は含まない。旧版の別測定は1.014～1.124であり、測定間の揺れを速度改善と解釈しない。
- B別checker: WAT解析器とは別にcode sectionとoperand stackを読む。224本中98部分要約を確認、501構造改変と224別hashを拒否。[監査](../../results/masters-security-20261024/checker-audit-v1/audit.json)。形式証明ではなく、元解析器より小さい実装にもなっていない。

## 再現

追加評価では、A第2設計に手書きの単一計画という強い対照を加えた。同じ36失効条件で両者とも誤判定0、[20 processの時間比](../../results/masters-security-20261024/effect-performance-v2/report.md)は約0.994～1.018で、明確な速度優位はない。[生成器単体の独立照合](../../results/masters-security-20261024/effect-compiler-audit-v1/audit.json)は12seed設定・異なるrecipe6種類・576入力で一致した。これは576実Component呼出しではない。

さらに[lift前の予算検査](abi-preflight-analysis.md)を補助実装した。45実Component条件が一致したが、memo化は正しい非memo対照に6例中5例で負けたため主発明へ追加しない。単なる上限検査はWasmtimeやCap'n Protoに先行する。

既存workspaceのPython 3.9、Node 24.15、`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`を使用。Pythonは標準ライブラリのみ。別環境では`WASM_TOOLS_ROOT`に同じ構造のtool directoryを指定する。Windowsの`.exe`を呼ぶ実装であり、他OSへの対応は未実施。

```powershell
python research/masters-security-20261024/probe.py results/masters-security-reproduce/probe
python research/masters-security-20261024/audit.py results/masters-security-reproduce/probe results/masters-security-reproduce/audit
python research/masters-security-20261024/report.py results/masters-security-reproduce/probe results/masters-security-reproduce/audit results/masters-security-reproduce/report
python research/masters-security-20261024/boundary.py results/masters-security-reproduce/boundary
python research/masters-security-20261024/boundary-audit.py results/masters-security-reproduce/boundary results/masters-security-reproduce/boundary-audit
python research/masters-security-20261024/setup-rust.py
python research/masters-security-20261024/compiler.py results/masters-security-reproduce/compiler-v1
python research/masters-security-20261024/reanalyze.py results/masters-security-reproduce/compiler-v1 results/masters-security-reproduce/compiler-v2
python research/masters-security-20261024/effects-audit.py results/masters-security-reproduce/effects-audit
python research/masters-security-20261024/consumer.py results/masters-security-reproduce/compiler-v2 results/masters-security-reproduce/consumer
python research/masters-security-20261024/query.py results/masters-security-reproduce/compiler-v2 results/masters-security-reproduce/query
python research/masters-security-20261024/fence.py research/masters-security-20261024/fence.wit research/masters-security-20261024/fence-policy.json results/masters-security-reproduce/fence
python research/masters-security-20261024/component-fence.py results/masters-security-reproduce/component-fence
python research/masters-security-20261024/setup-hash-library.py
python research/masters-security-20261024/library.py results/masters-security-reproduce/library
python research/masters-security-20261024/fence-performance.py results/masters-security-reproduce/component-fence results/masters-security-reproduce/fence-performance
python research/masters-security-20261024/fence-file.py results/masters-security-reproduce/component-fence results/masters-security-reproduce/fence-file
python research/masters-security-20261024/fence-teardown.py results/masters-security-reproduce/component-fence results/masters-security-reproduce/fence-teardown
python research/masters-security-20261024/fence-shapes.py results/masters-security-20261024/fence-shapes-v2/sources/fence-before.py results/masters-security-reproduce/fence-shapes
python research/masters-security-20261024/fence-negatives.py results/masters-security-reproduce/component-fence results/masters-security-reproduce/fence-negatives
python research/masters-security-20261024/effect-plan.py results/masters-security-reproduce/component-fence results/masters-security-reproduce/effect-plan
python research/masters-security-20261024/effect-performance.py results/masters-security-reproduce/component-fence results/masters-security-reproduce/effect-plan results/masters-security-reproduce/effect-performance
python research/masters-security-20261024/effect-compiler-audit.py results/masters-security-reproduce/effect-compiler-audit
python research/masters-security-20261024/abi-preflight.py results/masters-security-reproduce/abi-preflight
python research/masters-security-20261024/abi-performance.py results/masters-security-reproduce/abi-preflight results/masters-security-reproduce/abi-performance
```

出力先は未作成のdirectoryを指定する。既存結果を上書きしない。`probe.py`はWAT→Wasm→O3→validation→Node実行を行い、入力、seed、raw/O3、測定値、source copy、hashを保存する。`audit.py`は関係のない既存paperのhashも確認するため、このリポジトリを前提とする。

現在の`consumer.py`は事前計算対照を含む5方式版。古い4方式版は`consumer-v1/sources/`に保存した。`contract-audit.py`はこのworkspaceの固定結果directoryを横断する監査で、再現directoryを引数指定する汎用runnerではない。

`checker-audit.py`も固定結果directoryのcompiler-v2/effects-audit-v1/library-v1を読む。個別binaryには、下記の独立確認CLIを使用できる。終了コード0は明示されたhost前提の下での受理、2は拒否。実行時のhost排他をCLIが自動で強制するものではない。

A生成追試は既存の`.tools/component-resource`にあるJco 1.27.0も使用する。依存固定とセットアップ手順は[resource-triggerの環境説明](../resource-trigger/README.md)を参照。以前の難読化実験の結果をAの結果として再利用していない。

個別の実Wasmについて、限定したcallbackの書込み上界を取得するCLIもある。`callback(i32,i32,i32)->()`と`memory` exportを対象とし、前提・非対応をJSONへ記録する。出力を信頼していない第三者から受け取った場合は、内容を再検査する必要がある。

Rust追試は`rustc 1.97.0-nightly (64a965e90 2026-05-11)`を使用。`setup-rust.py`はインストール済みcompilerのmanifestを読み、一致する公式stdlibだけをworkspaceの`.tools/masters-security-rust`へ保存する。archiveのSHA-256を照合して通常ファイルのみ展開し、rustup設定を変更しない。別versionのcompilerではbyte同一再現を保証しない。今回のarchive URL/hashは各compiler結果の`toolchain.json`にある。

個別CLIは既定で`acyclic-v1`を使い、`--analyzer restricted-v1`で以前の限定解析を選べる。入力を一度読み、その同じbyte列をvalidation・解析・hashの対象にする。

```powershell
python research/masters-security-20261024/certify.py input.wasm new-certificate.json
python research/masters-security-20261024/check-certificate.py input.wasm new-certificate.json new-check.json
```

## スコープ

主試作はCore Wasm＋Nodeの制御したhostであり、A追試は限定WIT、Jco経由の実Component resource、workspaceに新規作成するファイルの実I/Oまで追加した。WASI 0.3・Wasmtimeの完全統合ではない。ネットワークサービス・既存のユーザーファイルへは効果を発生させない。各案の未実装要素を請求項の実施例として誤認しない。

第三者libraryは`setup-hash-library.py`で公開npmの固定4.12.0を取得する。archiveのSHA-512 integrityと固定SHA-256を照合し、通常ファイルのみworkspaceへ展開する。install/build scriptは実行しない。実験の結果には原binaryのhash・MITライセンス・取得元を含める。文献の任意取得に使う`fetch-leads.py`だけはpypdfを必要とし、実験runnerの依存ではない。

請求項は研究用の技術的なたたき台である。先行技術との差が文面上存在すること、発明として進歩性があること、第三者特許に抵触しないことは、それぞれ別の判断である。現時点ではいずれの登録可能性も保証していない。
