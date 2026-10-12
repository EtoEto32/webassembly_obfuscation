# メモリ上の対応関係を変える候補：具体的な規則の事前照合

2026-10-12。前回の作業は多項式の逆変換比較器を実装し結果を保存したためprogress。今回の作業はメモリ表現の方向を調査した。新しい難読化アルゴリズムの採用報告ではない。

## 検討した規則と判断

### 1. 複製・集約によって論理値と物理位置を一対一にしない

同じ論理値を複数位置へ置き、読み出しごとに位置を変える。また、複数値のXORを一つの場所へ置き、既に持つ値から必要な値を取り出す。単なる固定アドレス置換とは異なるが、この規則だけならMemCloakに直接の比較先がある。Wasmに移しただけでは新方式にしない。

### 2. 辺の値で論理メモリを表す案

有向グラフの辺に値fを置き、各頂点の論理値を流入和と流出和の差として表す。接続行列Bで書けばx=Bfである。ある頂点iの値をδ増やすには、予備頂点0からiまでの経路の辺へ符号付きδを加える。内部頂点では増減が打ち消され、端点だけの論理値が変わる。閉路に沿った追加更新もBfを変えない。

しかし、このままでは既知の線形な冗長表現の具体例であり、グラフが分かる解析者はBfを計算できる。物理write数や経路の多様性が増えること自体は、新しい解析耐性の根拠にならない。今回この単純な規則をWasm実装へ進めない。これは自分で検討した規則への代数的な判断で、MemCloakの安全性を破った実験ではない。

グラフの対応を解析者が容易に同定できるかは別問題である。まだ同定器を実装していないという理由だけで強いと判断することも、すべてのグラフ表現が無効と断定することもしない。非線形演算を付け足すだけでは、独自の更新アルゴリズムになったとは言えない。

### 3. 値を複数要素へ分け、分割表現のまま演算する

「分割して直接ANDや乗算をする」という説明だけでは既存のvariable splitting・homomorphic encoding・RNCと区別できない。新しい具体的な規則と成立条件が必要。ASPIREの確認範囲から、この一般的な説明を新規性として採用しない。

## 一次資料

**MemCloak: Practical Access Obfuscation for Untrusted Memory**, Weixin Liang et al., ACSAC 2018, DOI 10.1145/3274694.3274695。
https://list.zju.edu.cn/kaibu/memcloak.pdf

確認範囲：要旨、§1、§2.1–2.3、Fig.1。複製とXOR集約、CPU/cache/controllerを信頼領域に置く観測条件を確認した。§3以降の全手順や著者実装は未検証。バスを観測する条件での主張を、全内部状態を観測できるWasm解析者への保護保証に読み替えない。

**ASPIRE D2.01: Early White-Box Cryptography and Data Obfuscation Report**, revision 1.01, actual submission 31 October 2014, editor Mariano Ceccato。
https://www.aspire-fp7.eu/sites/default/files/D2.01-ASPIRE-Early-White-Box-Cryptography-and-Data-Obfuscation-Report-v1.01.pdf

確認範囲：表紙、§2.1の符号化例、§2.1.2–2.1.3、§3.3、§4冒頭。分割したブール値に対する表による演算と、符号化領域での演算が比較先。64ページ全体を読んだわけではない。著者TXL実装や性能実験は再実行していない。

検索語：software obfuscation memory overlapping encoding / data obfuscation difference array encoding / obfuscation memory secret sharing / obfuscation Nielsen transformations / obfuscation graph gauge / data obfuscation graph encoding memory。検索で見つからない語があることを新規性の証拠にしていない。

## 過去の実験との関係

bulk-layout-wasmは固定XOR配置の復元を確認済み。trap-prefix-recoveryは限定したbuffered store方式で元store列を復元した。これらの限定的な結果は保持するが、すべてのメモリ表現の復元可能性へ一般化しない。

今回の調査は、固定配置のパラメータ変更、storeの単なる遅延、既知の線形共有を別名で再実装することを避ける判断に使う。候補採用には、元のload/storeや通常計算をどの具体的な命令へ写すのかを示し、公開memoryのABI、trap後の観測、動的な別名参照も扱う必要がある。

今回の作業で新たなWasmバイナリや実測結果は作成していない。独自の具体的な規則は未確定で、研究目標は未達。CSEC原稿と既存実験は変更していない。
