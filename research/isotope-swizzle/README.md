# 符号化表を SIMD 命令へ移す案の反証

**動作する変換器と方式既知の回復器を作成した。既存白箱符号化との差が弱く、主発明には採用しない。特許を目指す主目標は未達。**

[事前計画](plan.md)、[アルゴリズムと意味保存条件](algorithm.md)、[先行論文・特許との照合](prior-art.md)、[評価の解釈](analysis.md)、[論文追補](paper-note.md)。

## 結果

主実験は `results/invention-20261019/isotope-swizzle-v2`。3式、plain/decode/table、2符号化seed、raw/O3 の30条件。各条件で元・変換後・回復後を JS 参照と比較し、708,480 Wasm呼出しで不一致・予期しないtrapとも0。7872入力には全 nibble 三つ組4096、境界1728、乱数2048を含む。seedやmode間で同じ入力を反復しており、全てを独立な入力とは数えない。

表方式12条件の全24表を、元式・seedなしで小さな置換＋加算/XORへ回復した。O3後も表は残るが、既知の principal isotope の正規化で局所的に戻せた。さらに192個のランダム符号化表の全49,152対を照合した。3種の非対応代数と、入力の範囲を証明できない1モジュールを拒否した。Binaryen interpreter の480照合も一致。有限検査を全プログラムの形式証明とはしない。

30変換後＋30回復後バイナリの再生成は byte 単位で一致した。[監査記録](../../results/invention-20261019/isotope-swizzle-audit-v2/summary.json)には入力parameter更新の拒否と、表の1要素を壊した場合の実際の出力不一致も保存した。主実験の再実行分を独立な追加入力として合算していない。

O3 の表方式は decode/op/encode 対照より実行2.47–4.71倍、サイズ3.72–5.72倍。回復処理本体は約0.79–3.39ms/モジュール（1または4表）、reader込み解析費用比は約1.03–1.18。詳細・生値は [測定表](../../results/invention-20261019/isotope-swizzle-report-v1/pairs.csv) と [集計](../../results/invention-20261019/isotope-swizzle-report-v1/summary.json)。回復費用の増分は存在するが、これを新規性や実用的な優位性の根拠にはできていない。

## 環境と再現

Windows 10.0.26100、Python 3.9.0、Node 24.15.0 / V8 13.6.233.17-node.48、WABT 1.0.42、Binaryen 133。ツールはリポジトリ内 `.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin` を利用する。CPUは i9-11900K、16 logical processors。外部追加パッケージ不要。各 output は未存在のディレクトリにする。

```powershell
python research/isotope-swizzle/run.py results/isotope-my-run
python research/isotope-swizzle/verify.py results/isotope-my-run results/isotope-my-verify
python research/isotope-swizzle/performance.py results/isotope-my-run results/isotope-my-perf
python research/isotope-swizzle/report.py results/isotope-my-run results/isotope-my-perf results/isotope-my-report
```

監査の再現は別ディレクトリへ `run.py` をもう一度実行した後、`audit.py <主結果> <再実行結果> <性能結果> <別実行器結果> <新しい監査出力>`。ソースとバイナリのhash、checksum、期待表数、負の対照、相対リンクを検査する。

実 `.wasm` への CLI（対応プロファイルは algorithm.md）：

```powershell
python research/isotope-swizzle/prototype.py transform results/isotope-my-run/mixed-source.wasm results/my-encoded.wasm --mode table --seed 71
python research/isotope-swizzle/prototype.py lower results/my-encoded.wasm results/my-recovered.wasm
```

初回probeは O3 による local.tee と local番号再利用に抽出器が未対応だった。probe-v1 の `status=ok, tables=0` は正常なツール終了であって回復成功ではない。probe-v2 で SSA 化を追加し、主実験では期待表数と残存 mux の不存在を検査した。v1 と v2 の主出力は、parameter mutation 拒否を追加した前後の記録。正当性集計は v2 のみ。古い試行を耐性に数えない。

性能は42ファイル×3 fresh Node process、各50000 warmup、9×50000呼出し。順序をseed付きで混ぜ、各processの中央値の中央値を報告する。JS呼出し・入力更新・checksum込み。Wasmだけの命令レイテンシではない。解析は30条件×7反復で、validation/disassemblyの外部process起動とPython処理を分けた。比較先の decode は同じ符号化を明示的に復号・演算・再符号化する除去対照であり、WASMixer等の独立した既存難読化ツールを性能再現したものではない。
