# 並行実行・データ化に関する照合（確認日2026-10-19）

| 資料 | 読んだ範囲と内容 | 今回との関係・限界 |
|---|---|---|
| Rasha Salah Omar, Ahmed El-Mahdy, Erven Rohou, **Thread-Based Obfuscation through Control-Flow Mangling**, 2013, arXiv:1311.0044（プレプリント）[本文](https://arxiv.org/pdf/1311.0044)、DOI 10.48550/arXiv.1311.0044 | abstract、§2–4、結論を確認。基本blockをthreadへ配り、guardで元の順序を保存。LLVM/Pthreads実装。§4は共有変数の書込みと待ちから順序を再構成できる点を述べる。費用は§4.2の1〜2桁と結論の10〜20倍で表現が異なるため単一の精密値として使わない。 | 今回は純粋演算の複数同時実行を許すが、同期で依存を保存するという原理は近い。thread数の組合せを解析コストと同一視しない。査読済み別版は確認していない。 |
| Dmitriy Dunaev, László Lengyel, **Method of Software Obfuscation Using Petri Nets**, CECIIS 2013, pp.242–246 [公式本文](https://archive.ceciis.foi.hr/public/conferences/1/papers2013/647.pdf) | abstract、§2のmanager・context保存・thread起動、§3を確認。Petri netでcode sectionを管理。タイミングと同期、遅延が未解決事項として残る。 | 公式会議録の論文。査読手続は今回未確認。定量的な適応的回復評価は読んだ範囲にない。今回のfair DAG schedulerはタイミング検出を使わないが、thread分割という大枠を新規とはいえない。 |
| Robert Durand, Andrew Hoyt, **Systems, methods, and storage media for obfuscating a computer program by representing the control flow of the computer program as data**, US11403372B2 [公報](https://patents.google.com/patent/US11403372B2/en) | 優先日2019-01-29、A1公開2020-07-30、B2公開2022-08-02。descriptionのモデル・行列・runtimeと請求項1〜21を確認。event/condition/execution、arc/token、データとしての保存、runtimeによる実行が記載される。 | source CFGをPetri netのモデルへ移す構成と、今回のbinary SSA DAGは同一ではないが、「コードの順序をデータにして解釈実行する」広い説明では差が弱い。EP3918494A1は本文取得失敗、検索抜粋とUS公報のfamily欄のみ確認。権利範囲・存続・侵害・登録可能性を判断したものではない。 |
| Johan Eker, Björn Johansson, Carl von Platen, **Obfuscating Computer Program Code**, US20100199354A1 [公報](https://patents.google.com/patent/US20100199354A1/en) | 書誌とdescription先頭のif-conversion、guard、制御をデータへ移す説明を確認。優先日2006-12-21、公開2010-08-05。 | 単純なatomic条件化の案に対する近接分野。請求項は今回未精査で、今回方式と同一と断定しない。 |
| WebAssembly Community Group, **Threading proposal for WebAssembly** [公式仕様案](https://raw.githubusercontent.com/WebAssembly/threads/main/proposals/threads/Overview.md) | thread生成はembedder、shared memory、active dataの再初期化、SC atomic、CAS、alignment、wait/notifyを確認。 | Wasm用の正当性条件の根拠。仕様機能を使ったことだけで新規な難読化原理にはならない。 |

今回の最大のReject理由は、既知のdataflow実行器・thread難読化に対し、worker数で増える回復費用を示せないこと。先行方式を再実装して直接比較したわけではない。同じ演算データと走査法を持つ逐次VM、通常Wasmを比較対象にし、並行化の増分を分離する。

独立した発明としての差分は未確立。WasmのSC atomic、1page共有memory、DAG順の回復という具体的構成を記録するが、これを特許請求項案へ格上げしない。
