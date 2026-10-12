from pathlib import Path
import re
p=Path('paper/main.tex')
old=p.read_text(encoding='utf-8')
head=old[:old.index('\\begin{abstract}')]
def env(label,kind):
    for m in re.finditer(r'\\begin\{'+re.escape(kind)+r'\}.*?\\end\{'+re.escape(kind)+r'\}',old,re.S):
        if '\\label{'+label+'}' in m.group():return m.group()
    raise ValueError(label)
body=r'''\begin{abstract}
公開WebAssembly採掘データセットの難読化機構と，正しいハッシュ計算を行った際の性能・構造変化を対応付けて評価する．Cryptic Bytesの静的比較に加え，Proof-of-Theftの配布10標本，SWAMPED入力1標本と公開コードから生成した2変換版を出力照合と反復測定の対象とした．xmr-wasmの平坦化版は配布基準に対して命令数1.166倍，速度中央値比0.678であり，命令置換版との間で命令増加と速度低下の順位が一致しなかった．さらに，一部の変換箇所は測定したv0入力では通らず，全体の静的増加だけでは負荷を説明できない．SWAMPEDの同一組立条件の対では，nop挿入・整数定数分割の命令数比1.097・1.034に対して速度中央値比0.960・0.973で，反復内の速度差は方向が入れ替わった．配布設定・最適化の不一致や同一標本の再収録を区別し，公開標本の機構，測定経路，出力，速度を結び付けた評価の範囲と限界を示す．
\end{abstract}
\begin{eabstract}
We relate obfuscation mechanisms in public WebAssembly mining artifacts to validated hashing throughput and structural changes. In addition to static comparisons of Cryptic Bytes, we validate outputs and repeatedly measure ten Proof-of-Theft artifacts, one SWAMPED input, and two locally generated transformations. For xmr-wasm, the flattened artifact has an instruction-count ratio of 1.166 and a median throughput ratio of 0.678. Instruction growth and throughput loss rank differently for flattening and substitution; some transformed paths are skipped by the measured v0 inputs. Under identical assembly conditions, SWAMPED NOP insertion and integer constant splitting yield instruction-count ratios of 1.097 and 1.034 and throughput ratios of 0.960 and 0.973, with within-round differences changing direction. We distinguish build discrepancies, optimization differences, and artifact reuse from causal effects and independent replication. Findings are limited to the evaluated artifacts, inputs, and conditions.
\end{eabstract}
\maketitle

\section{はじめに}
WebAssembly（以下Wasm）はブラウザなどで実行されるバイナリ形式であり\cite{webassembly}，暗号資産の採掘にも用いられる．採掘機能と，利用者の同意なく資源を使うクリプトジャッキングは区別する．関連する公開データセットには，実際に収集した標本と研究者が変換した標本の両方がある\cite{konoth2018,harnes2024,kim2025}．難読化手法や検出への影響は既存研究で評価されているが，配布設定名だけでは実際の変換範囲や測定経路を確定できない．本稿は一般的な手法説明より，公開標本の機構と正しい計算の性能との関係に焦点を置く．
\begin{description}
\item[RQ1] 公開WebAssembly採掘データセットにはどのような難読化手法と実装上の仕組みが確認され，通常処理・研究用計測コードとどのように区別できるか．データセット・実装ごとにどのような傾向があるか．
\item[RQ2] 難読化はハッシュ出力の正しさ，計算速度，コード構造・命令数・ファイルサイズにどのような影響を与えるか．その傾向は複数の採掘実装で共通するか．
\end{description}
RQ1で機構・適用範囲・計測処理を確認した標本を，RQ2の出力と速度に対応付ける．追加評価は，静的増加と速度低下の順位の相違，測定入力が通らない変換箇所，同条件の自生成対における変動である．新しい難読化アルゴリズムや検出回避能力は評価しない．また，収録数やデータセット名の数を攻撃での普及率や独立した実装数と扱わない．

\section{関連研究と追加評価の位置付け}
Cryptic Bytesはソース・LLVM中間表現・Wasmの各段階の変換と検出を扱い，100秒のハッシュ速度も評価している\cite{harnes2024}．WebAssembly diversification for malware evasionも通常版6・変換版120の約1000秒の評価とプールによる検証を行う\cite{cabrera2023}．MineSweeperの表10はWasm/asm.jsとCPU利用率による速度差を扱う\cite{konoth2018}．従って，採掘Wasmの難読化後の速度を初めて測定したとは主張しない．既存のプール検証を設計の参照としつつ，本稿の追加実測は公表入力とネットワーク無効のローカル実行を用いる．

Proof-of-Theftの第6節はグラフ簡約と検出を評価しており，確認した本文・補足には難読化前後の出力と反復hashes/sの対比較報告を特定できなかった\cite{sermchaiwong2026}．ただし公開コードにはhashrate.jsがあり，測定自体が行われなかったとは断定しない．本稿は配布標本2実装の機構・出力・速度を追加照合する．SWAMPEDの第IV.D節の実行時間評価は，JavaScript処理がないためimportを空の関数で置き換える\cite{kim2025}．本稿は必要なホスト処理を復元し，完全なハッシュ出力を検証した上で公開変換コードによる対を測定する．

MinerRayの第6.4節・表5の時間は検出用グラフの構築・走査であり，採掘速度とは異なる\cite{romano2020minerray}．WASMixerのarXiv第1版第5.2・5.5節では，ブラウザとJavaScriptへの依存を理由に採掘D3を実行時間評価から除外する\cite{cao2023}．刊行版\cite{cao2024published}の評価本文との版間照合は未完了である．今回のSWAMPED入力はこれらにも同一SHAで再収録されているが，自生成対はSWAMPEDの手法であり，WASMixerの変換を実行評価した結果ではない．未報告とする範囲は確認した資料に限定する．WasmBench\cite{hilbig2021}とSEISMIC\cite{wang2018seismic}は通常構造・計測コードの対照に用いる．

\section{対象と分析方法}
\subsection{配布物の範囲と役割}
採掘研究との関係と公開Wasmを確認できた資料を対象とする．Cryptic BytesはCryptoNight系列10プログラム，未最適化・最適化済みの2配布条件で，基準版を含む20,460件を対応付けた．LLVM・Tigress各8設定とwasm-mutateを含み，基準版自身との比較は20件である．元プログラムは関連する派生実装であり，独立した10マルウェア系統ではない．Proof-of-Theftは34ディレクトリを9設定へ整理した．元ファイル，中間ファイル，Wasabi計測版が混在するため，origという名称のみで変換前とは判断しない．

収集標本ではMineSweeperのminer samples 34種類中33，SWAMPEDのCryptojackers 43種類中42を静的解析できた．WasmMalの悪性区分は配布元による分類であり，全件を採掘と確認してはいない．比較用の良性群とWasmBenchも含めた特徴分布を表\ref{tab:features}に示す．各群内の同一SHAはまとめるが，群間の重複は残る．SWAMPED入力42種類中35は他の取得記録にも再収録されていた．これらから攻撃全体の難読化普及率は推定しない．

@@FEATURES@@

\subsection{機構と静的変化の確認}
SHA-256，取得元リビジョン，配布設定，基準版との対応を保存し，WABT 1.0.42で検証・逆アセンブルする．関数，命令，ループ内分岐表，直接・間接呼出し，ロード・ストア，セクションサイズを抽出する．検証失敗を特徴の不在とみなさない．設定名，特徴の存在，命令列で確認した機構を区別し，状態の生成・更新・戻り先，仮想命令の読出し，同値式を追う．全関数の意味保存や自動分類精度を評価するものではない．

基準版に対する差分$\Delta X=X-X_0$と比$r_X=X/X_0$を求め，基準が0なら差分のみを残す．Cryptic Bytesはまず同じ元プログラム・条件・設定の変換群の中央値を求め，次に10プログラムの分布を示す．大量の派生版を独立標本とした検定は行わない．未最適化と最適化済みをそれぞれ同条件の基準版と比較し，wasm-mutateの混合変換を単一手法の効果と扱わない．静的命令数は実行回数でもメモリ使用量でもない．

\subsection{出力と実行速度の測定}
追加のローカル反復測定の13バイナリは，Proof-of-Theftのwebminerpoolhashcnとxmr-wasm各5，SWAMPED入力1，自生成変換2である．全標本をSHAでRQ1の機構記録と対応付け，Wasabiのhookを持つ計測版は除く．Windows上のネットワーク無効のLinuxコンテナ，Intel Core i9-11900K，Node.js v18.20.4，V8 10.2.154.26-node.37，1 workerを用いる．配布JavaScriptまたはWasmのimportに基づくホスト処理から同期呼出しする．初期化は測定前とし，呼出しループ等の負荷を含むためWasm命令のみの速度ではない．

独立した期待値にはXMRig v6.18.0の\texttt{CryptoNight\_test.h}の公表v0入力5件を用いる\cite{xmrigvectors}．xmr-wasmでは先頭バイトからvariantを選ぶためv0に対応する3件を用い，最大targetでnonce不変と1ハッシュの出力を確認する．webminerpoolhashcnのcn-pico測定では，過去にプール受理された13件のジョブ・nonce・出力を照合する．これは新しいプール提出ではない．有限入力の一致を全入力の意味保存と区別する．

速度は完了したハッシュ数を実経過時間で割る．webminerpoolhashcnは1秒のウォームアップ後，各5秒・3反復の予備測定，xmr-wasmとSWAMPEDの対は3秒のウォームアップ後，各30秒以上・3反復とする．各反復で標本順を循環させ，最終出力を確認する．中央値と最小--最大，同じ反復内の基準比を示す．これらは逐次測定であり同時測定の対や信頼区間ではない．

\section{RQ1：確認した機構とデータセットの傾向}
\subsection{代表機構と通常・計測処理の対照}
研究用配布物は平坦化，偽制御フロー，分割，算術式・定数の変換，呼出し変更，仮想化などを含む．Cryptic Bytesは各設定に10本$\times$2条件を持つ一方，Proof-of-Theftの設定ごとの収録対象は均等でない．設定名の範囲と命令列で確認した範囲を分ける．

Cryptic Bytesのcn-0ではexport名\texttt{hash\_cn}で関数を対応付けた．Tigress flatten版は状態の初期値5を保存し，12要素の分岐表で選択後，状態を更新して共通ループへ戻る．virtualize版は仮想命令ポインタから1バイトを読み，16を引いて233要素の分岐表へ渡す．ポインタを1または4進めるため，状態選択のみの平坦化と区別できる．仮想命令全体の意味は復元していない．

LLVM subobf版では$x\ll3$が次の式へ変わる．
\[
(x\mathbin{\&}\mathord{\sim}8)(\mathord{\sim}x\mathbin{\&}8)
+(x\mathbin{|}8)(x\mathbin{\&}8).
\]
$u=x\mathbin{\&}\mathord{\sim}8$，$v=x\mathbin{\&}8\in\{0,8\}$とすると$u(8-v)+(u+8)v=8x$で，32ビット剰余演算で一致する．antialiasanalysis版ではメモリ上の番号を間接呼出しへ渡す箇所を観測したが，基準版の対応箇所との差分が未確定であり，難読化で追加されたとは断定しない．

\label{sec:rq1-controls}
通常処理にも同じ特徴がある．CreaturePackの分岐表は状態更新・ループを伴わない数値の選択であり，WASMixerのbase64-cliの状態更新と選択ループへの復帰とは異なる．xmr-wasm基準版の70箇所の分岐表は同梱CryptoNightRの演算選択に対応する．cryptonight-hash基準版の間接呼出しも，内部状態からBlake，Groestl，JH，Skeinを選ぶ通常の最終処理である．分岐表や間接呼出しの存在だけで難読化と判定できない．

WasmMalでは悪性121件，良性3件にSEISMIC計測関数と一致する関数があった．A-Star・CreaturePackではカウンタ更新を除去すると元の全147・756関数の命令列に一致した．命令増加が計測由来となる対照であり，採掘標本の確認件数には含めない．表\ref{tab:features}の特徴率も手法の確認率ではない．

\subsection{実測13標本の機構と測定経路}
\label{sec:proof-mechanisms}
webminerpoolhashcnでは基準・4変換ディレクトリすべてのMakefileが\texttt{-enable-bcfobf}を指定していた．過去の生成指示を確定できず，名称を確認済み手法と扱わない．xmr-wasmは名称に対応するフラグと，同梱C/C++・ヘッダ46ファイルのSHA一致を確認したが，過去のコンパイラやオブジェクトまで同一とは保証しない．分割設定はLLVMの基本ブロック分割を指す\cite{emccobfdocs}が，変換前後の中間表現がなく，Wasmの保存位置・block構造の変化のみでは適用履歴を確定できない．偽制御フローも機構未確認とする．

xmr-wasm平坦化版では公開hash，XOR補助関数112・118，初期化83，鍵取り込み82，解放86で状態の選択・更新・共通ループへの復帰を確認した．公開hashに分岐表がないことは，分岐表が平坦化の必要条件でもない例である．関数111の補助関数118への2呼出しは主ループ内にあるが，初期化等はループ外で，動的な回数と時間寄与は未測定である．

関数113への呼出しはvariant 4以上に限定され，今回のv0入力では通らない．さらに平坦化版の関数111の本体命令列は，この未実行ブロック内で9,428行増えた一方，それ以外の3,609行は局所変数・ラベル名を対応付けると一致した．従って，この増加をv0で追加実行された命令数とは扱えない．呼出し先の変化，局所変数の宣言，JITや配置の影響は残る．

置換版の公開hashには$(x-C)-6+C=x-6$と$n-(0-1)=n+1$を確認したが，今回の入力と最大targetでは両経路を通らない．一方，呼出し先の関数111の二重ループには，先の式の8を16に替えた$x\ll4$の同値変換を確認した．ラッパだけでなく計算内部にも機構の根拠はあるが，動的経路の全被覆は未確認である．

SWAMPEDの自生成対は，nop挿入30関数3,089箇所，整数定数分割29関数542箇所を記録した．挿入nopの除去と分割式の復元でモジュール全体のWATが基準版へ戻り，計測hookは追加していない．元配布の変換標本と今回の生成物は区別する．

\subsection{RQ1への回答}
設定横断では制御・算術・呼出しの各変換を含むが，確認できた機構と適用範囲は配布物によって異なる．実測対象では平坦化・置換・自生成のnopと定数分割を命令列で対応付け，通常の暗号処理と計測を区別した．名称不一致と未確認機構を残す標本は，確認済み手法の効果とは扱わない．収集標本全体の手法別普及率は確定していない．

\section{RQ2：構造変化と正しいハッシュ計算の性能}
\subsection{Cryptic Bytesの静的比較}
@@STATICFIG@@
全20,460件を解析し，図\ref{fig:methods}のように手法・配布条件で増加量が異なった．未最適化版の命令数比中央値はTigress encodearithmetic 2.515，LLVM subobf 1.461，平坦化はLLVM 1.098とTigress 1.394である．最適化済みのencodearithmetic・subobfは1.655・1.327となった．同じ名称でも変換段階と範囲が異なり，手法の優劣を示す値ではない．

virtualizeの命令数比は未最適化1.417，最適化済み1.418と近いが，サイズ比は1.834・2.322で異なる．cn-0の実際の対では，未最適化のcode・data増加が165,827・97,625バイト，最適化済みが86,969・97,598バイトだった．仮想命令列を持つ機構と整合するが，全dataを仮想命令として復元してはいない．サイズ比は基準の大きさにも依存する．

Tigress平坦化では両配布条件でループ内分岐表が中央値70増え，未最適化のストアは6,733増えた．antialiasanalysisでは直接呼出しが218減り，間接呼出しが358増え，一対一の置換ではない．全対にnameセクションはなく，名前除去の効果は評価できない．これらは静的な構造であり，実行負荷とは次節で分けて照合する．

\subsection{Proof-of-Theftの出力と速度}
\label{sec:runtime}
webminerpoolhashcnの5標本は公表v0入力5件がすべて一致し，cn-picoの保存済み受理出力13件もすべて一致した．各5秒・3反復の速度中央値は，基準204.04，平坦化名213.29，分割名222.99，置換名225.20，偽制御フロー名212.24 H/sであった．設定不一致と短時間測定のため，4手法の高速化・オーバーヘッドとは解釈しない．

\label{sec:xmr-runtime}
xmr-wasmの5標本も公表v0入力3件が一致した．各30秒以上・3反復の結果を表\ref{tab:xmr-runtime}に示す．全15ブロックで最終出力とnonce不変を確認した．
@@XMRTABLE@@
平坦化版は命令数1.166倍，サイズ1.170倍，速度中央値比0.678である．置換設定版は命令数1.655倍，サイズ1.641倍，速度比0.738であり，命令増加と速度低下の順位が一致しない．反復内の基準比も平坦化0.661--0.689，置換0.708--0.790で，いずれも3回とも1未満だった．ただし過去のビルド条件と全適用範囲を統制しておらず，機構だけで低下の全量を説明しない．

分割設定版は速度比0.943だが反復内の比0.906--1.011は差の方向が入れ替わった．偽制御フロー設定版は速度比2.534，命令数比0.413であったが，この版だけに明示的な\texttt{-O2}があり，難読化による高速化とは結論しない．実装・アルゴリズム・呼出し条件が異なるwebminerpoolhashcnとの絶対速度の比較も行わない．

実行不能な標本は出力不一致や0 H/sと扱わない．選定したProof-of-Theftの19標本のうち，上記10標本は照合できたが，Tigressの併用版と仮想化版は間接呼出しの実行時エラーとなり，原因未確定である．cryptonight-hashの7標本は入力ごとの公開呼出し口を確認できず，内部関数の部分ABIと一部平坦化を静的に確認した段階で，出力・速度の実測には含めない．

\subsection{SWAMPEDの同一組立条件の変換対}
\label{sec:swamped-hash}
\label{sec:swamped-controlled}
取得済み42標本のexport・ホスト依存性を調べ，SHA-256が\texttt{046dc081}で始まる標本の\texttt{\_cryptonight\_create}と\texttt{\_cryptonight\_hash\_variant\_0}を呼び出した．元JavaScriptがないため，importと命令列から旧Emscriptenのメモリ・表・時刻・UTC変換・プロセスIDを実装した．初期メモリ16 MiBで，必要なimportを空の関数にせず，未対応呼出しはエラーにする．元ホストの配置を完全再現したとは主張しない．公表v0入力5件がすべて一致した．この標本はMinerRay，WasmBench，WASMixer，WasmMalにも同じSHAで収録されており，独立した5標本ではない．

公開変換コードのコミット\texttt{04e2bcc}の本体を保持したWATアダプタで，nop挿入と整数定数分割を生成した．位置選択はbeta(1,1)，関数ごとの候補比0.1と最低1箇所の規則を保持し，乱数生成器を固定した．浮動定数の丸め誤差を避けるためvariant\_2関数は定数分割から除いた．整数定数$c$を$a+b=c$へ置き換え，例えば\texttt{i64.const 0}は$-1+1$の命令列となる．

基準・変換版を同じWABTで組み立て，基準のSHAは元配布物と一致した．3標本とも公表入力5件とimport/export一覧を確認し，同じホスト・メモリ・入力・固定初期時刻で反復した．全9ブロックで最終出力と測定後の5件の出力が一致した．追加評価は外部通信・プール提出・報酬を伴わない．
@@SWAMPTABLE@@
@@RUNTIMEFIG@@
nop版のサイズ・命令数・速度中央値比は1.042・1.097・0.960，定数分割版は1.024・1.034・0.973であった．反復範囲は重なり，反復内の基準比はnop 0.960--1.091，定数分割0.973--1.068と差の方向が入れ替わった．基準版自身も1回目27.09から3回目32.73 H/sへ20.8\%上がった．逐次測定の順序を循環させても時間変動は除けず，小さな中央値差を確定的な負荷と扱わない．Wasmエンジンが追加命令を除去した可能性はあるが，機械語を確認していないため断定しない．

\subsection{RQ2への回答}
評価した有限入力では実測した変換版も期待出力を保持した．静的な増加と速度変化は一様でなく，xmr-wasmでは増加量と速度低下の順位が一致せず，同条件のSWAMPED対では命令増加に対する小差が時間変動に重なった．実装間の共通則や手法の因果効果は確定しておらず，測定条件の異なる実装間の速度順位は付けない．

\section{考察と限界}
RQ1とRQ2を結び付けるには，変換された処理と入力の経路を照合する必要がある．xmr-wasmの関数111の増加はv0で通らないvariant 4以上のブロックに集中し，ラッパの置換式も測定条件では通らない．全体命令数の増加をそのまま追加実行量と扱うと，未測定処理の効果が混ざる．一方，主ループから呼ぶ平坦化された補助関数や，内部ループの置換には機構の根拠がある．その寄与を確定するには動的な経路・回数，JIT，生成機械語等の追加評価が必要である．

配布物比較と同条件で生成した対も区別する．前者では過去の最適化・コンパイラを統制できず，後者でも1入力標本・各1乱数設定・3反復に限られる．長時間・多数反復による安定性や，元配布の変換版を統一ビルドで再現する対照は未完了である．emcc-obfのDockerfileは一部をコミット固定する一方，Hikariをブランチ取得・サブモジュール更新するため\cite{emccobfdocs}，その手順だけでは過去の変換コードの版を確定できない．

データセット名の違いは独立した再現を意味しない．同一SHAの再収録に加え，webminerpoolhashcnとxmr-wasmはOpenAES設定と一部AES処理を共有する．部品の共有は計算全体の同一性も完全な独立性も示さない．対象はCryptoNight系列に偏り，他アルゴリズムへの一般化はできない．公開資料を網羅したとは主張せず，新しいクローリングや年次推移の調査は行っていない．MineSweeperのcrawled-sites 36種類は元ファイルの検証に失敗し，特徴表には別のminer samplesを用いた．解析可能性と取得範囲による偏りが残る．

機構解析は選択した箇所に限られ，全件の手法確認率や見逃し率は未評価である．解析・執筆にCodexの支援を用い，状態遷移，式の導出，引数対応には人間の独立レビューが必要である．過去のCryptic Bytesの外部プール試行は通常版・bcfobf版各1回で13・10 shareの受理を記録したが，本稿のローカル反復とは条件が異なり混合しない．プール受理・公表出力一致のいずれも全入力の正しさを保証しない．

入力SHA，リビジョン，配布条件，基準対応，機構の命令位置，生ログ，測定順序，Node/V8・イメージID，集計CSVと図生成コードを保存した．新しい大学PC上の実行は指導教員の許可確認後とし，報酬を発生させない隔離ローカル評価に限定する．本稿は既存の測定結果に基づき，未実測候補を結果へ混入させない．

\section{まとめ}
公開採掘Wasmの配布設定と確認した機構を整理し，通常処理・計測と区別した上で，13バイナリの出力・速度・静的変化を対応付けた．xmr-wasmでは命令増加と速度低下の順位が一致せず，一部の増加箇所は測定入力で通らなかった．SWAMPEDの同条件の自生成対では正しい出力を保持したが，小さな速度差の方向は反復で変わった．これらは，静的増加量だけで性能負荷を説明できず，適用範囲・測定経路・ビルド条件を合わせて評価する必要を示す．結論は対象標本・有限入力・測定条件に限られ，検出回避能力や手法の一般的優劣は示さない．
\bibliographystyle{ipsjunsrt}
\bibliography{references}
\end{document}
'''
replacements={
 '@@FEATURES@@':env('tab:features','table*'),
 '@@STATICFIG@@':env('fig:methods','figure*').replace('width=\\textwidth','width=0.82\\textwidth'),
 '@@XMRTABLE@@':env('tab:xmr-runtime','table'),
 '@@SWAMPTABLE@@':env('tab:swamped-controlled','table'),
 '@@RUNTIMEFIG@@':env('fig:swamped-controlled','figure*'),
}
for key,value in replacements.items():body=body.replace(key,value)
body=body.replace('手法別の命令数比とファイルサイズ比．各配布条件の基準版との比較．元プログラム10本の値をまとめた統計であり，独立した10系統のマルウェアについて推定したものではない．手法名は配布元の設定．','Cryptic Bytesの命令数比とサイズ比．同配布条件の基準との比較．元10プログラムの分布であり，手法名は配布設定．')
body=body.replace('各実装の基準版に対するサイズ・命令数・速度の比．左はxmr-wasmの配布物比較，右はSWAMPED入力への自生成変換．速度の棒は中央値同士の比，白丸は各反復の変換版の速度を同じ反復の基準版の速度で割った3点である．同じ反復内でも順に測定しており，同時測定や信頼区間ではない．最適化条件が異なるxmr-wasm偽制御フロー版は図から除き，表に残した．','基準版に対するサイズ・命令数・速度の比．左：xmr-wasm配布物，右：SWAMPED自生成対．速度の棒は中央値比，白丸は逐次測定した3反復の反復内基準比（信頼区間ではない）．最適化条件が異なる偽制御フロー設定版は表のみ示す．')
p.write_text(head+body,encoding='utf-8')
print('UTF-8 bytes:',len((head+body).encode('utf-8')))
