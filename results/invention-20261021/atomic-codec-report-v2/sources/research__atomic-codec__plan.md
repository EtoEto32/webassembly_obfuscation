# アトミック命令と両立する表現の生成：事前計画

2026-10-21。前turnは既存成果の説明・整合確認で、新候補の研究としてはno progress。ここから別の候補を検査する。有限環残差方式の限定採用は変更しない。

仮説：Wasmの共有memoryの命令集合から、再試行・追加共有状態なしで各更新を一つのatomicへ写せる符号化を選べば、通常の復号・更新・再符号化より安いデータ保護が得られるか。前のconcurrent-frontierは純粋なDAGの並列実行であり、本案は既に並行利用される共有セルの表現変換である。

選択規則は演算集合の共役条件を解く。全32bitの加算をnative add/subへ写すなら E(x)=a*x+b (a odd)。ANDもnative AND/ORのいずれか一命令へ写す場合、許される全単射は恒等と全bit反転だけ、という制限をまず証明・小幅列挙する。各更新のoperand変換は更新前の共有値を読めず、選択したtarget opcodeは固定である。CAS loopや複数cell、入力依存opcode選択まで排除する定理ではない。

実装対象は一つの固定1page共有memory import、i32 atomic load/store/add/sub/and/or/xor/xchg/cmpxchgと通常の整数制御。非atomic memory、混合アクセス幅、growth、data初期化、wait/notify、table、import関数、export memoryを拒否する。全参加者を変換し、hostがworker起動前に初期memoryを一度符号化する。生のmemoryを従来表現のまま読む任意hostとの文脈同値性ではない。

比較はplain、反転native、反転CAS、affine CAS、加減算profileだけのaffine native。誤AND置換と非原子的load/storeの負例を用意する。符号化形式は公知で秘密鍵を置かない。

評価を先に固定する：

- raw/O3の値・全memory・unaligned/OOB trapを差分検査する。即値offsetはi32加算へ変えない。
- 実workerのfetch-add返値が連番の置換になることと、短い混合操作履歴に逐次一貫な順序が存在することを検査する。
- バイナリと公開storeだけから2問い合わせでaffine係数を抽出し、memoryを回復できるか試す。成功を隠さない。
- 同じ符号化のnative/CASを比較して実行時間、サイズ、線形memory、process RSS、変換時間を記録する。
- 正当性、回復費用、性能、新規性を別判定する。既知の符号化・De Morgan則・CAS一般更新だけなら新原理と数えない。

CAS版は完了した操作のlinearizationを保存する比較対象であり、競合下での個別threadの有限時間終了を保証しない。native版もwall-clock実時間の上限を保証するものではない。
