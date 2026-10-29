# P候補：型signatureの区間を保持するWasm検証スタック

2026-10-26、実装前。Oの型アクセス制御とは別に、untrusted binaryの**検証時資源消費**を対象とする。新規性はまだ仮説。圧縮列・hash-consing・遅延展開そのものは既知であり、それを新発見とはしない。

## 問題と反証条件

多値block/callは短いtype indexで長いparameter/result vectorを参照する。通常のoperand stack実装は各使用時にvectorを要素ごとにpop/pushする。実際に読んだwasmparser 0.227.1のoperators.rsではvisit_block/loop/call/endが型の列を走査する。反復するwide signatureに対し、byte数だけに比例する仕事とは限らない。ただし実装がarity上限を固定すれば漸近的には定数倍であり、「従来のWasm検証は非線形」と一般化しない。

仮説は、operand stackをinternした型vectorのslice列で表し、同一slice同士の照合を定数時間で済ませると、受理言語を変えず繰返し展開の費用を減らせること。型が違う部分、singleton命令、slice境界を跨ぐ比較は通常の要素照合へ戻す。hash値だけで型一致と判定しない。

## 初期対象

Core module、scalar numeric型とv128、multi-value、structured control、local、direct call、限定numeric命令。metadataは標準Validatorで検証するが、function bodyは自作kernelが検証する。GC/reference subtyping、EH、threads、memory/table/global操作等は初期版ではunsupportedへ分離し、無条件受理しない。standalone production validatorとはしない。

unreachableのstack polymorphism、if-without-else、loop labelのparameter型、br_ifの型精密化、br_tableの「arityは同じだが型が違う」場合を必須境界とする。未対応をinvalidとして精度に加算しない。

## 比較・評価

1. 同じparser/control kernelでflat vector stackとsignature slice stackを比較し、表現の寄与を分離。
2. stock wasmparserでfull validationを測る。oursのkernel時間だけをstockの全処理時間と比較して優位性を主張しない。end-to-endも測る。
3. 同じ型だけのrun-length圧縮で十分ではないかを混合numeric型のsignatureで検査。
4. 生成したvalid/invalid例でstock、独立Node/WABTを照合。反復幅・回数は小さく制限し、ローカルfileのみを扱う。
5. 時間、binary bytes、型要素比較数、最大logical stackと保持segment数を記録。実行されるWasmを書き換えないためruntime speedupや意味変換の証明とはしない。
6. 実compiler出力で適用範囲とsmall-arity時の退行を確認しない限り、主テーマに昇格させない。

## 既知の隣接技術

Wasm仕様Appendix Validation Algorithmはsingle-pass skeletonを示す。single-passと各命令のコスト一定は同義でない。[仕様](https://webassembly.github.io/spec/core/appendix/algorithm.html)。wasmparser自身はTypeInfoのeffective type size上限を既に持つ。型展開資源の制限という問題自体は既知。

[wasm-tools #2755](https://github.com/bytecodealliance/wasm-tools/pull/2755)のexponential component validation修正と[#2726](https://github.com/bytecodealliance/wasm-tools/pull/2726)のrec group上限は近接実装として確認中であり、今回のscalar operand stackとの同一性はまだ未判定。

USENIX Security2025の[Wasm resource isolation論文](https://www.usenix.org/system/files/usenixsecurity25-yu-zhaofeng.pdf)はhost資源を含む攻撃面を扱う。今回読んだAbstract・fuel/mitigationの検索箇所から、Pと同じ検証アルゴリズムがあるとは確認できない。全文を読了したとはしない。

広いcompiler resource predictionやbaseline compiler/tieringも既知。予測器を作っただけ、timeoutを付けただけ、既存仕様の上限を変えただけでは新原理に数えない。
