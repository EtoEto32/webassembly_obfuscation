# 同期host契約を含むWasm診断の再現package

2026-10-24。修士研究候補Kの限定した条件合成と反証実験を再現する。新しい一般検証原理が成立したという成果物ではない。一般SMTのWP/量化消去と具体BFSも同じ課題を解くことを含めて再現する。

このpackageはlocal review用で、公開操作は行っていない。第三者復元器・実アプリcorpus・依存binaryは含まない。実復元器の保存PCや活性stackの自動証明も含まない。

## 環境

実測はWindows、Python3.9、Node24.15.0、WABT1.0.42、Wasmtime50.0.1、Z3 4.13.3.0。WABT呼出しに`.exe`を使うため、そのままLinux/macOSで動くとはしない。

[WABT 1.0.42](https://github.com/WebAssembly/wabt/releases/tag/1.0.42)のWindows packageを`.tools/wabt-1.0.42/bin/`へ置き、NodeをPATHへ置く。Python依存はlocalへinstallできる。

```powershell
python -m pip install --target .tools/import-alias-quotient-python wasmtime==50.0.1
python -m pip install --target .tools/encoding-synthesis-python z3-solver==4.13.3.0
python reproduce.py
```

既存のinstallを共用する場合は`WASM_TOOLS_ROOT`を`.tools`へ、`PYTHONPATH`を二つのPython dependency directoryへ設定してよい。研究sourceはpackage内部だけを使う。入力hashとsource rootを再現器が検査する。既存出力を上書きしないため、再実行は新しいdirectoryへ展開する。

## 期待する結果

v2では`results/state-witness/reproduction.json`に`passed`を出し、57 binary fileの同一bytesでの再生成を検査する。may契約の16 fileは旧controlと同じbytesで、57は独立programの件数ではない。

* import対照256契約、Node/Wasmtime各1,228比較、2,732診断API・1,988 host呼出し。
* 別array式1,164義務がUNSAT、unknown0。
* 具体BFSの1,024初期storeが条件合成と一致。
* 一般SMT WP/QEが256契約で同じ初期条件を生成。
* host readの遅延chain8条件でも同じ条件。両engine各564 API呼出しを照合。
* 未対応profile11件を拒否し、定数store8/一回通過loopの正規化4対照を両engineで検査。
* import/read/writeを省く意図的アブレーションで誤判定を再現。
* 改善した一般SMTでも256契約が同じ条件になる。
* may-writeの128追加契約、588 UNSAT義務、具体BFS512 store、一般SMTの同条件を確認。
* 2cell/2importの96対照と、32生成反例を2engineで再生。36 atomの限定したmask閉包を検査し、一般Boolean式への反例も確認。

一回の所要時間は正式性能比較ではない。SMT条件は同じparserで得た限定modelに対するもので、公式Wasm意味論からの機械化証明ではない。import summaryを信頼し、host再入・grow・例外・外部I/Oを除く。反例の最短性はこのprofileでは主張しない。

## CLI

host summaryを`summary.json`へ保存する。

`writes: public`は全対象cellへの**必須**上書きである。単なる書込み許可と解釈しない。何も書かない/一部だけ書くhostも含めるなら`writes: may-public`とする。いずれも値とmaskは対応する左右の実行で共通、host readはwrite前の観測である。

```json
[{"module":"env","field":"touch","reads":"none","writes":"public"}]
```

```powershell
python research/state-witness/guard-import.py results/state-witness/controls/memory-before.wasm summary.json diagnosis.json --left 000 --right 100 --observation public --after-trap reenter
```

この例は`impossible`になる。条件生成だけで実行を検査済みとはしない。具体host入力と実行traceはcontrolsのmanifestに保存される。
