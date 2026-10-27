# 0割当による符号化演算の補正削除：発明検討記録

追加照合：Hamburg(CHES2009)に特殊値表現とpermuteの零出力、飽和演算・log表を合わせる近い先行構成を確認した。書誌・読取箇所は[追加資料](../saturation-anchor/prior-art.md)。従来の単位bit版に加え、[飽和カウンタ版](saturation-anchor.md)を実装・測定した。広い零割当の着想を新規性とすることは、さらに難しくなった。

2026-10-21。目的は既存技術の実行費用を下げる改良発明。新しい数学原理を要件にしない。[実装・測定](../zero-anchor/README.md)があるが、出願に用いる主発明や請求項を確定したものではない。

## 課題から効果への対応

| 項目 | 今回具体化した内容 |
|---|---|
| 近い既存技術 | 小表の入出力置換による符号化計算、SIMD表引き、表の融合、範囲を利用する命令選択 |
| 不足・原因 | 小領域の加減算では符号化表を引く前にmod16補正が必要。範囲内だけを扱う軽量化では、実際に16や255になる添字は扱えない |
| 具体的変更 | 到達可能な範囲外添字のmod16結果集合Zを求め、各zにE(z)=0を要求する。置換に対する要求が一つ以下なら整合する表を生成し、対応する補正を除く。接続先復号表を更新する |
| Wasmとの関係 | swizzleの零出力とrelaxed_swizzleの許された複数結果を同時に満たすよう割当を制約。通常の型検証だけでは確認できない意味上の条件を生成段階に組み込む |
| 実施例 | 4bit状態と入力bitの加減、混在列を実.wasmから変換。自由置換、制約のみ、補正除去、二行融合表を比較 |
| 観測した効果 | 8/32段の一環境測定で、同じ制約を持つ補正あり版より約9–16%時間減。binaryも減少。追加linear memoryなし |
| 主張しない効果 | 解析不能性、新たな暗号安全性、任意Wasm対応、一般的な保護強度の維持、特許の取得可能性の確認 |

構成の最小単位は「符号化表の使用」ではなく、到達範囲→範囲外結果の制約→置換生成→補正除去→隣接表整合という処理列である。性能が出たことと、この処理列に十分な先行技術との差があることは別に検討する。

## 読んだ先行資料と反証

### 1. 仕様と先行する命令費用の問題

