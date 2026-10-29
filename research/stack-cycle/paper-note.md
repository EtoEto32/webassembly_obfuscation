# 同一型スタックの境界選択によるWebAssembly平坦化：費用と復元の比較

2026-10-18、日本語研究草稿。未投稿。[コード・データ・再現手順](README.md)。独立した新規難読化を確立した論文ではなく、限定候補の評価記録である。

## Abstract

Wasmの直線命令列を同じ型付きstack状態が現れる境界で分割し、block/loop parameterを用いて断片間の値を渡す平坦化を実装した。区間長を最大化し最大断片長を最小化する計画により、dummy値を加えず、追加localなしでdispatcherを構成できる。同じ分割・配置でlocalへ退避する対照と、4カーネル・4/8/16分割・raw/O2/O3を比較した。主84本と復元84本の611,730呼出しで返り値、trapの有無、全memoryの不一致はないが、最適化によるtrap理由差52件を別記録した。未最適化サイズは減る一方、最適化後の利点は一貫せず、定数制御の部分評価は全条件を同等の直線処理へ回復した。回復費用は元より増加したが既存のlocal方式と近く、新たな保護上の優位性は確認できなかった。

## Introduction

難読化の目的は正当なプログラムの解析費用を増やすことであり、解析不能性を要求しない。変換器の実装差分、実行・配布費用、保護目標を解く解析費用を独立に測定する。本実験は、Wasm固有の型付きstackと値付き分岐を使って平坦化の費用を削減できるかを検討した。

## Related Work

