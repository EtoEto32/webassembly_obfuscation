# SIMD演算幅をまたぐ配置変換の基礎検証

2026-10-12。状態: **実行可能な基礎部品。新規な難読化アルゴリズムとして未採用**。

ユーザーの目的は新しい難読化アルゴリズムの研究開発。既存方式の追加測定、名前変更、Wasm移植だけを完成としない。このフォルダは候補を設計するための基礎検証であり、目標達成の報告ではない。CSEC原稿は変更しない。

## 具体的な処理と規則

通常処理は16個の入力バイトを隣接2個ずつ加算し、8個の16ビット値それぞれを `s*s+37 mod 65536` へ変換し、さらに隣接2個ずつ符号なし拡張加算して4個の32ビット値を返す。全レーンが結果に寄与する、小さな通常の整数計算。マイニングやマルウェアは含まない。

通常版も同じ5個のi32引数と4個のi32戻り値を持つ。最初の4引数をlittle-endianで16バイトに分解し、第5引数uは配置選択専用で通常版の出力には影響しない。

`k=u&15, h=(u>>4)&7, t=(u>>7)&3` とし、バイト位置jを `j XOR d` にするswizzleを S_d とする。

- 入口: S_k
- 最初の拡張加算直前: S_(k XOR 2h)
- 非線形演算後、次の拡張加算直前: S_(2h XOR 4t)
- 出口: S_(4t)

これにより内部の16ビットレーンはj XOR h、32ビットレーンはj XOR tの配置となる。通常配置へ戻して再配置する自作対照roundtripはswizzle6個、直接接続transportは4個。比較先は著者の難読化ツール実行結果ではない。

意味保存の説明: S_a S_b = S_(a XOR b)。2hはバイト対内部の位置を変更せず、対の番号だけをhで並べ替える。拡張加算はその対の順序に従って出力し、同一のレーン演算はレーン置換と交換する。次の段階にも同じ議論が成り立つ。全swizzle indexは0..15、範囲外によるゼロ化は起こらない。これは対象処理の代数的説明であり、Wasmバイナリ全体を証明支援系で証明したものではない。

## 実装・検証結果

generate.pyはこの処理の専用WAT生成器。既存の任意Wasmを変換するパスではない。メモリ、import、ループ、trap、浮動小数点、一般のレーン置換、分岐合流には未対応。

verify.cjsは独立したスカラー参照計算を使用。512通りの配置それぞれについて境界・識別パターン5個と乱数1個、さらに32ビットuを含む乱数1024個。4,096入力/バイナリ、3形式×raw/O2の6本で24,576比較、出力不一致0。これは全128ビット入力の全数検証ではない。seed=0x4a821d39。inputs.jsonとresults.jsonに保存。

| 形式 | raw bytes | O2 bytes |
|---|---:|---:|
| normal | 179 | 134 |
| roundtrip | 371 | 325 |
| transport | 317 | 279 |

Node24.15.0、V8 13.6.233.17-node.48。コンパイラ版・コマンド・バイナリSHA-256はmanifest.json。高速化や解析耐性の測定はしていない。小さいコードサイズを強度の証拠にしない。

再現（PowerShell、独立リポジトリのこのディレクトリで）:

```powershell
& 'C:\Users\ettotto\Documents\webassembly_obfuscation\.tools\runtime-analysis-py312\Scripts\python.exe' .\generate.py 'C:\Users\ettotto\Documents\webassembly_obfuscation\.tools'
& 'C:\Program Files\nodejs\node.exe' .\verify.cjs
```

## 新規性・効果の判断

このXOR配置規則は置換の合成・打消しで説明でき、**これだけでは新しい難読化アルゴリズムという主張を支持しない**。選択値とswizzleを追跡できる解析者は各段階のレーン対応を復元できる。新しい復元困難性を実証していない。SIMDに未対応の解析器の失敗を効果に数えない。

したがって、この部品単独は採用しない。ただし「すべてのSIMD変換に新規性がない」「一般の動的配置はすべて無効」とする根拠でもない。次に必要なのは、単純な置換伝播で消せない具体的な変換規則と、それを最も近い既存方式との差として説明できる証拠。レーン数、配置数、乱数シードの変更だけでは次候補としない。

## 確認した先行実装

Ensia、公開リポジトリmainを2026-10-12取得、commit `cc79e0fa23d0ca2c0c0caba8a639cb1e62041152`。

https://github.com/Apich-Organization/ensia/blob/cc79e0fa23d0ca2c0c0caba8a639cb1e62041152/obfuscation/VectorObfuscation.cpp

確認範囲はVectorObfuscation.cppのbuildNoiseVector、tryGetChainedVector、applyShuffleNoise、liftBinOpToVector、liftCastToVector等。スカラーの実レーンとノイズレーンを構成し、shuffle後の実レーンを追跡する。前のベクトルからの連鎖処理もある。従って「演算間でベクトルを維持する」だけも差分にならない。ツール全体の実行・性能・保護効果は未検証。READMEの強度主張を実証済みの事実として引用しない。

参照用に取得したcpp/h/LICENSEはprior-art/ensia/に無変更で保存。AGPL-3.0-or-later。今回のPython/JSはこのC++実装を移植したものではなく、上記の限定した配置則を別実装したもの。

Wasm仕様のVector InstructionsとNumericsも参照:
https://webassembly.github.io/spec/core/exec/instructions.html#vector-instructions
https://webassembly.github.io/spec/core/exec/numerics.html

## 検索記録と未確認点

検索日2026-10-12: WAMO WebAssembly obfuscation / WebAssembly obfuscation 2026 algorithm / obfuscation recursive types WebAssembly / obfuscation carry-save / obfuscation redundant signed digit / SIMD code obfuscation lane permutation shuffle transformation / obfuscation vectorization / obfuscation SIMD / obfuscation lane shuffle。

WAMOは今回も本文未取得。著者Hao Hanのページ https://hhannuaa.gitlab.io/ を確認したが、取得したページではWAMOの論文リンクを発見できなかった。不在や非重複の証明ではない。探索過程の検索ヒットをすべて技術的根拠にはしていない。

研究目標の達成に向けて作業を継続中。採用された新規アルゴリズムはまだない。利用枠は今回取得時21%使用/79%残。ユーザーの最新の停止条件は残量25%。
