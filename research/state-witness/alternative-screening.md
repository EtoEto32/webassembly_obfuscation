# 別原理の候補を再検査した記録

2026-10-24。JとKの比較後に検討。以下を新発明3件とは数えない。

|方向|具体案|厳しい対照と採否|
|---|---|---|
|例外による権限データの封印|非公開tagでpayloadをthrowし、catch_all_refで保持、throw_refと自分のtagのcatchだけで開く。型が同じ別instanceのtagでは開けない|Wasm EH提案がfresh tagとpayload非公開を明記。MLの生成的例外によるuniversal typeも先行。現時点では仕様の直接利用であり、主案として採用しない|
|関数呼出し間の権限を制限|resourceの利用順序と借用状態をwrapperで管理し、再入時の権限を絞る|Component Modelがborrow/再入の動的規則を持つ。一般的なtypestate・capability interpositionも先行。独自の合成規則や効果がない段階で大規模実装へ進めない|
|公開storeを書ける環境に耐える復元診断|Kの条件をhostの共通任意書込みについて閉じ、guest APIとの交互実行を検査する|一般的な二項環境検証は既知。独立した新原理ではないが、現在の実装の明確な適用境界を検査できるため[限定した拡張](guard-environment-plan.md)として実験する|

## 実際に確認した先行資料

* [Wasm EH提案](https://github.com/WebAssembly/exception-handling/blob/main/proposals/exception-handling/Exceptions.md)：Overview、Exception references、JS API、tag index spaceを読んだ。instance化ごとのfresh tag、matching tagなしではpayloadを読めないこと、非import/export tagの一意性を明記している。従って封印機構を新しいWasmアルゴリズムとする根拠はない。
* [MLton UniversalType](https://www.mlton.org/UniversalType)：検索で公式本文のImplementation Using Exceptionsとgenerative exceptionsへの説明を確認。ページの直接取得は502だったため全ページ読了とはしない。具体的なWasm対応の先行証拠は上記EH提案で十分であり、この検索抜粋だけに採否を依存させない。
* [Component Model Concurrency](https://github.com/WebAssembly/component-model/blob/main/design/mvp/Concurrency.md)：検索で公式のReentranceとborrow説明を確認。全仕様の検証・著者実装の実行はまだ行っていない。権限wrapper一般を新規と数える前に必要な比較対象として記録した。
* Olav Blaak / Tom Van Cutsem, **Towards Least-Privilege WebAssembly Applications: Transparent Interposition for WebAssembly Components**, MoreVMs 2026, [DOI 10.1145/3801119.3801125](https://doi.org/10.1145/3801119.3801125)。[公式会議ページ](https://2026.programming-conference.org/details/MoreVMs-2026-papers/3/Towards-Least-Privilege-WebAssembly-Applications-Transparent-Interposition-for-WebAs)の書誌・Abstractのみを読んだ。componentを自動wrapperで包み、interfaceを保って境界に任意logicを挿入し、動的な権限制限を定義する。詳細アルゴリズム・定量結果・査読過程は未確認。権限wrapper一般の新規性には直接近い先行研究である。

例外参照を使う過去の難読化試作[exception-packet](../exception-packet/plan.md)は条件値の遅延解釈であり、今回の権限封印とは目的が異なる。ただし目的の変更だけでは原理の新規性にならない。特許出願を目標とする作業へ戻していない。
