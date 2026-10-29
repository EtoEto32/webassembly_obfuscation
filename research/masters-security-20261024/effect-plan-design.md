# A第2設計: 単一の処理計画に認可と実行を結び付ける

2026-10-24。第1設計の負例を受けた設計修正。特許新規性が確立したという意味ではなく、修士研究として検証可能な差分を具体化する。

## 問題と修正

第1設計はWITのresource pathへread/writeを注釈し、実効果を別のJS executorへ渡した。この構成ではpathが網羅されていても、copy先のwriteをreadと誤注釈できる。executorが対象を読み直したり待機したりする不備も、抽出器だけでは防げない。[実際の負例](../../results/masters-security-20261024/fence-negatives-v1/results.json)。

第2設計では、read/writeを含む限定recipeをWITに対して型検査し、実引数から一度だけ具体的な操作列を作る。独立の権限注釈を入力として受け取らず、各opcodeが必要権限を決める。同じ操作列から依存ticketを作り、その操作列だけを信頼する同期executorが実行する。

```mermaid
flowchart LR
  W[WITと限定recipe] --> C[型検査とbuilder生成]
  C --> V[borrow期間中の一度の具体化]
  V --> P[固定した操作列]
  P --> D[opcodeから権限依存を導出]
  D --> F[受付点の世代検査]
  P --> X[同じ操作列の同期実行]
  F --> X
```

## アルゴリズム

```text
compile(wit, recipe):
    check each resource path has borrow<resource> type
    check every value reference points to a prior read in its scope
    reject unsupported opcodes and independent permission attributes
    generate a bounded builder for the supported variants/lists/options

prepare(arguments):
    ops := build once from validated lifted arguments
    deps := [(resolve(op.resource), permission(op.opcode)) for op in ops]
    require all deps currently permitted
    fixed := copy opcodes, backend identities, constants, read-result indices
    retain host-owned resource records; discard borrowed wrappers
    store fixed and deps under a one-shot instance-local ticket

admit(ticket):
    consume fixed and deps exactly once
    synchronously with revocation:
        check slot and operation generations
        execute the fixed sequence with the trusted opcode interpreter
    release ticket reservations even if execution fails
```

`read`はread権限、`write`はwrite権限を要求する。copyは独立した隠れたopcodeでなく、read結果をwriteへ渡す二つの操作に展開する。list反復も具体的な操作列になる。aliasは同一実体へ解決するが、slot寿命は個別に照合する。

## 条件付きの対応関係

各操作oの依存に `(o.object, permission(o.opcode))` が必ず含まれ、executorがo.opcodeの規定効果だけを生じさせるなら、実行する全操作の必要権限が受付で確認される。操作列に関する単純な帰納で説明できる。これは一般のeffect systemやcapability languageに近い性質で、新しい証明原理ではない。

信頼するopcode表・resolver・FD ownerが隠れた別の効果を生じさせれば保証は崩れる。必要な事業ルールも型から自動では得られない。例えば「writeできるが特定内容は保存してはいけない」という規則は別の検査を必要とする。

## 実装と範囲

`effect-plan.py`が`effect-recipes.json`を読み、3,298byteのbuilderを生成した。`effect-engine.cjs`は固定した操作列と台帳を外部callbackから隔離する。観測用のdescribeはコピーだけを返し、FD配列も複製して保持する。FDを実際に開いたownerが、処理中にcloseして番号を再使用しないことは引き続き前提である。

subsetはtop-level variant、record field、resource borrow、list反復、単純なoption分岐、read結果の前方参照、固定文字列write。nested option自体は第1生成器で対応したが、第2recipeのifSomeは単純optionだけに制限した。同じleafにread/write両方を要求するrecipe、read結果で次のresourceを選ぶ処理、network、stream、一般loop、非同期backendは拒否又は対象外。

## 実測

同じ実Componentのraw/optを用い、[effect-plan-v2](../../results/masters-security-20261024/effect-plan-v2/results.json)の288条件で内容・戻り値・受付が一致。拒否64、実read44回・write312回で、第1設計と同じ処理を行った。計画の観測コピーを全条件で別実体へ書き換えても内部計画は変わらなかった。外部callbackを渡す2例では呼出し前に拒否した。6種類の不正recipeを生成段階で拒否した。

