# 非線形表現を保つcopy列の最小共有退避：実装前の計画

2026-10-23。observer-closureの失敗を受け、単一更新式を隠す方向から離れ、Wasm bulk copyの途中trapを含む表現変換の生成を調べる。主発明へ自動的に昇格させない。side-saveの線形空間では扱えない非線形Eに対し、有限状態の識別と彩色を用いる別の生成法を試す。

物理入口y、可逆符号E、copy prefix P_jについて、実行中の副情報S_j(y)=P_j(y)、修復先T_j(y)=E(P_j(E^-1(y)))とする。共通保存code c(y)は、S_j(a)=S_j(b)かつT_j(a)≠T_j(b)となる全a,bを区別しなければならない。

両prefix族の同値類は時刻に従い併合する。二状態が初めて同値になる時刻をs(a,b),t(a,b)とすれば、必要な区別はs<t。二つの階層の比較graphをunion/joinで分解できるという仮説を先に検査し、最適彩色とclique証明を生成する。最小保存bit数はceil(log2 χ)。一般の非線形index coding全体を解くとは主張しない。

注意：このgraph構造は既知のlater-divergence-time graph/cographと近い一次論文が見つかっている。定理自体を新発明とは扱わず、先行するcheckpoint/state-saving/compiler生成との対応を確認する。

主範囲は4bit状態を4つの0/1 byteで保持し、定数memory.copyを実行するWasm。全16入口・全trap位置を列挙できる小profile。一般byte全状態、任意heap、共有memoryには拡張しない。比較は原、全入口保存、最良の線形保存、彩色保存、故意に失敗prefix修復を省くbad。

評価条件：(1)全状態の正当性とtrap後の再入呼出し、(2)color数のclique下界一致、(3)全GF(2)部分空間を用いた線形最小保存との比較、(4)保存bit・実際のlocal数・code/dataサイズ・実行時間を分離、(5)方式既知の回復。公開reset/peekがあるため、有限状態全数学習による同等実装が安い可能性が高い。保存削減と保護効果を混同しない。
