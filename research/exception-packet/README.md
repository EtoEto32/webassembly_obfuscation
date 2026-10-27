# Wasm例外参照による条件packetの共有

2026-10-19。**実装・実験・適応的解除まで行ったが、独自で有効な難読化の主案としては不採用。特許を目指す研究目標は未達、継続中。**

同じSSA条件を複数のselectで用いるとき、二種類の例外tagのどちらかを投げてcatch_all_refで捕捉し、同じexnrefを後段のhandlerで再送する。handlerごとの解釈を反転しても、方式既知の解析は条件と値を通常selectへ戻せた。参照の共有は実行費用を削減したが、保護の独自効果は確認できなかった。

[事前計画と3方向比較](plan.md)、[算法・意味保存条件](algorithm.md)、[先行技術と未確認範囲](prior-art.md)、[実測表・採否](analysis.md)、[日本語草稿](paper-note.md)。既存の差分メモリ方式とは別原理だが、例外難読化そのものの発明とは数えない。

## 実装範囲

入力は実`.wasm`。単一exported関数、1–16個のi32引数、i32結果一つ、最大4,096個のi32 localと4,096命令。直線local代入・total整数算術・selectをSSA化する。既存のmemory、global、table、import、call、元の制御フロー、既存例外、division/remainder、float/SIMDは明示拒否。debug/custom metadataの保持は契約外。特定templateのbyte照合による変換ではないが、一般的なC/C++アプリ全体の変換器ではない。

plainは同じSSA/DAG構築を通す未保護対照、helperは通常select関数への共通化、freshはselectごとに例外生成、sharedは同じ条件式のpacketを共有。原入力に対しても独立JS oracleで検査する。元localの更新によるconditionの変化を追うため、単なるlocal番号の一致では共有しない。追加linear memoryは0。十分なVM資源を前提とし、資源不足・時間・デバッグの同一性は主張しない。

## 環境とCLI

実測環境：Windows、Intel Core i9-11900K、Python 3.9.0、Node 24.15.0 / V8 13.6.233.17-node.48、WABT 1.0.42、Binaryen 133。主変換器はPython標準libraryのみ。補助SMTには既存の`.tools/encoding-synthesis-python`のz3-solver 4.13.3.0を使う。

WABTを`.tools/wabt-1.0.42/bin`、Binaryenを`.tools/binaryen-version_133/bin`へ配置する（別の親directoryは`WASM_TOOLS_ROOT`で指定）。共通parser/tool wrapperは`research/connectivity-elimination/prototype.py`、命令平坦化は`research/stack-cycle/transform.py`を使うため、リポジトリ全体を保存する。Wasm EH/reference-typesが動くNodeが必要。

```powershell
python research/exception-packet/prototype.py input.wasm protected.wasm --mode shared
python research/exception-packet/recover.py protected.wasm recovered.wasm
```

出力は新規ファイルを指定する。方式既知の回復器の入力は対象binaryだけであり、元source、seed、正解manifestは渡さない。意味命令の解釈にBinaryenのprintを使う。未知のVM形式を発見する時間、人間の解析時間、汎用逆コンパイラの性能は評価していない。

## 再現

以下はrepo rootから実行する。全出力先は未存在であること。外部公開、push、出願、課金は不要。

```powershell
python research/exception-packet/run.py results/packet-reproduction
python research/exception-packet/measure.py results/packet-reproduction results/packet-performance-reproduction
python research/exception-packet/verify.py results/packet-reproduction results/packet-verification-reproduction
python research/exception-packet/compatibility.py results/packet-reproduction results/packet-compatibility-reproduction
python research/exception-packet/normal-form.py results/packet-reproduction results/packet-normal-reproduction
```

`run.py`は9個の人工カーネル、72target、72回復を作成し、各1,024入力を検査する。`measure.py`はO3の36条件を各3 fresh processで測定。`verify.py`は別エンジン、mutable条件の追加例、負の対照、scalar SMT、独立した解析時間測定。`compatibility.py`は全機能O3と宣言順変更。`normal-form.py`は整数の交換・結合則による補助照合。SMTのunknownや正規形不一致は不正な意味だという判定ではなく、当該検査で未証明という結果である。

保存済み主実験のソース・hash・再生成照合は以下。

```powershell
python research/exception-packet/audit.py results/invention-20261019 results/packet-audit-reproduction
```

遅い追加診断をそのまま再現する場合は`partition-check.py`へ主結果directory、`verify.py`の`scalar-model-equivalence.json`、新規出力directoryを渡す。条件領域を分けても一部は10秒上限に達したため、主成功件数に加えない。

## 支持された範囲

主147,456呼出し、追加24,864呼出し、互換性・宣言順9,216呼出しで不一致0。WABT288呼出しも一致。上記は別々の検査で、全入力証明や実製品への適用結果ではない。誤handlerとnull packetの反例、未対応拒否も保存した。

例外方式の36/36条件を通常整数計算へ回復。共有で例外生成を減らすと実行は軽くなったが、二タグの意味追跡も安くなる。最適化器が残したこと、ツール未対応、補助solverのtimeoutを解析耐性の証拠にはしていない。新規性の積極的根拠がなく、継続する主発明候補にはしない。
