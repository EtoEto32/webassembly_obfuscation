# A第2設計の性能比較（実行前）

3方式: 旧Aの手書き依存＋手書き計画、旧Aの生成依存＋手書き計画、新Aの生成計画＋opcode由来依存。全方式で同じ同期file executorを使い、同じ順序のread/writeを発生させる。全方式が正しく認可する対照である。文字列→byte変換の差を新Aの効果として混ぜない。

同じ最適化済みComponent、2実体、read/write/copy/batch8/optional1/idle。各方式5 fresh process、seed固定の実行順、30 warmup、50回×9batch。setup→prepare→JS継続→admit→実I/O→releaseの時間を測る。FDは事前に開き、case初期化は計時外。OS page cacheを無効にせず、cold diskやfsync耐久性の性能と呼ばない。process中央値、IQR、手書き対照に対する対応repの時間比を保存する。

別の非計時36失効条件で不要拒否・不正受付を検査し、同じ条件の5反復を新規ケースとして合算しない。通常のI/Oに対するpure sandbox費用の測定ではない。既存Aと新Aの生成・計画費用を比較する。
