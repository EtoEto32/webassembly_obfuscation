# 観測位置の引戻しと範囲式からの回復

## 意味保存

コピー前のmemoryをM、コピー後をM'、コピー引数を(d,s,l)とすると、範囲内のqについて

`M'[q] = M[s+q-d] (d <= q < d+l), otherwise M[q]`。

コピー元は常にそのcopyの直前の版である。この等式は重なった範囲にも成り立つ。複数copyについて逆順に位置qを置き換えれば、最後の1byte観測を初期memoryの1byte観測にできる。更新値の全域に対する可逆符号化は使わない。各copyは値を消し得るが、観測の出自は確定する。

Wasmでは、観測から使われないcopyが範囲外でもtrapし、長さ0でも範囲検査が先行する。各d+l,s+lをunsigned i64へ拡張して計算し、65536を超えればtrapする。unsigned i32で加算してから比較してはいけない。元のqについても引戻しの前に範囲検査する。これで全copyが正常なら返却byteが等しく、不正なcopyかqueryがあれば両方trapする。

本profileではmemoryはprivate、固定1page、importなし、run以外のexportなし。原版は各呼出しの冒頭に初期状態へresetする。したがってtrap前に原版で一部copyが済んでいても、そのmemoryは外部へ観測されず、次のcallもresetする。変換後の物理memoryが原版の途中の物理memoryと同じ、という主張はしない。共有、export memory、外部call、途中の観測、persistent stateへはこの論証を適用しない。trapメッセージの文字列や時間は比較対象外。

## 限定変換器

```text
validate input Wasm
extract initial data and ordered memory.copy argument triples
check full module matches the allowed source profile
replace scratch initialization and copy updates by full range checks
for each copy in reverse order:
    if unsigned(q-d) < length: q = source + (q-d)
load one byte at q from the immutable initial data
validate output Wasm
```

コピー引数は関数パラメータの任意の並び替え。変換対象は2/4/8段を実測し、CLIは1..16段を許す。初期非ゼロdataは4096byte、memory残りはゼロ。dataの秘密性は保護目標ではない。一般Wasmの任意memory命令を処理する実装ではない。

## 方式既知の回復

解析器は配布binaryをWABTで読み、operand stackとlocal変数を記号実行する。local.teeで上書きされる前にstackへ置かれた値も保持する。範囲比較 `q-d < l` と、真側の `s+(q-d)`、偽側のqという組から、d,s,lを抽出する。これを逆順に戻してnative memory.copy列を出力する。

コピー引数の対応、元のdata、生成seedを外部から渡さない。初期dataは配布binary自身から読む。回復したplanで変換後profileを再生成し、rawまたは同じO3結果との完全AST一致を要求する。未知のコードをこの形に勝手に解釈することはしない。

O3で消えた命令や関数名を当てる必要はない。効果の履歴が読み出し位置の条件式に移っただけなので、その式を直接読むと元の更新列になる。実測12条件で回復Wasmは元rawとbyte一致した。解析器の初版がimplicit stack operandsに未対応だった1条件は、攻撃失敗ではなく実装不足として修正した。

## 採否

単一出力へ必要な計算を集めるため、この例では高速化が起こる。しかしlazy copyとread forwardingの先行性があり、範囲検査の保存だけで独立した発明と判断できない。更新履歴の構造も容易に戻る。難読化としては早期不採用。主張できるのは、この限定条件での意味保存、既知技法による性能効果、回復の具体的実測である。
