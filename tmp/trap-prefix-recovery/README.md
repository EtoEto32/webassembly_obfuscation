# トラップ前書き込み統合の復元試験と棄却判断

2026-10-12。trap-prefix-fusionの追加検証。前回の作業は変換器と104本の正しさ試験を保存した進捗あり。今回はバイナリを入力とする復元器を実装し、保留だった候補の判断を更新した。

## 判断

**現在のtrap-prefix-fusionは難読化候補として棄却する。** 書き込みの物理的なcommit列を変えても、保留したstoreのアドレス・値・有効性がforwarding処理に残り、今回定義した強い観測者は元の有効store列を復元できた。

原方式の意味保存試験は有効なままであり、その結果やコードは変更しない。全Wasm変換やすべてのログ式難読化が容易だと示したわけではない。今回の具体的な変換規則と13プログラムに対する結果である。

## 実測

- 対象: 13プログラムのdeferred-coalesced版、raw/O2各1本、計26本。
- 各224入力、合計5,824実行。
- 元の実行で有効だったstore32の順序付き列は、全5,824件で一致。うち空でない列は5,308件、含まれるstore総数は10,228件。
- 最後に上書きされるstoreも含めて照合。trap以降の無効storeは除外。
- 計測を追加したバイナリの返り値・trap種類・最終memory SHA-256は、計測前の保存済み実行記録と全件一致。

この数字は元ソースの復元率でも、全入力に対する同値性証明でもない。入力ごとの実行時書き込み列を復元した結果。元の命令位置や任意入力に対するアドレス式まで合成したわけではない。

## 解析者の情報と実装

recover.cjsは別プロセスで、候補バイナリ、公開入力タプル、初期memoryだけを読み取る。元IR・元WAT・変換対応表を読まない。verify.cjsだけが元IRを独立に逐次解釈し、正解store列と照合する。

WABT wasm2watで候補を式形式へ戻し、唯一の5個のi32引数を持つ関数を補助関数と推定する。最後の3引数をアドレス・値・有効性と解釈する。関数名やlocal名はWABT生成名で、変換器の役割名に依存しない。ただし署名と引数の意味を知る方式依存のヒューリスティックであり、未知の汎用Wasmへの解析ではない。

loadから得たwordがlocal.set/get/teeと補助関数呼出しを通る経路を追い、同じwordに対するforwardingをグループ化する。最も大きいグループ（同数なら最後）を選ぶ。補助関数の入口に記録用importを挿入し、有効なレコードを呼出し順のまま取得する。正解に合わせて並べ替えたり要素を選んだりしていない。

今回の全プログラムでは最後のloadが全先行storeをforwardするため、このグループが全ログを含む。最適化後も補助関数が残った。他の最適化設定、helperがinline化された版、最後のloadがない版、同じ署名が複数ある版では同じ復元器の適用を確認していない。未対応命令・構造で止まることを耐性の証明にしない。

## 失敗した解析器と修正履歴

事前条件はprotocol.mdに残したが、実装は次の修正を行った。従って完全な事前固定・盲検の解析結果とは呼ばない。

1. v1は構文上の入れ子だけでグループ化。raw版ではlocalへの個別代入でforwardingが並び、最初のプログラムで必要なstoreを取りこぼした。recover-v1.cjs、verify-v1.cjsとartifactsを保存。
2. v2はlocalの値の由来を追跡。8本を処理後、forwarded-addressのrawで停止。ifの条件に使ったアドレスの由来と、そのifが返すload値の由来を混ぜていた。recover-v2.cjs、verify-v2.cjsとartifacts-v2を保存。
3. v3はifの返り値の由来をthen/elseからだけ求めるように修正。最新版recover.cjsとverify.cjs、artifacts-v3が最終結果。26本すべてで一致した。

v1/v2の失敗は解析器の制限・不備であり、候補の強度を示すとは扱わない。v3の適用範囲にも同種の制限は残る。入力集合は前回の正しさ試験と同じで、独立の未使用コーパスではない。方式を知った上で開発した限定解析である点を明記する。

## 先行研究の照合

Mahlkeほか、Sentinel Scheduling for VLIW and Superscalar Processors、ASPLOS-V 1992。Illinois大学配布の本文§3.1、§3.6、§4.1–4.2を確認。投機的storeの保留、有効性・例外情報、loadへの転送、後での確定/無効化が記述される。同一基本ブロック内の例外順序を保証しない点も本文に明記される。

https://courses.grainger.illinois.edu/ece511/fa2005/papers/mahlke.1992.asplos.pdf

今回のfirst-fault prefixと完全に同一とは言わない。一方、storeの保留・転送・確定を新しい原理とはできない。byte単位の最後のwriterによる統合まで、この一つの資料が同一に扱うとも主張しない。1993年TOCS版は書誌のみ確認し、今回読んだ本文は1992年版。

https://experts.illinois.edu/en/publications/sentinel-scheduling-a-model-for-compiler-controlled-speculative-e/

研究上の採否は、既存研究との完全一致を証明したからではなく、今回の保護対象を復元でき、独自の強度を裏付けられなかったために棄却とする。

検索: Mahlke sentinel scheduling 1993 pdf site:illinois.edu / Sentinel Scheduling filetype:pdf site:umich.edu / store coalescing precise exceptions。Michiganの講義ページ取得は502で失敗。著者コード・ハードウェアの再現は行っていない。

## 再現と保存内容

Node v24.15.0、WABT1.0.42。verify.cjsを実行すると、元候補のartifacts-v2を読み取り利用する。TRAP_FUSION_ARTIFACTSで参照元を変更可能。WASM_TOOLS_ROOTでWABTの親ツールディレクトリを指定できる。既存結果を保存する場合はこのディレクトリを別名へコピーしてから再実行する。

- artifacts-v3/results.json: 26本の入力・計測後バイナリSHA-256、静的なグループ選択、件数、照合結果。
- artifacts-v3/public-inputs.json: 復元器へ渡した公開入力。
- artifacts-v3/<入力ファイル名>/instrumented.wat, instrumented.wasm: 計測を挿入した実行対象。
- 同 observations.json: 全観測、復元列、返り値、trapメッセージ、最終memory hash。
- 同 extraction.json: 署名から選択した関数、グループ、使用したヒューリスティック。

elapsedMsは子プロセス内の変換・実行・記録を含む単発の所要時間で、解析アルゴリズム単体の反復性能測定ではない。棄却条件を満たしたため、候補の大規模性能測定は行わない。

## 全体目標との関係

この候補の保留を解消したが、新規性と有効性を支持できる採用アルゴリズムはまだない。次候補でbyte幅やログ順序を変えるだけの拡張はしない。保護したい情報が補助関数の引数や局所状態としてそのまま残る原因を解消する具体的な規則が必要。復元器を作る評価研究へ目的を置き換えず、研究全体の目標は継続する。
