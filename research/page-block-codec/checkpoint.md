# この区間の研究状態

2026-10-21。本区間は実装・実験・先行構成との照合を完了した progress。研究全体の目標は未達で、activeを維持する。ユーザーの既存有限環方式についての評価訂正を取り消さない。

- 実memory32 binaryのscalarメモリ操作を、同ページ数の符号化memory64へ変換。更新前loadの再利用と高アドレス優先対照を比較した。
- 主24正条件63,856比較と追加6条件15,964比較で不一致0。合計79,820比較、期待trap30,170。合成APIは同一で、独立30benchmarkではない。
- bad-partialの最初の反例は末尾store16で双方trapするが状態が違う。bad-wrapはp=4, offset=0xfffffffcのstoreが誤って成功する。零ページでは双方trapし、負条件に反例がないことも記録。
- O3、30fresh processでblockはbyte版より約4.45–5.47倍速い一方plain比約14.02–16.63倍。高アドレス優先より明確な優位はない。
- raw/O3の非空12条件から、型がv128->v128のhelperを選択書込み12回で同定。全論理memoryがsource実行と一致。攻撃はfixtureの書込みAPIを使う。任意アプリでの逆コンパイル成功率ではない。
- 6本byte再現、WABT70観測、4拒否、codec1024標本検査。audit-v1はshared fixtureのthreads flag不足で中断し、v2で完了。失敗履歴も保存。
- report-v1の368pinsを最終照合して一致。Python7ファイル・Node3ファイル構文検査、local link11件、git whitespace検査が通過。

主案への採用を見送る理由は、既知の高アドレス優先loweringで正当性の主要な動機を代替でき、復号器の再利用が安いこと。復元可能性だけを拒否理由にしない。WASMixer Algorithm1とMozilla Bug1343981の読めた本文、KSC2023の発表記録、KR103005503B1の検索抽出請求項1–9をprior-art.mdへ保存した。WeBMO本文は未読のまま。

次の区間でこの候補のページ数・codec段数・batch数だけを増やす実験は不要。表現変換の局所的な復号を消す方向にはEOC/LOKI等の先行構成があるため、別の具体的生成規則と解析課題を先に固定する。性能改善部品を、独立した主難読化方式の発明へ読み替えない。今回の全processは終了しており、待機対象のhandleはない。
