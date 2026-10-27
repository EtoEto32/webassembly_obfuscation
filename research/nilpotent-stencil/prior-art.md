# 近接研究と確認した範囲

2026-10-19調査。一次資料の実際に確認した内容と、こちらの推論を分ける。特許の新規性・進歩性や実施自由の判定は行っていない。

1. **Joan Feigenbaum / Lance Fortnow, On the Random-Self-Reducibility of Complete Sets**, Sixth Annual Structure in Complexity Theory Conference, 1991, preliminary version。[著者公開PDF](https://www.cs.yale.edu/homes/jf/FF-Structures1991.pdf)。査読会議版。表紙、§2、Fact 2.4の構成を確認した。多変数多項式を直線上で評価し、補間によって定数項を得る原理を明記している。次数dに応じたd+1回の評価と有限体を使う。今回の決定論的・非単射な写像は論文の乱数分布の条件を満たすと主張しない。定数項を回復する枠組みそのものの先行性があり、本案に最も近い数学的構成である。後年のSIAM版は存在を確認したが、その全文を今回精読したという扱いにしない。

2. **Ferhat Erata, TingHung Chiu, Anthony Etim, Srilalith Nampally, Tejas Raju, Rajashree Ramu, Ruzica Piskac, Timos Antonopoulos, Wenjie Xiong, Jakub Szefer, Systematic Use of Random Self-Reducibility in Cryptographic Code against Physical Attacks**, ICCAD 2024, 9 pages, DOI [10.1145/3676536.3689920](https://doi.org/10.1145/3676536.3689920)。[著者会議版PDF](https://www.cs.yale.edu/homes/antonopoulos-timos/ICCAD-2024.pdf)の書誌・要旨・導入を確認。査読会議論文。先に読んだ[arXiv:2405.05193v1](https://arxiv.org/html/2405.05193v1)は題名に“In Cryptographic Code”のないプレプリントで、§I、§VIII–IXの記述を確認した。入力を変えた複数回の計算による物理攻撃対策を扱い、RSA-CRT・Kyberで評価する。著者は電力漏洩指標の大幅な減少を報告し、並列化・vector化の可能性にも言及する。今回の公開バイナリからの意味回復とは攻撃モデルが違い、その効果を転用しない。評価表全体の再計算・著者実装の追試はしていない。

3. **Victor Shoup / Nigel P. Smart, Lightweight Asynchronous Verifiable Secret Sharing with Optimal Resilience**, Journal of Cryptology 37, article 27, 2024-06-06, DOI [10.1007/s00145-024-09505-6](https://link.springer.com/article/10.1007/s00145-024-09505-6)。査読誌論文。書誌と§2.1–2.3を読んだ。環上の補間には評価点差が単元となる条件を置く。本案の256刻みはこれを満たさないため、同論文の一意な補間や秘密分散の安全性を引用して正当化できない。本案は限定された係数の消滅と整数重みの恒等式を直接証明する。AVSSプロトコル・安全性証明の全体は今回未読。

4. **ASPIRE D2.01 (2014)** と **US7966499B2** は[前の有限環・多項式変換の照合](../polynomial-carrier/prior-art.md)を参照した。可逆符号化で更新則を変形する構成、有限環での同値式置換一般は既知。今回それら全文を再読したわけではない。非単射な評価点と定数係数射影は構成上の差であるが、保護効果の独立した差は実測で判定する必要がある。

5. **US20230079663A1, Optimized distributed private matrix multiplication**, 公開2023-03-16。[公報ページ](https://patents.google.com/patent/US20230079663A1/en)。直接openが失敗したため、検索抽出にある多項式符号化・workerでの乗算・補間の記載のみ確認。発明者全員、請求項全文、審査経過は未確認である。新規性を反証し得る追加調査先であって、今回の請求項対比が完了した公報ではない。

## 差と棄却理由

本案の具体的規則は「Z/(2^32)の256の倍数の方向へずらすと、元の次数によらず評価点変数の4次以上が消える」「各laneが非単射でも4点の重み付き合成で元結果を得る」「これをWasmのi32x4へ生成する」の3点である。通常の体上補間とは条件が違う。一方、代数上の恒等式・SIMD化・既知の自己還元構成の応用を、そのまま新規発明と断言しない。

最も大きな査読上の懸念は、既知の評価・再構成という枠組みとの差が限定的なうえ、方式既知の定数係数射影が元DAGの規模に近い費用で済むこと。今回の差分を有効な主発明として推す根拠は得られていない。各laneの非単射性だけを強度と呼ぶのも不適切である。

## 実装前に除外した方向

- 原子比較交換命令への単純置換：[M/o/Vfuscatorの作者README](https://github.com/xoreaxeaxeax/movfuscator)がCMPXCHG/XCHGを含む変換を明記。READMEの該当箇所を確認した。Wasmへの置換だけを新候補にしない。
- 状態集合の実行：[既存のNFA重なり実験](../overlap-automata/README.md)、[状態被覆](../quotient-lift/README.md)と重なるため、集合数を増やす方向を再実装しなかった。
- 例外を制御移送に使う案：Chenほかの[BOSH, MICRO2009著者資料](https://ipads.se.sjtu.edu.cn/_media/publications%3Abosh-micro09.pdf)の検索抽出と[大学書誌・要旨](https://experts.umn.edu/en/publications/control-flow-obfuscation-with-information-flow-tracking/)を確認。tag違反を制御移送に利用する先行例であり、例外を使うこと自体を新原理に数えない。今回の例外案は具体的な独立差を確立できず、Wasm実装には進めていない。

これらの除外した方向を「独創的な3算法を発明した」という数には加算しない。
