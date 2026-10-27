# メモリの射影だけを残す案：重なる読み取りと代表データへの復元

2026-10-18。可逆な配置変更と異なる方向として、利用結果だけを保存し元のフィールドを消す仮説を検査した。[実験前の設計・先行性照合](design.md)。実際のWasm変換器を実装したが、今回の限定規則は簡潔な等価実装へ戻せるため、アルゴリズム保護方式として採用しない。新規で有効な発明の完成を示すものではない。

## 規則と実装

元の `load8_u(base+a) XOR load8_u(base+b)` を、初期メモリから事前計算した表の1loadへ置換する。baseは `x << s (mod 2^32)`。全到達可能なbaseの正常な出力を保存し、元の範囲外入力は新しいmemoryに対する範囲外loadで同じmemory trapにする。物理配置を変えて後から元の値を復号する方式と違い、配布物に残るのはconsumerの結果だけである。

`transform.py input.wasm output.wasm` は実バイナリをvalidate・逆アセンブルして対象形を検査し、active dataを出現順に適用して初期メモリを得る。元のdataを出力へコピーせず、射影表を格納する。対象は非公開・非共有のmemory32 1ページ、単一のi32引数/結果の関数、同じアドレスの2個のload8_uとXOR。offsetは0–65535、shiftは0–15。より一般のconsumer、mutable memory、複数関数・import・start・global・table、メモリ公開には未対応。未対応を防御成功とは数えない。最適化前に変換し、その後にBinaryen133のO2/O3を適用した。

## 局所的な非単射性が消える条件

未知の先頭N byteと既知の零suffixという**公開schema**を仮定し、offset=(0,1)を検査した。全byte位置を読める場合、射影表は `t_i=m_i XOR m_(i+1)` を与える。既知の `m_N=0` から逆順に解くと元の全byteが決まる。単一のXORが非単射であることを、全体の情報消去と同一視できない。

一方、baseが2の倍数なら各pairは独立で、N/2成分それぞれに自由な1 byteが残る。元データと同じ出力を持つ入力の数は `2^(4N)`。N=32/128/512では、それぞれ128/512/2048 bitの自由度になる。これは公開schemaで固定したメモリ族における正確な個数で、攻撃計算量や暗号強度のbit数ではない。

`attack.py` はbyteのXOR制約グラフを作り、既知の零領域を1個のanchorへまとめる。anchorに接続した成分は一意、他の成分は1 byteずつ自由である。各自由成分の代表を0にして残りを伝播すれば、線形時間で同じ出力を持つメモリを作れる。その代表データと元と同じ2load+XORから、等価なWasmを生成した。元の値が一意ではないことを、元と同程度の簡潔な計算の回復に勝ったとは解釈しない。

零suffixを既知とする前提は必要である。N=65536の全ページが未知という対照では、全byte窓でも未接続成分が一つ残り、8 bitの自由度になった。この対照を含め、秘密の初期値を攻撃者に渡してはいない。公開I/Oが射影値を直接返す小例なので、強い難読化の肯定的評価には使わない。

## 実行結果

主結果は [manifest](../../results/invention-20261018/memory-quotient-v1/manifest.json)、[正当性検査](../../results/invention-20261018/memory-quotient-v1/checks.json)、[復元](../../results/invention-20261018/memory-quotient-v1/attacks.json)。3つのデータサイズ×2アドレス領域×raw/O2/O3を使用した。両領域で同じ元データを再利用し、18個の独立したデータセットを使ったとは数えない。

|検査|結果|
|---|---|
|元・射影・代表再構成|54バイナリをWABTとNodeでvalidate|
|全正常baseに対応する入力、wrap別名、境界、ランダム入力|3,553,335実行、不一致0。14,202回のmemory trapを含む|
|公開I/Oによる攻撃|全18条件で同じ挙動の代表データを回復。合計3,024問い合わせ|
|全byte領域|9/9条件で元データそのものを回復|
|2byte領域|9/9条件で元とは異なる代表データを回復。元の一意同定は不能|
|異なる元データからの同一出力|3サイズのpairデータで、異なる入力Wasmから完全に同一byte列の射影Wasmを生成|

各入力には同じデータと複数方式・最適化条件での再利用を含む。有限テストを全系の形式証明とはしない。全正常baseを列挙しても、全32bit入力を実行した意味ではない。アドレスのwrap別名はs=1で両方を試したが、範囲外の全入力は列挙していない。

