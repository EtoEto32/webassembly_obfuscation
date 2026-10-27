# API継続を保つメモリ条件の合成（実装前）

2026-10-24。具体状態の有限閉包より広い状態集合を扱えるかというKの追加仮説。独立した新原理が確認された別発明とは数えない。

## 入力と求めるもの

閉じたmemory32 module、globals/tableなし、元APIは引数なしの定数bulk memory/drop列か副作用なしの単一byte読取り。各memory.init/copy/fillの転送長128bytes以下、静的に触るcell合計256以下とする。二つのinstanceのmemory容量と初期bytesは等しく、segment有効状態だけが指定通り異なる。

任意の初期memoryについて、**任意長の元API列の各return/trap後でAPI結果とmemory全bytesが等しい**ための条件を求める。trapの後でもhostは次のAPIを呼べる。segmentsの全一致は要求しない。memory同一性を毎回要求する契約であり、内部memoryが異なっても読めない場合を含む最も弱いcontextual equivalenceとは区別する。

## アルゴリズム仮説

bulk演算のアドレス/長さが定数なので、segment状態を固定すると各APIの最初のtrap位置と最終segment状態が確定する。実行後の各cellは初期cellかbyte定数で表せる。overlap copyは更新前の値から同時に代入する。trapした命令は書かず、その前の書込みを保持する。

segment状態対を有限control stateとして、APIごとの結果一致とpost-memory一致からcell等式を作る。後続stateで必要な等式を、左側のcopy/constant写像へ逆代入して入口の条件へ戻す。等式の連言を同値類として正規化し、全APIについて固定点まで繰り返す。異なるbyte定数を同値類に含むとfalse。domainが有限なので、完走した固定点は選んだ契約内で全API列に対する条件になる、という論証を行う。resource capに達した場合は保留。

例：片側はinit Aですぐtrap、他方はAの固定bytesを書いてdrop A後に別の空segmentでtrapする。両者のmemoryが等しい条件は転送先が元々そのbytesであること。さらに別APIがその領域へcopyする場合には、copy元にも条件が伝播する。具体memoryでしか判断できなかった点を、条件として表現する。

## 反証・先行研究

コピーと定数の等式抽象、weakest precondition、register automataのbisimulation、関係的な変換検証は既存である。[A Self-Certifying Compilation Framework for WebAssembly](https://antonxue.github.io/files/papers/namjoshi2021self.pdf)（Namjoshi/Xue, VMCAI 2021）のabstract、§1、§3–4を読んだ。Wasm状態の関係とtrapを含む変換検証は既にある。ただしKが対象にするsegment寿命・hostによるtrap後の再呼出しと同じ契約かは区別する。同論文のcheckpoint edgeは証明上の区切りで、runtime snapshotと同義ではない。

[Weakest Precondition Synthesis for Compiler Optimizations](https://web.ist.utl.pt/nuno.lopes/pubs/psyco-vmcai14.pdf)、[Symbolic Register Automata](https://matteosammartino.com/assets/pdf/cav19.pdf)も近接技術として確認する。条件を自動生成しただけで一般的な合成原理の新規性を主張しない。Wasmの特定の復元誤差に対して、具体実行より適用範囲が広がるかをまず測る。

## 実験

固定点を要するcopy連鎖、重複copy、範囲外、0長、共通trap、異なるtrap位置、矛盾する要求、dropで揃う、readonly APIを含む小例を先に作る。満たすmemoryと破るmemoryを実binaryへ与え、API列をNode/Wasmtimeで比較する。公式memory_init例へも適用する。未対応は明記し、今回の入力集合に合わせて旧分類器を書き換えない。条件合成、前提の充足判定、反例実行を別々に記録する。

追加計画：12小例と実測由来11条件での実行照合後、生成器のcopy写像とは別にZ3 arrayのStore/Selectでbulk演算を記述し、各state/APIの条件が結果一致・post-memory一致・後続条件を含意するか確認する。入力profileのparserは共有し、完全に独立した仕様実装とはしない。条件を意図的に弱めた対照も入れ、検証器が反例を返すことを調べる。これは生成された条件の十分性の検査で、最弱性やchecker自体の機械証明ではない。
