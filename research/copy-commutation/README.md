# memory.copyを残せる表現の限界

2026-10-19。**これは新規難読化方式の成功報告ではなく、メモリ表現案の成立条件を調べた結果である。** 任意byte copyを同じアドレス・長さのまま実行し、追加修復や補助状態を使わない全域の可逆表現は、全位置共通のbyte置換に限られる。複数byteを混ぜる案では、copy自体を変えるか、対象操作・到達状態などの制限が必要になる。

[紙上証明](proof.md)、[事前計画](plan.md)、[先行研究との照合](prior-art.md)、[詳細結果と判断](analysis.md)を保存した。理論の全域条件と、有限のWasmテストによる実装検査を区別する。

## 実装範囲

`prototype.py` は実 `.wasm` を読み、1ページの非共有private memory、全ページのactive data、`copy`/`read`だけを公開するcanonical profileを変換する。2つのsource profileを使う。

- align1：copyの3引数をそのまま渡す。
- align2：**元のプログラム自体が**3引数を `& -2` で丸めてからcopyする。任意copyの引数を難読化の都合で切り捨てる変換ではない。

変換後もcopy関数を保持し、初期メモリとreadの復号だけを変える。比較はplain、全位置共通のbyte置換uniform、位置依存byte回転position、隣接pairを条件付き交換するcoupled。これらを原理の異なる新発明3案として数えない。

通常CLIは不成立の組合せを拒否する。実験だけ `--negative-control` で不正な組合せを生成し、検査が反例を発見するかを測る。汎用Wasm変換器ではなく、canonical source以外は拒否する。import、任意のstore、grow、共有memory、多メモリ、memory64、exportされたmemoryの外部変更等は対象外。readを公開した試験用APIであり、秘密データを保護するベンチマークでもない。

## 検査結果

| 項目 | 結果 |
|---|---|
| 有限全列挙 | 2値2セルの24置換→2、2値3セルの40,320置換→2、3値2セルの362,880置換→6。予想集合と完全一致 |
| 非可逆も含む小モデル | 2値2セルの256写像→4、同一1セル写像の集合と一致 |
| 一方向copyだけの小モデル | 3値2セルの362,880置換→48。全方向copyの6より広い |
| 整列pairの小モデル | 3,584条件で一致。byte copyで具体的反例あり |
| 実Wasm主実験 | 2初期data × 2source profile × 4mode × raw/O3 = 32 target |
| 主差分検査 | 242 copy条件/target、255,552 Wasm関数呼出し。正の20 targetで値・trap・全メモリの不一致0。不正な12 target全部で値・メモリの反例あり |
| 正常な拒否 | 不成立の6生成条件を通常CLIが拒否 |
| WABT/Node照合 | 32 targetの128 wrapper実行で一致。負の対照も含むエンジン間照合 |
| 復号の有限全列挙 | pair交換の65,536組、uniformの256値で逆写像を確認 |
| 再生成 | 32 targetと32観測用binaryがbyte一致。copy関数は32/32でsourceと同じAST |

255,552呼出しは元・変換後・観測用の3instanceを含む。すべてを提案方式の成功ケースとは数えない。主実験の各copy条件は新しいinstanceから始まる。WABT照合は同一instanceで4操作を順に実行するが、これも全状態の形式証明ではない。`unmodified_copy_counts=7744` は target×copy条件の数であり、関数呼出し数や別個の仕様証明数ではない。

## 再現

リポジトリrootから実行する。実験環境はPython 3.9.0、Node 24.15.0、WABT 1.0.42、Binaryen 133、Windows 10.0.26100。Wasmツールは既存の `.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin` を利用し、共有ツール解決処理もsources snapshotへ保存する。追加Python依存はない。

```powershell
python research/copy-commutation/model.py results/my-copy-model/results.json
python research/copy-commutation/run.py results/my-copy-main
python research/copy-commutation/verify.py results/my-copy-main results/my-copy-verify
python research/copy-commutation/run.py results/my-copy-replay
python research/copy-commutation/audit.py results/my-copy-main results/my-copy-replay results/my-copy-model/results.json results/my-copy-verify results/my-copy-audit
```

各出力先は未作成の名前を使う。32targetに含むnegative controlは意図的な誤変換であり、保護用に配布するものではない。単体CLIの正例：

```powershell
python research/copy-commutation/prototype.py results/my-copy-main/seed7-align2-source.wasm results/my-pair/output.wasm --mode coupled
```

記録済み結果：

- [主結果](../../results/invention-20261019/copy-commutation-v2/summary.json)、[全ケース](../../results/invention-20261019/copy-commutation-v2/native.json)、[生成manifest](../../results/invention-20261019/copy-commutation-v2/manifest.json)
- [有限モデル](../../results/invention-20261019/copy-commutation-model-v2/results.json)、[エンジン照合](../../results/invention-20261019/copy-commutation-verify-v1/summary.json)
- [再生成](../../results/invention-20261019/copy-commutation-replay-v1/summary.json)、[監査](../../results/invention-20261019/copy-commutation-audit-v1/summary.json)
- [v1の実験設定エラー](../../results/invention-20261019/copy-commutation-v1/failure.json)：wasm-optのbulk-memory機能指定不足。修正後にv2を実行。解析耐性・最適化器の破壊効果には数えない。

独自で有効な主方式、同等コストでの解析費用増、特許候補の確立は未達。今回の正当性gateを満たすだけでは、主研究の完了条件を満たさない。
