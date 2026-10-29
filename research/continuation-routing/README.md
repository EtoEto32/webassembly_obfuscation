# 継続の中断点と再開handlerの対応：実行可能性調査

追記：固定切断の実wasm変換・最適化・適応復元実験を完了。[結果と不採用判断](split-results.md)。以下は初期の実行可能性調査と設計仮説をそのまま保持した記録。

2026-10-21。目的は特許取得につながる具体的な変換の発明。これは成立した発明ではなく、次の設計を選ぶための小実験である。前turnは方針再確認のみでno progressだったため、今回は実コードと実行ログを追加した。

## 確認できた事実

`probe.wat` は引数をsuspendし、handlerで3倍してresumeし、継続内で1を加える。Binaryen 133で実際のwasmへ組み立て可能。Binaryen wasm-shellで5境界入力のassert_returnを実行して全通過。単なるmodule構築の成功とは分けた。全入力同値性の実証や難読化効果の証明ではない。

Node 24.15.0では通常実行・stack-switchingフラグ・wasmfxフラグ・両フラグの4条件ともコンパイル失敗。wasmfx有効時でもsuspendのopcode 0xe2を拒否した。実行環境の未対応であり、解析耐性として数えない。独立エンジン検証とJIT性能測定は未実施。

再現（新しい出力ディレクトリを指定）：

```powershell
python research/continuation-routing/probe.py results/invention-20261021/continuation-probe-replay
```

[6呼出しの全記録](../../results/invention-20261021/continuation-probe-v1/records.json)、[集計](../../results/invention-20261021/continuation-probe-v1/summary.json)。試行時の3件のNode失敗も同じ引数で再現して保存した。最初の手動実行ログそのものではない。

## 先行資料の確認範囲

- Kenny Zhuo Ming Lu, *Control Flow Obfuscation for FJ using Continuation Passing*, arXiv:2012.06340v2 (2021), Extended Version。[実際に読んだPDF](https://arxiv.org/pdf/2012.06340)のAbstract、動機、§5末尾、§6、§7を確認。CPSによる制御フロー難読化、固定長call-string解析の不精密性、direct-style復元への議論が既にある。結論では実装途中と明記。今回、形式化全体を精読・検証したとはしない。PDF内のDOIはplaceholderであり引用しない。PEPM 2021 short paperと拡張プレプリントを混同しない。
- [US8756435B2, Obfuscation of control flow of software](https://patents.google.com/patent/US8756435B2/en), Julien Lerouge / Jonathan G. Mclachlan / Daniel F. Reynaud, 公開2014-06-17。要約・説明の一部と請求項1–14を読んだ。以前の分岐で計算された値に依存する分岐先表現が中心。履歴依存の行先を導入しただけでは強い差分としない。権利有効性・非侵害・特許性の判定はしていない。
- [公式stack-switching explainer](https://github.com/WebAssembly/stack-switching/blob/main/proposals/stack-switching/Explainer.md)。型付き継続と動的handlerへの中断、継続の一回使用を扱う。仕様機能を使うだけでは発明としない。

## 次に検査する具体規則（未実装の仮説）

単純に全ての基本blockをCPS化する案は差が弱い。検査対象を「複数の計算を、型適合する同じ中断点に割り当てる際、**中断時に捕捉される残処理と再開handler側の処理を対にして再分割する**規則」に限定する。元の依存DAGから切断点を選び、捕捉側のlive値とhandler側のlive値を割り当て、同じtag・継続型を共有しても各動的instanceで元の依存関係を保存する。

入力依存で切断点を変えるには複数の等価な分割が必要。全経路を複製するだけならサイズ費用が増す。独自性候補は分割計画規則であって、継続や入力依存分岐自体ではない。現時点で計画規則の有効な定義・費用優位は未確定なので新規アルゴリズムとは呼ばない。

反証を優先する：各継続生成点に残処理のsummaryを付け、handlerの入力を記号代入してdirect styleへ戻す解析を比較対象にする。線形個数のsummaryで常に復元できるなら、切断点を増やすだけでは本来の目標を達成しない。動的handlerの追跡をしない弱い解析だけで成功扱いしない。

比較対象は通常関数分割、明示的state-machine/CPS、固定切断、提案分割。まずBinaryen interpreterで正当性と適応解析を検査できるが、実用性能を確認できるエンジンを確保するまでは特許の効果を実証済みとはしない。未対応回避だけのためにWasm固有性を捨ててJSへ置き換えた測定を代用しない。
