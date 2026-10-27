# J再評価からKの追加検証まで：現在の研究判断

2026-10-25。目的は修士研究の新規性。特許の取得可能性を判定する作業ではない。未達を成功へ言い換えず、既存の研究論文本文`paper/main.tex`とは別の研究記録を保持する。

## 判定

**Jの主要原理はWeaveと重なる。Kも現状では「新しい解析アルゴリズム」を主張する主テーマとして推奨しない。404契約で既知の等式解析の別backendと同じ条件を得て、人工chainではその対照がK worklistより約1.5–3.7倍速かった。評価・診断研究としての候補は残るが、自然な用途での必要性は未実証である。**

最新の[修士研究としての厳格な採否判断](masters-verdict-20261025.md)に、既存研究との差と主テーマへ昇格する実証条件をまとめた。

Jはstateを論理化して戻す方式、Kは異なる復元状態をどのAPI/host契約で区別できるか検査する方式である。「Jと違う原理」と「既存研究全体に対して新しい原理」を区別する。

|検証した点|得られた証拠|厳しい結論|
|---|---|---|
|JとWeave|容量・境界・segment寿命を仮想化する主要機構が先行。poolingに負ける条件も実測|Jを新規な主アルゴリズムとして押さない|
|Kの条件合成|memory/table、公開/private、trap後契約、host read/writeを扱う実装。別array式と2engine照合|限定modelの実装検査は進んだ。Wasm全体の機械化証明ではない|
|同じ課題の一般手法|一般SMTも初期版256契約、may版128契約、別2-import対照を同じ条件で解く|Kだけが解ける能力差はない|
|既知のデータフロー計算|atom worklistも400契約で同じ全状態条件。96 cell例で全反復より約8.4倍速い|既知の分配性・増分処理でも解ける。計算順の変更を別の新発明にはしない|
|別実装の既知等式WP|404契約で全状態条件一致。generic IRへloweringし、等式backendはKと別実装|適切な既知対照ではK固有の速度優位も残らなかった。frontendは共有|
|解析費用|人工read-chainで単純一般対照比25–34倍、対照を改善すると約8–23倍|特化の費用効果はあるが、先行最良実装への優位や新原理の証拠ではない|
|具体反例の構成|SMTを使わず280否定caseと長さ最大97の12反例を2engine再生。小caseの生成部分37.8倍|共通前処理込み概算は約1.3倍。既知の二値候補の拡張で、独立した新発明ではない|
|自然な用途|旧corpus242完了本に明示dropなし。目的抽出ffmpeg-mtには7,320 dropがあるが起動後のreader到達なし|自然な復元不具合での必要性を実証できていない|
|実配布binaryの制御変種|ffmpeg-mtのdrop省略で7,320寿命差を両engineで確認し、1 GiB memory hashは一致|元APIの実行数は0。不可観測性は静的十分条件による。自然な不具合ではない|
|実アプリの元の処理を追加実行|ffmpegの音声/画像/失敗処理40回、元と変種20対が一致。wrapper無し対照も一致|上段の元API未実行を有限workloadで補ったが、単純な到達性で説明できKの必要例ではない|
|Wizerの公式CLI|4受理例で2engineの観測一致、drop/table更新4例は明示的未対応|寿命問題の認識・active/passive保存は既存。未対応をbugへ数えない|
|契約の取り違え|必須全上書きと任意部分書込みは旧試験群で区別できず、別の2-import対照で判定が分かれる|試験件数だけでは十分でなく、契約境界の独立対照が必要|
|第三者の再現|source-only artifactを新directoryで展開して実行。v3は79 binary fileを同じbytesで生成|公開/投稿はしていない。外部復元器全体や全corpusは小artifactに含まない|

## 残る貢献候補

限定した復元差について、利用者が観測する範囲、trap後の再呼出し、host効果を明示すると、同じ状態差が一致・条件付き・反例へ分かれる。その条件と実行できる反例を一緒に出し、誤った観測器や環境契約による誤診も検査する、という研究対象は具体化できた。

一方、WP、等式抽象、bisimulation、finite BFS、data independence、may/must effect、call-graph reachabilityは既知である。[文献比較](prior-art.md)にはWhisk、PSyCO、Iris-Wasm、register automata、Interface Automata、GenWasym、StateFork等を含めた。組み合わせを実装しただけとの反論は残り、主題の学術的新規性を確認済みとはしない。

## 成果を確認する順序

1. [Jと先行技術、およびKの新規性評価](novelty-analysis.md)
2. [同期importの設計・実行](guard-import-results.md)、[may/mustの区別](guard-import-may-results.md)
3. [同じ条件を出す一般SMTとの比較](guard-import-generic-results.md)
   および[直接反例生成の成立範囲・費用](guard-import-direct-results.md)
4. [corpusの否定的結果](coverage-results.md)、[ffmpegの到達検査](post-start-results.md)
   および[実binaryの起動・寿命差対照](post-start-live-results.md)
5. [再現手順](quickstart.md)、[artifact v3](../../artifacts/state-witness-import-v3.zip)、[日本語草稿](paper-draft.md)

追加の[既知worklistとの比較](guard-import-worklist-results.md)も保存した。v3 archiveは直接反例までを含み、後から追加したworklist比較はrepositoryのCLIから再現する。

今後、自然な用途・先行著者実装との直接比較・公式意味論への接続が得られないまま、この枝の小例だけを増やして完成扱いにはしない。別方向の候補は[棄却記録](alternative-screening.md)と照合し、仕様の直接利用や既知手法の名前変更を新規発明に数えない。

2026-10-25の追加結果は[等式解析の反証](guard-herbrand-results.md)、[実アプリ処理](ffmpeg-workload-results.md)、[Wizer直接実行](wizer-comparison-results.md)を参照する。これらはartifact v3作成後の追加で、repository内CLIから再現する。
