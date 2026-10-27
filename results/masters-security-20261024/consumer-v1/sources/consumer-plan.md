# Bのhost consumer比較（実行前固定）

2026-10-24。範囲解析はcompiler-v2の結果を固定し、新たな改修は加えない。

現行試験は復帰後にR全体をmaterializeしているため、保存量削減だけで速度改善を主張できない。次の4方式を、同じRust最適化2の8 fixture・同じ136入力系列・全8192byteのchecksum処理で比較する。

1. 全コピー：再入前にR全体を保存し、その保存bufferを読む。
2. 部分退避＋materialize：R∩Wを保存し、復帰後にR全体をコピーして保存値を埋め戻す。
3. 部分退避＋区間読取り：R∩Wを保存し、保存区間と変更されていない区間を順に読みchecksumを計算する。復帰後の全buffer生成を省く。
4. 手書きの区間読取り：fixture固有の最小書込み範囲を別コードで計算し、同じconsumerを用いる。条件付きstoreは実際に選択する枝の範囲だけを保存する。loopも既知の上界を手で指定するため、未対応解析器の不利も計上する。

第三者RLBox/SafeFetch実装との比較ではなく、その代用品と称さない。3/4は非共有memoryへ再びwriterを許可する前にconsumeを完了する。viewを任意の期間保持できるAPIではない。

各方式を新しいNode processで実行し、process順をseed付きでshuffleする。5反復、各fixtureのwarmup100呼出し、測定300呼出し×9 batch。checksum値は方式間で一致を検査し、測定外でも実行前のコピーをoracleとして照合する。中央値、IQR、process間の比を記録する。

保存payload byteと復帰後に新規確保するpayload byteを分けて記録する。JS objectの管理費は含まない。RSSはprocess全体の値であり、退避方式単独のpeakとはしない。今回の8KiB自作fixtureでの速度を、大規模実アプリケーションの性能へ外挿しない。
