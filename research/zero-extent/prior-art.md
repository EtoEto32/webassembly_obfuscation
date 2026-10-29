# 先行技術・公開公報との照合

確認日2026-10-19。技術的な比較であり、特許の有効性、権利範囲、侵害や登録可能性の判断ではない。新しい方式名やWasmへの移植だけで新規性を認めない。

|資料|著者・時点・種別|実際に確認した内容と範囲|今回との関係|
|---|---|---|---|
|[Obfuscating computer program code, EP1947584B1](https://patents.google.com/patent/EP1947584B1/en)|Johan Eker, Björn Johansson, Carl Von Platen。B1公表2009-05-27、A1公表2008-07-23。特許公報|書誌、if-conversionの説明、dummy領域を使う例、請求項1–15を読んだ。A1本文取得には失敗し、B1を確認した。|分岐をguard付きの直線コードにし、guardを算術等へ移す一般構成は近接する。今回の零長・identity-copy検査の具体的な記載を確認したわけではないが、「分岐をデータにする」ことを新規性の根拠にできない。|
|[Eliminate Branches by Melding IR Instructions](https://drops.dagstuhl.de/storage/00lipics/lipics-vol372-ecoop2026/html/LIPIcs.ECOOP.2026.18/LIPIcs.ECOOP.2026.18.html)|Yuze Li, Srinivasan Ramachandra Sharma, Charitha Saumya, Ali R. Butt, Kirshanthan Sundararajah。査読済ECOOP2026、DOI 10.4230/LIPIcs.ECOOP.2026.18|Abstract、§1–4.7、§5.1–5.2を確認。MERITは命令列の対応づけ、operand選択、安全なdummyアドレスを用いる。著者報告では24 microbenchmarksで幾何平均1.52倍高速化。今回再現していない。|対応命令の共有や安全な投機を今回の新規性にはしない。全公開memory・0ページではdummyを置けないという対象条件が具体的な差。ただし、それだけで難読化効果や進歩性を示さない。|
|[GCC PR102202: length [0,1] memsetをconditional storeへ](https://www.mail-archive.com/gcc-cvs%40gcc.gnu.org/msg52987.html)|Naveen、2026-07-03、コンパイラcommit通知の公開ミラー。査読論文ではない|作者のcommit説明と変更一覧を読んだ。範囲情報を利用して長さ0を分岐で飛ばし、長さ1をbyte storeへ変える。GCC公式commit URLとGitHub mirrorの本文取得には失敗。|零長による書込み選択も、その逆向きの正規化も既知コンパイラ技術に近い。GCC本体を実行したとの主張はしない。Wasm特有の零長時boundsを追加した専用解析器を作った。|
|[GCC PR102202: length1, nonconstant fill](https://gcc.gnu.org/pipermail/gcc-patches/2026-June/720047.html)|Naveen、2026-06-11、公式patch mailing list|説明とdiff冒頭を確認。非定数のfill値でも1byte storeに変換する提案。|byte値が動的であることだけでは今回の差にならない。|
|[LLVM WebAssemblyISelLowering.cpp](https://llvm.org/docs/doxygen/WebAssemblyISelLowering_8cpp_source.html)|LLVM project、確認時公開ソース。版番号を固定した論文ではない|LowerMemcpy/LowerMemset付近の零長チェックと分岐生成を確認。|Wasm bulk命令とC/LLVMの零長意味の差への対応は既に実装上の課題。零長なら無条件に安全と仮定できない。|
|[WebAssembly core execution semantics](https://webassembly.github.io/spec/core/exec/instructions.html#memory-instructions)|WebAssembly 3.0、ページ表記2026-10-13、規格|store、memory.fill、memory.copy、memory.size/growの規則を確認。|fill/copyは長さ0の処理より先にboundsを検査する。各bulk命令は範囲検査前にbyte更新しない。今回の条件付き正当性説明に使用。|

## 特許向けの構成対応

|構成|既知の近接技術|今回試した具体化|現時点の評価|
|---|---|---|---|
|条件分岐を直線的なguarded effectsへ|EP1947584B1 請求項1,3–8、MERIT|Wasmのifを条件式付きのeffect列へ展開|一般原理は既知|
|非選択側の副作用を消す|dummyアドレス、述語化、零長memset|アドレスも0へ選択し、長さ0のbulk命令にする|限定条件の実装差。単独の新規性未確立|
|広幅storeの失敗前の副作用を保存|精密例外・事前範囲検査|同一宛先のcopyで全幅を検査してbyte fill列を実行|具体的構成は保存。ただし明示boundsと同等で、保護上の追加効果は未確立|
|非wrapの実効アドレス|Wasm標準意味|i64でoffset加算し、overflowを確実に範囲外へ写す|意味保存に必要な処理であり、それ自体を発明効果としない|

最大のReject理由は、known predicationと通常の範囲解析の間にある小さな実装差に留まり、特有の解析費用増加を実証できていないこと。公報の全family、審査経過、各国の現在の法的状態は調べていない。特許公報の記載が近いことと、個別請求項を充足するという法律上の結論は区別する。

検索で見つけたが今回の根拠にしなかった資料：WAMO (WWW2026)、Proof-of-Theft (ECOOP2026)、LLM-based Wasm deobfuscation (IEEE Access2026)。これらの本文を今回精読したとは記録しない。検出回避を最適化する実験は行っていない。
