# 観測契約によってWebAssemblyの復元差をどう評価すべきか

修士研究候補の日本語草稿、2026-10-25。投稿・公開はしていない。新しい一般解析アルゴリズムの成立を主張する完成稿ではない。追補が重なった旧稿は[履歴](../../results/state-witness/paper-revision-v1/previous-paper-draft.md)に保存した。追加の強い既知対照により、現状では新解析算法を主張する主テーマへの採用を推奨しない。

## Abstract

WebAssemblyの復元をmemory bytesだけで検査すると、segment寿命や関数参照の差を見落とし得る。しかし、内部状態の差が全て元APIの不具合とは限らない。本研究は観測範囲・trap後の再呼出し・host効果を明示し、復元差を内部差、元APIの反例、限定モデルでの一致、未対応へ分ける診断試作を示す。定数bulk memory/table APIについて初期storeの一致条件と具体反例を生成する。旧393反例の63件は追加observerだけの差だった。同じ78初期storeでもtrap後再入を許すと21差、終端とすると13差となった。同期host profileの384契約を一般SMT等と照合し、直接生成した280小反例と最大97 APIの12反例を二engineで再生した。一方、一般SMTと既知worklistも同じ条件を解き、固有の一般解析能力は示せなかった。実配布ffmpegの制御変種は7,320寿命差を持つが、起動後のreaderへ到達しない。これらを契約依存の評価事例として提示し、自然な復元不具合での必要性と主題の学術的新規性は未確立と結論する。

## Introduction

保存した内部状態を正確に戻すことと、利用者が見る動作を保つことを区別する必要がある。前者の失敗は復元契約への違反になり得るが、後者の失敗、脆弱性、情報漏えいと同義ではない。逆に返値だけの比較では、trap前に変わった公開memoryを見落とす場合がある。

先行試作Jは同一instanceの論理状態を戻した。しかし主要な容量・境界・segment寿命の仮想化はWeaveと重なり、大memory条件ではpoolingより遅かった。[厳格な比較](../logical-reset/strict-review.md)に基づき、Jを新規な主アルゴリズムとして採用しなかった。Kは復元機構ではなく、その差を診断する試作である。

研究質問は、(1) 同じ内部差でも観測契約により評価が変わるか、(2) 制限したAPIについて具体storeを超えた一致条件と実行可能な反例を出せるか、(3) 既知の一般手法でも解けるか、(4) 自然な適用状況があるか、である。最初の二つには限定した実証がある。三番目では固有能力を支持できず、四番目は未達である。

## Related Work

Wasm仕様のbulk-memory test、Weaveの寿命保存test、関係witnessを検査するWhiskは状態やtrapの検査を既に扱う。Iris-Wasmはhostを含むWasm論理を機械化し、WasmVerifierはCHCによる安全検証を扱う。KのprobeやWPを新しい一般原理とはしない。

PSyCO、register automata、関係論理、分配的データフロー解析には条件合成・等式関係・有限fact計算という近い原理がある。Interface Automata等は利用順序を扱い、StateForkは許された将来操作に対する観測同値を復元契約として記す。観測を基準にすること自体も独自ではない。

ESOP2005のInterprocedural Herbrand Equalitiesは、等式連言の逆代入、未知値代入、異なる二値への簡約を具体的に示す。追加実装ではこの既知の規則をcopy/constantの汎用IRへ適用した。Wizerもactive/passive segmentを区別して保存し、dropを明示的に未対応とする。これらをK独自の問題発見や解析原理に数えない。

GenWasym/OOPSLA2026はsnapshotを使うWasm concolic compilerで、Kとは出力課題やprofileが異なる。著者toolへの速度優位を主張しない。全文が読めなかったWEST等の内部手法を推測しない。著者・年・発表先・URL・読了範囲・査読論文とpreprintの区分は[文献表](prior-art.md)を参照する。

## Motivation