**WASMixer: Binary Obfuscation for WebAssembly**、Shangtong Cao, Ningyu He, Yao Guo, Haoyu Wang、2023、arXiv:2308.03123v1。今回参照した版はプレプリント。[本文](https://arxiv.org/html/2308.03123v1)の§4.2.1 Algorithm 2/3では分割境界のstackを追加localへ保存・復元し、dispatcherで処理を接続する。今回はこの部分との構成上の比較で、論文の他の難読化要素や著者実装の評価結果を再現したものではない。

**WebAssembly Design Rationale**、WebAssembly設計コミュニティ、継続更新の技術資料、査読論文ではない。[Control Flow Instructions with Values](https://github.com/WebAssembly/design/blob/main/Rationale.md)は、値付き制御によるlocal.get/set削減とSSA phiとの関係を説明する。今回の核となる省サイズ効果はこの既知の設計動機に含まれる。

**Multi-value Extension**、WebAssembly提案仕様、技術資料。[Overview](https://github.com/WebAssembly/spec/blob/main/proposals/multi-value/Overview.md)はblock input、loop label arguments、backward-edge phiを説明する。Sとstateをloopへ渡すこと自体に新規性はない。一般のsequence partition DPも既知であり、本稿は新しい計算原理を主張しない。exactな分割規則が全先行実装にないことの証明はない。

## Motivation

WASMixer型の分割ではstackをlocalへ逃がせば任意の区間を接続できる。一方、Wasmの型検査を利用して同じSに揃う分割点を選べば、値を直接branch payloadへ載せられる。本案の検証可能な仮説は、同じ保護区間・case数・配置でlocal退避費用を省けることである。強い復元耐性は仮定せず別に測る。

## Threat Model

解析者は配布Wasm全体、Wasm仕様、変換規則を知り、逆アセンブル・通常最適化・専用解析を使える。秘密鍵や非公開runtimeはない。元source、選んだcuts、配置seed、生成時JSONは与えない。タスクはdispatcherを取り除き、等価な直線のデータ演算と副作用列を回復することである。単なる元の変数名や唯一のsource字面の回復は要求しない。人間の初回解析費用は未計測。

## Proposed Method

入力Iの命令境界iに型stack T[i]を付与する。出現回数がk+1以上の非空Sごとに、最初と最後の出現位置で区間を定める。区間長を最大化し、同長なら|S|を最大化、さらに同点なら型列の辞書順で決める。Sの出現列p[0..m-1]について、次のDPでk分割を求める。

```text
DP[0,0] = 0; other entries = infinity
for r = 1 .. k:
  for j = r .. m-1:
    DP[r,j] = min over h in [r-1,j-1] of
              max(DP[r-1,h], p[j]-p[h])
backtrack from DP[k,m-1] to obtain cuts
```

計画はこの目的関数の範囲で最適であり、実行費用や解析耐性の最適性ではない。型走査後のDPはO(km²)時間、O(km)領域。prototypeは命令数・kを制限する。

```text
execute prefix                      # pushes S
push state 0
block done   : (S,i32) -> S
  loop again : (S,i32) -> S
    nested case blocks : (S,i32) -> S
      br_table case0 ... case(k-1), default done
    at case i:
      execute fragment i            # S -> S
      if i = k-1: br done with S
      else: push i+1; br again with (S,i32)
execute suffix
```

caseの物理順は固定seedでshuffleする。次stateは隠しておらず、提案が暗号化による秘匿性を持つとは主張しない。比較対照は同じcuts・配置・stateでSとPCをlocalに置く。

意味保存の論拠は断片の実行順に関する帰納法である。prefix後に元と同じSがあり、case iの入口に元の同一時点のoperand値・locals・memoryがあるなら、元の命令列を同順序で実行して同じ次状態になる。分岐は値をコピー・受渡しするだけで、追加のload/storeやtrapする数値演算を行わない。最後はsuffixへ同じSを渡す。元命令がtrapする場合、そこまでの副作用列が一致する。資源不足やstack限界、外部非同期操作、非対応機能はこの主張の外である。実装全体の機械検証はしていない。

## Implementation

PythonがWABT出力を型走査・再構成し、WABTでbinary化・validateする。Binaryen 133のO2/O3後も検査する。対象は単一直線関数と列挙したscalar命令、任意の非共有32-bit memory。mixed4ではS=(i32,i64,f64,i32)、他の3カーネルではS=(i32)。元のif/loop/call等は未対応。復元器はWasmのcontrol frameと型stackを実装し、定数stateだけを追跡、データ演算をSSA temporaryへ順に出力する。未定の条件分岐を成功扱いせず拒否する。

## Evaluation

事前の[plan.md](plan.md)から実装し、xorshift16、crc32word、mixed4、memory16の小カーネルを使った。主検査168条件・611,730呼出し、追加型検査30条件・30,990呼出しで値/trap/全memoryの不一致0。WABTで336呼出し一致。誤state対照4,106件を検出。DPの200小例を全列挙と比較した。これらは有限試験である。

84条件すべてを復元し、rawではカーネルごとに7方式の復元関数命令列が同一になった。O3/8分割のpayload解析時間は0.46–1.02ms、元の約1.19–1.68倍で、local退避方式と近い。元より費用が増えた事実を認めるが、新しい構成による保護の増分は支持されない。

未最適化8分割のサイズはlocal比で48–156B減少した。O3ではxorshift16とcrc32wordがそれぞれ9B、11B小さくなる一方、mixed4とmemory16は37B、7B大きくなった。mixed4は非引数localがlocal版では6→1、payload版では1→9となる。実行時間の差は標本のばらつきと重なり、一般的な高速化を主張できない。[全比較表](../../results/invention-20261018/stack-cycle-v2/comparison.md)

性能は252 fresh process、各10,000 warmupと9×30,000 timed calls。JS呼出し費用を含む。変換58.8–77.5ms、追加線形memory 0、process maxRSS 41,564–44,412KiB。RSSはエンジン全体の指標である。

初回の厳格なエラーメッセージ比較で52件の理由差を検出した。Binaryenによるload/divの並替えで、trapの有無と停止時memoryは同じだった。主観測をCoreの値/trap/状態へ分け、理由差を消さず別保存した。具体的なJSエラーメッセージの同一性は保証しない。

## Discussion

最適化前に退避命令が減ることと、最適化後の実行表現が小さくなることは同じではない。local対照では不要な保存・復元を最適化器が消す。一方multi-valueの実装変換でlocalが再導入される条件があり、表現を変えただけの削減量を成果の中心にできない。

定数state列は値をstackへ移しても定数である。解析者はWasmのlabel arityとcontrol frameを解釈すれば同じ順序を得られる。未知の鍵や暗号を要求する必要はないが、データ表現の変更だけで難しい解析課題が生まれるとも限らない。本実験で測った追加解析費用を0とは扱わず、その差が通常のlocal表現からの改善を示さない点を重視する。

## Limitations

小カーネル4個、単一CPU・Node/V8、実アプリケーション未評価。一般CFGや入力依存の繰返しは対象外。著者WASMixer、NotDec、StackSightを本候補へ実行していない。単一specializerへの適応的比較であり、全攻撃の下界ではない。人間の解析時間、初回開発費用、ネイティブレジスタ使用量は未測定。文献調査はexact構成の非存在を証明しない。

## Conclusion

追加localを使わない平坦化構成は実装でき、未最適化サイズの削減を測定した。しかし標準の値付き分岐の利点を超える新規性と、既存dispatcherに対する保護費用の優位性を確立できなかった。この限定候補は主方式として採用せず、コード・測定・失敗条件を再現可能な比較資料として残す。
