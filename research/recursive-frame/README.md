# 再帰frameごとの混合：実Wasm変換と要約回復

2026-10-22。**実装・実験を完了したが、主発明には採用しない。** 実行時に2語の表現を変え、親の表現へ戻り値を接続する案を検査した。通常O3後にも機構は残る一方、方式を知る解析者は呼出し履歴を展開せず1つの関数要約で等価計算を回復できた。構成上の新規性・Wasm固有性も弱い。[事前計画](plan.md)、[アルゴリズムと意味保存](algorithm.md)、[先行技術](prior-art.md)、[短い論文記録](paper-note.md)。

以前の[有限環残差フィードバックの構成的提案](../novelty-status-20261022.md)は保持する。今回の不採用を研究全体の完了、または過去に提案が存在しなかったという評価へ置き換えない。

## 実装と攻撃モデル

実.wasmをWABTで読んで、閉じた2関数の再帰profileと一致することを検査し変換する。run(n,x,y)->i64、n&31の深さ、2つのi32の純粋な演算が対象。固定幅rotate/add/xorを含む同じ計算骨格の3係数設定であり、3つの実アプリではない。任意の関数・メモリ・import・float・除算・例外には未対応。debug/custom section保持も契約外。

z=Mv、det M=1として状態を持つ。子ごとに混合値からshear係数を作り、N=L(l)U(k)Mへ更新する。親Mはcall frameへ残し、子の返値をN^-1で解釈して親の計算へ接続する。2語はi64へpackする。暗号鍵・秘密runtimeはない。Wasmの剰余整数とcallを使うが、他の形式へも実装できる。

保護課題は混合のない等価な再帰計算の回復。元source・生成係数・manifestを回復器へ渡さず、方式と公開binaryだけを使う。解析器は行列式の恒等式と記号的な関数要約で検査し、対象外を拒否する。人間の解析時間、汎用逆コンパイラ、最良の攻撃の下界は測っていない。

## 正当性・回復

- 3設定×4方式（plain/fixed/dynamic/bad）×raw/O3の24本と、正18条件の回復18本、計42本。WABT・Nodeでvalidate。
- 正36条件×7,380入力＝**265,680呼出し、不一致0、想定外trap0**。各深さの境界値と4,096固定seed乱数、公開nの上位bitも含む。独立BigIntモデルと比較。同じ入力を各条件で使い、独立した約26万入力とはしない。
- 誤った子行列d1+1の6負条件は全て7,121件の不一致。最初の反例はn=1,x=y=0。回復器もdetを確認できず拒否する。正常入力でtrapを作る負例ではない。
- **18/18条件を回復**（plain6、固定6、動的6）。未対応・crash・timeoutは最終正条件では0。要約数1、stack展開数0。O3でも動的workerの7引数と再帰callは残った。通常最適化が除去したという結果ではない。
- 現行生成器から**42本をbyte一致で再生成**。別エンジンWABT interpreter **288呼出し**も独立Python整数oracleと一致。
- sourceのmemory/演算変更、回復側のmemory/非減少call/base再帰/root出力変更の有効Wasm6条件を拒否。
- 小語長1–3の全det=1行列と全2語状態で**25,368**組、32bitのランダム10,000組をモデル検査。frame移送恒等式の検査で、全Wasmの実行回数や形式証明には数えない。

最初のsmokeでは固定版O3の定数shiftを乗算として扱えず未対応だった。対応後に主実験を実行。これは実装不足であり保護効果ではない。初期tracebackは会話に残るが、主JSONへ元ログとして捏造していない。reportの初回実行はPythonの文字コード診断で停止し、UTF-8指定後に生成した。

初回v1は動的版だけrootをIとしていた。動的更新の有無の比較にそろえるため、主結果v2は固定・動的ともrootを[[1,3],[5,16]]にし、正当性・回復・監査・性能を再実行した。v1の同じ入力の結果を加算して試験数を増やさない。model-v1は任意のdet=1行列を扱う同じモデルなので再利用した。

## 費用と解釈

[詳細比較表](../../results/invention-20261022/recursive-frame-report-v2/comparison.md)、[集計JSON](../../results/invention-20261022/recursive-frame-report-v2/summary.json)。

|O3、wide設定|plain|固定混合|動的混合|回復|
|---|---:|---:|---:|---:|
|深さ8、ns/run|9.22|45.58|52.62|9.49|
|深さ31、ns/run|44.58|181.38|201.25|46.74|
|core bytes|142|359|408|142|

全6比較区分の動的版はplain比**4.51–6.30倍**、固定比**1.085–1.174倍**の実行時間。O3要約本体は固定約0.469–0.487ms、動的約0.764–0.823msで、設定別比**1.59–1.76倍**。読取・validateを加えた中央値和の比は**1.004–1.033倍**で、観測された増加は約0.4–3.3%。両時間の直接の比を保護強度にはしない。有限な解析費用増は認めつつ、主仮説である履歴依存の難しさを支持しない。小さい時間差の統計的確立や、あらゆる解析器での費用増加を主張しない。

72 fresh Node process、648 batch。各processは16,384回warmup後、10msを目安に最大2^20呼出しまで校正し9batch。126batchは10ms未満で、特に短いplainは上限に達する。3processの各中央値の中央値を報告。共通Wasm loopで入力更新とchecksumを行い、coreへO3を適用してからwrapperを付ける。回復coreにもO3を適用。CPU affinity・周波数は固定していない。edge/depth31動的版にはprocess中央値196–223nsのばらつきがある。

全条件linear memory 0。Node maxRSSは36,348–36,756KiBでruntime/JITを含む。Wasm stackだけのpeakと変換器Pythonのpeak memoryは未測定。変換は49.9–56.8ms（profileの再構成確認、compile/validate込みの各1回）。解析11反復は同一Python process、compileは別。Intel Core i9-11900K、16 logical processors、Windows 10.0.26100、Python3.9.0、Node24.15.0/V8 13.6、WABT1.0.42、Binaryen133。

## 再現

追加Python package不要。repo rootから毎回未存在の出力先を指定する。ツールは`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`。共通S式parserは`research/connectivity-elimination/prototype.py`。

```powershell
python research/recursive-frame/run.py results/recursive-frame-replay
python research/recursive-frame/model.py results/recursive-frame-model-replay.json
python research/recursive-frame/audit.py results/recursive-frame-replay results/recursive-frame-audit-replay
python research/recursive-frame/performance.py results/recursive-frame-replay results/recursive-frame-runtime-replay
python -X utf8 research/recursive-frame/report.py results/recursive-frame-replay results/recursive-frame-runtime-replay results/recursive-frame-audit-replay results/recursive-frame-model-replay.json results/recursive-frame-report-replay
```

個別変換は`prototype.py SOURCE OUTPUT --mode dynamic`、回復は`recover.py SOURCE OUTPUT`。主結果は[main-v2](../../results/invention-20261022/recursive-frame-v2/manifest.json)、[checks](../../results/invention-20261022/recursive-frame-v2/checks.json)、[recovery](../../results/invention-20261022/recursive-frame-v2/recovery.json)、[audit-v2](../../results/invention-20261022/recursive-frame-audit-v2/audit.json)、[runtime-v2](../../results/invention-20261022/recursive-frame-runtime-v2/summary.json)、[model](../../results/invention-20261022/recursive-frame-model-v1.json)。各実験のcommands・source snapshot・hash pinsも保存した。外部公開・push・出願は行っていない。
