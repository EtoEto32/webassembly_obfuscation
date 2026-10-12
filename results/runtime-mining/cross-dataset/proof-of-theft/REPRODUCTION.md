# 完了したProof-of-Theftのハッシュ計算実験

既存の作業フォルダと`wasm-hash-reference:local`イメージを使う。記録したイメージIDは次のとおりである。
`sha256:a05286e66b0f1ca712671db5849229594c92e035bae253362cc8b6d0af4a70b6`.
追加の測定前にイメージIDを確認する。保護設定は変更しない。

完了したxmr-wasm実験の正式な結果は`xmr-repeated-throughput-20261008.json`にある。
5ファイルを各3回測定し、ウォームアップは3秒、各測定区間は少なくとも30秒とした。
同期実行するワーカー1個を使い、実際の経過時間で速度を求めた。
測定前に、適用できる公開CN/0テストベクトルとの出力照合を行った。
各測定区間でも、最後の出力とnonceが変化していないことを確認した。
これらの確認では、目標値を最大にして、目標値に達するまで探索を繰り返すループを防いでいる。

入力と、元の生成済みJavaScriptの一覧は、ハッシュとともに`glue-control-input.json`へ保存した。
独立した期待出力には、XMRig v6.18.0の`CryptoNight_test.h`を使った。
`original-glue-public-vector-check-corrected-20261008.json`には、
元の連携用JavaScriptによる出力の確認を修正した結果がある。
それ以前のホスト側ローダーの失敗は、問題の診断用の記録であり、データセットの出力が誤っていたことを示すものではない。

xmr-wasmの実験では、次の例と同じ隔離設定でコマンドを実行した。

```powershell
docker run --rm --network none --cpus 2 --memory 2g --pids-limit 128 --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --entrypoint node -e EXPERIMENT_IMAGE_ID=sha256:a05286e66b0f1ca712671db5849229594c92e035bae253362cc8b6d0af4a70b6 -v 'C:\Users\ettotto\Documents\webassembly_obfuscation:/work' wasm-hash-reference:local /work/experiments/runtime-reference/proof-xmr-benchmark.cjs /work /work/results/runtime-mining/cross-dataset/proof-of-theft/xmr-repeated-throughput-new.json
```

再実行する前に、スクリプトの出力先を確認し、完了済みの報告ファイルを退避する。
性能測定を同時に実行しない。既存の無関係なコンテナは停止していないため、
ホスト上の他の処理による負荷は測定の制約として残る。

集計と図の生成には、次のコマンドを使う。

```powershell
.tools/runtime-analysis-py312/Scripts/python.exe scripts/summarize_proof_xmr.py
.tools/runtime-analysis-py312/Scripts/python.exe scripts/summarize_proof_hash_experiment.py
```

`runtime-mechanism-audit.json`には、静的な特徴、ビルド時のフラグ、
限られた入力による出力照合、変換の仕組みを確認した根拠を対応付けている。
エクスポートされたハッシュ関数のラッパーでは、制御フロー平坦化を確認した。
また、確認した箇所では、値を変えない2つの命令置換も見つかった。
これらの置換箇所は、目標値を最大にしたCN/0ベンチマークで通る経路の外側にある。
いずれの確認も、すべての入力で同じ動作をすることを証明するものではない。ハッシュ計算本体の全関数を確認したわけでもない。

xmr-wasmでは、偽の制御フローを加えたファイルのMakefileだけに、`-O2`が明記されている。
その速度は測定したファイルの値として示せるが、難読化の効果を確定する根拠にはならない。
webminerpoolhashcnの5つのMakefileは、参照版のディレクトリも含め、
すべて同じ偽の制御フロー用フラグを指定している。
ディレクトリ名だけでは、4種類の異なる変換が行われたとは確認できない。
有効な測定値は、こうした解釈上の制約を添え、配布ファイル同士の比較として保持する。

完了したwebminerpoolhashcnの予備測定は、
`hash-throughput-preliminary-20261007-retry.json`にある。5秒の測定を3回繰り返した。
`-retry`が付かない0バイトの報告ファイルは保存に失敗したものであり、使わない。
仮想化版とfsplitflatten版は、アダプターと元の連携用JavaScriptの両方で失敗した。
cryptonight-hashの配布ファイルに必要なエクスポートがない場合は、実行できる範囲の制約として扱う。
ハッシュ結果の不一致ではない。

この記録時点のLaTeXソースは`paper/main.tex`である。組み込みコンパイラは
`Unable to find standard directories for platform`を報告しており、
コンパイル、出力したPDFのページ数、レイアウトは未確認である。代替のPDFも作成していない。