[WebAssembly Relaxed SIMD Overview](https://github.com/WebAssembly/relaxed-simd/blob/main/proposals/relaxed-simd/Overview.md)のswizzle疑似コードを確認した。0..15では表の値、16..127では零または下位4bitの表参照、128..255では零。本試作の一致条件はこの公開仕様から導かれる。命令そのものを発明とはしない。

[Inefficient x64 codegen for swizzle #93](https://github.com/WebAssembly/simd/issues/93)、abrown、2019-08-12のissue本文を確認した。Wasmの範囲外零処理とx86 PSHUFBの差による追加命令という課題は既知。今回実測したV8の機械語を確認した資料ではない。零出力を活用する着想や費用問題を初発見とはいえない。

### 2. 零保存と符号化によるmod演算省略を記載する公報

Jan Hoogerbrugge、Wil Michiels、NXP、[US20160328543A1](https://patents.google.com/patent/US20160328543A1/en)、2016-11-10公開。題名 *Protecting the input/output of modular encoded white-box RSA*。同一系統の[US10726108B2](https://patents.google.com/patent/US10726108B2/en)は2020-07-28公開。

A1の配列添字符号化の説明、modular exponentiationへの適用説明、請求項1–15を確認。B2の対応する配列・mod説明と請求項1–6も確認。配列の乗算置換で0が0に対応すること、その固定を避けるための平行移動、符号化の法を計算の法と合わせてmod処理を省く記述がある。零保存や「表現選択で補正を減らす」という広い主張は避けるべき根拠となる。

本案は有限byte表の範囲外結果に合わせる置換制約であり、当該公報のsplit-variable RSA/ECC処理と同一実装ではない。しかし、上位の発想が既知である以上、命令種の違いだけでは差分を確定できない。明細書中の公知記載と、その公報の個々の請求項の範囲を混同しない。権利の存続や実施自由の判断はしていない。US20190251233A1の直接読取は失敗し、読めたB2と2016年A1で確認した。

### 3. SIMD表による符号化実装

Luoqi Chen、Yufeng Tang、Liangju Zhao、Zheng Gong、*SIMD Optimizations of White-Box Block Cipher Implementations with the Self-equivalence Framework*、Inscrypt2024改訂論文集2025、LNCS15543、pp129–149、[DOI:10.1007/978-981-96-4731-6_7](https://link.springer.com/chapter/10.1007/978-981-96-4731-6_7)。出版社abstract・書誌と[著者コードREADME](https://github.com/scnucrypto/SIMD-White-Box-Block-Cipher)を確認済み。本文は未読で、今回の制約付き生成規則が本文にないと断言できない。

小領域の表をSIMDで並列参照することは近い既存構成。今回の二行融合表はその一般的な構成を比較用に自作したもので、この論文の特定実装を再現したと扱わない。白箱暗号が対象でも、表現変換やSIMD実装の先行技術として比較する。今回の保護対象を暗号鍵へ変更したわけではない。

追補として著者公開コードを作業領域へ取得し、commit `5f36390beb98bcbd914a35998e231ad9141a2773` の次を読んだ。論文本文の未読は解消していない。全コードの監査や実行ではなく、明示した関数・範囲の読取である。

- [CEJO wbaes.c](https://github.com/scnucrypto/SIMD-White-Box-Block-Cipher/blob/5f36390beb98bcbd914a35998e231ad9141a2773/CEJO-White-box-AES/src/wbaes.c#L14)：generatePermutationとwbaes_genの先頭。16要素の自由置換・逆置換を生成する既存構成を確認。
- [Luo AVX2実装](https://github.com/scnucrypto/SIMD-White-Box-Block-Cipher/blob/5f36390beb98bcbd914a35998e231ad9141a2773/Luo-SE-White-box-AES/src/wbaes_se_lt_avx2.c#L86)：GEN_TABLE_DATA_F4/E4、AFFINE_ENCODING。4bitの線形表を生成し、上位/下位nibbleをmaskで抽出してshuffle表参照・XORで合成する。線形表の零入力が零になること自体も既知構成に含まれる。
- [Speck AVX2実装](https://github.com/scnucrypto/SIMD-White-Box-Block-Cipher/blob/5f36390beb98bcbd914a35998e231ad9141a2773/Vandersmissen-SE-White-box-speck/src/wbspeck_se_avx2_128_256.c#L4700)：同種の表生成・AFFINE_ENCODING、gen_tableとencryptを部分確認。表参照の入力maskとbyte加算・carry処理がある。今回の範囲外結果集合から零割当を決める処理は、読んだ範囲では確認できなかった。

この読取は「公開実装には零保存がない」という主張を否定する。一方、実装の全体に今回と同じ規則がないことを証明するものでもない。固定commitと読んだ3ファイルのhashは[prior-code.json](../../results/invention-20261021/zero-anchor-report-v1/prior-code.json)に保存した。元の研究コードを変更・実行していない。

### 4. 符号化の制約が解析に使われること

Adrián Ranea、Bart Preneel、*On Self-Equivalence Encodings in White-Box Implementations*、[SAC2020の著者preproceedings PDF](https://sacworkshop.org/SAC20/files/preproceedings/02-WhiteBox.pdf)。Abstract、導入、6.1、6.2、Appendix E/Fを部分確認。符号化の構造を利用して候補空間を絞る攻撃が記載される。全本文・出版版のDOIを新たに照合した記録ではない。

本案の1点固定も解析者に公開される構造なので、選択肢が15!残ることを耐性の根拠にしない。今回の適応解析は自由置換版も含む132本を回復した。

## 検索の範囲・残る穴

2026-10-21に英語で、white-box/zero-preserving encoding、obfuscation/instruction-set constraints、SIMD lookup/encoding optimization、swizzle/zero/mask、公開特許の具体題名等を検索した。対象の狭い制約生成規則との同一記載は、今回読んだ資料では確認できていない。検索結果がないことは新規性の確認ではない。SIMD合成表の自動生成にも関連し得る検索結果があったが、本文取得に至らず、内容を補完していない。

不足は、Inscrypt論文の本文、コンパイラの範囲外表引き最適化とデータ符号化生成の実装、公報のより広い同義語・分類による調査。公報調査を完了したという状態ではない。

## 採否と次に必要な証拠

**性能改善部品として保持、特許の主核としては保留**。通常O3後も差が残り、アブレーションで補正削除に由来する時間・サイズ減を確認したため、単に既知要素を含むという理由で棄却しない。一方、最大の弱点は、公開命令仕様から自然に導ける条件付き最適化と見なされ得ることと、適用が単位bit演算に狭いことである。

現在の補正なし版は、自由置換に比べて零への対応を露出する。特定復元器で両方全復元できた事実は、全攻撃で保護が同等であることを示さない。性能利益だけをもって難読化としての全体価値を確定しない。

次の価値ある検査は、一般的な範囲補正削除の先行実装との照合、実アプリ内で単位更新が支配する箇所への適用、二つ以上の零要求や分岐合流を追加負荷なく扱えるかの具体設計。一般加算に使えないという反例を無視して範囲を広く請求する資料は作らない。公開・push・出願は行っていない。
