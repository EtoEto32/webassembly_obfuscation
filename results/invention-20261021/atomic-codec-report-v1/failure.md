# 集計v1の中断

2026-10-21。report.pyのplatform.platform()がsocket→selectors→selectをimportする際、同じディレクトリのselect.pyが標準moduleを隠した。select.pyがreportのargvを使用し、既存runtime出力へのmkdirを試みてFileExistsErrorで停止した。既存出力の上書きを拒否したため実験データ変更はない。

この出力には途中のreport.jsonのみあり、完成した環境・比較表・pinsはない。failed-source-*はその時点のsource。choose_codec.pyへ改名してreport-v2で再集計する。実験や攻撃の成功/失敗件数へ加算しない。
