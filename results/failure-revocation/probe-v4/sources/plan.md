# L候補：初期化失敗後に残る関数参照の失効

2026-10-25、実験前。Kの等式解析は独立した既知方式の実装に費用でも負けた。Kの微調整を新原理として数えず、別の安全性課題を検査する。修士研究の新規性が目的であり、特許性を主張しない。

## 3方向の初期選別

|方向|原理と検査対象|強い既知対照／現時点の採否|
|---|---|---|
|L: 初期化失敗後の参照失効|失敗したWasm instanceから既に外へ出た関数参照を、生成元の失敗領域へ結び付ける。直接呼出しと参照として外へ出る入口を分け、後者で失効を検査する|既知のrevocable forwarder、全関数入口へのguard、独立Storeの破棄。問題のWasmへの具体化に差が残るかを実験する。新規性未確認|
|M: 再帰型を使ったCFI境界の細分化|関数型を役割ごとに分離して、同じscalar signatureの誤った呼出し先をengineの型検査で除外する|LLVM CFIとWasm公式Security文書が既に細粒度CFI・homogeneous table利用を説明。単なる型分離では差が弱く、主実装しない|
|N: 中断中のホストborrowに対する安定view|JSPIで中断している期間に、guest再入の書込み・memory.growからホストが読む領域を保護する|既存のborrow/effect解析、safe JSPI、当リポジトリBのprefix-write viewと重なる。固有の追加規則を得ていないので主実装しない|

これらを独創性が確立した3発明とは数えない。Lも既知の失効原理を利用する。研究候補として残るのは、Wasmの失敗したinstantiationと参照の流出経路を網羅する変換条件・費用・実アプリケーション上の必要性である。

## Lの仮説

Wasm startがtrapしてInstanceが返らなくても、importしたtableやhost callbackに関数参照が残り得る。その参照は元のmodule instanceを閉じ込めている。失敗した初期化の権限を無効と扱う埋込みでは、外に残った参照から後続の実行を開始できないことが必要となる。

これはWasmの仕様違反でも、エンジンの脆弱性の発見でもない。埋込みのポリシーを追加する。開始前の副作用の巻き戻し、実行中の処理の停止、共有memory越しの既存dataアクセスの取り消しは契約に含めない。

### プロトタイプの契約

単一thread、同期Core Wasm instantiation。元binaryをvalidateしてから変換する。新しいhost所有のmutable i32 globalを追加し、元命令がそのglobalを書いたり外へexportできないようindexを再配置する。hostは初期化中と成功後を1、失敗を捕捉した直後に0とする。値は再利用しない。

方式Lでは定義関数の各参照生成先に一意なwrapperを割り当て、`ref.func`、elementの関数番号、関数exportをwrapperへ写す。直接call/startは元関数へ写す。wrapperはgateを読み、0ならtrap、1なら元関数へtail callする。型と参照の同一性を対応付けて保つ。importされた関数は既存の外部権限なので巻き込まない。

```text
validate(original)
reserve one host-owned gate global, shifting defined global indices
for each defined function f:
    wrapper[f] := same signature; check gate; return_call f
rewrite direct function uses to original f
rewrite defined-function reference uses to wrapper[f]
rewrite original global uses to original globals after index shift
instantiate with fresh gate = 1
on synchronous instantiation failure: set gate = 0 before returning error
```

まずscalar function type / reference-types / multi-value / tail-callの範囲を明示的に受理する。GC、EH、threads、stack switching、typed function refsは対応を検査するまで拒否する。無制限の汎用変換としない。

## 比較と採否を先に固定

1. original、hostでtableだけを元へ戻す方式、全定義関数に同じgateを挿入する方式、参照wrapper方式を比較する。
2. table rollbackがhostへ保存済みの参照を消せないことを確認する。これだけをLの新規性としない。全入口guardは正しい強い対照として扱う。
3. 参照経路: active element、table.set、passive element/table.init、hostへref.func引数、外へ返したfuncref、別moduleが保持した参照。正常初期化・trap・host例外も分ける。
4. 正常初期化では出力・memory・参照identity・初期化中callbackを比較する。失敗後は残った参照がguardで拒否され、元関数の副作用が増えないかを検査する。
5. NodeとWasmtimeで実行する。未対応・失敗・実際の拒否を混ぜない。
6. direct-heavy / indirect-heavy / mixedで全入口guardと実行時間・サイズ・変換時間を比べる。単にguard位置を減らす既知最適化で説明できる費用差を新原理とは呼ばない。
7. 関連研究が同じ条件・構成を既に扱う、または独立Store破棄で同じ用途を十分満たす場合は主研究に昇格させない。第三者の自然な必要例がない段階では主テーマ採用を留保する。

## 先行資料と確認範囲

- [Wasm Core Specification](https://www.w3.org/TR/wasm-core/): module/start、function instance、table instanceの節を確認。startの実行順序と関数がmodule instanceのclosureであることは既知。新発見としない。
- [Wasmtime architecture](https://docs.wasmtime.dev/contributing-architecture.html): 初期化失敗でもimported tableに関数が入っている場合がある旨の説明。詳細は再読して記録する。
- Mark S. Miller, Ka-Ping Yee, Jonathan Shapiro, **Capability Myths Demolished**, 2003, [著者資料](https://papers.agoric.com/papers/capability-myths-demolished/abstract/): 著者・年・Abstractを確認。失効そのものは先行。本文のforwarder構成は次の精読対象。
- [ArnaudらのHandles論文PDF](https://archive.marcusdenker.de/publications/Arna14a-SCICO-Handles.pdf): 検索でmembraneと動的実行範囲の失効の違いの本文抜粋を確認。全文と正式書誌は未確認。Lの「実行中は止めない」という境界と近い。
- [Wasm Security](https://github.com/WebAssembly/design/blob/main/Security.md)および[LLVM CFI](https://clang.llvm.org/docs/ControlFlowIntegrity.html): Mの直接の反証候補。Mを新規方式とはしない。

検索日2026-10-25。検索で同一論文を見つけないことは不在証明ではない。