非空passive segmentをdropしてもmemory bytesは変化しないが、後続initはtrapし得る。他方、元APIから読む道がなければ寿命差を利用者は観測できない。検査用exportを追加して初めて見える差もある。

hostの書込み契約も重要である。毎回必ず全上書きするhostは差を消し得るが、書込みが許されるだけなら、何も書かずに差を残せる。旧対照128契約では両者の条件が同じで取り違えを検出できなかった。別2-import対照では、必須全上書きで無条件一致、任意部分書込みで全初期storeに反例となった。試験数だけでなく契約境界を検査する対照が必要である。

## Threat Model

trusted test hostが二つのWasm状態の以後の動作を比較する。観測は全store、公開memory/table、return/trapのみから選び、trap後の終端または再入も指定する。host効果は公開領域のread有無、writeなし、必須全上書き、任意subsetへの書込みを区別する。左右に対応する入力とmaskは共通とする。

同期import profileはvoid・引数なしで、readはwrite前に行う。summaryは信頼入力であり、hostコードから自動証明しない。host再入・grow・host例外・外部I/Oを含めない。条件合成はshared state、任意分岐、活性stackを扱わない。指定された継続位置と実復元PC/stackの対応も自動証明しない。

別の到達検査と最初のffmpeg対照はshared memory宣言を扱うが、最初の起動対照では並行workerを起動しない。追加の実アプリ試験はNode worker_threadsの局所adapterで公式JS glueとworkerを動かす有限実行であり、Kの非共有modelの適用範囲を拡張する証明ではない。時間・OOM・engine-private introspectionは観測外である。詳細は[攻撃モデルと信頼条件](threat-model.md)に記した。

## Proposed Method

まずmemory、数値global、table参照、segment寿命のobserverを生成する。非空segmentの寿命はdst=0、src=1、len=0のinitの成功/trapで区別でき、0byte転送なのでguest storeを変えない。空segmentにはこの区別を要求しない。既存仕様に基づく観測である。

元APIへの影響は別に判定する。exportと全literal関数参照をrootとしてdirect/tail call閉包を作り、segment readerが到達しない場合を十分条件として分類する。start完了後・保留frameなしという前提が必要で、readerが到達する場合は保留する。

条件合成では寿命状態対からAPIを次のimportまたは終了まで実行し、copy/constant写像とtrap位置を得る。左右storeを別変数で保ち、必要な一致を等式連言として逆伝播する。

```text
R_0(q) := true
R_(n+1)(q) := AND over APIs a of
    WP(a, local observations AND R_n(successor(q, a)))
at a terminal trap, omit only the successor condition
```

必須全書込みでは対象cellの左右を共通新変数へ置換して普遍量化する。任意部分書込みは等式連言に限りR AND close_all(R)へ簡約できる。一般Boolean式では成立しない反例を保存した。初期条件だけでなく各状態で環境効果を閉じる必要がある。

不成立storeからは固定点のrankを下げて反例列を取り出す。host値はSMTで生成できる。直接生成では全base代入と一cell変更のN+1候補から等式を破る値を選ぶ。may-writeではno-opまたは全書込みで構成できる。この特化を新しい一般探索原理とはしない。import profileの最短性は主張せず、閉じた旧profileの結果と区別する。[設計と限定論証](guard-import-direct-results.md)を参照する。

## Implementation

Python3.9、WABT1.0.42、Node24.15、Wasmtime50.0.1、Z3 4.13.3を用いる。Rust/wasmparser0.227.1で実binaryを全走査する。CLIは観測契約を指定し、未対応・上限到達を成功へ含めない。

比較用に一般SMT WP/QE、有限domain BFS、CHC/Spacer、等式atom worklistを実装した。自作encoderであり先行著者toolの追試ではない。array版は実行式を別に持つがparserを共有し、worklist版はWPも共有する。独立性の度合いを区別する。

