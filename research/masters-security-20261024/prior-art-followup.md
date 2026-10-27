# 単一計画と境界予算の追加照合

確認日2026-10-24。一次資料で実際に読んだ範囲を以下に記す。検索結果だけの特許候補を読了済みに数えない。今回の検索で見つからないことを新規性の証明にはしない。

## ShillDB

Ezra Zigmond, Stephen Chong, Christos Dimoulas, Scott Moore. **Fine-Grained, Language-Based Access Control for Database-Backed Applications**. The Art, Science, and Engineering of Programming, 4(2), Article 3, 2020。査読済み。[出版社](https://programming-journal.org/2020/4/3/)、[著者配布本文](https://people.seas.harvard.edu/~chong/pubs/programming20-shilldb.pdf)、DOI 10.22152/programming-journal.org/2020/4/3。出版社のonline公開は2019-09-30、本文表紙は2019-10-01と異なるため、巻年2020と区別する。

読了：書誌・Abstract、§3冒頭とproxy説明、§4.2–4.3、§5.1–5.2の設定・本文結果。付録や全図表、コードは未再現。capabilityを契約proxyで包み、許可操作だけを実行する。joinの複数資源にまたがるstateful契約も扱う。予約システム5endpointと4実装、各workload50回の評価で、本文は最大5.43%のslowdownと報告する。SQL機能やtransactionの制限を明記する。

A2の「同じ命令定義が権限と効果を決める」原理は、この系統に近い。WIT borrowの寿命や遅延受付への対応は違うが、言語の制限によって任意executorを排除する一般形を新しいとはできない。環境・用途が違うため上記性能と今回のNode測定を直接比較しない。

## ACE

Evan Li, Tushin Mallick, Evan Rose, William Robertson, Alina Oprea, Cristina Nita-Rotaru. **ACE: A Security Architecture for LLM-Integrated App Systems**. NDSS 2026。査読済み。DOI 10.14722/ndss.2026.230352。[会議本文](https://www.ndss-symposium.org/wp-content/uploads/2026-s352-paper.pdf)、[公式採択一覧](https://www.ndss-symposium.org/ndss2026/accepted-papers/)。著者版arXiv:2504.20984と会議版を区別する。

読了：書誌・Abstract・Introduction、§IV A–Cの計画、executor説明、§IV Fの情報流、§Vのutility結果とTable III/IVの抽出テキスト。全appendixや実装、攻撃評価全体は未検証。信頼する情報から計画を作り、具体化した計画を検証して制約された実行環境で実行する。単一query等の範囲に制限する。表の最終結果正答率はモデルとsuiteにより66.7～100%であり、全条件80%以上という一般化はしない。

A2はLLM計画ではなく定型WIT入力から生成する。しかし、固定した計画に実行を拘束するという広い主張には先行する。A2の新規性を補強するために「不変な計画」という語だけを足しても差分にならない。

## 境界の割当・走査予算

- Bytecode Alliance / Alex Crichton、**Guest-controlled resource exhaustion in WASI implementations**, GHSA-852m-cvvp-9p4w、2026-02-24。[公式advisory](https://github.com/bytecodealliance/wasmtime/security/advisories/GHSA-852m-cvvp-9p4w)。Impact、設定、Patchesを読了。host側のresource・copy・bufferingを対象に、hostcall fuel等の上限を導入した。今回この修正をWasmtimeで再現したわけではない。
- Bytecode Alliance、**Dynamic record lifting can allocate beyond the hostcall fuel limit**, GHSA-jqpg-j7w6-42pr、2026-09-24。[公式advisory](https://github.com/bytecodealliance/wasmtime/security/advisories/GHSA-jqpg-j7w6-42pr)、[修正PR14415](https://github.com/bytecodealliance/wasmtime/pull/14415)。Impact、Patches、PR説明とmergeを読了。dynamic Val APIのrecord等の割当計上漏れで、静的bindgen APIは対象外と明記。修正コード全文の検証は未実施。WITでhost割当を計上する原理は既知。
- Kenton Vardaら、**Cap'n Proto Encoding Spec / Security Considerations**。[公式仕様](https://capnproto.org/encoding.html#security-considerations)。Pointer Validation、Amplification attack、Stack overflow DoS attackを読了。重複参照も毎回走査費用に数え、zero-size要素も費用を持たせる。査読論文ではなく実装仕様。公開現行ページの確認であり、全記述の初出年は未確定。

今回のmemo付き事前検査は、同じdescriptorの再計算を省きつつ出現回数を費用へ戻すが、memoizationと上限計算は一般的技法である。正しい非memo対照に勝てなかった[実測](../../results/masters-security-20261024/abi-performance-v2/report.md)もあり、主発明へは昇格しない。

## WASIへの適用範囲の確認

[wasi-filesystem v0.2.0の公式types.wit](https://raw.githubusercontent.com/WebAssembly/wasi-filesystem/v0.2.0/wit/types.wit)のdescriptor、read/write系、open-at周辺を確認した。WASIにはoffset、byte列、結果型、stream生成、pathとflagsに依存する操作がある。A2の小さいread/writeは全体読取り・全体置換であり、そのまま標準WASI adapterを置換するものではない。一般WASI適用率を、6自作recipeの成功率から推定しない。
