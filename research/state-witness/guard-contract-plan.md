# 観測範囲を選べる二つのstoreの条件合成（実装前）

2026-10-24。観測監査で393反例中63が追加observerだけのprivate store差と分かった。次の実装は、元APIの結果だけ、元からexportされたresource、全storeの三つを区別する。既知の関係解析・predicate transformerの特殊化であり、新しい一般的な観測同値理論とは主張しない。

## 必要な変更

従来の解析は毎API後の全store一致を要求するため、次のAPIを単一の共通storeで扱えた。非公開stateの差を許す契約では、左右のstoreを別々の変数として持たなければならない。segment状態が揃ってもstore差が将来公開resourceへcopyされ得るため、その時点で探索を打ち切ってはいけない。

状態対sごとに、左右の初期cell変数l_i/r_iと定数の等式連言G(s)を置く。各APIの左右効果L/Rを求め、結果と指定resourceの一致Eだけを局所条件にする。式は`G_next(s)=AND_a E(s,a) AND G(T(s,a))[L,R]`とする。元の前提が共通初期storeの場合、最後にl_i/r_iを同じm_iへ置換する。観測対象外のcellに差を許す中間条件まで、この最後の置換を早めてはいけない。

単一load8_u(i32) APIは任意i32入力を受けるので、当該APIではmemoryの影響範囲全体の左右一致を要求する。影響範囲外のbytesは初期に共通で、どのAPIも変更しない。副作用のない定数返却APIは同じ値を返す。その他の受理範囲は既存bulk profileと同じにする。

## 厳しい対照

1. 従来134moduleの全store契約で既存条件・反例長が一致すること。
2. 公開resource契約で、監査の63private-only反例を誤って公開API反例としないこと。
3. private tableへの差が生じ、segment寿命が一致した後でpublic tableへcopyされる対照を作る。早期打切りを行う不完全版は見逃し、正しい版は公開差を出すはずである。
4. public tableへcopyする前にprivate slotを必ず同じ値へ上書きする対照では、元公開resource契約で一致するはずである。
5. 個別の条件・反例はNode/Wasmtimeと、別array式で照合する。table参照の一般的contextual equivalenceは主張せず、元exportされた純粋関数とのidentityを外部から照合できる対照を使う。

新規性の評価は、単に観測対象を選べるUIや既知の二項関係解析を実装したことから行わない。外部復元差の診断へ必要な契約を具体化し、誤った短絡を反証できる限定手法・実証として評価する。
