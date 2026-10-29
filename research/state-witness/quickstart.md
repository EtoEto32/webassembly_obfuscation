# 契約を指定した診断CLI

2026-10-25の[修士研究としての判定](masters-verdict-20261025.md)は、現状のKを新しい解析算法の主テーマとして推奨しない。[既知等式解析との比較](guard-herbrand-results.md)、[ffmpegの実処理](ffmpeg-workload-results.md)、[公式Wizerとの直接対照](wizer-comparison-results.md)が最新の追加実験で、それぞれ再現コマンドを記載した。これらは次のarchive v3には含まれない。

最新の[import artifact v3](../../artifacts/state-witness-import-v3.zip)は直接反例構成と長い列の検査を含む。[新directoryの再現結果](../../results/state-witness/import-bundle-replay-v3/results.json)はpassedで、79 binary fileを同じbytesで生成した（重複を含み独立program数ではない）。archiveは96,388 bytes、SHA256 `d06adf99f257c1eadd4b28677641e809e06941a58f1a1fc9359b54af4ee4bb68`。[直接生成の結果](guard-import-direct-results.md)と、archive作成後の[worklist比較](guard-import-worklist-results.md)を参照する。

現在の目的は修士研究の新規性と検証可能な効果である。Jの主要機構はWeaveと重なるため主案にしない。Kは新しい一般理論ではなく、Wasm復元差の観測契約に応じた条件・反例の研究試作である。[採否](novelty-analysis.md)、[草稿](paper-draft.md)、[論証](guard-proof.md)を併読する。

## 環境

既存workspaceのPython3.9、Node24.15、WABT1.0.42を使用する。WABTは`.tools/wabt-1.0.42/bin`、Python Wasmtime50.0.1は`.tools/import-alias-quotient-python`、Z3 4.13.3は`.tools/encoding-synthesis-python`。CLIの条件生成だけならWasmtime/Z3は不要。既存parserは`research/logical-reset`を参照するので、単独scriptだけのコピーでは動作しない。実験の出力先は新しいdirectoryを選ぶ。

## 一例を診断する

`guard-contract-v1/private-byte-reader.wasm`はprivate memoryを持ち、maskとreadを公開する。左は両data segmentがdrop済み、右は先頭だけliveとする。初期memoryの影響位置0を66と置く。以下のJSONを新しいファイルに保存する。

```json
{"cells": [[0, 66]]}
```

```powershell
python research/state-witness/diagnose.py results/state-witness/guard-contract-v1/private-byte-reader.wasm results/diagnosis-reenter.json --left 00 --right 10 --observation public --after-trap reenter --store results/initial-store.json
python research/state-witness/diagnose.py results/state-witness/guard-contract-v1/private-byte-reader.wasm results/diagnosis-terminal.json --left 00 --right 10 --observation public --after-trap terminal --store results/initial-store.json
```

reenterではmask→read(0)の2呼出しで返値が異なる。terminalではmaskのtrapで終わるため、このprivate差は公開観測へ伝わらない。fullを選べばtrap直後のprivate memory差も観測する。外部書込みなしでreturns/terminalを選ぶ場合だけ、[一回判定の限定命題](guard-terminal-lemma.md)に基づいて固定点を省く。

出力のguardが空配列なら共通初期storeの全割当てで一致、nullなら満たす割当てなし、等式の配列なら条件付きである。`conditional`は表示上の構文分類であり、有限domain上の恒真式を全て簡約するものではない。`--store`を省略すれば条件だけ生成し、具体storeを検査済みと表示しない。

cell位置は`resource * 2^32 + index`。resource0はmemory、table tはresource t+1。byteは0–255、tableはnull=256、元function index iは257+i。store JSONは出力footprintの全位置を明示する。初期tableのJSONにはこの範囲のdescriptorを指定する。segment bitsはdata→elemの順で、active/空segmentをliveへ戻す指定は拒否する。

## 公開resourceへの書込みを許す

