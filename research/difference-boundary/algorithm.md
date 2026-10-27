# 差分メモリ上の重複copy

## 意味と対象

論理配列AのN byteを、D[i]=A[i] XOR A[i-1]、A[-1]=0で表す。Nは1–65536、memory32は非共有・非公開の1page固定。公開APIはcopy(d,s,n)とdigest()。copyの正常条件はunsigned i32引数をi64へ拡張したd+n<=Nかつs+n<=Nであり、0長でも条件を検査する。違反すれば状態を変えずtrapする。digestは順次byteについてh=(h XOR byte)*16777619 mod2^32、初期h=2166136261を返す。

変換器は実バイナリをvalidateして初期dataを読み、公開profileの関数・型・memory・export・命令列と厳密照合する。限定profileのrawまたはBinaryen133 O3を受け付ける。一般のload/store、他の関数、共有memory、hostアクセス、grow、import、memory64等へ自動適用するものではない。初期data segmentの最大末尾からNを推定し、関数中のNとprofile照合するため、最適化でdata末尾が消えるmodule等は拒否することがある。

## 更新規則

```
check unsigned(d)+unsigned(n) <= N and unsigned(s)+unsigned(n) <= N in i64
if n == 0 or d == s: return
lo = min(d,s); hi = max(d,s); L = hi-lo
if d+n == N:
    c0 = XOR D[lo:hi]
else if n < L and shared mode:
    left   = XOR D[lo:lo+n]
    middle = XOR D[lo+n:hi]
    right  = XOR D[hi:hi+n]
    c0 = left XOR middle
    c1 = middle XOR right
else:
    c0 = XOR D[lo:hi]
    c1 = XOR D[lo+n:hi+n]
memory.copy(D, d, s, n)
D[d] ^= c0
if d+n < N: D[d+n] ^= c1
```

区間は右端を含まない。補正値を必ずcopy前の状態から計算する。両補正が必要な場合、two版の読取り2Lに対しshared版はL+min(n,L)。copy自体のn byte転送費用は残る。右端補正不要ならL、同一範囲なら追加scanなし。Pythonモデルと実Wasmは独立した形でこの関係を検査した。

## 保存される理由

copy後のAをA'とする。内部d<j<d+nでは、D'[j]=A[s+j-d] XOR A[s+j-d-1]=D[s+j-d]。Wasmのmemory.copyは重複時にも元の区間をsnapshotした結果と等しいため、内部全体はDのbulk copyで正しくなる。

左端では必要な値はA[s] XOR A[d-1]だが、コピーされたD[s]はA[s] XOR A[s-1]。差はA[s-1] XOR A[d-1]であり、これはD[lo:hi]のXORへ望遠和として縮む。右端d+n<Nでは、古いD[d+n]をA[d+n] XOR A[s+n-1]へ変えるため、A[d+n-1] XOR A[s+n-1]、すなわちD[lo+n:hi+n]を加える。その他の位置は変わらない。

補正のscan範囲は、成功したbounds検査の後では0..Nに収まる。n>0のdはN未満であり、最後のstoreも条件付き。sourceと変換後の不変式D=ΔAが各正常呼出し後に保たれる。範囲外では変更前にtrapする。全配列の復号・再符号化版も、前置bounds検査があるからtrap時に途中の復号状態を残さない。

これは更新則の代数的な説明であり、parser・compiler・runtimeを含む実装全体の機械証明ではない。trapのPC、stack trace、実行時間、資源不足の同一性は契約に含めない。

## 比較と攻撃

plainは元のcopy、xorは各byte XOR167の既知対照でcopyと可換、roundtripは同じ差分表現を全復号してからcopy・再符号化、twoは境界2区間を別々に走査、sharedは共通区間を共有する。three delta modesは同じ初期dataと同じ呼出し後表現を持つ。違いは更新の計算方法だけである。

方式既知の攻撃は、公開profileへ合致することを確認した後、A[i]=XOR D[0:i+1]を1scanで求め、元copy/digestの標準実装へ置換する。元データ・元Wasm・seedは回復計算に渡さない。採点だけが元binaryを読む。初期版はprofile候補を順番に再構築したが、その試行順を耐性としない。indexed版は零初期dataの公開profileをNごとに10個生成してcode hashを索引化し、型・関数・memory・export・codeが一致したものを受け付ける。

dataとdata-countは索引対象から外す。active segmentのみ許可し、照合されたcodeにはmemory.init/data.dropがないため、初期memory適用後は個数が意味を変えない。実際のdataは別に読み、累積XORする。任意の改変Wasmをこのprofileへ無条件に同一視するものではない。profile外の等価変形への適用範囲は限定される。

復元の計算量はO(N)、必要な累積状態は8bit。前回とは異なる実行機構だが、ここでも小さい復元状態が残った。またdigestループの累積byteを計測すればAが現れるため、snapshotを隠す工夫だけでは解決しない。動的計測攻撃そのものは今回実装していない。
