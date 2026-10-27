# 最も近い資料との照合

2026-10-21。以下は公開一次資料の読取であり、著者実装の再現ではない。

|資料|書誌・読取範囲|本試作への意味|
|---|---|---|
|Mike Hamburg, Accelerating AES with Vector Permute Instructions|CHES2009、査読会議、LNCS5747 pp18–32。[出版社・DOI10.1007/978-3-642-04138-9_2](https://link.springer.com/chapter/10.1007/978-3-642-04138-9_2)、[著者PDF](https://www.shiftleft.org/papers/vector_aes/vector_aes.pdf)。要旨、§2.1/2.4/2.5、§3.3、§4.1を部分確認。全評価表は再検証していない|特殊値表現をpermuteの零出力に対応させ、飽和加算とlog表を共同設計する先行構成。§4.1には零出力が表への加算の融合を妨げることも記載。今回の一般的な着想の新規性を弱める|
|Dgraph Labs and Contributors, Ristretto sketch.go|著作権表記2019、実装資料、査読論文ではない。[固定commit](https://chromium.googlesource.com/external/github.com/dgraph-io/ristretto/+/32c8947bc5c10e8d7b90fd539e27eaabe1db3d39/sketch.go)。ファイル全体を読取。TinyLFUとCM4を参照するコード|2カウンタ/byteの4bit表現、15で止まるincrement、右shiftと0x77による半減が実用コードに存在する。本試作の動機であり、そのcache全体や実行速度を再現したものではない|

Hamburgの対象はAESの有限体演算とtiming attack対策。本試作はprivateなカウンタの任意置換と上限への合流、Wasm strict swizzleを使う。対象が異なることだけで特許上の差が十分とは判断しない。今回のE(15)=0規則が読取範囲にそのまま記載されているとは確認しなかったが、零出力・特殊値・表の設計という中心的な先行要素はある。

関連するNXP公報、InscryptのSIMD white-box符号化、self-equivalence符号化とその解析、Wasm命令の費用問題は[zero-anchorの文献記録](../patent/zero-anchor.md)を参照。Inscrypt本文未読という制約は継続する。特許公報を網羅調査した状態ではない。

採否の基準は、既知要素を含むこと自体ではなく、具体的な変換規則に残る差と、比較によって確認できる効果。今回の飽和版だけを独立の新発明として数えない。
