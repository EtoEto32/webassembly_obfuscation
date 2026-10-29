# この区間の到達点

2026-10-22。実Wasmの逆向き受理vector・ANF混合・binaryのみの回復器を実装し、実験と監査を完了した。独立した主発明は未達。元の有限環構成候補の評価を取り消してはいない。

- 主reverse-observer-v1：48条件、正42/unique正24、182,532呼出し、840trap、bad6反例、回復18/18 byte一致。99pins。
- 性能reverse-observer-performance-v1：27process/189batch、短batch0。混合/plain比1.165/3.975/11.288。59pins。結果はruntime.jsonに保存済み、待機対象なし。
- 監査reverse-observer-audit-v1：主99/性能59pins検証、48本byte再現、helper7,488、WABT336/42trap、拒否9、回復反復60。409pins。プロセス84936はexit0確認済み。
- BonchiほかTOCL2014 §3–4の反転構成が核に対応する。出力観測の閉包はEによらず最大n。この案はsuffix-transport方向とも近く、独立した新発明として加算しない。

今後の条件：単なる非線形符号化や明示的decoderの削除では、この閉包は変わらない。gate数・seed・状態幅だけを変えた案を別原理の候補として再開しない。全入力の形式検証や実用性能の確立は主張しない。
