# Hostの全上書きと、書込みを省略できる契約

2026-10-24。[事前計画](guard-import-may-plan.md)。旧`writes: public`は解析footprint内の全公開cellへの共通代入を**必ず**行う効果であり、単なる書込み許可ではない。この区別を明文化し、各cellへの書込みを省略できる`writes: may-public`を実装した。旧の保存結果を新契約で検証済みとは読み替えない。

## 変換と限定した簡約

各cellについて左右共通のmaskと任意値を取り、maskが真なら共通代入、偽なら左右それぞれの値を残す。read契約の観測はwrite前に行う。等式連言Rなら、全maskに対する閉包は`R ∧ close_all(R)`で得られる。

必要性は、許されるmaskがno-opと全上書きを含むことによる。十分性はatomごとに考える。全上書き後の任意値について成立する非自明atomは、書込み外の項同士の等式か、同じ公開cellの左右一致に限られる。前者はどのmaskでも不変。後者はno-op側のRが元の一致を保証し、代入すると共通値で一致する。各domainに少なくとも2値があり、異なるsortの値をcopyしない前提を使う。普遍量化は連言へ分配できるのでatomから全Rへ延長できる。

これは手書きの限定論証で、新しい一般的なWP理論ではない。2公開cell・1非公開cell・定数0/1の36 atomについて、Boolean maskを直接ForAllした別array式との同値をSMTで検査し、36 UNSATだった。一般Boolean式には成立しない。`(L0=R0) ⇔ (L1=R1)`は、両cellが不一致の状態でno-opと全上書きではtrue、片方だけ上書きするとfalseになる。この反例も保存した。

## 既存試験群での追加契約

従来16 binaryにmay-writeの[128契約](../../results/state-witness/guard-import-may-controls-v1/manifest.json)を追加した。無条件74、条件付き14、充足不能40。固定256初期storeは肯定162、否定94だった。各engineの2,038比較・4,536診断API・4,076準備call・3,020 import・1,504 cell書込み・2,584 pure tag呼出しが整合した。肯定例もno-op、全書込み、偶数/奇数位置だけの書込みを含む。ただしfootprintが1cellなら複数mask指定は同じ動作になるので、独立したcoverage数にはしない。

[別array式](../../results/state-witness/guard-import-may-check-v1/results.json)は588義務UNSAT、unknown0。[具体BFS](../../results/state-witness/guard-import-may-finite-v1/results.json)は512代表初期storeで一致310/差202、最大14状態、12,304遷移でKと一致した。[一般SMT](../../results/state-witness/guard-import-may-generic-v1/results.json)も128契約すべて同じ条件を生成した。[旧256契約の回帰検査](../../results/state-witness/guard-import-may-regression-v1/results.json)でも条件・proofを保存版と照合し、1,164義務UNSATだった。

**既存128対応契約ではmustとmayの初期条件は全て同じだった。** この試験群だけなら、両契約を取り違える実装でも検出できない。件数の多さを契約境界の網羅性と解釈しない。

## 二つのimportを持つ区別例

[2cellのmemory/table対照](../../results/state-witness/guard-import-may-pair-v2/manifest.json)を追加した。`arm`は寿命差により片側だけAを書いて共通trapする。`finish`は書込みimportを呼び、別の観測importが公開値を読んでから共通trapする。観測はreturnsとhost trace、trap後の再呼出しを許す。全上書きなら差が修復され無条件一致、may-writeなら全初期storeについて反例API列が存在した。4条件の24 array義務もUNSATだった。

まず固定列`arm→finish`で、2kind×4初期割当て×4mask×3書込値=96組を両engineで検査した。各384 API・192準備callで、54組一致/42組差を再現した。この固定列で一致することは、全API列で一致することを意味しない。

さらに[生成した反例](../../results/state-witness/guard-import-may-witness-v1/manifest.json)を、定数＋2代表値の32共通初期storeで再生した。全件で具体BFSと否定判定が一致し、両engine各132 API・64準備callで差を確認した。初期値が全てAの場合も、`finish`で共通の別値を書く→`arm`→書込みを省略/部分化した`finish`の3 callで差が出る。一般SMTもこの2条件を充足不能と判定した。最短性はこの拡張の主張に含めない。

pair-v1はtag用exportを解析入力から除外した版である。v2では既存tableから参照を取り、追加exportなしの同じ入力binaryを解析・実行して同じ結果を得た。pure tagを呼べるのは、定数だけを返すこの試験関数に限る。

## 解釈と再現

[import artifact v2](../../artifacts/state-witness-import-v2.zip)へmay契約・改善一般対照・2-import対照を含めた。35 source/設定file、83,120 bytes、SHA256 `8c1924d8f92ebefcda87a1d52e1a44eb7f0a9c44e393e1088def43ce7805a31d`。[新directoryでの再現](../../results/state-witness/import-bundle-replay-v2/results.json)で57 binary fileを同一bytesで生成し全チェックを通過した。57には異なる契約で使う同一binaryも含み、独立program数ではない。反復性能測定・外部復元器・ffmpegはこの小packageに含めない。

hostのmay-effectと必須効果の違い自体は既知である。今回残る成果は、限定Wasm復元診断の具体的な契約違いを実装し、旧試験群が見落とす対照と、再入後に初めて出る反例を示したこと。新しい一般解析原理、実用製品の新規bug、自然なアプリの有効性とはしない。

```powershell
python research/state-witness/guard-import-controls.py results/state-witness/local-may --writes may-public
python research/state-witness/guard-import-check.py results/state-witness/local-may results/state-witness/local-may-check
python research/state-witness/guard-import-finite.py results/state-witness/local-may results/state-witness/local-may-finite
python research/state-witness/guard-import-cached.py results/state-witness/local-may results/state-witness/local-may-generic
python research/state-witness/guard-import-may-pair.py results/state-witness/local-may-pair
python research/state-witness/guard-import-may-witness.py results/state-witness/local-may-pair results/state-witness/local-may-witness
```
