# 他の原理候補を先行技術と照合した記録

2026-10-23。三つの「新発明」を数えるための表ではない。実装前後に何が否定されたかを残す。

|原理|生成規則の仮説|解析タスク・意味保存|費用・実装|最も大きい反証／Reject理由|判断|
|---|---|---|---|---|---|
|入力依存span|Boolean式をmembershipへ移し、入力を係数にした可逆shearを展開|局所ゲートへの復元。入力固定時の可逆性とspan構成で正答|係数評価＋O(m d²)、実Wasmを実装|spanと可逆多項式行列生成の直接的適用。適応解析で回復、実行費用が大きい|本実験後に不採用|
|Boolean差分のイベント実行|D_i f=f[x_i=0] XOR f[x_i=1]を生成し、入力変化ごとにyを更新|元式への回復。更新時点の他入力を正しく使えばy'=y XOR D_i f|n回の更新、微分式の膨張。未実装|初期値と公開微分を積分すれば元関数になる。生成法を微分置換だけにした場合、既知のBoolean calculus/incremental computationとの差がない|独立した生成規則を作れず保留|
|借用領域を戻す計算|未知のmemory wordを可逆操作で利用して復元する|依存消去による同等コード回復。normal/各trap時点の復元が必要|約2倍以上の局所操作＋load/store。限定Wasm実装|dirty ancillaに近い。6/6で初期値への依存を正規化消去|早期実験後に不採用|

## 差分案の既知性

[Sheldon B. Akers Jr., On a Theory of Boolean Functions](https://epubs.siam.org/doi/abs/10.1137/0107041?journalCode=smjmap.1), Journal of the Society for Industrial and Applied Mathematics 7(4), 487–498, 1959, DOI10.1137/0107041。出版社の書誌を確認。本文は取得していないので、具体的な生成手順が同一だと断定しない。[著者のIncremental λ-Calculusページ](https://www.informatik.uni-marburg.de/~pgiarrusso/ILC/)の概要にもprogram derivativeによるincrementalizationが示される。今回は詳細定理の読解前に、独立した規則がないため主案にしなかった。

## データ配置への再検討

同時に生きているfieldをアクセス履歴で移動させ、固定offsetの型回復を妨げる方向も検索した。しかし「更新に合わせて置換を徐々に変更する」という現時点の案だけでは、以下の具体的な先行技術と差がない。

- Zhiqiang Lin, Ryan D. Riley, Dongyan Xu, [Polymorphing Software by Randomizing Data Structure Layout](https://www.cs.purdue.edu/homes/dxu/pubs/DIMVA09.pdf), DIMVA2009, DOI10.1007/978-3-642-02918-9_7。査読論文。abstract、導入、§6 limitations、§7.2を確認。コンパイル時にfield配置を変える方式で、今回想定する履歴依存と同じとはしない。安全に変換できる構造の自動判定が限界として述べられる。
- Yunsi Fei, Zhen Jiang, [US12177328B2: Methods and systems for protecting against memory-based side-channel attacks](https://patents.google.com/patent/US12177328B2/en)。優先日表示2021-04-22、A1公開2022-11-17、B2公開2024-12-24。書誌とFIG.4/5付近の説明を確認。アクセス前のswapを重ね、旧・新配置の混在状態を管理して移す構成が記載される。目的はアクセスパターン保護だが、現仮説との構成上の近さがある。請求項全体・法的状態は評価していない。

この動的配置案は今回未実装。以前のlifetime-overlayとの違いだけを新規性の証拠にはしない。次に進めるには、単なる置換・移動頻度の変更を超えた生成規則と、方式既知のalias追跡に対する効果が必要になる。
