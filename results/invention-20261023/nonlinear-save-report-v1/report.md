# 非線形共有退避の実測結果

2026-10-23。有限状態のrepair表生成として保存する。独立した強い難読化原理・特許性の確立には至っていない。

探索600例中1例、独立holdout600例中1例で、最良の線形保存2bitに対して非線形保存1bitとなった。主ベンチマークの改善例は探索結果から選んだもので、平均的な効果ではない。3bit・固定copy列の全8!置換40,320例では改善は0件。

主42条件40,362 API呼出し（16,128run、4,032reset、20,202peek）と追試14条件12,614呼出し（5,040run、1,260reset、6,314peek）は一致。期待trapは主9,828、追試3,024。負対照8条件は全て反例を検出。WABT別実行器の42条件420run・420peek、期待trap294件も一致した。

回復器は元encoding・copy列・生成manifestを受け取らず、公開APIを使って全24変換条件の同等遷移表を生成した。2copyでは150 API呼出し、3copyでは200。全状態・全失敗位置を含む試験で一致したが、未知の隠れ状態を持つ任意Wasmの同値性を有限観測だけから保証したわけではない。元ソースの一意な回復という評価でもない。

|case|full / linear / color 保存bit|同じ順のrepair表byte|同じ順の全表byte|
|---|---|---|---|
|copy0|4 / 2 / 2|768 / 192 / 192|816 / 240 / 240|
|copy1|4 / 2 / 1|768 / 192 / 96|816 / 240 / 144|
|copy2|4 / 2 / 2|1024 / 256 / 256|1072 / 304 / 304|

全方式の保存localはi32一つ、temporaryはi32一つ。保存bitの減少はlocal数・実メモリの減少を意味しない。全表byteにはencoding、inverse、save mapを含む。各prefixのrepair表には未使用組合せの領域もある。表のlayout自体を最小化した値ではない。

|case|元 ns|full ns|linear ns|color ns|回復 ns|color/元|
|---|---:|---:|---:|---:|---:|---:|
|copy0|5.7512|12.3501|12.3785|12.1367|3.7945|2.110|
|copy1|6.5692|12.3384|11.7528|11.7604|3.8692|1.790|
|copy2|2.6341|5.1230|5.0906|5.0450|3.7491|1.915|

各processの7batch中央値を3process間で再び中央値にした。45process・315batch、10ms未満のbatchなし。全て同じWasm内loopでreset/run/peekし、入力stateをLCGで変え、出力をchecksumへ反映する。coreはO3後にwrapperを付加し、回復coreには追加O3なし。V8によるinlineを含む。trap経路の速度は未測定。linear/colorの速度差は小さく、安定した高速化とは主張しない。

|case|元 / full / linear / color / 回復 O3 core byte|
|---|---|
|copy0|188 / 734 / 641 / 638 / 354|
|copy1|188 / 731 / 649 / 606 / 354|
|copy2|208 / 970 / 830 / 820 / 370|

改善例copy1ではlinear649→color606byteで43byte（約6.6%）減少。holdoutの改善例もlinear651→color595byte。ただしfull/linear/colorは共通lookup emitterであり、それぞれに最適化した手書き実装との比較ではない。全条件のlinear memoryは65536byte。RSSはwhole-processで、生値とばらつきはruntime/summary.jsonとraw.jsonを参照。

変換 78.205–81.082ms、主回復 66.136–495.987ms、holdout回復 66.865–70.896ms。各条件1回でprocess起動やWABT呼出しを含む。反復した実行時間測定と混同しない。

失敗分類：今回の正条件にvalidation失敗・実行器クラッシュ・timeoutはなかった。profile外のmemory export、extra global、wrong peekの3入力は意図して拒否。audit-v1は正常voidのログparser不備により未完了で、修正後v2を正結果に用いた。未対応やログ不備を保護成功に数えない。

脅威モデルの限界：4個のbinary byteだけで全状態は16。公開reset/peekが全状態学習を容易にする。一般byte・任意heap、実アプリ、実デコンパイラ評価は未実施。既知のfunctional index codingとcographとの差が弱いため、表削減という工学的な結果を強い特許候補や新しい解析耐性と呼ばない。

入力・出力・実測・証明書・別実行器ログ・未完了audit-v1をsha256.jsonで固定。sourcesに集計時のコードと共通helperを保存した。model.pyに後から追加したXOR線形性assertは出力を変更しない検査であり、holdout実行時にも通過した。
