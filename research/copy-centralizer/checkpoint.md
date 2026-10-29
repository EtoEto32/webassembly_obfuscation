# 2026-10-21 継続地点

この区間はprogress。コピー操作から中心化制約を生成する別表現を実装し、32主条件と8回復条件を実行した。全実験processは終了している。

- 主v2：22,016呼出し、192 trap、全memory不一致0。
- recovery-v2：8条件5,504呼出し、48 trap、不一致0。初期O3 reader未対応を修正。
- direct-v1：8条件それぞれ32 readだけで等価版を生成し、検証済み回復とbyte一致。
- runtime-v1とruntime-dispatch-v1：計96 fresh process。非自明な3profileの入力選択処理はconjugate比約30–58%短いが、plain比1.32–2.84倍。
- audit-v2：28小モデル7,392行列、32byte再現、40WABT/Node probe、4誤変換反例、3非対応拒否。初回監査のpath不備はv1に保存。

source-to-codecの具体的な生成器と費用削減は保持する。既知の中心化代数・線形符号化からの独立した新規性と、公開ABIに対する保護上の優位は未確立で、主方式には不採用。既存の有限環残差方式の限定した構成的提案を取り消さない。

探索中にはData Randomizationのunion-findによるmask割当と、word-level resolutionのmask説明も確認した。等価クラスのmask統合や、maskを付けたresolutionを独立の発明として数えない。前者の読解範囲はprior-art.md、後者の本文URLは https://arxiv.org/html/1706.09229v1 （今回確認したのは導入部の提案要素、詳しい全規則を検証したとはしない）。

次の段階では公開の低水準APIだけから計算全体を再構成できるtoy profileを避け、具体的な入力から意味を抽出する手間を測れる保護対象と新規則を同時に決める。単に既存の大きいベンチマークへ移すだけでは別原理にならない。目標は未達でgoalをactiveのまま維持する。
