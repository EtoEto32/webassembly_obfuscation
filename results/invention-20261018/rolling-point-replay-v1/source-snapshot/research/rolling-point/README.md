# 固定文字列の群上rolling照合：先行性・exact semantics・費用の検査

**新規発明としては不採用。** 群上の点関数は既知であり、窓更新との結合から独立した新規性は確認できない。実装は動くが、一般のアルゴリズム保護、既存研究を超える保護、実用的な速度の達成を意味しない。研究goalは継続中。

[実験前の設計・先行資料・攻撃モデル](design.md)、[全測定表](../../results/invention-20261018/rolling-point-v1/comparison.md)。この枝を実装した目的は、前回の容易な公開I/O復元から離れ、出力が一致位置に限られる課題で、one-way表現の適用範囲と費用を調べることだった。独創的な規則が得られないまま、この用途だけに全研究の目標を縮めない。

## 実装

`transform.py INPUT.wasm OUTPUT.wasm --method rolling|recompute` は実Wasmを読み、固定文字列scanの正規templateとAST全体が一致する場合だけ変換する。一般のstrstr変換器ではない。対応pattern長は1..255 byte。基準templateは `source(pattern)` で生成できる。

RFC3526 group14のp、q=(p-1)/2、g=2を使い、patternの整数値sを `g^s mod p` に置き換える。L<=255で `256^L < q` なので対象領域の一致はexactである。rollingは先頭byteの寄与を取り除き、新しいbyteを入れる。recomputeは全windowを再計算するアブレーション。暗号計算はWasmのi64による32bit limb Montgomery積であり、ホストへの暗号importはない。

入力の公開memoryは固定1page。範囲検査を64bitで行い、範囲外はmemory load trapとなる。表・作業領域は非export第2memoryに置くため、公開memoryのbyte、size、grow(0)の結果を維持する。Wasm multi-memoryとbulk-memoryが必要。私有memoryはrecompute 128KiB、rolling 192KiB。私有memoryも解析者に秘密とは仮定しない。

## 実測

保存先：`results/invention-20261018/rolling-point-v1/`。

|検査|結果|範囲|
|---|---:|---|
|主プログラム|27条件、1,998呼出し、不一致0|L16/64/128 × plain/recompute/rolling × raw/O2/O3。135 memory trapを含む。各正常入力を同一instanceで2回実行|
|多倍長演算|1,947比較、不一致0|Node BigIntを参照。0、p-1等と600 random pair。出力が左右入力とaliasする場合も含む|
|別エンジン|WABTで27呼出し、不一致0|O3の9条件。正例・空入力・範囲外各1回。主実験全体の別engine再現ではない|
|長さ・値の端点|24条件、192呼出し、不一致0|L1/255、全00/全FF、raw/O3、先頭/末尾配置。Node OpenSSLのmodp14定数との一致も確認|
|適応的回復|54/54成功|未知1/2/3 byte以外のprefix/suffixが既知。18保護条件 × 3未知幅。実行oracleへの問い合わせ0|
|性能|81 fresh process|27条件 × 3process。各process 7 batch|
|非対応入力の拒否|3条件|公開memory書込み、memory size変更、L256|

回復はbinaryのactive dataからtargetを取り出し、公開された既知prefix/suffixの寄与を除き、baby-step giant-stepを行う。24bit未知の場合、walkの群乗算4,299–5,200回、準備を含む単発59.7–74.0msで回復した。分解済み群指数や生成seedを回復関数へ渡していない。完全に未知の高entropy patternを回復した結果ではない。

ベンチマークのpatternとseedは検証・再現のため保存されている。従ってこれら公開fixtureそのものの秘密性を主張しない。方式の安全性定理も証明していない。低entropy、既知部分、一度得た一致入力、関連patternの露出が問題になる。任意の分布に対するVBBはDLPだけから結論できない。

O3、全零の非一致入力（長さL+16）の中央値：

