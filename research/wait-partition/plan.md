# native waitの観測範囲から混合可能性を決める検査

2026-10-22。未検証の設計仮説を実装前に固定する。

課題は共有memoryの二つのi32を混ぜても、memory.atomic.wait32/wait64とnotifyの値比較・待機queueを保てるかである。atomic-codecの単一cell・wait非対応から対象を変える。ただしCASへの展開、可逆shear、演算に応じたcodec選択自体は既知であり、新規とは数えない。

仮説：waitの観測集合Sごとに πS E(x)=eS(πS x) となる全単射eSがあれば、同じ幅・同じアドレスのnative waitを使い、期待値を純粋計算で変換できる。観測集合から、各可逆shearが混ぜてよいフィールドを機械的に選ぶ。全てのSについて i∈S⇒j∈S なら x_i ^= f(x_j) を許可する。二fieldのwait32両側が必要ならcross-field shearは許せない。

対象：固定1pageの共有memory32、全参加者を変換、i32 atomic load/store/RMW、wait32/64、notify。ホストは開始前の符号化初期化と検証のみ。完了した操作の値と副作用を比較し、CASのstarvation、実時間timeoutの一致、実行資源枯渇は保証しない。

対照は元のnative32操作と、恒等表現で同じ64bit CASを使う版。アブレーションはwait footprintによるlow/high/both/wide。危険なsnapshot後のwait翻訳について、失われた通知を作る実行履歴を実Wasmで再現する。

採用の条件は、(1)値・trap・並行更新・wait/notifyを保つ、(2)費用が実測可能、(3)方式既知の解析者に対する追加の回復費用がある、(4)既存のデータ符号化とatomic loweringからの独立した差が説明できること。正当性だけを新規の強い難読化の成功としない。低コストで表現を同定できるなら、その具体的な失敗理由を記録し主発明には採用しない。
