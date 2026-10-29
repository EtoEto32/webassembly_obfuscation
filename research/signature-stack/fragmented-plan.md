# Pの最悪ケース反証（実行前）

区間版に残る反例：型列Vを前半A・後半Bに分け、`call makeA; call makeB; call sinkV`を反復する。A/Bを合わせるとVと同じ型列だが、別のintern ID・別chunkである。現在の区間版はVとの照合時に全要素へ戻る。短いcall列の反復だけで、型幅W×反復Rに比例する照合が残るはずである。

W=8/64/512、R=1024で、同じ4比較器・11batch sample・3processを測る。これはPの「どんな短いbinaryでも検証費用を幅から切り離せる」という強い解釈の反証である。もともとの限定仮説である「同一signature sliceの再利用が速い」は直ちに否定しない。

他の型vectorや部分slice間の一致をmemoizeすれば回避できる可能性はあるが、その場合は既知のrange equality cachingとの差と、tableサイズ・初回比較・GC subtypeの費用を再評価する必要がある。今回の成功として先取りしない。
