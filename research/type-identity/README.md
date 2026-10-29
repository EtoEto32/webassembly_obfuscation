# 型グループへ制御状態を移す案：実装と反証

2026-10-19。**動作する実Wasm変換器は得たが、新規で有効な主難読化方式としては採用しない。** 再帰型グループの複製と兄弟型の追加は、既存の型正規化と整数ラベル化で解除でき、通常のGC状態表現に対する十分な追加効果を確認できなかった。

[事前計画](plan.md)・[アルゴリズムと意味保存](algorithm.md)・[先行研究・特許資料の確認範囲](prior-art.md)・[結果の分析](analysis.md)・[論文ノート](paper-note.md)。目標は解除不能性ではなく、実用的なコストでの解析費用増である。

## 実装

`prototype.py transform input.wasm output.wasm --mode groups --groups 8 --siblings 32` は、最大16状態の2文字DFAを実行するcanonical source `.wasm`を読み、整数の状態番号を空のGC structの参照へ置換する。同じrec groupの別複製の型で`ref.test`を行う。sourceは `run(x,n)` が `n&31` 個のbitを処理して受理を返す限定profile。任意Wasm用ではない。

`prototype.py lower protected.wasm recovered.wasm` は、配布binaryだけを入力として型を正規化し、型検査を整数比較へ置換する。元source、生成seed、正解対応表を攻撃へ渡さない。回復先は通常の整数状態機械であり、元のpacked-table構文や最小DFAと完全一致するという意味ではない。

比較：packed table、整数branch、通常GC状態、group複製2/8×兄弟型0/32。後者の4条件を別々の新発明として数えない。GC版raw binaryは手動writerでgroup複製を保持する。付属WATは既存readerによる正規化済み表示で、raw binaryの忠実な再生成sourceではない。

## 結果

| 検査 | 結果と範囲 |
|---|---|
| 主実験 | 3カーネル×7方式×raw/O3＝42 target、各回復42本 |
| 主差分検査 | 各1,615入力。元・target・回復を合わせ203,490呼出し、不一致0・予期しないtrap0 |
| 追加境界検査 | 型group数32、兄弟型512等の12 target＋12回復、58,140呼出し、不一致0。定数4条件と非定数8条件を区別 |
| 別engine | Binaryen interpreterで主504＋追加144の公開API照合。主405＋追加114の全状態・全記号/受理照合 |
| Nodeの追加遷移照合 | 主405＋追加114。実行器間の同じ検査であり、独立した519設計の証明ではない |
| 適応的解除 | 主GC系30/30をGC型・命令のないMVPへ回復。group系24条件の22は通常GC版の回復先とbyte一致 |
| 負の対照 | 使わない兄弟型を変更した3例すべてに反例 |
| 非対応拒否 | source4例、解除2例を拒否。これらを保護成功に数えない |
| 再現 | 42 target＋42回復のbyte一致。sources hashを照合 |

主入力は長さ0–9の全二進語1,023、境界80、seed固定random512。元プログラムの呼出しも総数に含む。すべて同じAPIを持つsynthetic例で、実製品の代表標本ではない。一般の全入力同値性を有限テストから主張しない。

126 fresh Node processで測ったgroup数8・兄弟型32の通常GC版比は、実行約0.96–1.04倍、reader込み解析約0.90–1.05倍、Pythonの後処理約1.09–1.25倍、binary約1.13–3.41倍だった。reader計測はプロセス起動を含み、後処理の小さい増分は追加の型を読む費用を含む。これを人の解析費用や強い保護効果へ一般化しない。[全比較表とばらつき](../../results/invention-20261019/type-identity-report-v1/comparison.md)。

## 再現

Windows、Python 3.9.0、Node 24.15.0 / V8 13.6.233.17-node.48、WABT 1.0.42、Binaryen 133。CPUはi9-11900K、16 logical processor。追加Python packageなし。`.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin` の既存バイナリを利用する。コード・入力・生値・source snapshotをローカル保存した。外部公開・push・出願はしていない。

リポジトリrootから、未作成の出力先を指定する。

```powershell
python research/type-identity/run.py results/my-type-main
python research/type-identity/verify.py results/my-type-main results/my-type-verify
python research/type-identity/performance.py results/my-type-main results/my-type-performance
python research/type-identity/report.py results/my-type-main results/my-type-performance results/my-type-report
python research/type-identity/extra.py results/my-type-extra
python research/type-identity/verify.py results/my-type-extra results/my-type-extra-verify
python research/type-identity/null_probe.py results/my-type-null
python research/type-identity/run.py results/my-type-replay
```

監査 `audit.py OUTPUT` は下の記録済み実験名を照合するスクリプトである。任意の再現先を自動探索するコマンドではない。

- [主結果v3](../../results/invention-20261019/type-identity-v3/summary.json)、[manifest](../../results/invention-20261019/type-identity-v3/manifest.json)、[入力](../../results/invention-20261019/type-identity-v3/inputs.json)
- [追加結果](../../results/invention-20261019/type-identity-extra-v1/summary.json)、[別engine主検査](../../results/invention-20261019/type-identity-verify-v2/summary.json)、[別engine追加検査](../../results/invention-20261019/type-identity-extra-verify-v1/summary.json)
- [性能生値](../../results/invention-20261019/type-identity-performance-v2/native.json)、[解析生値](../../results/invention-20261019/type-identity-performance-v2/analysis.json)、[比率](../../results/invention-20261019/type-identity-report-v1/summary.json)
- [最終監査](../../results/invention-20261019/type-identity-audit-v1/summary.json)、[raw型数の監査](../../results/invention-20261019/type-identity-audit-v1/type-census.json)

初期のreader/解除器の非対応とnullable localの処理不備は[analysis.md](analysis.md)に分けて記録した。難読化の解析耐性として加点しない。研究全体の目標である独立した新規性・有効性・特許候補の確立は未達。
