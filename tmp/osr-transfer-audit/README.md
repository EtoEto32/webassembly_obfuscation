# 非同時点の状態移送案：先行研究と過去候補との照合

2026-10-12。前回の作業はcontrol-analysis-auditを保存したためprogress。今回の作業は、異なる進捗の実装へ状態を移す案を調査した。新しいアルゴリズムの採用・実装成功を意味しない。

## 検討した規則

元の純粋な反復を s_(i+1)=F(s_i,u_i) とする。実装Aがs_iを保持し、実装Bが先行計算を含む状態zを保持する場合、境界移送Cを生成し、残りの入力列vについて次を要求する。

`finish_A(s_i, v) = finish_B(C(s_i), v)`

進捗の差がある場合は、入力を消費した個数も状態関係へ含める。移送後の入力列を適当にずらしてテストに合うようにしてはいけない。未来の入力を必要とするFは、その入力が利用可能になる前に評価できない。

単にz=F(s_i,u_i)を先に計算し、ループの入口・出口をずらす案は既存temporal-cut-gateと同じ機構になる。その記録には隣接観測から20,868状態を復元した結果がある。この件数は今回再実行した結果ではない。別の名称で再試作しない。

計算の配置を変えて失われた値を移送時に補う案も、OSRの補償コードと比較する必要がある。同じ変数を同じ値で渡さない、という説明だけでは新規性を確定できない。新しい移送規則と、解析に対する具体的な差が未確定なので、今回この案のWasmの生成は行わなかった。

## 一次資料と確認範囲

Daniele Cono D'Elia and Camil Demetrescu, *On-Stack Replacement, Distilled*, PLDI 2018, pp.166–180, DOI 10.1145/3192366.3192396。

取得成功した著者研究室の本文：
https://season-lab.github.io/papers/osr-distilled-pldi18.pdf

確認範囲：要旨・導入、§2.1の意味定義、§4.1のlive-variable equivalenceとFig.5、§5.3のメモリ処理。すべての証明・全アルゴリズム・著者実装の検証は行っていない。共通の生存値を使う状態の対応、コード移動を含む変換、メモリ処理の前提が比較点になる。本文は任意の意味保存変換すべてへの汎用解を主張するものとは扱わない。

最初に試した https://www.diag.uniroma1.it/~delia/papers/pldi18.pdf は、webでtimeout、PowerShellのInvoke-WebRequestで接続切断となった。後者のプロセスはexit 1で終了し、ローカルPDFは生成されなかった。別ミラーの本文をwebで読めたため、資料未取得を作業を継続できない障害にはしない。

## Wasmへ転用する際の注意点：こちらの分析

論文§2の意味関数は、最終outへ到達しない実行をundefinedとする。この定義から、Wasmでtrapした後に呼出し元が観測できるmemory・globalやtrap種類の一致は導けない。これは論文の誤りではなく、今回の観測モデルとの差である。

§5.3の実装上の十分条件と、そこで議論される拡張案も分けて読む。将来の候補でstoreを境界の反対側へ移すなら、正常終了の戻り値だけでなく、失敗時点までの外部観測を検証する。対応していない場合は純粋演算だけに適用条件を限定するが、その限定だけをWasm固有の新規アルゴリズムとして数えない。

## 今回の判断と次の作業

- 「進捗の異なる変種へ切り替える」という概念だけの案は採用しない。
- 今回は既存方式との差がなくても動く実装を増やす段階へ進めず、具体的な規則が未確定であることを残す。
- 次に検討する候補は、temporal-cut-gate、encoding-cosynthesis、control-analysis-auditの既存規則へ還元できない差を先に式で示す必要がある。
- 新規性と有効性が確認されたアルゴリズムは依然として未完成。これは追加測定へ研究目的を変更する根拠にはしない。

追加の検索手掛かり：Yusuf, El-Mahdy, Rohou, *On-Stack Replacement to Improve JIT-based Obfuscation: A Preliminary Study*。検索結果と大学公開PDFの存在まで確認し、本文は未読。https://feng.stafpu.bu.edu.eg/Electrical%20Engineering/836/publications/Marwa%20Yusuf%20Abdelraouf%20Mohammed_2.pdf 。今回はその具体的方式に基づく判断をしていない。

検索語：on stack replacement obfuscation state reconstruction loop iteration different program points compensation / obfuscation stuttering simulation state transition program transformation / On-Stack Replacement Distilled pdf arxiv。

この記録は独立研究の作業資料である。CSEC原稿や既存実験は変更していない。コード・性能結果を作成したと報告しない。
