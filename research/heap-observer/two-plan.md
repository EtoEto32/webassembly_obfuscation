# 既存Two / fuzz-importとの比較計画

2026-10-27、実行前固定。前段のGC読出しhelperについて、既存のランダムな外部context生成への追加効果を検査する。既存のTwo handler全体を再実装したと称さず、その主要部である`--fuzz-import`生成と実interpreter/JSでの2module実行を使用する。merge、全passのランダム選択、上流の長時間campaignは今回範囲外。

## まず測るもの

1. 先の8故障系列＋NaN正対照に対し、版固定Binaryen133で同じseed列から第2moduleを生成する。必ずfuzz-importを指定（上流Twoの指定率0.8より有利）。独立最適化を想定するopen-worldのみ。第2moduleのstartは上流と同じく除去する。
2. 各contextを元/意図的変種へ同じままlinkし、実Binaryen interpreter、upstream JS shell、typed/multiに直したshellで比較する。対象binaryの変更によってcontextを再生成してはいけない。
3. raw stdoutを保存し、upstream fix_outputの関数をASTで抽出して使用する。独自のstatus/identity比較も併記する。timeout・process error・instantiate失敗・trapを分ける。
4. 計算予算はcontext数1/4/16/64の累積と、context生成＋2実行の実測msで表示する。helperは生成＋2実行の費用を含める。後から都合のよいseed順に並べない。最初は4 contextのpilot、変更が必要なら主実験を別directoryへ保存する。

## 過大評価を避ける条件

手製系列はhelperに有利なので、この結果だけで修士テーマへ昇格しない。通常のscalar観測の故障対照も加え、既存harnessの実行不能を誤って能力不足と数えない。小さな手書きgetterなら同じ差を検出できることも明示する。既存fuzzerが同じ差を検出した場合は検出成功として計数する。差が残るなら対象の型を抽象型/具体型で返す条件を比較し、原因を調べる。実生成物または独立した公開修正済み不具合での検証が次に必要。
