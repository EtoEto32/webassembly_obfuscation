# ffmpegの元の処理を実行した追加対照

2026-10-25。[事前計画](masters-retest-plan.md)の追加実験。

## 結果

[実測summary](../../results/state-witness/ffmpeg-workload-v1/summary.json)では、元binaryとstart内のdata.dropを省略した制御変種の間で、終了コード・出力bytes・記録したerror logが全て一致した。音声resampling、FLAC符号化、復号、画像拡大縮小、存在しない入力の拒否を、各instanceで順に実行した。

|単位|実測|
|---|---:|
|元と変種、3入力seed、計数wrapper有り|6 process、30 command|
|計数wrapper無しの独立対照|2 process、10 command|
|比較したcommand対|20対、一致20、不一致0|
|lossless音声roundtrip|8/8で元のPCM bytesへ復帰|
|main threadのWasm export呼出し|計数有り6 processで768回|
|そのうち元ffmpeg entry `Ma`|30回|
|起動したworker|各process32、計256|
|timeout/harness error|0|

同じseedのwrapper無し対照も一致した。4種類の正常出力はいずれも3 seedで3通りのhashになり、処理が入力を無視していないことも確認した。入力音声・画像、出力ファイル、各runのJSON、stdout/stderr、source copyとSHA256を保存した。結果の単位は実行回数であって、独立したbugや独立した実アプリ数ではない。

配布npmのUMD JS/workerはintegrity検証した原本のまま使用した。ただしこのglueはbrowser-worker専用buildなので、self/location/Worker/importScriptsをNode worker_threadsへ対応付ける局所adapterを用いた。実ブラウザでの再現、Wasmtimeでのアプリ全体の実行、任意のbrowser APIの忠実な再現とはしない。worker内部のexport呼出し総数は測定していない。公式glueは終了時のAborted例外を捕捉してretを返すため、正常処理にもそのstderrが出る。正常codeと生成物の検査を満たすこのlogを新規trap障害へ数えない。

## 新規性への影響

前の[起動のみの試験](post-start-live-results.md)に残った「元API実行数0」という不足は、この有限workloadについて解消した。一方、7,320の寿命差が全入力で不可観測であるという主張は、この有限試験では証明していない。単純な起動後到達性の十分条件が既にこの事例を分類するので、複雑なK条件合成の必要性を示した結果でもない。

自然に発生した復元bugや実復元器の実行は含まない。制御変種の差をアプリ不具合件数へ換算しない対照としては強くなったが、Kの修士研究主テーマへの昇格条件は依然未達である。内部状態の完全一致を要求する契約なら、寿命差を報告する検査は正しい。

## 再現

repository rootで、未使用の出力directoryを指定する。

```powershell
python research/state-witness/ffmpeg-glue-fetch.py .tools/state-witness-ffmpeg-glue-v2
python research/state-witness/ffmpeg-workload-suite.py results/state-witness/ffmpeg-workload-new
```

fetchは既存directoryへ上書きしない。既に取得済みなら最初の行を省略する。必要な元Wasmと制御変種は[先行実験の再現手順](post-start-live-results.md)から用意する。実行時間はprocess完了確認用の単発値であり、性能比較ではない。
