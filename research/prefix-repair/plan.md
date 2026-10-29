# コピー列の失敗prefixを含む共有修復

2026-10-21。前turnのHasse実験はprogress。今回は別の原理として、符号化memoryのcopy列の修復を扱う。
既存copy-centralizerはBC=CBを要求し、copy-fiberも固定copyとの可換性を使った。
今回Bはcopyと可換でなくてよい。複数copyをnativeのまま実行し、終了/失敗prefixの差分を補う。

GF(2)でbyteを混合し、Y=B X。copy列のprefix行列をP_jとする。
native列の途中はP_j Yだが、観測時に必要なのはB P_j B^-1 Yである。
`D_j = B P_j B^-1 XOR P_j`。全D_jのrow spaceの基底Vと、`D_j=U_j V`を求める。
入口でz=VYを保存し、終了時/失敗copyの直前に `memory ^= U_j z` を実行する。

比較：plain、毎copyでrank修復(eager)、入口全snapshot(full)、共有basis(basis)。
全encoded条件で同じBを使う。basisが常に速いと仮定しない。
故意に失敗時修復を省くbad版を負の対照にする。

対象はprivate memory32/1page、定数区間copy列、各copyのdestinationを指定した番号だけOOBにする公開引数、
digest観測の限定profile。trapの後にも次のAPI呼出しで状態を観測できることを意味保存に含める。
動的な任意範囲、共有memory、host import、memory grow、任意関数への適用は未実装。

事前判定：

- 元binaryを読み、profileを検査して変換する。
- raw/O3で各失敗位置、反復呼出し、byte境界値/ランダム状態を照合する。
- 方式既知の解析でBと元copy列を回復できるかを調べ、生成manifestは攻撃へ渡さない。
- 性能・サイズ・変換時間・メモリ、eager/full/basisのアブレーションを分離する。
- 低rank差分のLINVIEW、補償コードのOSR、data encodingと比較する。
  これらを使っただけで独立した発明とは判定しない。
- 共有基底のrank最小性は「修復を入口で保存した線形値だけから計算する」方式内に限定する。
  現在memoryを補助情報に使う一般方式の最小性ではない。
