'use strict';
const fs=require('node:fs'),path=require('node:path');
const out=path.join(__dirname,'artifacts'),load=n=>JSON.parse(fs.readFileSync(path.join(out,n)));
const summary=load('summary.json'),manifest=load('manifest.json'),erasure=load('erasure/results.json');
const lines=['# B2 GC型によるdispatcher状態表現：実験記録','',
'判定：この実装を新アルゴリズムとして採用しない。既存の状態符号化を型付きtokenへ写した方式であり、独立した難読化原理を示せない。今回の範囲では元ソースなしに型表現を整数表現へ変換でき、追加の保護効果を支持する証拠も得られなかった。', '',
'## 実施範囲','',
'2計算 × 5条件 × raw/O2 = 20本。整数mixerは積・回転・XOR・入力依存分岐を含む。GCD側は減算式の反復を最大63回まで実行して途中の両オペランドを返す。一般GCDの完了や実用ハッシュを測定したとは主張しない。任意Wasmの変換器ではなく専用WAT生成器である。', '',
'通常版、整数state固定、整数state回転、GC型固定、GC型回転を比較した。回転は反復ごとにeを0/3で切り替えるs XOR eで、型だけの効果と回転の効果を分離するため整数回転版も含めた。GC tokenはモジュール初期化時だけ生成し、ループ内では確保しない。', '',
'## 正しさと表現除去','',
'BigIntによる別実装と各4,608入力を比較し、20本で92,160件の不一致0。境界値512件と固定シード乱数4,096件を全条件で共用した。batch wrapperも20本で独立参照と照合した。これらは有限入力の確認であり、全入力の証明ではない。意味保存の不変条件はdesign.mdに記録した。', '',
'erase-gc.cjsはバイナリを逆アセンブルし、型・不変global・ref.testから整数tagへの表現変換を構築する。生成器、元WAT、manifest、期待結果は解析入力にしない。GC版8本すべてで変換でき、元バイナリとの36,864件の出力比較は不一致0。解析器構築は方式を知った状態で行った適応的解析であり、未知方式への盲検評価ではない。', '',
'この変換では静的に区別できる各token型Tに整数k(T)を与える。global取得をその定数へ、参照localを整数へ、型検査を整数比較へ置き換える。対象ではフィールド参照・書換え・参照の外部公開がなく、型だけが観測されるため、この対応が保たれる。回転状態は整数計算として残る。元ソースや元の構造化CFGまで復元した結果ではない。', '',
`解析と逆アセンブル・再アセンブルを含む時間は1本あたり${(Math.min(...erasure.results.map(r=>r.analysis_and_assembly_ns))/1e6).toFixed(2)}–${(Math.max(...erasure.results.map(r=>r.analysis_and_assembly_ns))/1e6).toFixed(2)} ms。各1回の処理時間であり、解析速度の比較実験とは扱わない。実行oracleへの問い合わせは変換構築時0回、正しさ確認時は別途実施した。`, '',
'## サイズ・実行時間','',
'Node 24.15.0 / V8 13.6.233.17-node.48 / Binaryen 133、Windows x64、Core i9-11900K。各条件20 × 65,536呼出しのウォームアップ後、7ラウンドを測定。各ラウンドで全条件を一度ずつランダム順に実行し、入力seedを共通化した。1観測はWasm内batchによる65,536回のrunを含む。表はbatchの時間を呼出し数で割った値で、runの反復回数は16–47。', '',
'時間比は各ラウンドの同じ計算・同じ最適化の通常版との比を取り、その中央値を示す。各条件の中央値同士の単純な割算ではない。初期化コストは除外し、単発のcompile+instantiate時間をcorrectness.jsonに別記した。', '',
'|条件|bytes|Binaryen IRノード数|時間中央値 ns/run|最小–最大|通常版との時間比|',
'|---|---:|---:|---:|---:|---:|'];
for(const s of summary){const f=manifest.files.find(f=>f.name===s.name),nodes=f.metrics.match(/\[total\]\s*:\s*(\d+)/)?.[1]??'未取得';lines.push(`|${s.name}|${s.bytes}|${nodes}|${s.median_ns.toFixed(2)}|${s.min_ns.toFixed(2)}–${s.max_ns.toFixed(2)}|${s.median_paired_ratio.toFixed(3)}|`);}
lines.push('',
'Binaryen IRノード数はバイナリ命令数そのものではない。whole-module集計にはhelperとbatchを含む。WABT 1.0.42のobjdumpはこのGC出力を扱えず、ref type/0xfbのエラーを返したため、部分的な逆アセンブル出力から命令数を数えていない。命令数の厳密な計測は未実施。', '',
`GC回転版のO2時間比はmixer約${summary.find(s=>s.name==='mix-gc-rotating-O2').median_paired_ratio.toFixed(2)}倍、GCD反復約${summary.find(s=>s.name==='gcd-gc-rotating-O2').median_paired_ratio.toFixed(2)}倍。各条件の大小関係は上表を参照。CPU/JITの具体的な原因は未分析で、全ランタイムへ一般化しない。`, '',
'## 測定上の修正・失敗','',
'最初の短いウォームアップ（3×4,096）ではGCD GC固定条件が約100–234 ns/runに分かれた。JITの段階変化が原因とは確定していない。初回のコードと全結果をevaluate-initial.cjsおよびartifacts/initial-timing/へ保存し、全条件のウォームアップを20×65,536へ揃えて再測定した。最終データだけを残して都合の悪い初回値を捨ててはいない。OS負荷やJIT状態を完全に制御した実験ではない。', '',
'表現除去器の初回実装はnullable参照のeqref省略記法を変換し忘れ、アセンブラでeqref != i32として拒否された。失敗WATをartifacts/erasure/failed-eqref-alias.watに保存し、修正後に8本を再生成・照合した。これは実装バグであり、候補の解析耐性ではない。', '',
'## 先行研究との比較・判断','',
'[O-MVLL公式文書](https://obfuscator.re/omvll/passes/control-flow-flattening/)のImplementation/Limitationsを2026-10-11に本文確認した。文書では状態変数の符号化を扱い、関数ごとの固定式 E(S)=(S XOR A)+B を説明する。本試作の反復ごとの変化やGC表現と全く同一とは言わない。O-MVLL著者実装は実行しておらず、性能表の整数条件は自作対照である。', '',
'前候補の監査にある領域別符号化・表現変更とも比較すると、B2の差は型tagによる状態表現と簡単なepoch切替である。今回、その表現は通常の整数比較へ除去できた。この差だけを新アルゴリズムの貢献として採用する根拠は不足している。一般的なGC難読化や動的参照解析が無効だという結論ではない。', '',
'## 次の判断と未完了','',
'B2を改名・シード変更して新方式として続けない。次は不変tokenの型置換ではなく、観測可能な状態関係に本質的な差を生む候補が必要である。ただし可変参照やaliasを加える場合も、既存のpointer-based opaque predicateや動的データ符号化と照合する。そこに固有の差がない場合はGC系から離れ、別の変換原理を検討する。', '',
'研究全体は未完了。有望な新方式、著者実装との比較、実用規模・複数ランタイムでの評価は残っている。本結果だけで目標達成とはしない。CSEC原稿・既存実験は変更していない。','');
fs.writeFileSync(path.join(__dirname,'REPORT.md'),lines.join('\n'));
console.log('REPORT.md generated from saved results');