全方式で同じfile executorを使う[15 process比較](../../results/masters-security-20261024/effect-performance-v1/report.md)を行った。新方式の手書き対照に対する時間比中央値は、read1.004、write1.005、copy0.999、batch8 1.003、optional1 0.992、idle0.999。30 warmup、50回×9batch、5 fresh process/方式。1 KiB入力・warm OS cache・fsyncなし。受付以降の実I/Oを含むが、FDのopen/closeを含まない。36失効条件は全方式で誤判定0。統計的な高速化や本番での同等性能を確立した値ではない。

意図的な誤設定を入力から排除した結果であり、現実の開発者の誤り率が下がることを測定したわけではない。正しい手書き実装を超える新しい安全性を獲得したとも主張しない。

## 先行技術との差分仮説

- OmerのWacky/Shimmerはshimの雛形生成と配置に近い。今回の狭い差分は、効果recipeの実操作と権限集合を同じ具体化済み計画に束縛する点。
- SHILLはcapabilityと契約で効果を制約する言語であり、「言語を制限して権限外の効果を防ぐ」は既知。
- root-scoped quiescenceやepoch revocationは受付時の失効を扱う。受付時検査そのものも既知。
- 従って、WITのborrow期間内に計画を具体化し、hostの所有記録へ移し、同一計画から依存と実行を導く接続に非自明な効果があるかが未解決である。

**最大のReject理由**: 既存のcapability DSLにWIT adapterとepoch検査を付けた自然な構成であり、制限したDSLに従うことで誤設定の自由度が減るのは当然である。第三者の実adapterを同程度の表現力で置き換え、作成・保守上の効果を示せなければ主特許案と断言しない。

## 改訂した請求項のたたき台

### 強い対照を追加した後の判断

[同じ計画を手書きする方式も含めた20 process](../../results/masters-security-20261024/effect-performance-v2/report.md)では、全方式が同じ36失効条件を満たした。生成版の手書き単一計画比は約0.994～1.018。手書き単一計画も独立権限注釈を必要としないため、注釈ずれの排除を生成固有の安全性と主張できない。

[生成器の独立照合](../../results/masters-security-20261024/effect-compiler-audit-v1/audit.json)では、12seed設定（内容が異なるrecipeは6種類）・576入力でPythonの直接recipe実行と生成JS＋実ファイルの最終byteが一致した。scope外参照12設定と上限超過2例を拒否。これは生成器単体の試験であり、576件の実Component呼出しではない。

[ShillDB・ACEとの追加比較](prior-art-followup.md)も広い新規性主張を弱める。WASIのoffset・stream・path操作への適用は未実装。値のlift前の割当を制御する[補助案](abi-preflight-analysis.md)も試したが、正しい非memo方式に対する優位がなく主発明要素には採用しない。

### 技術文案

元のA1と別に第2設計を明確化するための研究用文案であり、出願範囲の判断ではない。

**A1-v2**: WebAssemblyコンポーネントからの要求を処理する情報処理方法であって、型付きインターフェース記述及び資源効果命令を含む処理記述を取得し、前記記述を型検査して処理計画生成部を生成し、借用資源が有効な呼出し期間中に前記生成部を実引数へ適用して具体的な効果命令列を形成し、当該命令列の資源をホストが管理する実体へ解決し、各効果命令の種類から必要権限及びその世代に関する依存記録を導出し、命令列の対象・値参照・依存記録を一回限りの要求記録へ固定し、権限変更と直列化された受付処理で依存記録を照合した場合に、前記固定した同一命令列のみを実行部へ渡す、情報処理方法。

**A2-v2**: A1-v2において、効果命令の権限を独立に上書きする属性及び任意の実行callbackを受け付けず、効果命令の規定権限と実行を同じ命令定義へ対応させる方法。

**A3-v2**: A1-v2又はA2-v2において、資源のaliasを実体別の権限依存に集約しつつ、参照した各slotの世代を別に検査し、borrow wrapperを呼出し終了後の要求記録へ保持しない方法。

**A4-v2**: A1-v2～A3-v2において、readの結果を後続writeの値参照として命令列内に束縛し、受付時に資源の送信先を未固定の入力から再読取りしない方法。
