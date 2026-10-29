# 先行技術と新規性の境界

確認日2026-10-23。検索語には `data structure obfuscation indirection`、`obfuscation pointer re-encoding`、`pointer permutation obfuscation patent`、`obfuscation pointer composition`を使用。検索で同一式を見つけられないことを新規性の証明にしない。

## 最も近い公報

Bertrand Raphaël Anckaert、Mariusz H. Jakubowski、Ramarathnam Venkatesan、Chit Wei Saw、**Data location obfuscation**。US9117094B2、公開2015-08-25。先行する公開US20100106920A1は2010-04-29。[公報](https://patents.google.com/patent/US9117094B2/en)。書誌、要約、説明の概要とメモリ管理、請求項1–19を読んだ。実行中の配置交換、pointer scrambling、アクセスの仲介を既に述べる。請求項10にはアクセス時の部分的な並べ替えを含む。

今回の限定差は、successor写像を二表の合成で表し、書換えと二位置交換を旧接続値の保存なしに四storeへ融合した点。公報の暗号化page管理とは粒度と規則が異なる。しかし、実行中に表現を変える大きな着想は既知であり、この狭い差だけで進歩性や保護効果を認めない。公報の法的状態、権利範囲への該当、全familyの調査は実施していない。

## データ構造変換の先行研究

Stephen Drape、**Generalising the Array Split Obfuscation**、Information Sciences177(1),202–219,2007、DOI[10.1016/j.ins.2006.03.012](https://doi.org/10.1016/j.ins.2006.03.012)。査読誌掲載の書誌を[Oxfordの著者所属機関一覧](https://www.cs.ox.ac.uk/activities/publications/type/algprog.html)で確認。出版社の要旨は抽象データ型、data refinement、list/matrixへの一般化を説明する。今回は本文・個々の変換の証明や評価表は未読で、同じ四store規則があるとは推測しない。

既存の構造分割・間接参照・表現不変条件と比べ、単に二表へ分けたことは独立した原理にならない。本方式で検証した一更新関係はこのdata refinementの枠組みに入る、というのが今回の技術的評価。

## 補助的な探索結果と未読範囲

- **Computer implemented masked representation of data tables**, [US8140809B2](https://patents.google.com/patent/US8140809B2/en)。Google Patents検索抽出でmasterTable、pointer置換handler、table更新の説明を読んだ。全ページ取得は失敗。発明者・全請求項の確認を終えた公報としては登録しない。
- Majumdar/Drape/Thomborson、**Slicing Obfuscations: Design, Correctness, and Evaluation**, DRM2007。著者PDFの検索抽出で要旨・導入のみ確認、openは失敗。変換の詳細・実測を今回の根拠にしない。
- WAMOの著者掲載情報とWWW2026の採択情報は再確認したが、ACM本文は403。モデル用の難読化との詳細な技術差を解決したとはしない。

## 今回の採否

同じ中間indexで複数の論理値を誤更新しない条件と、aliasした場合にも正しいstore順を実装・検査した。ただし方式既知なら二表を合成したNだけで更新要約が閉じ、変更履歴を消せる。先行性の弱さと実測した回復を合わせ、主特許候補には採用しない。小さな構成や意味保存の成功を、新規性・実用的な保護・特許取得の三つへ拡大しない。
