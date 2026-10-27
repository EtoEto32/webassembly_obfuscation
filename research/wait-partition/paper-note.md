# 日本語論文草稿追補：待機の観測集合と共有状態表現

## Abstract

Wasm共有状態のfield混合を、native waitの観測射影から制限する変換器を試作した。24条件50,088呼出し、393,216並行更新と待機・通知48条件を検査した。snapshotを使う素朴なwait翻訳の競合反例を再現した一方、適合表現も4回の選択書込みで同定できた。これは表現変更の適用条件と限界の実験であり、新規な強い保護方式の実証ではない。

## Introduction

値のread/writeを可逆にするだけでは、比較と待機を一体化した操作を保てない。Wasmのwait32/64は幅とアドレスで観測を定めるため、メモリ表現の生成がこの観測と両立する必要がある。

## Related Work

LLVMの部分word atomic lowering、Tigressの演算適合codec選択、Burckhardtのpacked wordsは既存の基盤である。[先行資料の読了範囲とURL](prior-art.md)を分けて保存した。一般のCAS展開や可逆shearを新規とはしない。

## Motivation

論理fieldが変化しても混合後の観測wordが変わらない場合、snapshotとwaitの間にnotifyが通過すると誤った待機が発生する。この問題は単一threadの値比較では見つからない。

## Threat Model

方式既知、公開binary、評価APIへの選択書込み、物理memoryの読出しを許す。目標は二fieldの論理値の回復費用。閉鎖された実アプリや型回復ツール一般への強度は主張しない。

## Proposed Method

πS E=eS πSかつeS全単射をnative待機比較の条件とする。各待機集合Sについてi∈S⇒j∈Sを満たす組のみ、可逆shearでfield jをiへ混ぜる。元のi32更新は64bit CAS loopへ、wait64期待値は純粋な全word符号化へ変換し、wait32のanchorとnotifyのアドレスを保つ。論証と擬似コードは[algorithm.md](algorithm.md)に記録した。

## Implementation

Python、WABT、Binaryenを使う実binary CLI。固定1pageの共有memory、整数atomic操作、限定されたimportと状態を対象とする。64bitで有効アドレスを検査し、範囲／整列trapの前にmemoryを更新しない。全参加者を変換する契約が必要である。

## Evaluation

4footprint、3方式、2最適化条件を比較した。主試験の期待trap13,680件と792全memory照合も一致した。別WABTの逐次試験288件、24binaryの再生成、非対応入力の拒否も確認した。負のwait履歴はスケジュール用のprepare/commit分割で5回再現した。

非自明な自動混合版の単一thread実行費用は元版の約1.33～1.47倍、恒等CAS版の約1.09～1.19倍。36process、324batchで測定した。全24条件を4回のstoreで同定し、同定decoderで全memoryが一致した。主結果、環境、反復と限界は[README](README.md)と生JSONに示す。

## Discussion

待機を扱える変換範囲の拡大と、保護効果の拡大は別である。最適化で表現が残っても、公開APIと低費用decoderがあれば目標情報を回復できる。観測範囲に応じた表現生成という差分候補はあるが、既知技術からの独立性は確立していない。

## Limitations

4設定は同じ小さなfixtureで実アプリ群ではない。並行試験は有限の実行例で、全interleaving、実時間timeout、公平性を検証していない。CASは個別threadの進行保証を弱め得る。解析は4codecの有限族に適応したもので、完全なbinary同値判定ではない。先行特許を網羅した評価でもない。

## Conclusion

native待機の比較を保つ生成条件と、素朴な翻訳の具体的反例を得た。一方、試作の追加保護効果を支持する実験結果は得られず、主発明には採用しない。
