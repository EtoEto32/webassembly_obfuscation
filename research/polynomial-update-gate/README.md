# 可変多項式表現の更新差分による回復

2026-10-21。**可変辞書への拡張は実装できたが、新しい主発明としては採用しない。**
静的辞書の多項式表現を可変にしても、1件の更新前後の係数差から更新キーが直接
分かる。既知の補間を使った拡張の反証であり、別原理の難読化を発明した成果ではない。
[有限環方式の構成的提案](../repository-assessment-20261021.md)の限定採用は維持する。

- [事前計画](plan.md)、[実装](prototype.py)、[snapshotだけを入力とする回復器](attack.py)
- [正当性・回復集計](../../results/invention-20261021/polynomial-update-gate-v1/summary.json)
- [全呼出しの集計](../../results/invention-20261021/polynomial-update-gate-v1/checks.json)
- [各snapshotの回復結果](../../results/invention-20261021/polynomial-update-gate-v1/recovery.json)
- [別processの回復](../../results/invention-20261021/polynomial-update-gate-v1/isolated-attack.json)
- [性能・再生成・不正入力対照](../../results/invention-20261021/polynomial-update-audit-v1/summary.json)

## 対象と意味

固定キー集合を持つprivateな辞書。`lookup(k)->value`、`set(k,v)->found`を公開する。
setは既存キーだけを更新し、未登録キーなら0を返す。登録済みなら同値更新でも1。
値・キーは全u32を扱い、重複初期キーは最初の値を採用する。最大512キー。
任意の入力Wasmを変換するCLIではなく、同じ抽象辞書を実装する実Wasm生成器である。

元の静的版のp=2^32-5、根多項式P、値の剰余R0・商R1の補間を再利用する。
体に入らない末尾5キーは存在flagと平文値を持つ。これらを難読化したとは数えない。
変更キーkについてQ=P/(X-k)を合成除算し、Q(k)の逆元と値差からR0/R1を更新する。
商Qの作業領域は関数が戻るまでに零へ戻す。逆元は既知のFermatべき乗で計算する。

各Q更新、Horner、係数更新の積・和はp(p-1)以下、逆元計算の積は(p-1)^2以下で、
unsigned i64でoverflowしない。pへの剰余・除算は非零除数。登録キーが相異なるため
Q(k)は非零。最大512件でも作業領域末尾は8,224bytesで、全load/storeは1page内。
通常の実行でtrapは生じない契約であり、今回の結果はtrap保存実験ではない。
挿入・削除、共有memory、import、外部memory、callback、外部によるmemory変更は対象外。
抽象辞書の意味保存についての手作業の説明であり、全入力の機械証明とはしていない。

## 差分からの回復

Pをmonicな次数nの多項式とし、単一キーkの値成分がdeltaだけ変化したとする。
既知のLagrange基底より、更新前後の差Dは

```text
D(X) = alpha * P(X)/(X-k),  alpha = delta/P'(k).
P(X) = X^n + a X^(n-1) + ...
P(X)/(X-k) = X^(n-1) + (a+k) X^(n-2) + ...
k = D[n-2]/D[n-1] - a  (mod p),  n >= 2, delta != 0.
```

キー候補の抽出は上位2係数の差とPの1係数、体の逆元1回で済む。入力全体の読取・
候補検証はO(n)であり、攻撃全体を定数時間とは呼ばない。回復器は全係数で
`D*(X-k)=leading(D)*P`を照合する。R0とR1の両方が変化した場合は同じkを要求する。
値差がpでもR1側から回復できる。n=1はP自体からkが直接分かる別条件とする。

回復器へ渡すのは更新前後の係数bytesだけで、元辞書、更新引数、生成seed、lookup
oracleは与えない。これは引数や命令途中まで観測できるデバッガより制限した条件。
取得にはprivate版を生成・O3適用した**後**にaudit用memory exportを追加する。
private版とaudit版の双方を同じ逐次テストで照合した。export済みmemoryのバイト列を
通常版と一致させる意味保存契約ではない。任意のデータ表現から自動的に係数領域を
発見する汎用解析器でもない。公開formatと境界snapshot取得位置を知る解析を測っている。

RにPの倍数を足して係数を変更しても、公開Pによる剰余を取れば同じRへ戻る。
これは代数的な観察で、ランダム再符号化版を別に実装・測定した結果ではない。
複数の更新をまとめた場合の最適な攻撃は今回未実装。

## 実測結果

7種類の辞書（空、単一、2件、境界値、重複キー、8件、32件）について、配列/多項式、
raw/O3、private/auditの56本をWABTとNodeで検証した。JS Mapと逐次比較した
**170,298呼出しで不一致0**。同じfixtureの各版を独立ベンチマーク数へ水増ししない。

