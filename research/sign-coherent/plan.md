# 整数領域での同符号群を使う係数混合

2026-10-22。前turnのprefix-repairは実装・監査を完了したprogress。
その失敗原因は公開decoderから表現全体が戻ることだった。今回はdecoderを置かず、非線形演算を通過できる表現を入力領域の性質から生成する仮説を検査する。

対象は低byteをsigned8へ変換した2入力、4個の整数affine式z_i、ReLU相当のmax(z_i,0)、重み付き和を持つ実Wasm。
全65536入力で、z_i>0の真理値が同じchannelをgroup化する。単にテスト集合で同じだったという条件にはしない。
group内で非負の整数可逆行列Bを選び、z'=Bz、後段係数c'=c B^-1へ置換する。
Bはunimodularな行加算から作り、逆行列も整数とする。z'のi32 signed overflowがないことを範囲評価で確認する。

同符号groupでは、各入力で全z_iが正、または全z_iが非正なのでReLU(Bz)=B ReLU(z)が成立する。
実装にB^-1や明示decodeは残さず、前後の係数へ吸収する。
この恒等式だけの新規性は主張しない。通常の全実数領域のscale/permutationや同一incoming weightの複製に対し、
有限整数格子では非比例のaffine式にも同符号関係が生じる点を具体的な差分候補とする。

3方向を早期比較した：

1. 任意のdense混合をReLUへ通す：一般にはReLU(Bz)≠BReLU(z)。採用しない。
2. 符号が固定した領域だけを混合：activationが単なる線形となるため容易に除去可能。主案にしない。
3. 正負は入力で切り替わるが、同時に切り替わる組だけを混合：これを条件付きで実装する。

事前評価：plain、permutation、同符号mixをraw/O3で比較。3合成fixtureを使うが、学習済みmodelの代表標本とはしない。
全低byte入力、上位bit違い、負例と対象外を検査する。実行時間・サイズ・変換費用を測る。
方式既知の攻撃には元係数・B・seedを渡さず、binaryからaffine式を抽出し、同符号groupを再発見して
そのgroupを一つのpredicateとaggregate affine式へまとめる。小係数predicateを再合成できるかも調べる。

成功条件は正しさだけでなく、同じ費用のperm対照に対する回復コスト増加、あるいは既存方式に対する具体的な構成差を示すこと。
正規化で同じ短い処理へ戻るなら、初期の独自性候補を保護効果と読み替えない。
近接先行研究はneuron splitting、ReLUのhidden symmetries、入力領域に限ったfunctional equivalence。
WAMO本文は取得できておらず、差分を確認済みにはしない。