既定の`--host-writes none`は外部書換えを除外する。`--host-writes public`は、元からexportされたmemory/tableへ同じ値を両側に書くhost入力を含める。停止中・固定容量・growなしで、guest呼出しの間に限る。[手順と結果](guard-environment-results.md)、[論証](guard-environment-proof.md)を参照。

```powershell
python research/state-witness/diagnose.py results/state-witness/guard-environment-interleave-v1/interleave.wasm results/diagnosis-host-condition.json --left 01000 --right 11000 --observation public --after-trap reenter --host-writes public
```

この例は`none`なら無条件一致、`public`なら充足不能となる。具体反例も必要なら、次のstore JSONを`--store`へ渡す。

```json
{"cells": [[4294967296, 257], [8589934592, 258], [8589934593, 256]]}
```

新契約の反例は`witness.steps`へ`call`と`write`を記録する。最短長はguest呼出しと一括host代入を各1として数える。tableのhost反例で使う`foreignReference`は元関数とは異なる一つの外部参照の記号で、CLIが実際のhost参照を割り当てるわけではない。実行例では専用の定数関数を使って再現した。条件生成CLI自体はbinaryを実行して検証するコマンドではない。

## 追試の入口

同じ条件を出力する[一般SMTとの比較](guard-import-generic-results.md)と、[実アプリの起動後到達検査](post-start-results.md)も再現手順を付けた。後者はKの限定bulk parserとは別の保守的な静的検査であり、実アプリの全動作を記号解析したものではない。

同期void importを含む限定profileは別CLI [guard-import.py](guard-import.py)を使う。[結果と再現手順](guard-import-results.md)にhost summaryと適用範囲を示す。従来のCLIへ黙ってimportを許可する変更はしていない。

書込み権限を指定したい場合は`writes: may-public`を使う。`public`は対象全cellを毎回共通値へ上書きする必須効果である。[両者の区別](guard-import-may-results.md)を確認する。最新の[artifact v2](../../artifacts/state-witness-import-v2.zip)は省略/部分書込みを含む57 binary fileの再生成と2engine検査を[新directoryで再現済み](../../results/state-witness/import-bundle-replay-v2/results.json)。

import版と一般SMT/BFS対照をまとめて試す場合は [import artifact](../../artifacts/state-witness-import-v1.zip) を使う。[新directoryで再現済み](../../results/state-witness/import-bundle-replay-v1/results.json)で、39 binaryの同一bytesでの生成を含む。archive内READMEに環境構築とCLI例がある。

小さく独立に追試する場合は [minimal artifact](../../artifacts/state-witness-minimal-v1.zip) を新しいdirectoryへ展開し、そのREADMEに従う。archiveは49,583 bytes、SHA256 `2bc7e222b4e9d870e748323d88f506908179eadda17756fef83568246479e9cd`。[別directoryでの実行結果](../../results/state-witness/minimal-bundle-replay-v1/results.json)で、package自身のsourceだけから9 binaryを同じbytesで再生成し、2engine照合と44個のUNSAT義務を通過した。依存runtimeは既存installを共有した。このpackageは小対照の再現用で、過去の全実験を含まない。

- [選択した観測の条件合成・二つのengine](guard-contract-results.md)
- [実復元器での公開差と再入契約の制約](guard-external-results.md)
- [trap終端、簡約、適用外の反例](guard-protocol-results.md)
- [host書込みと呼出しの交互実行](guard-environment-results.md)
- [汎用CHC/Spacerとの比較](guard-chc-results.md)
- [準備費用を含む具体BFS比較](guard-cost-results.md)
- [保存結果のhashと再現監査（host拡張前）](../../results/state-witness/audit-v9/results.json)

Node/Wasmtimeの一致は実装検査であり全入力証明ではない。Z3は共有parserで作った限定modelの義務を検査する。table descriptorは任意関数の意味的等価性ではなく、公式Wasm全体のcontextual equivalenceを保証しない。実復元器の診断列は、そのhost APIの許すprotocolでのみ評価する。