追加の汎用等式backendは、Wasm frontendと区間effectを共有する一方、等式の正規化・逆代入・任意入力・固定点をKのhelperとは別に実装した。任意部分書込みをcellごとの選択として合成し、Kのmask簡約を使わない。これはESOP2005全体の再実装ではない。

Weaveのwrapperで参照や再開metadataが変わる場合、sourceのobserverをそのまま合成しない。観測用複製とresume用複製を分け、参照directoryにも信頼前提が残ることを対照で示した。

[package v3](../../artifacts/state-witness-import-v3.zip)は新directoryで79 binary fileを同じbytesで再生成した。複製を含み79独立programではない。worklistとffmpegは小packageに含めず、repositoryの[再現手順](quickstart.md)と各実験CLIを用いる。

## Evaluation

### 契約と反例の意味

全store契約の393反例は元return/trap差96、元公開memory差234、追加observerだけのprivate差63に分かれた。最後の63を公開API不具合と数えない。同じ964初期storeはfullで393差、publicで330差、returnsで114差だった。[観測範囲の監査](guard-observation-audit.md)に対応する。

別78初期storeでは再入を許す21差が終端で13差となった。Weaveの公開driverはtrap後再入を拒否するため、coreの呼出し規約だけを根拠にdriverの不具合とはしない。限定terminal/returnsでは一回判定と固定点が7,536寿命対で一致し、全契約に深い探索が必要という主張も支持されなかった。[protocol比較](guard-protocol-results.md)を参照する。

### 正当性と一般手法

同期hostの旧256契約は別array式1,164義務がUNSAT、may128契約は588義務がUNSATだった。旧BFSの1,024 store、may版512 storeも一致した。一般SMTは384契約と別2-import対照で同じ条件を得た。worklistは旧384＋chain16の400契約で全状態条件が一致した。未知結果を成功へ含めない。

さらに独立した等式backendの全反復版・worklist版も、上の400契約と別2-importの4契約で全状態条件を一致させた。Wasmからgraphへのloweringは共有するため、公式意味論から独立した検証とはしない。[追加反証](guard-herbrand-results.md)に記録した。

直接生成器は384契約・768初期storeを照合し、その248否定caseと別32 caseの計280反例を二engineで再生した。肯定520 storeは今回の追加試験では条件照合であり全列実行の件数ではない。長いchainの12反例は2/9/33/97 APIで再現した。実行試験だけで任意入力の同値を主張しない。[直接生成](guard-import-direct-results.md)、[may/must](guard-import-may-results.md)、[worklist](guard-import-worklist-results.md)に詳細がある。

### 費用

人工read-chainでは一般SMTにcache・support限定置換・solver再利用を追加すると、等式版の速度差は初期対照比25–34倍から約8–23倍へ縮んだ。条件だけのworklistは96 cellで全反復比約8.4–8.7倍速い一方、小例では遅かった。両者ともrank履歴を保存しない条件で比べた。

このSMT比較だけでは優位を主張できない。追加した汎用等式worklistは16人工chain条件でK worklistより約1.5–3.7倍速かった。96 cellのhost-read/必須write条件では9.381 ms対34.392 msである。4方法各3独立process、各2warmup/5測定で、graph構築を含めparseを別計上し、Z3をロードしない。既知原理による強い対照にはKの速度優位が残らなかった。

280反例のbatchは直接版22.457 ms、自作SMT版848.841 msだった。3独立process・各2warmup＋5反復のprocess中央値の中央値である。共通前処理は約2.65 sあり、前処理と生成中央値を足す概算では約1.3倍となる。38倍を解析全体の改善と表示しない。whole-process memoryは両harnessがZ3を含むため単独CLIの値ではない。自然なアプリや先行最良実装への一般化も行わない。

### 外部実装と自然な用途

公開wasm-migrate/Weaveを固定sourceからbuildし、公式由来14 module・17中断位置の272変換条件を比較した。前者の4元moduleでentry成功/trap差を得たが、作者確認済みbug数ではない。別import fixtureでは24復元中4条件で公開memory差があり、entryのtrap/host traceは一致した。4条件は二サイズ×二停止位置である。Weaveの対応24条件は一致した。保存PC/stackや復元metadata全体の証明とは分ける。

