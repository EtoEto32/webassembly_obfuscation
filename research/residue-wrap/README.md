# 剰余表現のWasm移植：成立性と解除の検査

2026-10-23。**新発明の成功ではない。** 二成分RNCをword演算へ移す規則を試したところ、単純な版はwrapで誤答し、正しい二修正版は既知構成に留まった。法を合わせる版はraw/O3全6条件を元とbyte一致するWasmへ回復できた。主特許候補には採用しない。

[計画](plan.md)／[アルゴリズム・成立条件・修正履歴](algorithm.md)／[先行技術](prior-art.md)／[測定集計](../../results/invention-20261023/residue-wrap-report-v2/report.md)。

3人工式、plain・odd・repair・aligned、raw/O3と回復版を検査した。正24実行条件101,208呼出しで不一致0、trap0。oddの6条件には全て反例があり、正しい変換や性能対照には数えない。各条件の入力は121境界組と固定seedランダム4,096組。同じプログラムの派生版を独立したアプリケーションとは数えない。

別WABT interpreterで正192・負48呼出し、local.tee回帰例16呼出しを確認。30本をbyte再生成し、回復6本は元とbyte一致。消去不可のtrap、副作用、未対応命令等8対照を射影器が拒否した。縮小幅2–8bitの524,256比較と、64→32bit射影の6補題をZ3で確認。テスト総数も補題も、全Wasm意味論についての実装の完全証明ではない。

O3の実行中央値はplain約0.97–1.28ns、repair約7.51–19.54ns、aligned約2.99–5.91ns、回復約0.99–1.28ns。repairは元の6.93–15.25倍、alignedは2.76–4.61倍。3 fresh process×7 batch、warmup16,384、約20ms以上へcalibrate、Wasm内ループの同一wrapperを用い、wrapper出力144比較も一致。無効なoddは性能比較から除いた。

実行環境はWindows 10.0.26100 x64、Intel Core i9-11900K（16 logical）、Python3.9.0、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133、Z3 4.13.3。coreにlinear memoryはなく0byte。記録RSSはNode process全体の最大値で、変換追加分やregister/stack量の測定ではない。CPU affinityなし。transform時間は35.80–38.64ms、回復36.56–39.45msで各一回の診断値。

## 再現

repository rootで実行する。全出力directoryは未作成の場所を指定する。WABT/Binaryenは`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`、Z3は`.tools/encoding-synthesis-python`。WABT/Binaryenの場所は`WASM_TOOLS_ROOT`でも指定できる。Python helperの依存は`research/isotope-swizzle/prototype.py`→`research/connectivity-elimination/prototype.py`。性能driverは`research/span-mask/bench.cjs`。

```powershell
python research/residue-wrap/run.py results/new-residue/main
python research/residue-wrap/model.py results/new-residue/model
python research/residue-wrap/performance.py results/new-residue/main results/new-residue/runtime
python research/residue-wrap/audit.py results/new-residue/main results/new-residue/audit
python research/residue-wrap/report.py results/new-residue/main results/new-residue/model results/new-residue/runtime results/new-residue/audit results/new-residue/report
python research/residue-wrap/prototype.py transform INPUT.wasm OUTPUT.wasm --mode aligned
python research/residue-wrap/prototype.py project OUTPUT.wasm RECOVERED.wasm
```

`--mode odd`は意図的に不正な負の対照。範囲と未対応機能はalgorithm.md参照。実アプリ、メモリ表現、NotDec等の逆コンパイラへの耐性は今回測定していない。最適化器が単独で全て解除したという結果でもない。範囲制限や別符号化を含むRNS方式一般の不可能性は主張しない。
