# 検証する不変条件と、検証していない範囲

可変二表はAがD={0,...,n-1}の置換、B:D→D、N=B∘Aを表す。入力u,vを範囲検査し、任意のw∈Dについて、a=A[u],b=A[w],t=B[b]を保存して、A[u]=b,A[w]=a,B[a]=t,B[b]=vの順で更新する。

Aへの書込みは転置なので置換を保つ。u=wでも最後のB[b]=vが優先され、N[u]=vとなる。他のN[j]は変わらない。したがってwの選び方を複雑にしても、範囲内である限り同じ抽象更新になる。前回の[一更新モデル](../mutable-factor/model.py)は任意wについてこの関係を検査している。今回の新しいSMT検査は、そのwを生成する式がWasmの32bit演算で範囲内か、という別の義務を扱う。

`recover.py`の入力は配布Wasmのみ。source、manifest、乱数seedは渡さない。data segmentからnと初期A/B/payloadを得て初期不変条件を検査する。入口の三つのguardが副作用のない同じ範囲検査である場合のみ順序を正規化し、Binaryen133 O3でlocal番号・無意味な算術を正規化する。

次に、更新相手wの式一個だけを穴にした生成形式と、モジュール全体を照合する。穴の式はparam0/1/3、定数、add/sub/mul/and/or/xor/shl/shr_u/selectからなる純粋なi32式に限る。shift量はWasmと同じ下位5bitを使う。除算、load、call、local.tee等はこの式の証明器では扱わない。

```
validate delivered.wasm
check initial permutation, B range, private memory, full surrounding profile
capture candidate partner expression e
ask SMT: valid(u,v,start) AND unsigned(e)>=n
accept the range obligation only when UNSAT
emit N[i]=B[A[i]] and the ordinary update/walk implementation
```

全体の一致は、guardより前の副作用、payloadの別更新、memoryの公開、別のstore順序などを誤って消さないための制限である。これは任意のWasmから不変条件を自動発見する手法ではない。生成形式の穴を一般化した方式既知の解析であり、回復の成功を一般逆コンパイラの成功率へ読み替えない。

`w=u`版の正当性は同じ不変条件から従う。しかしO3で余分なload/localが消え、周囲の生成形式との一致が成立しなくなった。正しい対象であっても本ツールが拒否する反例として保存した。より多くの形式を列挙して100%にすること自体は、難読化研究の目的ではない。

今後の候補評価では、(1)通常最適化、(2)方式の意味を利用する適応解析、(3)解析器の形式未対応、を区別する。今回の否定結果は、複雑なwを追加するだけでは直近方式の小さな抽象更新を消せない、という範囲に限る。あらゆる可変表現や将来の独立原理の方式が簡単に解除されるという証明ではない。

不変条件・抽象解釈・SMT範囲検査・テンプレート照合そのものを新発明とは主張しない。構成の新規性は具体的な生成規則を先行技術と比較して判断すべきであり、既知の数学を使うというだけで否定することもしない。本追試では新しい難読化生成規則を確立していない。
