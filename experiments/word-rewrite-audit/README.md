# ワード単位の依存関係書き換え：採用前の具体的な規則照合

1. **状態: Inconclusive**。新しい難読化原理は未確立。今回の3案はこの形では採用しない。前回の復元器を拡張せず、候補の原理と既存の構造変換との関係を調べた。研究全体の目標は継続。

2. **達成事項**。固定コミットの先行実装から、局所置換、共役による補正、CNOTによる共役のコードを取得し、具体的な条件分岐を確認した。「回路の中間状態と依存辺を変える」という一般的な説明だけでは既存方式との差にならないことを、実装に対応付けた。未実装の相互依存ケースがあることも、新規性の証明として扱わない。

3. **未達成事項**。新規原理の仕様・変換器・SHA-256適用・解析困難性の優位性は不足。新しいWasmの生成・攻撃実験は今回行わない。既存方式と同じ説明に留まる案を、実装の容易さで選ばない。

4. **検討した具体的な規則**。純粋なwビットunsigned演算、加減算はmod 2^w、XORはワード単位、回転数rは固定。メモリ、trap、外部呼出しなし。以下は想定した変換であって、実装済みの新しいアルゴリズムではない。

   **R1: 読み取り側を補正して更新順を変更する。**

       Before: x = x+y; y = y XOR z
       After:  y = y XOR z; x = x+(y XOR z)

   yの更新は自分自身が逆操作である。Afterの第二式が読むy XOR zはBeforeの旧yなので、すべての幅で最終状態が一致する。途中状態と依存辺は変わるが、変更の原理は逆操作の代入による共役。Afterにも旧yを求める式がそのまま存在する。命令数増加を保護根拠にできない。

   **R2: 互いの更新値を読む演算を共役で交換する。**

       A(x,y) = (x+y, y)
       B(x,y) = (x, y XOR rotl(x,r))

   Bはinvolution。時間順にA;BをB;Cへ変えるには C=B∘A∘B とすればよい（∘は右から適用）。Cは次の明示式になる。

       t  = y XOR rotl(x,r)
       x1 = x+t
       y1 = t XOR rotl(x1,r)
       return (x1,y1)

   時間順B;CはB;B;A;Bとなり、先頭のB;Bが消えてA;Bに一致する。全幅の意味保存はこの恒等式で説明できる。しかしtで旧状態を復号する構造が残り、原理は既知の共役である。先行実装がこのケースをskipすることと、独立した新方式であることは別。融合後に別の保護機構が生じるかは未検証だが、その具体的な追加規則も今はない。

   **R3: 複数演算のwindowを同じ全入出力関数の別回路へ置換する。** Boolean gateの代わりにi32語演算を候補にし、辞書または合成で別実装を選ぶ構想。境界の状態を保ち内部DAGを変更する機構は、以下の先行実装に既にある。ワード幅、命令集合、生成器だけを替えても、今回要求された独立した原理とは認定できない。ビット幅が小さい場合の等価性だけでi32等価性を代用してはならない。