復元器に与えたのは公開schema N、shift、offset=(0,1)と問い合わせ結果だけ。バイナリや正解データを読むのは実行・採点側で、復元関数が返した後に正解を参照する。コード上の分離でありOSの隔離ではない。既存のNotDecやRetypdを再実装したものでも、それらを実行した勝敗でもない。

## 正当性の追加監査

[監査結果](../../results/invention-20261018/memory-quotient-audit-v1/audit.json)を別保存した。O3入力条件の元/射影/回復をWABT interpreterで各6入力、計108実行し、Python参照との不一致0。元のdataの値・暗黙零・wrap・trapを照合した。

offset=(0,1)/(1,7)/(65535,0)/(65535,65535)、shift=0/1/8/15の16構成を追加生成し、先頭と末尾のactive dataおよび重なるdata segmentの上書きを含めた。32バイナリ、5,344実行で不一致0、4,836trap。[境界結果](../../results/invention-20261018/memory-quotient-audit-v1/boundaries.json)。この検査は大きな即値offsetをi32 wrap加算へ誤変換しないことも対象にする。

N=3/6/8、shift=0/1/2、3種のoffsetの27構成では、各byteを0/1に制限した全初期状態を列挙し、実際の逆像集合数と制約グラフの自由成分数が一致した。一般byte値に対する自由度の説明はXOR制約の構造から導くもので、この0/1全数検査を全8bit値の列挙とは呼ばない。矛盾する自己制約を拒否した。exported memory、store、アドレスの異なる2loadの3入力も対象外として拒否した。

## 性能と費用

[全比較表](../../results/invention-20261018/memory-quotient-v1/comparison.md)と[生の測定値](../../results/invention-20261018/memory-quotient-v1/performance.json)を保存した。54条件ごとに3個のfresh Node process、各10,000回warmup、その後20,000呼出し×9回、計162 process。中央値は各processの中央値3個の中央値。入力は元データ内を巡回する。ホストループ、呼出し、checksumの時間を含む。

O3入力条件では、元/射影の各中央値はおおむね11.6–12.7ns/呼出しだった。ただしprocessの中央値が約5.6–15nsに広がる条件もあり、この小差から速度の優劣を判断しない。Wasm本体だけの時間、製品全体の予測、統計的有意差を測った結果ではない。回復した出力に追加のO3をかけてはいない。

O3のサイズは全byte領域で元92/190/574 byte、射影98/196/580 byte。pair領域では元97/195/579 byte、射影93/141/335 byte。全条件の線形memoryは1ページ（65,536 byte）で、変わらない。O3の元/射影のprocess peak RSS中央値は約38.5–38.9MiBで、Node/JITやホストを含む。コードからのlogical memoryとprocess RSSを混同しない。

6変換の単発時間は約63–71ms。WABTの入出力・validate・Python処理を含み、別々のsourceを一度ずつ変換した診断値である。攻撃グラフ処理は約0.036–0.451ms/条件で、oracleの実行やWasm再構成を除く。反復した攻撃性能測定ではない。サイズ・時間の改善だけでは保護効果にならない。

## 判断と再現

部分評価・データ表現合成という既存の原理を越える新規性は確認できていない。今回の差分候補は、consumerの局所的な非単射性ではなく、到達可能なアドレス全体の制約で消去の可否を測る点だった。ただしランク・連結成分の計算自体は既知で、一般的な射影選択器も実装していない。この限定構成は元データを消せる場合にも簡潔な等価アクセス式へ戻せるため、主目的のアルゴリズム保護として棄却する。

次の設計で引き継ぐ条件は、「元の状態が一意でなくなる」ことに加えて「同じ計算をする容易な代表も作れない」機構が必要という点である。元データの消去を確認しただけで新発明の成功とはしない。一般の情報消去やWasm難読化の不可能性は主張しない。

環境：Windows x64、Core i9-11900K、Python3.9、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。Python外部パッケージ不要。ツールは`.tools`、別配置は`WASM_TOOLS_ROOT`。既存出力を上書きしない。

```powershell
python research/memory-quotient/transform.py input.wasm projected.wasm
python research/memory-quotient/experiment.py results/memory-quotient-new
python research/memory-quotient/audit.py results/memory-quotient-new results/memory-quotient-audit-new
python research/memory-quotient/report.py results/memory-quotient-new
```

WATパーサとツール呼出しは`research/observation-synthesis/transform.py`（import先`core.py`を含む）を再利用する。監査のsource snapshotに依存ファイルを含めた。`results/`のWasm/WATは既存gitignore規則により追跡対象外だが、ローカルに保存され上記コマンドで再生成できる。pushや外部公開は行っていない。
