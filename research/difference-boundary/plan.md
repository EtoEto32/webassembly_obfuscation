# 差分表現のbulk copyと境界補正：実験前計画

2026-10-19。前回hurwitz-supportの実装・反証・監査はprogress。今回の候補は置換の積ではなく、私有byte配列の永続的な表現と、重複コピーの更新則を変える。新規性は未確立。

## 選別した方向

1. 入力依存でmemory位置を動かす案：EP2831797B1のM-register、既存bulk-layout試作との重複が大きく、新しい規則を定義できないので見送る。
2. GCの型階層によるdispatch：既知の型変換と近く、今回の単純な構成では公開subtype関係を読むだけでよい。実装せず、新案数へ加算しない。
3. 差分配列のbulk操作を境界で修復する案：以下の具体的な規則を試す。差分符号化・prefix scan自体を発明とはしない。

## 固定する規則と仮説

N byteの私有状態AをD[i]=A[i] XOR A[i-1] (A[-1]=0)で保持する。元のcopy(d,s,n)は範囲をi64で検査してからmemory.copyする。n>0のコピー後に必要な修復はD[d]と、d+n<NならD[d+n]だけ。コピー前のDから、c0=XOR D[min(d,s)..max(d,s))、c1=XOR D[min(d,s)+n..max(d,s)+n)を求める。D自身をmemmoveしてから境界へc0/c1をXORする。補正はコピー前に計算する。

二つの区間が重なる場合、左端・共通部分・右端に分け、共通部分のXORを一度だけ計算する。読取り量は2*abs(d-s)からabs(d-s)+nへ減る。末尾の補正が不要ならc1を計算しない。距離0と長さ0は別途処理する。

H1：この規則は範囲内・重複・同一範囲・0長・範囲外trapとtrap後の状態を保存する。
H2：全配列を復号→copy→再符号化する対照より更新費用を下げられる。重複区間共有の効果を二つの区間を別々に読む版と比較する。
H3：元データと元更新則の回復費用が、独立byte XORとの比較で増すか。累積XORによる適応的回復を最初から実装する。回復可能性だけで棄却せず、実行費用・一件当たり解析費用を比較する。

## 実装範囲・観測・対照

固定1page、私有非共有memory32、既知のcopyとFNV型digestの2exportを持つ限定moduleを、実.wasmから読んで変換する。任意の一般Wasmパスとは呼ばない。初期dataはN byte、1<=N<=65536。copyはi32三引数、結果なし。digestは全論理byteを順にhashする。元memoryは外部へ公開しない。テスト用にのみmemory exportを追加し、復号した全pageと公開digestを照合する。

plain、固定byte XOR、delta-roundtrip、delta-two、delta-sharedのraw/O3。3配列長、異なるデータ、境界と固定seed乱数、同じinstanceの連続更新。単発の初期状態だけでなく履歴を検査。WABT interpreterによる別エンジン、誤った補正順・補正省略・wrap境界の負の対照も対象。

解析者は全binary・方式・初期memory・I/Oを知る。元データ・元binary・manifest・seedは回復器に渡さない。公開profileの命令列を照合した上でdataの累積XORと元copy/digestへ置換する。profile未対応・クラッシュ・timeoutは保護効果に数えない。hash loopには復号値が現れるので、動的値観測も潜在的な弱点として記録する。

性能はcopyのみ、digestのみ、両者のworkloadを分ける。3 fresh process、warmup、11標本、同一Wasm内loop、サイズ・memory page/RSS・変換時間。解析のprefix計算とtool/照合の時間も分ける。実行時間比とPython解析時間比を直接割って強度とはしない。

差分表現の高速化に留まり保護優位性がなければ主案不採用。通常optimizerに残ることだけでは成功としない。一般のデータ符号化の先行性と、この境界規則そのものの先行性は区別する。外部公開・push・出願はしない。
