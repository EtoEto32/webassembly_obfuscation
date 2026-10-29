# メモリ効果候補の後継設計：近接方式の追加照合

## 結論

trap-prefix-fusion の採用判断は変更しない。以前の復元器が補助関数の署名と引数へ依存することは確認できたが、補助関数のインライン化だけを新しい方式にはしない。前回の原結果とコードは変更していない。

## 新しく確認した一次資料

Zhou et al., **Polaris: MIR-Level Obfuscation in LLVM for Efficient and Robust Decompiler Resistance**, ICSE-Companion 2026 (Demonstration), DOI 10.1145/3774748.3787619。

https://ttfish.cc/content/Papers/ICSE26-Polaris.pdf

本文§4.2–4.5を確認。コンパイラ情報を使う無害な命令、間接的なスタックアクセス、スタック基準の変更が含まれる。関数境界に関する機械語の仮定を崩す部分は、構造化されたWasmへそのまま移せるとは言えない。今回の最初のtrap以前の書き込み統合と同一方式だという証拠ではない。本文の説明を読むことと、意味保存・性能を独立に検証することも区別する。著者実験は再現していない。

著者コード https://github.com/za233/Polaris-Obfuscator の固定コミット:

    1e066e69652be6c93885823b8cbbabdba8a16c73

`src/llvm/lib/Transforms/Obfuscation/AliasAccess.cpp` 全体を確認。局所変数を構造体へ配置し、参照グラフとgetterを通じたアクセスへ変える。これはIRのAliasAccessであり、論文§4のMIR手法全体とのコード対応を確認したとは言わない。X86AsmPrinter.cpp/X86MCInstLower.cppは検索したが、目的のバックエンド変換を同定できなかった。未発見をコード不在の根拠にしない。ビルド・実行は未実施。

GitHubの最初の全体tree応答はtruncated=trueだった。libサブツリーを別取得した応答はtruncated=false。取得した3コードのGit blob SHAはこの固定サブツリーと照合する。最初の省略された一覧から実装の有無を結論付けない。

## 後継案の比較（今回の設計判断）

| 案 | 変えるもの | 足りない点 | 判断 |
|---|---|---|---|
| forwardingのインライン化 | 補助関数呼出しを式へ展開 | 同じアドレス・値・有効性のデータ依存が残る。古い復元器が止まるだけでは効果を示せない | 単独案を採用しない |
| アドレスを参照グラフで表現 | 局所値へのアクセス経路 | 直接近いIR実装を確認した。追加の転送規則なしでは新しい原理とできない | 単独案を採用しない |
| ログを持たず各最終byteの式を生成 | 逐次ログからmemoryの関数表現へ変更 | 単なる式展開では元の値を式の構文木に埋め直すだけ。既存memory SSA・store最適化との差、式の膨張、trap境界の保存が未解決 | まだ具体候補として採用しない |

三番目については、元storeの各byteを、後続storeのアドレス一致条件に従い優先選択するだけなら旧候補のcommit式と同じである。この式を別名にしたりインライン化したりするだけでは再試作しない。新しい更新表現を設計できた場合に、改めて採用するかを判断する。

## 今回行っていないこと

新規Wasmの生成、復元器の再実行、性能比較、新しい算法の採用は行っていない。得られた進捗は、これまで未照合だった2026年の近接一次資料と固定コードによって、後継案のうち参照グラフだけの変更を除外できたことである。新規性のある方式の開発という目標は未達成のまま。

検索語: compiler store coalescing precise exceptions / store sinking exceptions compiler / obfuscation memory SSA / Polaris MIR-Level Obfuscation github。

CSEC用の原稿・既存実験は変更していない。研究全体の目標の停止目安は、ユーザーが後から指定した利用枠残量25%を優先する。今回の照会時点の残量は65%であり、停止条件には達していない。
