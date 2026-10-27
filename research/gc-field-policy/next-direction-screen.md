# Oの失敗を踏まえた次方向の事前反証

2026-10-26。以下はまだ新規発明の候補として確立していない。

1. **custom descriptorによるowner識別**。同じ構造型でもdescriptorのobject identityでproducerを分ければOの型衝突を避けられる可能性がある。しかし[提案本文](https://github.com/WebAssembly/custom-descriptors/blob/main/proposals/custom-descriptors/Overview.md)は`ref.get_desc`でdescriptorを取得し、それを`struct.new_desc`へ渡せることを明示する。従って正規objectを一つ受け取ったconsumerによるpayload偽造まで防げるとは考えない。これは提案の欠陥という主張ではなく、nominal castとauthority authenticationを混同しないための反証条件。descriptorを用いるnominal cast自体も[issue #107](https://github.com/WebAssembly/custom-descriptors/issues/107)が2026-07-13に既に具体化している。
2. **非公開exception tagでGC payloadを封印**。Wasm固有の生成的identityを使えるが、以前の棄却記録に加え、[Andy Wingoの2026-03-10の記事](https://www.wingolog.org/archives/2026/03/10/nominal-types-in-webassembly)がまさにtagによるnominal data、throw/catchによるconstructor/accessor、module間偽造対策を実装例で説明している。新しいWasm封印原理として採用しない。記事は個人の一次技術解説であり査読論文とはしない。
3. **mutable値のread-only契約でCanonical ABIのcopyを省く**。[GC ABI #525](https://github.com/WebAssembly/component-model/issues/525)がmutabilityとrec groupによるcopy問題を既に指摘。consumerのみwrite禁止でも、producerが後から変更するとWITの値コピーの意味と一致しない。全aliasの寿命・後続書込みを制限する追加条件は既知のborrow/effect analysisに近い。現在のOをそのままcopy eliminationの保証へ流用しない。

この3方向を「独創的な3発明」として数えない。未知の構成へ着手する前に、明確な保護目標と先行反例を固定する。

## descriptor案の実行可能な反証

`descriptor-screen.py`で同じ型の2個のdescriptorを持つlibraryと4個のconsumerを作成した。正規値は17を返し、別descriptorと新規descriptorは拒否されるが、正規値から`ref.get_desc`で取り出したdescriptorを使い、payload 77の新しいobjectを作ると同じdescriptor照合を通る、という仮説を固定した。

Binaryen 133 validatorは全5moduleを受理した。Node 24.15/V8 13.6はexperimental flagを付けても新しいopcode encodingを受け付けず、Node上の実行結果は得られなかった。この未対応を防御成功と扱わない。

代わりに[Binaryen 133 interpreter](../../results/gc-field-policy/descriptor-interpreter-v1/summary.json)で4assertionを実行し、正規17・別brand trap・新descriptor trap・**同descriptorでpayload77の再生成成功**を確認した。コンパイラと同じprojectのinterpreterなので独立engineの検証ではない。これは仕様に沿うauthority仮説の反例であり、engineの脆弱性ではない。初回のexact型不足とNode非対応は別ログに保存した。

descriptor equalityだけをデータの真正性保証に使う次案はこの段階で採用しない。生成禁止の受理検査へ戻せばOと同じ課題になる。非公開tag封印は上記の直接先行がある。
