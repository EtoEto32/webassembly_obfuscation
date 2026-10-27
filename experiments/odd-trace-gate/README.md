# 奇数長トレース案：先行性と32bit移植条件の早期ゲート

2026-10-21。**新しい主難読化方式としては採用しない。** 各読書きの復号をなくし、
計算全体を行列べき乗のtraceへ移す方向を調べたが、先行論文に近い構成があり、
奇数長への変更は有限環の単元条件への対応に留まる。実Wasmの小実験でも、
元ソースなしで重み積へ戻せた。新しい発明数を増やさない。

- [事前計画](plan.md)、[先行研究と今回の差分判定](prior-art.md)
- [正当性・負例・回復の結果](../../results/invention-20261021/odd-trace-gate-v1/checks.json)
- [binary-only回復](../../results/invention-20261021/odd-trace-gate-v1/recovery.json)
- [小語長全列挙](../../results/invention-20261021/odd-trace-gate-v1/model.json)
- [別engine・再現監査](../../results/invention-20261021/odd-trace-gate-audit-v1/audit.json)

## 構成と失敗条件

f=(x+y)*(z-t)をmod 2^32で計算する小例を使う。L頂点の有向閉路を作り、最初の
2辺にx+yとz-t、残る辺に1を付け、隣接行列Aを作る。実行時にはdense i32行列
積でA^Lを求め、traceを計算する。閉路のどこから始めても辺積はfで、始点がL個
あるためtrace(A^L)=L*f。これは一変数ごとの符号化ではなく計算全体の表現だが、
traceによる計算モデルそのものは既知である。

Lが奇数なら、L^-1 mod 2^32を掛ければfを得る。Lが偶数ならf=0とf=2^31が
同じtrace=0になり、traceだけから全域で復元できない。これは任意行列方式の
不可能性ではなく、このスカラー出力契約の問題。通常のunsigned除算もwrapで
失われた情報を取り戻せない。奇数でも通常除算と逆元乗算は異なる。

Wasmでは固定1pageのprivate memory、4個のi32入力、1個のi32出力を使う。
全アクセスは固定の行列範囲内、加算・乗算・減算はi32 wrap。入力値によるtrapなし。
生成器はこの小例専用で、任意Wasmを変換するcompilerではない。診断版のみtraceを
追加exportするが、回復器へ渡すのはrunだけをexportしたcoreである。

## 実測した範囲

L=3,5,7×raw/O3の6正条件で、共通134入力の804比較が一致。6回復版も同じ804比較
が一致。L=2,4,8×raw/O3の6負条件では整数除算版が誤答し、raw診断版で3件の
具体的な衝突を検出した。raw6本のtrace値も804比較でL*fと一致した。これらの
804件は互いに独立な入力集合ではない。

小語長1..6bit、L=2..8、全f値について、独立なPythonの実行列積で882条件を全列挙。
うち奇数長378条件では逆元復元も一致した。全i32入力の実装検証とはしない。

回復器は配布binaryから行列初期化を読み、単一閉路であることを検査する。
抽出した行列から評価器を再生成し、rawまたはO3のASTが一致することを確かめてから、
閉路の辺重みの積を出力する。元式・元sourceファイル・JSON・seedを読まない。
結果は全6条件とも同じ52byteのWasm。初期化の元のsource名や閉路の切断点を復元する
必要がない。再生成検査は限定profileを確認するもので、一般逆コンパイラではない。

全工程の単発回復時間は約74–119ms。外部WABT起動、再生成の確認、O3、出力コンパイル
を含む。統計的な解析費用や人間の時間の評価ではない。WABT interpreterではO3正3本と
回復3本の1入力ずつを照合し、O3正3本を再生成してbyte一致を確認した。

小例は公開I/Oからも容易に推測できる低次数式である。これを大規模プログラムの
保護効果や、一般の行列難読化への攻撃成功と読み替えない。早期ゲートで新規性と
保護の根拠が弱いと分かったため、性能・RSS・アブレーションの大規模評価や
汎用変換器は作らなかった。その未実施を研究全体の完了に置き換えない。

## 再現

Python3.9+、Node24.15.0、WABT1.0.42、Binaryen133。リポジトリ内の`.tools/`と
共通WAT helperを使用。追加依存なし。rootから未存在の出力先を指定する。

```powershell
python experiments/odd-trace-gate/gate.py run results/odd-trace-new/main
python experiments/odd-trace-gate/audit.py results/odd-trace-new/main results/odd-trace-new/audit
python experiments/odd-trace-gate/gate.py recover results/odd-trace-new/main/L5-O3.wasm results/odd-trace-recovered.wasm
```

有限環残差方式の既存の構成的提案は保持する。次の研究は、既知の別計算モデルへ
移すだけでは得られない生成規則を対象にする。単に閉路長・次元・基底を変えることを
次の独立原理に数えない。goalは未達のまま継続。