実アプリ由来242完了binaryには明示dropがなかった。追加したffmpeg-mtには7,320 dropがあったが、全readerがstart専用で起動後到達なしの十分条件を満たした。drop省略変種を二engineで起動すると7,320寿命差が生じ、1 GiB memory hashは同一だった。全29,280 probe callもmemoryを変えなかった。ただし元API実行数は0で、動画変換や自然な復元bugの再現ではない。[静的調査](coverage-results.md)、[ffmpeg対照](post-start-live-results.md)を参照する。

この元API未実行という不足に対し、追加試験では公式glueを使い、音声resampling、可逆圧縮/復号、画像処理、不正入力の拒否を計40回実行した。元と寿命差変種の20観測対は一致し、8 roundtripは元PCMへ戻った。計数wrapper無しの対照も一致した。Node上のbrowser-worker adapterを使った有限試験で、実復元器のbugではない。到達性だけで説明できるため、Kの条件合成が必要な例ではない。[実処理の結果](ffmpeg-workload-results.md)を参照する。

公式Wizer/Wasmtime CLI50.0.0も実行した。active/passiveの順序と初期化値を変えた4例を受理し、二engineでそれぞれ20観測対が一致した。data.dropの位置3対照とtable.initの1対照は明示的未対応で、不具合に数えない。[直接比較](wizer-comparison-results.md)にsourceとreleaseのhashを保存した。

## Discussion

観測契約が評価の結論を変えること、observerの合成失敗があること、契約境界を区別しない試験群が誤解を見逃すことを実測した。これらは具体的な評価事例と実装成果である。

全内部状態の一致を契約として要求する復元器なら、元APIで観測できない差もその契約への違反となる。その検出を誤検出とは呼ばない。本稿が避けるのは、内部差の検出結果を、別の観測契約におけるアプリ失敗や脆弱性の件数へ説明なく換算することである。先行研究の契約を読み替えて欠点を作らない。

しかし観測同値・WP・等式抽象・data independence・worklistは既知である。Kだけが解ける課題や先行最良法を超える能力は示せなかった。速度差も特化と実装改善で説明可能である。修士研究として残る候補は、Wasm復元評価の判断を変える独立した事例と評価手順である。世界初、採択可能、学位研究として十分という結論はまだ出さない。

## Limitations

* 最大の不足はKの条件合成が必要な自然な復元不具合で、ffmpeg対照もこの不足を埋めない。
* 自作SMT/BFS等との比較はあるが、Whisk、Iris-Wasm、GenWasym等の著者実装との同一課題比較は未実施。
* 公式Wasm意味論への機械化接続はない。共有parser、trusted summary、指定継続位置、参照対応などの前提を持つ。
* 一つのWindows環境と限定profile、主に人工・公式test由来の差であり、一般アプリの精度や発生率へ外挿しない。
* ffmpegのWasmtime実行では固定Python bindingのpointer型不整合をlocal adapterで補った。元packageは変更せず小controlを通したが、通常bindingをそのまま使った追試ではない。
* 小artifactは全実験や依存binaryを含まない。単発時間と正式測定、観測回数と独立事例数、内部差と元API差を区別する。

## Conclusion

Jの主要原理は先行技術と重なり、主案採用を見送った。別原理のKでは契約に応じた復元差の分類、限定条件合成、具体反例、実装と再現資料を得た。同時に一般手法も同じ条件を解けることと、自然な用途の不足を確認した。

現段階は診断実装と反証を含む評価事例であり、新しい解析アルゴリズムを主張する修士研究の主テーマとしては推奨しない。契約依存の評価手法として再検討するには、独立した用途で既存手順の判断を改善する実証が必要である。次の判断は[厳格な採否条件](masters-verdict-20261025.md)に基づく。
