# 先行技術の照合記録

調査日: 2026-10-24。以下は実際に取得できた一次資料の読了範囲に限定する。検索結果だけの文献を読了扱いにしない。特許公報は技術の開示として比較し、登録可能性・抵触の法律判断は行っていない。公報のA/B種別と論文の査読状態を混同しない。

## 論文・仕様

|資料|状態・読了範囲|確認した内容と今回への含意|
|---|---|---|
|Shravan Narayan, Craig Disselkoen, Tal Garfinkel, Nathan Froyd, Eric Rahm, Sorin Lerner, Hovav Shacham, Deian Stefan. **Retrofitting Fine Grain Isolation in the Firefox Renderer**, USENIX Security 2020. [会議](https://www.usenix.org/conference/usenixsecurity20/presentation/narayan), [本文](https://www.usenix.org/system/files/sec20fall_narayan_prepub.pdf)|査読済み。Abstract、double-fetchの例、§4.3のfreeze/unfreeze付近を読了。全評価は未読。|RLBoxはコピーと検査で二重読み取りを扱い、選択したfieldへのfreezeを提供する。「全コピーより部分コピー」はBの新規性にならない。BではWasm本体からの書込み上界と、戻り／trap後の読取り復元の生成を比較対象とする。RLBox実装との実測比較は未実施。|
|Dirk Vogt, Cristiano Giuffrida, Herbert Bos, Andrew S. Tanenbaum. **Lightweight Memory Checkpointing**, DSN 2015. [著者配布本文](https://download.vusec.net/papers/dsn-2015.pdf)|査読済み。冒頭、静的解析による先行方式の説明、§V-Aを読了。全評価は未読。|更新され得る領域の退避、不要なstore計装の削除、空間的に近いstoreの集約は既知。Bの「書込み解析でコピーを減らす」という広い主張を否定する重要資料。|
|Asim Kadav, Matthew J. Renzelmann, Michael M. Swift. **Fine-Grained Fault Tolerance using Device Checkpoints**, ASPLOS 2013. [本文](https://scail.cs.wisc.edu/papers/asplos13_fgft.pdf)|査読済み。Abstract、checkpoint概説、§5.4–5.6の一部を読了。|呼出し単位のcheckpoint／復旧と注釈による境界処理は古い。Bは障害復旧全体を再発明したと主張できない。|
|Genliang Zhu, Chu Wang. **Authorization Revocation for Long-Running AI Agents: Root-Scoped Quiescence under Delegation and Asynchronous Execution**, arXiv:2609.21284v1, 2026-09-18. [書誌](https://arxiv.org/abs/2609.21284), [本文](https://arxiv.org/html/2609.21284v1)|プレプリント。Abstract、§4.1–4.3のroot cut・support antichain・rebindを読了。全証明・評価は未読。|依存する権限の具体的な集合、過剰な失効の回避、効果受付時の検査、別権限への付替えをすでに扱う。Aの意味論の核に非常に近い。差分候補は限定されたWasm境界から依存を生成し照合する実装であり、失効原理自体ではない。|
|Ameen Shaheen, Wael Alzyadat, Aysh Alhroob. **CROC Core v6 Reproducibility Package**, Zenodo v2, 2026-08-28, DOI 10.5281/zenodo.22141849. [公開記録](https://zenodo.org/records/22141849)|ソフトウェア公開資料。ページの説明・メタデータを読了。査読掲載は未確認、zipは未取得／未実行。|非同期Wasmのキャンセル、解決種別、所有権、borrow識別・多重度のtrace検査を扱うと著者が説明。Cでこれらの区別自体を発明とはしない。実資源の残存予約という量的属性と、生成された解放条件を区別して検証する必要がある。|
|David Goltzsche, Manuel Nieke, Thomas Knauth, Rüdiger Kapitza. **AccTEE: A WebAssembly-based Two-way Sandbox for Trusted Resource Accounting**, Middleware 2019, pp.123–135, DOI 10.1145/3361525.3361541. [所属機関の書誌・Abstract](https://cris.fau.de/publications/277973669/)|査読済み会議の書誌・Abstractのみ。本文は未読。|WasmとTEEを利用する信頼できる資源会計は既存。最大10%の会計overheadは著者のAbstractの報告で、今回再現した値ではない。CはCPU課金の新原理ではない。|
|Zhaofeng Yu, Dongyang Zhan, Lin Ye, Haining Yu, Hongli Zhang, Zhihong Tian. **Exploring and Exploiting the Resource Isolation Attack Surface of WebAssembly Containers**, USENIX Security 2025. [本文](https://www.usenix.org/system/files/usenixsecurity25-yu-zhaofeng.pdf)|査読済み。Abstract、Rust async解析の説明、§6への導入と倫理付録の防御議論を読了。全攻撃・全評価は未読。|WASI/WASIXを通じたホスト資源消費と他インスタンスへの影響は既知の課題。Cの問題設定そのものを初発見とはしない。|
|WebAssembly Component Model, **Concurrency.md**. [公式設計資料](https://github.com/WebAssembly/component-model/blob/main/design/mvp/Concurrency.md)|仕様設計資料。Cancellation、Reentrance、borrowとterminal statesを確認。取得時mainであり固定版の実装を検証したのではない。|キャンセル要求と解決を区別し、borrow解放条件を既に定義。一般のキャンセル要求後も実行が続く。A/Cの前提であって新規要素ではない。|
|WASI, **Security** / **Design Principles**. [公式](https://wasi.dev/security), [設計](https://github.com/WebAssembly/WASI/blob/main/docs/DesignPrinciples.md)|公式の能力ベースセキュリティ説明を確認。|WITのresource handleと外部効果を仲介するhostは利用できる既存基盤。型だけから任意のhostの業務認可や資源費用を推定できるとは書かれていない。|
|Wasmtime Config; Tokio spawn_blocking. [Wasmtime](https://docs.wasmtime.dev/api/wasmtime/struct.Config.html), [Tokio](https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html)|公式APIのblocking host calls／abortの説明を確認。取得時docsはそれぞれ51.0.0-dev／1.54.1。|fuel/epochの対象外となるhost処理、開始済みblocking taskの中断制約は既知。Cの「キャンセル後にも残る仕事」はWasm専用の発見ではない。|

## 特許公報と請求項の具体的な照合

### Bの追試で追加した近接研究

|資料|状態・読了範囲|含意|
|---|---|---|
|Xiaojia Rao, Aïna Linn Georges, Maxime Legoupil, Conrad Watt, Jean Pichon-Pharabod, Philippa Gardner, Lars Birkedal. **Iris-Wasm: Robust and Modular Verification of WebAssembly Programs**, PACMPL 7, PLDI, Article 151, 2023, [DOI 10.1145/3591265](https://doi.org/10.1145/3591265), [著者配布本文](https://iris-project.org/pdfs/2023-pldi-iris-wasm.pdf)|査読済み。Abstract、導入の貢献一覧、§3のhost相互運用・再入例を読了。全証明は未読。|Wasm 1.0の高階separation logicとhostを含む再入の合成検証は既存。Bのframe的な安全説明を新しい証明原理とはしない。今回のPython解析器は機械検証済みでない。|
|Victor Duta, Mitchel Josephus Aloserij, Cristiano Giuffrida. **SafeFetch: Practical Double-Fetch Protection with Kernel-Fetch Caching**, USENIX Security 2024, pp.1207–1224. [会議](https://www.usenix.org/conference/usenixsecurity24/presentation/duta), [読んだprepublication本文](https://www.usenix.org/system/files/sec24fall-prepub-1439-duta.pdf)|査読済み。Abstract、導入、§7.3のcache寿命・zero-copy、§9.3のzero-copy比較を読了。全評価・実装は未検証。|byte単位の既読値cache、既存staging bufferの再利用と寿命延長は既存。Bの区間consumer自体も一般的なコピー削減であり独立の新原理ではない。論文のLinux実測と今回のNode小例を直接比較しない。|
|Dinghong Zhong, Alexander Bai, Mikail Khan, Guannan Wei. **Compiling WebAssembly Concolic Execution with Staging, Continuations, and Snapshots (Extended Version)**, arXiv:2608.18327v2, 2026-08-21. [書誌・Abstract](https://arxiv.org/abs/2608.18327v2)|Abstractと書誌のみ。arXiv上にOOPSLA 2026採録済み論文のpreprintと記載。出版社の最終版は未照合、本文は未読。|分岐点snapshotと継続から再実行を減らすGenWasymを説明。Bのhost旧値viewとは目的が違うが、Wasmのsnapshot・stagingを広く新規と呼べない。|

Midas（USENIX Security 2022）は[会議Abstract](https://www.usenix.org/conference/usenixsecurity22/presentation/bhattacharyya)とSafeFetchの関連説明まで確認。原論文の全構成を比較済みとは扱わない。

公開日は取得ページの記載による。優先日、法的存続、各国ファミリーの範囲は別途調査が必要。異なる用途というだけで進歩性があるとは判断しない。

|公報・発明名|確認した箇所|共通する部分|今回の差分仮説／残る拒絶リスク|
|---|---|---|---|
|[EP3493461A1 — Capability revocation](https://patents.google.com/patent/EP3493461A1/en), 公開2019-06-05|請求項1–6、9–12、公開日|能力の失効情報・版の検査を利用の可否に結び付ける。|AではWasm呼出しの実際のvariant/引数からresource実体・slot世代・操作別世代の依存を生成する。ただし既知の版検査をWasmに適用しただけ、と評価されるリスクが高い。上記root-scoped論文も併せて検討する必要がある。|
|[EP4343593B1 — Method, device, and electronic apparatus for securely passing data](https://patents.google.com/patent/EP4343593B1/en), B1公開2026-04-15、A1公開2024-03-27|請求項1–6、7–15、書誌|信頼側cacheへコピーし、以後のcheck/useをそのcacheに向ける。引数アドレスの変更、サイズ制限も開示。|Bでは非共有Wasmの全prefixの書込み上界とホスト読取り集合の交差を取得し、一部は元memoryから読む。単なるshadow bufferやサイズ別コピーを請求しない。静的checkpoint論文との組合せで容易とされるリスクがある。|
|[US20230136888A1 — Asynchronous transaction processing](https://patents.google.com/patent/US20230136888A1/en), 公開2023-05-04|請求項1–14|callbackに関係するデータの一部をsnapshotとして供給。|BのWasm命令効果からの範囲生成とは処理が異なるが、「callback時に必要な部分だけsnapshot」は広すぎる。狭い差分を明細書に残すための反証資料。|
|[US10579422B2 — Latency-managed task processing](https://patents.google.com/patent/US10579422B2/en), B2公開2020-03-03、A1公開2017-01-26|請求項1–4、説明中のquota/cancel、公開日|要求者groupの未完了task数と閾値に基づき受付を制限する。請求項1は待機latencyに応じた閾値変更を含む。|Cは固定または設定された資源別上限、実解放までの予約、型付き境界からの解放条件生成が対象。単なる未完了task制限は新しくない。この公報だけからCの全要素が開示／非開示とは結論しない。|

## 未読・取得失敗の扱い

追加公報：[US6154877A — Method and apparatus for portable checkpointing using data structure metrics and conversion functions](https://patents.google.com/patent/US6154877A/en)、公開2000-11-28。書誌、背景のmemory exclusion optimization、請求項1–13を読了。source precompiler、保存するdata structureの識別、shadow構造、異なる機器間の変換・復元を開示する。Bは移送可能な再開checkpointを生成する方式ではないが、「解析で保存対象を絞りコードを生成する」という広い説明は先行する。失効・存続は判断していない。

- *Flexible access control for WebAssembly-based serverless computing*は最初の取得がtimeoutしたが、下記の追試でPDFを取得した。未読扱いは更新した。
- WO2026150382A2は効果受付・policy epochに近い検索結果があったが、本文が取得サイズ上限を超えた。請求項未読であり、差分確認済みとはしない。
- Cornucopia（IEEE S&P 2020、DOI 10.1109/SP40000.2020.00098）は所属機関Abstractと検索された本文部分のみ。世代／失効の一般性を示す探索leadであり、全構成の比較は未実施。
- 特許庁の[ソフトウェア関連発明の審査ハンドブック](https://www.jpo.go.jp/system/laws/rule/guideline/patent/handbook_shinsa/document/1001kaitei/app_b1.pdf)等は検索結果を取得したが直接取得は403。法的要件を全文確認済みとは扱わない。

## 再検索用の語と取りこぼし

`WebAssembly reentrancy double fetch`; `sandbox selective copying`; `static analysis copy-on-write checkpointing`; `Wasm WIT capability revocation`; `authorization support antichain`; `WebAssembly cancellation resource ownership`; `asynchronous quota reservation release`; `capability revocation patent`; `securely passing data shadow buffer patent`。

Google Patentsと英語の論文・公式仕様を中心とする限定調査。J-PlatPat／Espacenetの分類・日本語同義語・出願人・引用網を通した網羅調査、未公開出願、クレーム全ファミリーの比較は未実施。「検索で見つからない」ことを新規性の証明にしない。

## 生成追試の公式仕様

[Bytecode Alliance WIT Reference](https://component-model.bytecodealliance.org/design/wit.html)の冒頭、record/variant/resource/option/listの説明を確認。WITは振舞いを定義せず、境界の契約を記述するため、Aでは操作権限を別の信頼する契約へ明示する。resourceを持つ値は所有・borrowの寿命に従う必要がある。生成試験は既存JcoのAPI型宣言とCLI helpも実際に読んで組み込んだ。Jco APIのwebページは取得失敗のため、ローカルの1.27.0の型宣言を使用した。

## 追加の反証検索

- **US8789025B2 — Path-sensitive analysis for reducing rollback overheads**、John K. P. O'Brien, Kai-Ting Amy Wang, Mark Yamashita, Xiaotong Zhuang、IBM、B2公開2014-07-22、A1公開2012-01-19。[公報](https://patents.google.com/patent/US8789025B2/en)。概要と請求項1–7を読了。基本blockごとの復元register集合、先行blockとの合併、変化がなくなるまでの解析、rollback位置を示す変数とroutineの生成を開示する。Bはregister rollbackでなくhostの旧値memory viewであり実装構成は異なるが、経路に依存する保存範囲の解析・生成自体は新しくない。この差だけで進歩性を認められるとは判断しない。
- Leo Cao, Luoxi Meng, Deian Stefan, Earlence Fernandes. **Stateful Least Privilege Authorization for the Cloud**, USENIX Security 2024, pp.3477–3494。[会議](https://www.usenix.org/conference/usenixsecurity24/presentation/cao-leo)、[本文](https://www.usenix.org/system/files/usenixsecurity24-cao-leo.pdf)。査読済み。Abstract、§3.1.1、§3.2のtoken revocation/expirationを読了。Wasmのpolicy/state updaterを登録し、履歴に依存する最小権限を適用する。AはWasmで認可を実装すること自体を新規性にできない。WITからのleaf抽出と、遅延効果受付の世代検査が当該読了範囲に含まれるかは別問題であり、全文に存在しないと断言しない。
- [wasmCloud v1 Security](https://wasmcloud.com/docs/v1/hosts/security/)の公式記述を確認。WITに宣言された呼出しにruntime policyを適用する基盤は既存。現行最新majorの全実装を調べた意味ではない。

取得できなかった近接資料は未読のまま残す。*Static Analysis for Checkpoint Size Reduction in Array-Based Programs*（Greg Bronevetsky/Radu Rugina）は検索indexのAbstractだけを確認、CiteSeer本文403、直接downloadも404。*Compiler-based checkpointing for support of error recovery*（US6708288B1）は当初未取得だったが、後述の追加取得で請求項まで確認した。未読のleadと、取得後の更新を区別する。

## Aに近い生成器の本文取得後の照合

Shahd Izzeldin Karar Omer, **Flexible access control for WebAssembly-based serverless computing**, Aalto University School of Electrical Engineering / Security and Cloud Computing、修士論文、2025-11-23。[機関配布PDF](https://kth.diva-portal.org/smash/get/diva2%3A2046977/FULLTEXT01.pdf)。査読済み会議論文とは区別する。表紙・Abstract・§5.3–5.4（pp.48–51）・評価の設定部分（pp.52–53）・§7.3–7.4.4（pp.64–66）を実際に読んだ。全論文・実装は検証していない。PDF SHA-256は `e1e0d40a75e7c4521741f354f5c36f870e595896fab0936cca832ed2ff858268`。

Wackyは宣言的manifestに従ってWACの構成ASTを書き換え、既存component間へshimを挿入する。ShimmerはWITからRustのshimプロジェクトと関数stubを生成するが、認可の中身は開発者が書く。評価のpass-through shimは認可ロジックの費用を含めないため、Aの依存抽出時間とは直接比較できない。

本文は、静的なcompositionの変更では実行中の細かい権限変更を扱いにくいこと、resourceの寿命・proxy・methodの仲介、record/enum/variantの自動生成に制約があることを明記する。Aが検討する「選択されたvariant内のborrowから、実体・slot・操作別の世代を抽出し、遅延した効果の受付で再照合する」具体的処理は、この読了範囲の生成器とは異なる。ただし、WITからpolicy shimを生成する一般的な構成は先行する。未対応型を追加しただけ、既知の失効検査をstubに埋めただけ、という反論は残る。Aの現在のhost台帳模型は同論文のresource課題全体を解決した実装ではない。

## Wasmの効果導出に近い別分野の研究

Nicolaas Kaashoek, Oleg A. Golev, Austin T. Li, Amit Levy, Wyatt Lloyd. **Running Consistent Applications Closer to Users with Radical for Lower Latency**, SOSP 2025, DOI [10.1145/3731569.3764831](https://doi.org/10.1145/3731569.3764831)、[著者配布本文](https://nicolaas.io/radical-sosp25.pdf)。査読済み。Abstract・導入・§3.3・§4・§7を読了。全評価・形式証明は未検証。

Wasmの関数から記号実行と依存解析により、入力に応じたstorage read/write集合を返す関数を生成する。Eunomiaへ認識するstorage呼出し等を追加し、生成結果とruntimeの結線には手作業が残る。導出不能・高費用の場合に別実行位置へ退避する。Bはstorage keyの分散整合性でなくlinear memoryの旧値供給を対象とするが、「Wasm実行前に実引数で効果集合を生成・評価する」こと自体は既知。用途の違いのみで新規と判断しない。

第三者ライブラリ試験では[hash-wasm公式repository](https://github.com/Daninet/hash-wasm)と[WASMInterface.ts](https://github.com/Daninet/hash-wasm/blob/master/lib/WASMInterface.ts)を確認した。4.12.0の公開packageも取得し、save/loadが内部stateだけをコピーしbinary識別子を付ける実装を読んだ。Bを全memoryコピーとだけ比較してこの既存APIを無視するのは不公正である。引用時のmasterと、実験に使う固定4.12.0を区別する。

## 別checkerの新規性を抑制する資料

- George C. Neculaの[Proof-Carrying Code説明](https://people.eecs.berkeley.edu/~necula/pcc.html)、最終改訂2002-07-22。一次の技術解説で、Overview・Implementation・Experimentsを確認。安全方針、コードに結び付く証明、生成側と独立の検査側は既知である。今回の式集合の二重導出は形式証明を運ぶPCCを実装したものではない。
- Averの[Artifact Behavioral Certificates](https://github.com/jasisz/aver/blob/main/docs/certification.md)（2026-10-24に取得したmain）。冒頭、Generate/verify、target matrix、successful certificationの前提まで読んだ。文書は特定Wasm byte列へLean証明を対応させ、hashだけではない性質の検査、対象export・runtime契約・未認証対象の区別を説明する。査読論文ではなく開発者文書で、実装・Lean証明の再現は未実施。Bの「実binaryと独立checkerを結び付ける」という一般形を新しいとはしない。
- Quentin Stiévenart, Coen De Roover. **Wassail: a WebAssembly Static Analysis Library**, ProWeb 2021、発表Abstract。[会議ページ](https://2021.programming-conference.org/details/proweb-2021-papers/3/Wassail-a-WebAssembly-Static-Analysis-Library)、[実装README](https://github.com/acieroid/wassail)を確認。大学の書誌はunpublished abstractと分類するため、full査読論文として扱わない。Wasm static analysisの汎用基盤は先行する。今回このtoolを性能対照として動かしたわけではない。
- Akihisa Yagi, Ken Sakayori, Naoki Kobayashi. **CHC-based Automated Verification of WebAssembly Programs**, arXiv:2607.17220v1、2026-07-19。[書誌・Abstract](https://arxiv.org/abs/2607.17220)。HCVS26で発表と記載されるpreprint、本文未読。型によるindirect call候補の絞込みとpanic handlerの要約を説明する。今回の限定checkerを一般的なWasm検証の初手法とはしない。具体的なsnapshotとの差は全文調査が必要。

## 効果受付と取消しを区別する公表済み設計

Deonté Watts. **External Authorization and Bounded CLOCKOUT for Agentic Systems**, draft-watts-agent-clockout-profile-00、2026-10-12、[IETF Datatracker](https://datatracker.ietf.org/doc/draft-watts-agent-clockout-profile/00/)。個人提出のInternet-Draftであり、RFC・IETF採用標準・査読済み研究ではない。書誌・Abstract・status、§4–7、§9–10を読了。

当該案は、待ち行列入口の認可では不十分とし、実効果側での世代照合と受付の原子性、受付済み不可逆効果の残存、取消し・完了との区別を明記する。実装・実測の報告ではないが、Aの受付点検査や今回のI/O途中失敗の区別自体を新しい着想と呼べない。WITからの依存抽出生成はこの読了範囲で扱わない。公開設計の存在と、実装上の保証・特許性は分けて評価する。

## 認可生成の追加特許

**US11736525B1 — Generating access control policies using static analysis**。Neha Rungta、Willem Conradie Visser、Daniel George Peebles、Amazon Technologies Inc、公開2023-08-22、[公報](https://patents.google.com/patent/US11736525B1/en)。書誌・概要・請求項1–20を読了。プログラムの外部呼出しを静的に認識し、認可基盤のactionへ対応させてpolicyを生成する。resource識別子のplaceholder、ユーザー入力、注釈、過不足比較も扱う。Aは明示したWIT効果契約から実引数の依存を具体化するため、入力と処理段階が異なる。ただし認可処理をコードや注釈から生成する一般形を新しく主張できない。上記の技術比較は法的な権利範囲・抵触判断ではない。

## 未取得特許を公式公報で確認した結果

**US6708288B1 — Compiler-based checkpointing for support of error recovery**。Michael L. Ziegler、Lawrence D. K. B. Dwyer、Carol L. Thompson、Hewlett-Packard Development Company, L.P.、公開2004-03-16。[USPTO公報](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6708288)。2026-10-24に475,354byteの10頁PDFを取得し、SHA-256 `5555cf56065576c49b45e9f82e4ce65778e1d18d745263dc16afb912cd92ca0b` を記録した。画像PDFのため、表紙、PDF7–10頁（説明column1–5、請求項1–13）をページ画像で読了。図面5枚そのものの詳細比較は未実施。

中間コードからcheckpointを特定し、関連するdata object集合を対応させ、状態保存コードを自動生成する。請求項4は区間前後の保存、10は保存要求量の局所最小点を扱う。説明は外部書込みがrollback可能性を制限することも記述する。Bの限定binary効果解析とhost旧値viewとは対象・保存後の用途が異なるが、境界に応じて保存対象とコードを生成する一般形は先行する。用途をWasmへ変えたという差だけで進歩性を認めない。法的な有効性・権利範囲の判断は行っていない。

## A第2設計に近い言語による保護

ShillDB、ACE、Wasmtime hostcall fuel、Cap'n Protoとの追加比較は[追補](prior-art-followup.md)に記録した。

Scott Moore, Christos Dimoulas, Dan King, Stephen Chong. **SHILL: A Secure Shell Scripting Language**, OSDI 2014, pp.183–199。[USENIX本文](https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-moore.pdf)、[Harvard書誌](https://dash.harvard.edu/entities/publication/73120378-e79e-6bd4-e053-0100007fdf3b)。査読済み。Abstract・Introduction、§2.2の契約説明、§2.4.2のinterfaceと機能の分離、§4.2の測定方法・本文の結果を確認。コード・形式的結果全体の再検証や図表全体の精査は未実施。

capabilityを通じてのみシステム資源へアクセスし、契約とsandboxで実行効果を制約する言語である。実引数の権限と実操作を言語で結び付け、認可を個別の手書き防御から切り離す発想は先行する。A第2設計の限定recipeは、WIT borrowから固定計画・操作別世代へ移す構成が異なるが、DSLやcapability安全性自体を発明と呼べない。SHILLのFreeBSDでの測定と、今回のNode/Jcoの少数ファイル測定は直接速度比較しない。
