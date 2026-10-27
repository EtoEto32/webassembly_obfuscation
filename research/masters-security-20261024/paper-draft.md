# Wasm再入境界における書込み上界に基づく旧値viewの生成と適用限界

研究草稿、2026-10-24。査読提出稿・特許出願稿ではない。新原理の確立を主張する段階にない。

## Abstract

WebAssemblyとhostの再入境界では、hostが検証したlinear memoryの値がcallbackにより変化する場合がある。本研究候補では、実行binaryから導く書込み上界Wとhostの読取り契約Rの交差のみを退避し、旧値viewを生成する限定プロトタイプを検討した。自作Rust処理8種の48 binaryで部分退避の適用は12本から28本へ増え、同じ6,528入力の旧値viewは一致した。128本・8,960入力の追加試験では、308 trapを含み観測変更の上界漏れはなかった。別bytecode解析も98部分要約を確認したが、機械検証済みではない。性能はconsumer契約に依存する。checksumの事前計算が可能な場合、本方式の必要性は弱い。読取り位置が再入後に渡される小実験の7例では、全コピーの約0.41–0.73倍の時間となった。一方、第三者hash-wasmの48条件・1,680入力では全量fallbackが多く、保存量の削減は0だった。既存state saveの小ささも、本方式の必要性を弱める。静的checkpoint等との近さ、用途の限定、解析器の形式的健全性が未証明であることが主な限界である。

## Introduction

本研究の長期目的は、修士研究と両立する範囲でWasmセキュリティの発明候補を検証することである。難読化だけに限定せず、認可依存の失効フェンス（A）、再入時の旧値view（B）、非同期資源の返却義務（C）の3案を比較した。本稿は、契約・正当性・性能を一つの境界で測定できるBの検証結果と適用限界を報告する。特許可能性の高さを確認した研究ではない。

従来のIP保護に関するリポジトリ内の研究結果は、本稿の新しい成果として再計上しない。本稿はBの具体化と、その適用限界の報告に対象を絞る。

## Related Work