5. **先行研究・具体比較**。Local-Mixing/local_mixing、commit `5ce6daab669f50665f0c9aecf958f4066f407d01`。以前はgadgetとobserverを中心に調べていた。今回は新たに以下を確認。

   - [docs/local_mixing_documentation.md](https://github.com/Local-Mixing/local_mixing/blob/5ce6daab669f50665f0c9aecf958f4066f407d01/docs/local_mixing_documentation.md): 824–855行のLocal replacements / Sampling subcircuits。window境界の機能を保存し、内部回路を別の同値回路へ置換する。合法な可換移動で非連続windowを集める説明もある。
   - [transformations.rs](https://github.com/Local-Mixing/local_mixing/blob/5ce6daab669f50665f0c9aecf958f4066f407d01/src/engine/mixer/transformations.rs): 102–169行のconj_wake。片方向のread/write衝突に応じて補正gateを生成し、相互衝突ならNone。405–475行のCNOT共役は `cfg(test)` 付きであり、本番pipelineの常時有効機能と報告しない。CNOT代入による場合分けと補正は既にコードにある。
   - [replacement.rs](https://github.com/Local-Mixing/local_mixing/blob/5ce6daab669f50665f0c9aecf958f4066f407d01/src/engine/mixer/replacement.rs): 599–663行のtry_db_splice_curated。db_verifyが有効な場合に同値性を検査する分岐。supportが24を超える場合のANF比較と未決定時の拒否を含む。コメントの説明だけを読んで「全置換を常時検証する」とはしない。呼ばれるpolys_equivalent本体と全呼出し経路は今回未読。

   | 比較項目 | R1 / R2 | R3 |
   | --- | --- | --- |
   | 数学的な原理 | 可逆操作による共役・逆操作の代入 | 局所機能等価性 |
   | 表現体系 | 元の語状態と復号式が明示される | 既存の可逆回路window |
   | 状態変換 | Boolean版との差は演算と展開式 | 候補命令集合・ワード幅の変更 |
   | 依存関係 | 補正式で辺を移す、既存共役と同原理 | 境界を保ち内部DAGを変更、既存置換と共通 |
   | 困難性の原因 | 既知の逆操作を超える原因が未定義 | ワード単位にするだけでは新しい原因にならない |
   | 一般化 | 純粋可逆演算に限る | 等価性検証可能なwindowに限る |

   このコードにR1/R2のi32式がそのままある、と主張しているのではない。同じ数学的機構の命令集合変更だけでは採用しない、という判断。一般枠組みに属するすべての将来の具体発明を否定するものでもない。

6. **過去成果の再利用**。`tmp/local-mixing-source-audit/tree.json` の固定Git treeを取得物の照合に使用（A: Git blob SHA1との一致を今回確認）。同READMEと `tmp/local-mixing-observer-audit/README.md`、`tmp/semantic-fusion-audit/README.md`、`tmp/decoder-feedback-gate/README.md` を参考Cとして利用。gadgetの過去テストを今回のmixerの正確性証拠へ流用しない。

7. **実施・検証結果**。公開3ファイルを取得し、すべて保存済みGit treeのblob SHA1と一致。SHA256とサイズは `verified-sources.json`。読み取り範囲は上記の部分と関数位置検索のみ。取得した全コードを監査した、Rustをbuild/runした、回路生成やセキュリティを検証した、とは扱わない。fetch_sources.pyは保存先が既存なら上書きしない。

8. **攻撃比較**。今回未実施。R1/R2の式に逆操作が残るという説明は設計上の判断で、未知バイナリから復元した実験結果ではない。前回settling-recoveryの3/3結果もこの規則に対する成功率ではない。

9. **費用・最適化**。Wasmの処理時間・サイズ・最適化後の残存性は未測定。今回は採用前の調査を25分枠とし、固定3ファイルの取得と3規則の照合に限定。ネットワーク取得には各20秒timeoutを設定。新規性の理由が不足したためbackend実装へ進めない。

10. **改善判断**。露出したDAGの反復回数を変える案から、DAGそのものを変更する案へ移った。しかし共役と局所等価置換だけでは既存原理の範囲を出ない。R2の相互衝突対応を「先行実装にない」という理由だけで発明と数える方針は棄却する。これが今回の次行動を変える判断である。

11. **Before/After**。第4項のR1およびA;B→B;Cが想定例。手書きの仕様で、変換器の実生成物ではない。新規性gateに達していないためAfterのWasm・最適化後コードは未作成。原研究のコードは参照資料としてそのまま保存した。

12. **成果物・再現**。本ディレクトリにfetch_sources.py、sources.json（最初の取得失敗）、verified-sources.json（成功時のURLとハッシュ）、3取得ファイル、本報告。元のtree.jsonを保ったまま、experiments直下の空のコピーにfetch_sources.pyだけを置き、既存Pythonで実行すれば再取得・照合できる。既存ファイルがある場合は停止。Git tree/固定コミットが消えた場合の永続取得は保証しない。

13. **制約・調査ログ・残る課題**。ePrint PDFへのweb取得は403、raw GitHubへのweb取得はcache miss。通常shellのネットワークは10013で失敗。公開ファイル読み取りのsandbox escalationは許可され、固定3ファイルの保存に成功した。拒否を迂回したものではなく、権限レビューの結果に従った。元の論文全文の読了範囲は増えていない。

   検索日2026-10-12。検索語: `obfuscation reversible circuit local mixing arithmetic word gates conjugation commutator`; `program obfuscation polynomial automorphism tame automorphism triangular maps`; `Towards general-purpose program obfuscation pdf Canetti Chamon local mixing`; `local mixing obfuscation conjugation`。数学の検索結果は参考候補であり、本件の具体的難読化実装を否定する証拠に使わなかった。

   未解決なのは、共役・冗長表現・既存の局所等価置換との差を持ち、露出した更新全体の解析にも耐える具体的な規則である。今回の作業でそれを発見したとは報告しない。新規性と比較上の優位性を含む元の研究目標は未達成のまま保持する。
