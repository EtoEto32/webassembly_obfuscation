# 例外参照方式の先行技術照合

確認日2026-10-19。査読論文、公開特許、仕様、本文未取得を区別する。検索結果なしは新規性の証明ではない。ここでは技術的な差を調べ、出願可否や権利侵害を判定していない。

## 本文を確認した資料

**Michael Batchelder / Laurie Hendren, “Obfuscating Java: the most pain for the least gain”, Compiler Construction (CC), 2007**。査読会議論文。[著者研究室の書誌](https://www.sable.mcgill.ca/publications/papers/)、[著者PDF](https://www.sable.mcgill.ca/publications/papers/2007-1/batchelder-cc2007.pdf)。要旨、§2、§6.3–6.8、§7–8を確認した。例外領域とhandlerの重なり、分岐の間接化などJavaソースとbytecodeの差を利用する。著者の評価はdecompilerの成功・不正出力・クラッシュ、実行時間とCFG規模を含む。報告された平均実行時間比は各方式0.96–1.16。今回JBCOは実行していない。当時のツール失敗やCFG規模から現在の適応的解析コストは導けない。

**WebAssembly exception-handling proposal, 2023年10月の合意を反映した版**。仕様・設計資料であり査読論文ではない。[公式explainer](https://raw.githubusercontent.com/WebAssembly/exception-handling/main/proposals/exception-handling/Exceptions.md)のOverview、Exceptions、Exception references、Try blocks、Throwing/Rethrowing、JS traps、binary encodingを読んだ。タグとpayloadから例外を作り、catch_all_refで参照化、throw_refで再送できる。nullの再送はtrap。Wasmのtrapはtry_tableで捕捉されない。[Core 3.0実行仕様](https://webassembly.github.io/spec/core/exec/instructions.html#exec-throw-ref)も照合した。参照の保持・再送はこの既知機能であり発明ではない。

**John P. E. Tobin, US7243340B2, “Method and system for obfuscation of computer program execution flow to increase computer program security”**, 公開2007-07-10、先行公開US20030093685A1は2003-05-15。[公開特許本文](https://patents.google.com/patent/US7243340B2/en)の概要、詳細説明、請求項1–37を確認（全39項の完全な対比ではない）。重要部分を例外handlerへ移すこと、handler内の選択や多段例外などが記載される。kernel/user modeやdebug資源を含む構成と、今回のVM内完結の参照共有は異なる。しかし例外内で処理する一般発想の新規性は主張できない。文献のdebuggerに関する記載を現在の事実として採用しない。

## 確認範囲が限定される資料

**Daniel Dolz / Gerardo Parra, “Using Exception Handling to Build Opaque Predicates in Intermediate Code Obfuscation Techniques”, Journal of Computer Science & Technology 8(2), pp.71–77, 2008**。[出版元書誌・要旨](https://journal.info.unlp.edu.ar/JCST/article/view/744)、[機関書誌](https://sedici.unlp.edu.ar/handle/10915/9626)、[出版元PDF](https://journal.info.unlp.edu.ar/JCST/article/download/744/271)。通常の雑誌原著で、プレプリントではない。今回のページから個別の査読過程は確認していない。PDF直接取得はtimeoutだったが、検索索引が返した§4とMSILのExample 1/2を読んだ。単純な条件を通常分岐ではなく例外発生へ移す提案。Wasmでは除算trapをEHで捕まえる移植はできない。全文、実験表、著者実装は未確認で数値効果を補完しない。

**Yusuke Sakabe / Masakazu Soshi / Atsuko Miyaji, “Java Obfuscation with a Theoretical Basis for Building Secure Mobile Agents”, CMS 2003, LNCS 2828, pp.89–103**。査読会議論文。[著者公開PDF](https://www.sos.info.hiroshima-cu.ac.jp/~soshi/y-sakabe-cms03.pdf)、[JAIST書誌](https://dspace.jaist.ac.jp/dspace/handle/10119/4446?locale=en)、[出版社目次](https://link.springer.com/book/10.1007/b13863)。書誌と要旨の検索抽出を確認したが、本文取得は失敗。多相性・例外とpoints-to解析が関係することは確認でき、近接性が高い。NP困難という要旨の主張を、今回の二タグ構成の難しさへ転用しない。例外参照の共有規則が一致するかは未確認。

## 今回の差分と反証

検査した具体規則は、i32のSSA条件式ごとに二タグpacketを一つ生成し、複数の選択箇所で同一参照を再送すること。handlerごとの反転に応じて真偽側の値を交換する。前案の差分メモリとは、算術符号化を用いず、制御移送とVM管理参照を使う点で原理が異なる。

ただし共有は通常の共通式・allocation削減に近い。参照identityを観測しないため、同じオブジェクトであるという情報は出力の計算に必要ない。タグをBooleanへ写す局所summaryが全利用点に適用できた。具体的なWasm loweringの全く同一の先行記載を見つけていないことと、独立した発明性があることは違う。保護上の追加優位性と新規性の両方が弱く、主案に採用しない。

検索語：`"exception reference" "obfuscation"`、`"throw_ref" "obfuscation"`、`"WebAssembly" "obfuscation" "exception"`、例外オブジェクト・handler・control-flowの公開特許。全特許DB、非英語の全公報、全実装、未公開資料を網羅していない。外部公開・出願はしていない。