[RLBox](https://www.usenix.org/conference/usenixsecurity20/presentation/narayan)には境界値の検査とfield単位のfreezeがあり、[Lightweight Memory Checkpointing](https://download.vusec.net/papers/dsn-2015.pdf)には静的解析による保存・計装削減がある。[SafeFetch](https://www.usenix.org/conference/usenixsecurity24/presentation/duta)はkernelでの既読値cacheによってdouble-fetchを防ぎ、既存buffer再利用も扱う。[Iris-Wasm](https://doi.org/10.1145/3591265)はWasmとhostの相互呼出しを含む合成検証の基盤である。

公報[EP4343593B1](https://patents.google.com/patent/EP4343593B1/en)には信頼側cacheによるcheck/use、[US6154877A](https://patents.google.com/patent/US6154877A/en)には保存するdata structureを識別するprecompilerとshadow構造の生成がある。したがって、部分コピー、保存コードの生成、旧値の提供、hostを含む検証をそれぞれ初めて実現したとは主張しない。

読んだ節・請求項と未読箇所は[調査記録](prior-art.md)に固定した。既存資料を組み合わせれば容易に得られる構成である、という反論をまだ解消していない。

## Motivation

例えばhostがguest内のdescriptorとbufferを検査し、callback後に検査時点の値を利用する場合がある。callbackが触るbyte数が少なくても、単純な全コピーではbuffer全体を境界をまたいで保持する。静的効果の上界が十分小さければ、保存量を減らす余地がある。

ただし、最終consumerが既知のchecksum等であれば、callback前に結果を計算して保持できる。これを無視して全コピーだけに勝つことは、採用理由を示さない。本研究ではこの反証を実装し、読取り位置がcallback後に決まるview契約と分けて評価した。

## Threat Model

hostと解析器は信頼し、guestは検証を通る任意のWasm命令を含み得る。対象は単一の非共有memory32で、callback実行からhost consumer終了まで、対象callback以外のwriterを許可しない。R、引数、対象binaryを事前に固定する。未知の効果は全コピー、共有memory等の契約外は拒否する。

本方式はWasm engineの脆弱性、host自体の任意メモリ破壊、共有writer、任意期間保持するview、一般的なguestのメモリ安全性を扱わない。外部サービスへの攻撃や資源枯渇実験は行っていない。

## Proposed Method

callbackのすべての実行prefixに対する書込み上界をWとし、S=R∩Wを保存する。callback後の各a∈Rについて、a∈Sなら保存値、そうでなければguest memoryの値を読む。Wが健全ならR\Sは不変であるため、旧値viewは実行前と等しい。

解析は入口引数・定数・i32演算の式とunknown値を追う。値がunknownでもstore先が既知なら範囲を得られる。分岐先ごとにlocal環境を分け、store前の評価順を守る。直接呼出しでは実引数を代入する。trapまでの副作用を含める。loop・再帰・indirect call等は全コピーへ退避する。[詳細な条件付き論証](soundness.md)を参照されたい。

この手順は既知の抽象解釈とframe性を使う。ここで示す限定実装を、新しい静的解析原理と呼ばない。

## Implementation

Python 3.9、Node 24.15.0、WABT 1.0.42、Binaryen 133を使用した。Rust追試には1.97.0-nightly（2026-05-11）を用い、対応する公式stdlibをhash照合してworkspace内に配置した。実行するbinaryをWABTでvalidateし、folded WATを解析する。

`certify.py`は入力byte列を一度だけ読み、同じbyte列のvalidation・解析・hashを行う。JSON証拠を第三者から受け取る場合は再検査が必要であり、hash一致だけで内容は信頼しない。WIT・Canonical ABI・WASIの完全統合、独立な証明checkerは未実装である。

## Evaluation

|実験|対象|結果|解釈|
|---|---|---|---|
|初期B|18 binary、3,744入力|旧値不一致0、466 trap|限定命令の動作確認|
|実再入|14 binary、1,498入力|旧値不一致0、232 trap|Wasm→host→同じWasm、到達calleeと疎なR|
|Rust compiler|同じ48本、6,528入力|部分退避12→28、両版不一致0|自作8処理のcoverage。第三者アプリではない|
|制御フロー監査|128 binary、8,960入力|308 trap、観測変更13,240byteの上界漏れ0|等値storeの動的検出ではない|
|契約の反例|別writer、引数再束縛、別binary|3例すべて旧値不一致|前提を外すと成立しない|
|checksum consumer|5方式×5 process|事前計算対照が有力|この用途でsnapshot必須とはいえない|
|復帰後query|4方式×5 process|受理7例の全コピー時間比0.41–0.73、loop 1.12|読取り位置が準備時に未知という限定契約|
|第三者library|hash-wasm 8種×3入口×raw/O3、1,680入力|不一致0、部分解析2/48、保存量削減0|既存saveの小さいstateに対する効果なし|
|別bytecode checker|224本、部分要約98|98受理、501構造改変・224別hashを拒否|二重実装による確認。機械検証ではない|

Rustの受理28本における保持payload合計は31,195,136byteから150,648byteへ減った。これは同じ入力集合の合計で、RSSや全体のメモリ使用量の比ではない。materialize版では復帰後に全bufferの確保が必要である。

性能は各processで100回warmupし、300呼出し×9 batchを測定した。process順はseed付きでshuffleし、5回の独立反復の中央値とIQRを保存した。query試験では全bufferのchecksumを対照へ課さず、4方式とも要求された16byte値を返す。

原表：[checksum v1](../../results/masters-security-20261024/consumer-v1/report.md)、[強い対照を追加したv2](../../results/masters-security-20261024/consumer-v2/report.md)、[復帰後query](../../results/masters-security-20261024/query-v1/report.md)。複数版の数値を独立標本として合算しない。

第三者libraryの[48条件](../../results/masters-security-20261024/library-v1/report.md)では、保存payloadは147,000byteから減らなかった。既存stateは4～208byteで、同libraryのsave()はstateと4byteのbinary識別子だけを保存する。この既存処理を無視して全memoryコピーと比較すると効果を誇張する。別checkerの[結果](../../results/masters-security-20261024/checker-audit-v1/audit.json)は構文の異なる経路から要約を確認したが、checker207行に対しproducer136行であり、trusted codeの縮小を達成していない。

## Discussion

実験は、対象callbackの効果が小さく、hostが実行前の任意のbyte値を後から必要とする場合に、保存量と一部の費用を減らせることを支持する。単純なchecksumのようにconsumerを前倒しできる用途では、その方法を優先するべきである。読取り位置が先に分かる場合は、その位置だけを保存する対照も必要となる。

研究上の価値候補は、誤りやすいWasmのtrap・分岐・アドレス計算を含め、どの範囲まで自動で安全な旧値viewを生成できるかの測定である。これが従来checkpointの移植以上の技術的貢献になるかは、まだ判断できない。

## Limitations

性能fixtureは自作である。第三者hash libraryのコードをharnessで呼ぶ試験は追加したが、実アプリケーションでの採用効果、複数engine、BへのWITからの生成、loopやindirect callの実用的coverage、機械検証されたchecker、既存RLBox/SafeFetch実装との比較は未達である。テスト成功は全入力の同値性・健全性の証明ではない。性能にはJIT・GC・機器負荷の影響がある。前倒し計算との比較から、benchmarkのconsumerを選ぶだけで見かけの価値が変わる危険も分かった。

## Conclusion

旧値viewを生成する限定Wasm解析器と、正負の実行例、compiler出力へのcoverage、consumer契約ごとの性能を再現可能に保存した。強い特許新規性の確立は未達である。次の採否判断には、実アプリケーション2種で、前倒し計算・手書き最小退避・既存のfreeze相当処理に対して自動生成の利点を示す必要がある。
