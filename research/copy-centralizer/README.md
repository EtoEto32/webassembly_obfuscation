# コピー互換なメモリ混合の自動生成

2026-10-21。実Wasmの固定copy群から可換な線形表現を生成する限定変換器を実装した。同じ混合表現を毎回復号する自作対照より軽く動いたが、公開ABIに対する安い回復も成立した。**自動構成と高速化の実装成果として保持し、独立した主発明には採用しない。** 過去の有限環方式の構成的提案は維持する。

- [事前計画](plan.md)、[規則・疑似コード・意味保存・攻撃モデル](algorithm.md)
- [先行研究と新規性の限界](prior-art.md)、[結果の詳細](analysis.md)
- [継続地点](checkpoint.md)

## 再現方法

Windows 10.0.26100、Python 3.9.0、Node 24.15.0/V8 13.6、WABT 1.0.42、Binaryen 133。Python追加packageなし。WABTを`.tools/wabt-1.0.42/bin/`、Binaryenを`.tools/binaryen-version_133/bin/`に置く。共有readerは`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`。repo rootから、未作成の出力先へ実行する。既存結果は上書きしない。

```powershell
python research/copy-centralizer/run.py results/cc-main
python research/copy-centralizer/recover.py results/cc-main results/cc-recovery
python research/copy-centralizer/direct.py results/cc-main results/cc-recovery results/cc-direct
python research/copy-centralizer/performance.py results/cc-main results/cc-sequence
python research/copy-centralizer/performance.py results/cc-main results/cc-dispatch --dispatch
python research/copy-centralizer/audit.py results/cc-main results/cc-recovery results/cc-audit
```

性能測定は他の重い処理を止めた状態で順番に行う。各performanceは16条件×3 fresh processを逐次実行する。基準版と回復版のテスト結果、モデル全列挙、別実行器、負例、byte再現を保存する。

単体変換は、canonical source profileに対して次の形式。

```powershell
python research/copy-centralizer/prototype.py results/cc-main/blocks16-source.wasm results/cc-custom.wasm --mode native
```

全一般Wasmへ適用できるCLIではない。固定private領域に閉じたcopyと、規定のread/write関数以外は拒否する。

## 記録済み結果

主実験は[copy-centralizer-v2](../../results/invention-20261021/copy-centralizer-v2/checks.json)、回復は[recovery-v2](../../results/invention-20261021/copy-centralizer-recovery-v2/recovery.json)、安い直接回復は[direct-v1](../../results/invention-20261021/copy-centralizer-direct-v1/direct.json)。主32条件22,016呼出し、回復8条件5,504呼出しで不一致0。別のdirect 8生成物は検証済み回復とbyte一致し、追加の独立coverageには数えない。

性能は[固定列](../../results/invention-20261021/copy-centralizer-runtime-v1/summary.json)と[入力選択](../../results/invention-20261021/copy-centralizer-runtime-dispatch-v1/summary.json)、監査は[audit-v2](../../results/invention-20261021/copy-centralizer-audit-v2/audit.json)。raw/O3とも全8 native条件を回復。直接回復は1条件32 read、0 write。byte混合行列の回復より安い。

初回manifest生成の重複keyword、初回回復器のO3 load/store未対応、初回監査の相対path不備は、それぞれv1のfailure.mdと旧ソースへ保存した。未対応や実装ミスを保護効果へ数えていない。主sources.jsonは主実験時点のhashで、後に回復reader対応を追加した。最新ソースから主32本が同じbyteに再生成されることをaudit-v2で確認している。
