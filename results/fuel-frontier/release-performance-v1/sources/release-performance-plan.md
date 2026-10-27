# 最適化後に残る公開payload例の性能計画

2026-10-24。release-v6の受理3構成（WAT/Rust2/Rust-s、全てO3+flatten）を使用する。同一の計算の異なる生成系であり独立した3アプリではない。

7方式（元コード、dynamic、late、whole、segment、frontier、手書きhost予約）×5fresh process。順序seed2026102409、warmup2,000、5,000 call×9反復。全方式をさらにO3し、元の論理費用scheduleは固定する。各入力の戻り値と公開payloadのchecksumが全方式で一致することを確認。手書き予約は独立interpreterで求めた2経路のprefix最大値を使う。

raw process値、反復値、中央値/IQR、heap/RSS、binary size、生成/normalization時間を記録。manual対照が速い場合はそのまま報告。追加のmeter cross-boundary callを省くhost shimへの融合は既知の実装最適化であり、それを新発明とは数えない。