| snapshot分類 | 件数 | 結果 |
|---|---:|---|
| 通常キーへの非零更新 | 1,102 | キー・旧値・新値が全件一致 |
| 上記のうちn>=2 | 912 | 上位2係数差の式を適用 |
| 上記のうちn=1 | 190 | Pから直接キー取得 |
| 例外5キーの更新 | 176 | 平文位置から取得、保護成功に数えない |
| no-opまたは未登録キー | 978 | 全てno_changeとして区別 |
| 異なる2キーを更新した対照 | 10 | 全てnot_single_updateとして区別 |

R1だけ変化した44件も通常キー1,102件に含む。各snapshotの解析を同一Python processで
11反復し中央値を記録。32件辞書の回復214件では40.2–94.2µs、中央値44.4µsだった。
これはbytes入力からの読取・検証・値評価を含み、ファイルI/O、snapshot採取、解析器を
書く人間の時間は含まない。32件O3の1件は別processでもsnapshotパスだけで回復した。

| O3対象 | set中央値 ns | 3 process中央値の範囲 ns | binary bytes |
|---|---:|---:|---:|
| 8件・配列 | 5.06 | 4.95–5.15 | 237 |
| 8件・多項式 | 153.48 | 148.72–154.06 | 710 |
| 32件・配列 | 9.13 | 8.73–9.29 | 431 |
| 32件・多項式 | 466.46 | 460.06–483.61 | 905 |

Node24.15.0/V8 13.6、Windows10.0.26100、`--no-liftoff --no-wasm-lazy-compilation`。
各条件3 fresh process、8,192呼出しのwarmup、5ms目標で呼出し数を調整（上限131,072）、
9 batch。JS loop・キー選択・JS/Wasm呼出し・status集計を含む。最終値の検証は時間外。
キーは循環順で、性能時の値は連続整数。境界値の正当性テストと性能workloadは異なる。
軽い配列対照は上限に達して最短0.607ms/1.123msとなり5ms未達。CPU固定なし。
僅かな差の優劣には使わず、多項式更新が約30倍/51倍高コストという規模を読む。
全版のlinear memoryは64KiB。測定processのpeak RSSは43,640–44,904KiB。

生成本体は1回計測で0.013–2.213ms、WATコンパイル・validateは20.220–25.924ms。
これを汎用Wasm変換の時間とは呼ばない。全56本のbyte再生成が一致。
保存済み4,644ファイルのhashと4つの共有依存を照合し、壊れたsnapshot2件も拒否した。

## 先行性と判断

Lagrange補間・合成除算・逆元を新発明としない。
[NPTELのLagrange補間の導出](https://archive.nptel.ac.in/content/storage2/courses/122104018/node113.html)
は今回式を確認した教育資料であり、Wasm難読化の査読論文ではない。
[既存の静的版の先行調査](../polynomial-lookup/README.md)にあるFNP2004の集合多項式とも
区別する。公開係数からの回復を、暗号化した係数や多者プロトコルの攻撃とは呼ばない。

関連探索で[Sam JaquesによるALLOSAURの著者解説](https://sam-jaques.appspot.com/allosaur)の
TECHNICAL節も読んだ。失効集合を根とする更新多項式や係数配布は既に利用されている。
これは著者解説の閲読で、リンク先の長い論文本体やVitto/Biryukov論文を通読したとは
していない。本実験の2係数差の式と同一の既報攻撃を特定したとの主張もしない。
単純な補間式の帰結を独立した難読化の新規性へ転用する根拠はない。

回復可能であることだけを不採用理由にはしない。現方式では静的版の因数分解を
必要とせず、更新1件について直接O(n)で有用情報を検証できる一方、実行費用が大きい。
更新中も保護が強まるという根拠が得られず、これを新しい主案として拡大しない。
Wasm固有の新しい生成規則・既存方式を超える技術的効果・特許性は未確立である。

## 再現

Python3.9、Node24.15、リポジトリのWABT1.0.42とBinaryen133を使う。
追加Python/Node packageなし。rootから未作成の出力ディレクトリへ実行する。

```powershell
python research/polynomial-update-gate/run.py results/poly-update-new/main
python research/polynomial-update-gate/audit.py results/poly-update-new/main results/poly-update-new/audit
python research/polynomial-update-gate/attack.py results/poly-update-new/main/n32-poly-O3-audit-32-before.bin results/poly-update-new/main/n32-poly-O3-audit-32-after.bin
```

最初の起動では共有moduleの検索pathを先頭へ入れたため同名attack.pyへ衝突した。
出力生成前に検索pathの末尾追加へ修正。保存されたv1は修正後に完走した1回である。
計測中に別の重い処理を動かさない。hashとsource snapshotは各実行時点の版を保存する。
