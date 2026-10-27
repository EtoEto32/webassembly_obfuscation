# 位置依存表現のコピー後補正：検査計画

2026-10-21、実装・測定前。前turnはsaturation-anchorの正当性、適応解析、性能と先行性を追加し、進捗あり。新しい検査は表引き零割当とは別のメモリ更新原理。ただし既存のコピー・再符号化と近く、独創的新案として数える判断は未了。

問題：private memoryの値を位置依存のE_a(v)=P(v) XOR K(a)で表すと、通常のmemory.copyは不正になる。素朴な復号→再符号化と、融合した補正を比較する。Kは公開の周期16byte mask、Pは上下nibbleの置換。秘密鍵や暗号安全性は仮定しない。

仮説：memory.copy(d,s,n)後、移動先各byteをK(s+i) XOR K(d+i)で補正すれば、Pの復号を一切行わず正しい表現に戻る。Wasmのcopyは範囲検査後に全copyを行い、重なりも正しく扱う。補正は移動先だけを読むため順序を固定できる。private/nonshared、追加trapしない補正が条件。scalar/128bit SIMD双方を作る。

対照はplain、位置表現の復号再符号化による方向付きcopy、Pを代数的に相殺した方向付きscalar/SIMD、bulk後補正scalar/SIMD。SIMD化だけの利益を提案の利益と数えない。全方式は同じ位置表現、追加memoryなし。大きいcopyでは二重走査が不利と予想する。小さいcopyでは境界検査・方向判定の省略が有利かを調べる。

限定profileの完全一致だけではなく、任意の関数列・分岐・ループを持つbyteアクセス中心の入力Wasmを走査して変換する。ただし固定1/2page private memory、imports/grow/別幅load/store/共有memory/table等は拒否。複数小アプリfixtureとscalarの独立状態oracleでtrap後も全byteを比較する。任意C/C++対応を主張しない。

先行資料：US20140189366A1にはアドレス/添字由来maskによる配列難読化がある（検索の長文抽出で概要・説明を確認、直接open失敗、請求項未読）。MSR-TR-2008-120 Data Randomizationの§4.3/5/6.1を部分確認し、位置に合うmask選択とlibrary wrapperが既知。US11354420B2は位置依存/非依存の表現とcopyを組み合わせる（書誌確認、本文の指定部分をこれから照合）。これらの一般発想を発明と扱わない。差の候補はコピーのtrap/overlap契約を利用した一方向の事後補正だけ。

性能はコピー長16/256/4096、重なり方向2種と非重複、5 fresh process、Wasm内loop、warmup10,000、9batch×10,000回で比較。最適化後も確認し、NS単位はcopy1回。復号状態の回復は方式既知の表・mask抽出で試し、復元可能性を隠さない。効率の利益がなければこの修復を発明の主核にしない。
