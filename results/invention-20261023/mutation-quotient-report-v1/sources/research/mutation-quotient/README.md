# 更新可能な状態から情報を消す案：成立条件と反証

2026-10-23。**動く実装と正当性の限定検証を得たが、新しい主難読化方式・特許の核としては不採用。** 公開更新を考慮して消去可能な情報量を分類し、readonlyの場合の消去をそのまま更新へ使えないことを示した。一方、同等の通常実装を公開I/Oだけから回復できる。独立した新規性と有用な保護効果の確立という研究目標は未達である。

- [事前計画](plan.md)、[成立条件・意味保存・回復法](algorithm.md)、[先行研究と読了範囲](prior-art.md)
- [実測と証拠一覧](../../results/invention-20261023/mutation-quotient-report-v1/report.md)
- [実Wasm変換・コード検査付き回復](prototype.py)、[公開I/O回復](io-recover.py)

対象はprivate配列と、差の照会・加算・相対コピー・定数k倍という限定API。消せるのは共通加算の d=min(32,nu_2(k-1)) bit。k=1なら32 bit、k=257なら8 bit、定数代入相当のk=0なら0 bitとなる。元初期状態が一意に戻らなくても、短い等価状態機械の回復を妨げない。

主90バイナリ448,230呼出し（trap16,110）、診断54バイナリ268,938呼出し（trap9,666）、I/O回復54バイナリ268,938呼出しで不一致0。診断版は内部状態関係とtrap時の全memory不変も検査した。同じ系列・入力の再利用があるため、これらの和を独立標本数にしない。別WABTの324呼出し、90本のbyte再生成一致、6件の32bit SMT閉性検査も確認した。全Wasmの形式証明ではない。

方式既知のバイナリ回復は変換36条件で成功。公開I/O回復はplain対照を含む54条件で成功し、配列長n回の値を返す問い合わせとreset1回を用いた。n=4/32/256の3サイズは同じAPIの設定違いであり、3つの実アプリではない。公開schema n,kを与える攻撃モデルの範囲を超えて一般化しない。

O3のk=257で、毎回差を再配置するcanonicalは元版の約1.58〜1.78倍だった。初期データだけ変えて元操作を維持するrepresentativeは約0.998〜1.013倍で、微小差を加速の証拠とはしない。この軽量な等価実装の存在は、情報消去を難しい実行表現へ結び付ける主張への反証になる。

## 再現

Windows、Python3.9、Node24.15.0、WABT1.0.42、Binaryen133。model.pyのSMT検査はZ3 4.13.3.0を`.tools/encoding-synthesis-python`から読む。変換自体はPython標準libraryのみ。共通処理はisotope-swizzle/prototype.py、connectivity-elimination/prototype.py、性能driverはspan-mask/bench.cjs。tool配置はrootの`.tools`。rootから未作成の出力先へ実行する。

```powershell
python -X utf8 research/mutation-quotient/run.py results/mutation-new/main
python -X utf8 research/mutation-quotient/model.py results/mutation-new/model
python -X utf8 research/mutation-quotient/audit.py results/mutation-new/main results/mutation-new/audit
python -X utf8 research/mutation-quotient/io-run.py results/mutation-new/main results/mutation-new/io
python -X utf8 research/mutation-quotient/performance.py results/mutation-new/main results/mutation-new/runtime
python -X utf8 research/mutation-quotient/report.py results/mutation-new/main results/mutation-new/model results/mutation-new/audit results/mutation-new/io results/mutation-new/runtime results/mutation-new/report
```

個別CLI：

```powershell
python -X utf8 research/mutation-quotient/prototype.py transform source.wasm target.wasm --mode canonical
python -X utf8 research/mutation-quotient/prototype.py recover target.wasm recovered.wasm
python -X utf8 research/mutation-quotient/io-recover.py target.wasm recovered-from-io.wasm --n 32 --k 257
```

初回main-v1はO3がdata segmentを分割することにreaderが未対応で停止した。readerを修正したmain-v2を主結果とする。このツール未対応を解析耐性・正当性の失敗に数えない。過剰消去版は実Wasmで出力差を検出し、不正schema・更新命令改変・公開memoryを回復器が拒否することも確認した。結果Wasm/WATはgitignore下でもローカルには保存される。外部公開・push・出願は行っていない。
