# ページ内ブロック表現：意味保存と既知手法による代替

2026-10-21。実Wasmのprivate memoryを16byteごとの可逆表現へ変換し、memory64の有効アドレスと更新前のblock読込みで、非整列・範囲外・trap後状態を保存した。**実装上の改善を確認したが、特許を目指す主案には未採用。** 既知の高アドレス優先storeでも同じ意味を保て、最適化後も復号helperを取り出せた。過去の有限環方式の構成的提案は維持する。

- [事前計画](plan.md)、[アルゴリズム・条件・攻撃](algorithm.md)、[先行構成と公報の確認範囲](prior-art.md)、[論文ノート](paper-note.md)
- [主比較の正当性](../../results/invention-20261021/page-block-codec-main-v1/checks.json)、[高アドレス優先対照](../../results/invention-20261021/page-block-codec-extra-v1/checks.json)
- [性能生値・集計](../../results/invention-20261021/page-block-codec-runtime-v1/summary.json)、[別実行器](../../results/invention-20261021/page-block-codec-audit-v2/interpreter.json)、[回復](../../results/invention-20261021/page-block-codec-audit-v2/recovery.json)
- [最終比較表](../../results/invention-20261021/page-block-codec-report-v1/comparison.md)、[証拠とソースのhash一覧](../../results/invention-20261021/page-block-codec-report-v1/pins.json)

## 結果

30正条件、79,820の入力呼出し比較、30,170の期待trapで、返り値・trap有無・全論理メモリの不一致0。比較ごとにsourceとtargetを1回ずつ呼ぶ。これは同じ合成APIを0/1/2ページ、方式、raw/O3で変えた結果であり、30個の独立プログラムでも全入力の証明でもない。12負条件中8条件で反例を検出し、0ページの4負条件は双方trapするため反例なし。WABTの同一instanceでtrap後の観測を含む70照合も一致した。

O3の共通Wasm loopで測った1 iteration（store64とload8を含む）の中央値：

|方式|block内 ns|block跨ぎ ns|core bytes|
|---|---:|---:|---:|
|plain memory32|1.779|1.778|732|
|符号化なしmemory64|1.774|1.729|763|
|同じ符号化・byte更新|136.467|131.483|1,764|
|block事前読込み|24.940|29.576|2,285|
|既知の高アドレス優先|23.773|29.622|2,298|

block版はbyte対照より約4.45–5.47倍速いが、plain比では約14.02–16.63倍遅い。高アドレス優先方式に対して明確な優位はない。同じ符号化・処理単位の比較であり、WASMixer/WeBMOの性能を再現した数値ではない。

各方式×2位置×3 fresh process=30 process、128×64 warmup、7 batch、8ms目標calibration。plain/liftedでは上限に達して目標未達のprocessがあり、実測時間をJSONへ保存した。CPU affinity未固定、Node/V8の内部loop・inlining込みで、単独関数呼出し遅延ではない。全条件1ページ=65,536byte、RSSはNode全process最大値。block変換は0/1/2ページで約40/50/58msの単発値、WABTの読取り・コンパイルを含む。

方式既知の攻撃は、1/2ページ×3符号化方式×raw/O3の12条件すべてで、12回の選択書込みから復号helperを同定し、全メモリを回復した。同定実行は約0.225–0.285ms、64KiB復号は7反復中央値約0.740–0.818ms。reader/compile・攻撃開発時間を含まない。型を使う候補抽出と任意書込みAPIを前提とし、一般の逆コンパイラの性能とはしない。

## 再現

repo root、Python3.9、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133、Windows10.0.26100。追加package不要。`.tools/`の既存ツールと `research/isotope-swizzle/prototype.py` / `research/connectivity-elimination/prototype.py` を使う。memory64とSIMD対応実行器が必要。出力は未作成のdirectoryを指定する。

```powershell
python research/page-block-codec/run.py results/page-main
python research/page-block-codec/extra.py results/page-main results/page-extra
python research/page-block-codec/performance.py results/page-main results/page-extra results/page-runtime
python research/page-block-codec/audit.py results/page-main results/page-extra results/page-audit
python research/page-block-codec/report.py results/page-main results/page-extra results/page-runtime results/page-audit results/page-report
```

単体CLIと、元sourceやcodec定数を渡さない回復例：

```powershell
python research/page-block-codec/prototype.py source.wasm encoded.wasm --mode block
python research/page-block-codec/recover.py encoded.wasm results/page-recovered
```

単体回復は本fixtureの `i32_st4` と `bench` APIを使う専用実験。変換器一般の入力で成功する保証はない。範囲・非対応条件はalgorithm.mdを参照。通常実行のmemoryは非exportで、正当性検査と攻撃だけに観測用exportを追加する。

監査v1はshared拒否対照を生成する際のthreads flag不足で中断。v2へ修正し、これを保護効果や変換失敗に数えていない。主blockのraw/O3計6本は再生成byte一致。個別出力を再利用する際はmanifestとsource snapshotを参照する。
