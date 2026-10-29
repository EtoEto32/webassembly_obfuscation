# 次原理の早期選別

2026-10-24。以下は考察途中の方向であり、発明3案や実証済み方式として数えない。

1. 非公開Wasm例外tagにpayloadを封じ、exnrefだけを渡す能力表現。例外identity・生成的型・sealer/unsealerの先行性が強い。既存例外packet難読化とは目的が違うが、目的変更だけでは新規でない。[Wasm公式例外説明](https://github.com/WebAssembly/spec/blob/main/proposals/exception-handling/Exceptions.md)にある既知参照機能が中核になる。独立した新原理がないため追加実装しない。
2. 型ごとに権限を付け、未公開型で偽造を防ぐ表現。Wasmの構造的型を単に秘密の型名と扱えない。既知の能力参照・型生成との差が不足。既存type-identity研究の名称を変えて新案に数えない。
3. 相互運用時のcoercion/reentryの前後に権限検査を生成する方法。TOCTOU対策・型に沿う変換順序・既存A処理計画との重なりが強い。現時点で独立した新しいアルゴリズムになっていない。

新しい調査の手掛かりとして、Thalakottur, Bernstein, Lehmann, Pradel, Tip, **An Empirical Study of WebAssembly Usage in Node.js**, ICSE2026、DOI10.1145/3744916.3764533の[著者PDF](https://dlehmann.eu/publications/NodeWasmStudy-icse2026.pdf)abstract・Introduction・§2冒頭を読んだ。510 package/217 unique moduleは著者のdataset規模で、当方はまだ取得・追試していない。table mutation等の相互運用と未検査部分が次の具体問題候補。全文読了扱いにしない。

Yu, Zhan, Ye, Yu, Zhang, Tian, **Exploring and Exploiting the Resource Isolation Attack Surface of WebAssembly Containers**, USENIX Security2025の[出版元PDF](https://www.usenix.org/system/files/usenixsecurity25-yu-zhaofeng.pdf)abstract・Introduction・末尾の緩和方針を確認。WASI経由で生じるhost側費用の帰属が既知課題である。攻撃実験の追試はしていない。本研究で次に扱うなら小さいローカル模型で防御会計を検証する。

先行性の反証を通過する具体的機構がまだない方向へ、名称と請求項だけを作って成功としない。

追加screen（2026-10-24）:

- instantiation前にsegment範囲を全検査して失敗時の外部memory変更を防ぐ案は、[bulk memory提案のSegment Initialization](https://github.com/WebAssembly/bulk-memory-operations/blob/master/proposals/bulk-memory-operations/Overview.md)でMVPが元から全segmentを事前検査していたことを確認し、単純なpreflightを新発明とは扱わなかった。
- importの型照合をmemory制約の検査oracleにする方向は、既存linkingとtype reflectionが近い。[2020会議記録](https://github.com/WebAssembly/meetings/blob/main/main/2020/CG-02.md)の型反射・動的limit議論と[Yuta Saitoの2024-06-01 polyfill記事](https://zenn.dev/katei/articles/wasm-js-types-polyfill)導入を確認。後者はmodule binaryの型情報取得であり、hidden objectのlimit検索と同一実装だとは読んでいない。独立した発明として実装していない。
- 単純な全relaxed決定化は既存Wasmtime optionで可能だった。一方、共通profileの相関を考慮する部分変換は[Iの限定候補](../profile-repair/README.md)として実装・反証評価した。CEGISの一般原理は既存で、特許性は未確立。