|pattern長|plain μs|recompute ms|rolling ms|recompute/rolling|rolling bytes|
|---:|---:|---:|---:|---:|---:|
|16|0.0124|12.87|1.606|8.01|132,813|
|64|0.0126|51.64|3.837|13.46|132,815|
|128|0.0151|103.93|6.925|15.01|132,818|

通常検索は各候補の最初のbyteで拒否できるため、この入力は通常検索に有利である。速度比を全workloadへ一般化しない。群方式は各byteで多倍長積を繰り返す。rollingの改善は同じ群方式の再計算との比較に限られ、最適化された暗号libraryや他の暗号的難読化との同コスト比較ではない。手書きMontgomery実装が最速であるとの根拠もない。

測定環境はWindows 10.0.26200 x64、i9-11900K、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。plainのwarmupは10,000回、200,000回/batch、群方式は8回warmup、rolling 8回/batch、recompute 2回/batch。各processの7 batch中央値から3 processの中央値を求めた。RSSはNode全体のpeakで、明示的memory容量との差を区別する。変換時間は各条件1回で約137–174ms（WABT subprocess等を含む）、分布は測っていない。

主検証の初回は `memory.grow(0)` 後の古いTypedArrayを使った検証器のエラーで停止した。viewを再取得して修正し、変換器を変えず全主検査を実行し直した。記録は `check-initial-failure.json` と `checks.json`。試験合格を全入力に対する全系の形式証明とはしない。

## 棄却理由と次に残る課題

1. 新規性：点関数・秘密substring照合の先行性が明確。今回のrolling式は公開群演算の線形更新であり、独立した発明という根拠がない。
2. 対象：保護するのは未提示patternの値。変換後プログラムをそのまま複製でき、一般アルゴリズムの模倣阻止にはならない。
3. 費用：今回の実装では私有表と多倍長積の費用が大きい。rollingで8–15倍改善しても通常検索との大きな差が残る。
4. Wasm制約：prime-orderの指数をi32 wrapの同態的代替として使えない。word全域を忠実に表す巡回像は2冪位数となり、既知のbitごとの対数回復が使える。長さ制限を外すと0とqの異なる256byte列が同じ群要素になる。`domain-checks.json` に反例とsmooth-orderの309件を保存。

この枝を主候補へ昇格させない。次の設計では、既知one-way primitiveを追加しただけの構成、公開APIから容易に学べる資産、Wasm wrapを無視した代数を除外する。残っている本来の課題は、独立した新しい変換規則と、それが実用的な復元課題に与える効果を示すことである。

## 再現

Windows、Python3.9以上、Node24.15.0、repo内 `.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin` を使用する。外部Python packageは不要。既存の `research/observation-synthesis/transform.py` のWAT parserと、そのimport先 `core.py` に依存する。ツールrootは `WASM_TOOLS_ROOT` で変更可能。出力先は新しいdirectoryを指定する。

```powershell
./research/rolling-point/reproduce.ps1 -OutputDirectory results/rolling-point-new-run
```

個別の手順：

```powershell
python research/rolling-point/build.py results/rolling-point-new-run
node research/rolling-point/check.cjs results/rolling-point-new-run
python research/rolling-point/attack.py results/rolling-point-new-run
python research/rolling-point/followup.py results/rolling-point-new-run --part engines
python research/rolling-point/followup.py results/rolling-point-new-run --part domain
python research/rolling-point/followup.py results/rolling-point-new-run --part performance
python research/rolling-point/edges.py results/rolling-point-new-run
python research/rolling-point/report.py results/rolling-point-new-run
python research/rolling-point/record.py results/rolling-point-new-run
```

`manifest.json` の `sha256` と `bytes` はその条件の実ファイルを示す。各optimized entryに継承される `output_sha256` と `output_bytes` はraw変換時の記録で、optimized fileのhash/sizeではない。`source-snapshot` に最終ソースと依存parserの写しを保存する。実測値は環境依存で再現時に同じ値になる保証はない。
