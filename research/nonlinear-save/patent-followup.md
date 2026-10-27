# 状態再構成の先行特許との技術比較

2026-10-23。実験集計の固定後に行った追加調査。主結果のsha256収録時点には含まれない。以下の関連箇所を実際に読み、表現の復元一般と今回の具体的生成手順を分けた。審査経過、全ファミリー、権利の有効性、抵触を判定する調査ではない。

|公報|閲覧範囲と内容|今回の構成との差|
|---|---|---|
|[US9436447B2](https://patents.google.com/patent/US9436447B2/en), Technique for live analysis-based rematerialization to reduce register pressures and enhance parallelism。発明者Xiangyun Kong, Jian-Zhong Wang, Yuan Lin, Vinod Grover。公報上の出願人Nvidia、優先日2011-11-07、B2公開2016-09-06、A1公開2013-05-09|書誌、説明末尾、請求項1–8。PPU用のコードについてlive-in変数が最多のblockを選び、変数部分集合の再計算の利益を評価して、後続blockでrematerializeする|今回はlive-in部分集合を選ぶのではなく、全入口状態の衝突関係から共通の非線形codeを作る。PPU、最多live-in blockの選択、利益最大化の再計算選択を実装していない。「復元を利用して保存費用を減らす」だけの説明では差分にならない|
|[US9235433B2](https://patents.google.com/patent/US9235433B2/en), Speculative object representation。発明者Thomas Wuerthinger, Lukas Stadler。公報上の出願人Oracle International、優先日2012-12-31、B2公開2016-01-12、A1公開2015-04-23|書誌、説明中のpacked/read-only/read-write表現とtokenによる復元、請求項1–6。想定を超えるobjectアクセスに応じてdeoptimizeし、次のアクセス水準を推測してflag付きコードを再compileする|今回は失敗位置を含む固定copy列の意味を事前に保つAOT変換であり、実行時の推測更新・再compile・アクセス水準の段階拡張はない。現在状態と補助情報から元表現を復元する一般的構図は先行している|

差分が記述できることと、その差分に新規性・進歩性があることは別である。今回の最も近い数理的先行研究は引き続き[functional index codingとcograph](prior-art.md)である。上記二件が同一方式だと結論づけたわけではなく、逆に二件と異なるだけで出願可能と結論づけることもできない。

残る具体的な技術要素は、二つのprefix損失階層からの彩色・clique同時生成と、Wasmの失敗copy前のrepair生成を一つの限定変換器へ落とした点である。全実験条件に安価な同等動作の回復が成立した事実は変わらず、この追加調査によって主候補へ格上げはしない。
