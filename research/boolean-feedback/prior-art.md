# 読んだ範囲と類似原理の照合

2026-10-23。検索語と一致文献の不在は新規性の証拠にしない。数値評価を読んでいない文献は推測で補わない。

|文献|区別・読んだ範囲|今回との関係、未確認範囲|
|---|---|---|
|Gadouleau, Richard, *Simple dynamics on graphs*, TCS628:62–77,2016, [DOI](https://doi.org/10.1016/j.tcs.2016.03.013)|査読論文。大学書誌、[著者版](https://webusers.i3s.unice.fr/~richard/PUBLICATIONS/JOURNALS/2015_Simple.pdf)要旨・Prop8(2)と証明|nilpotent Boolean dynamicsは既知。残差への挿入は別の条件を要し、今回反例を得た。全定理・実験再現はしていない|
|Anashin, Khrennikov, Yurova, *T-functions revisited: new criteria for bijectivity/transitivity*, Designs,CodesandCryptography71:383–407,2014（online2012）, [DOI](https://doi.org/10.1007/s10623-012-9741-z)|査読掲載書誌と要旨。[arXiv版1111.3093v2](https://arxiv.org/pdf/1111.3093)導入・§2.1の定義と演算例|加算・乗算・bitwise命令の合同保存とbit単位の三角性は既知。普遍残差補正器の有限収束分類が同論文にあるとは確認していない。主定理と評価の独立再現なし|
|Haitao Li, Xiaojun Pang, *A polynomial-time criterion for stability of large-scale switched conjunctive Boolean networks*, Automatica, article111340, [DOI](https://doi.org/10.1016/j.automatica.2023.111340)|査読論文、出版社要旨・導入、2023 DOI。本文全体は未読|任意切替・node removal・joint graph条件による安定性判定が既知。今回の残差族と同一の生成則だとは断定しない|
|F. F. Li, *Global stability at a limit cycle of switched Boolean networks under arbitrary switching signals*, Neurocomputing133:63–66,2014, [DOI](https://doi.org/10.1016/j.neucom.2013.11.031)|査読論文、出版社要旨・導入|switching-incidence matrixと安定性判定が先行。有限遷移graphのcycle除去を発明の中心には置けない。数値例未再現|
|Schurr, Szabó, *Finding the Sink Takes Some Time*, ESA2002:833–844、拡張版DCG31:627–642,2004, [著者掲載一覧](https://page.mi.fu-berlin.de/szabo/optimization.html)|査読掲載書誌、著者PDFの検索抽出された要旨・outmap定義まで。本文直接openはtimeout|三角Fの残差s XOR F(s)はcubeのoutmapとしても検討できる、という今回の類似性推論。一般のoracle下限を公開コードの難読化へ転用しない。一般USOの定理を今回のNへ直接適用してはいない|
|Holroyd, Levine, Winkler, *Abelian logic gates*, CPC28(3):388–422,2019, [DOI](https://doi.org/10.1017/S0963548318000482)|査読掲載は大学・出版社で確認。[2015プレプリント](https://arxiv.org/abs/1511.00422)要旨と検索抽出の導入|粒子の処理順序に依存しない計算・単純gateによる有限processor実現は既知。sandpile/abelian networkへprogramを移すだけの案を新発明として実装する根拠はない。本文全体・性能例未確認|
|Moore, Nilsson, *The Computational Complexity of Sandpiles*, JournalofStatisticalPhysics96(1–2):205–224,1999, [研究機関書誌](https://web-prod.santafe.edu/research/results/papers/1466-the-computational-complexity-of-sandpiles)|査読掲載書誌・要旨、[1998プレプリント](https://arxiv.org/abs/cond-mat/9808183)要旨|sandpileへの論理計算表現に先行性がある。P-completeという最悪時の並列計算量を、ソフトウェア保護の解除費用と同一視しない|

検索した方向：`obfuscation sandpile/chip firing/abelian network`、`rotor router Boolean circuit`、`switched Boolean networks arbitrary switching`、`2-adic Boolean convergence`、`unique sink orientations memoryless pivot`、`T-functions fixed point`。実装前の着想検査も含み、sandpile案を追加実装済み候補として数えない。

今回得た25,968個の分類、word持上げ、任意切替族の具体的構成には論証と実験がある。一方、同一先行記載の不存在、進歩性、広い適用範囲、実用的保護効果は未確立。WO2012040383A1の座標変換との数学的差は[前候補の照合](../hidden-filtration/prior-art.md)も参照する。
