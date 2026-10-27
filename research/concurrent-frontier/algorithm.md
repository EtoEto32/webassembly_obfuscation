# 同期を用いた演算グラフ実行と、その逐次回復

## 変換

WABTで実入力Wasmをvalidate/disassembleし、全域i32命令だけからなる単一関数をSSA DAGへする。localの再代入は別SSA値となり、localの初期値0も含める。同一式は共有する。元の関数名は変換CLIの記録に残すが、新しいAPIは`init`、`work(worker)`、`result`、単一worker用`run`である。`init`/`run`は16引数に揃える。元のarityにない引数は使わない。

```text
transform(P, seed):
    G = pure_i32_SSA(P)
    permute node positions using seed
    store opcode and predecessor indices in shared linear memory
    allocate value, state, owner for each node

init(args):  # 全workerが停止中
    done = 0
    constants / parameters: value = input; state = READY
    operators: value = 0; state = FREE

work(worker):
    scan = worker*73 mod node_count
    while done < operator_count:
        i = scan; scan = (scan+1) mod node_count
        if i is an operator and state[i] == FREE:
            if every predecessor is READY:
                if cmpxchg(state[i], FREE, CLAIMED) == FREE:
                    value[i] = evaluate(opcode[i], predecessor values)
                    owner[i] = worker
                    state[i] = READY
                    atomic_add(done, 1)
```

stateはFREE=0、CLAIMED=1、READY=3。atomic版のmemory accessはすべてSC atomic。演算は整数wrap、shift、比較等のWasm命令をそのまま使い、trapを起こすdivision等は拒否する。全域純粋なselectの両辺を先行計算してよい。命令の追加でnodeを増やすのは本方式の新規性ではない。

## 意味保存の条件と論拠

1. 入力・定数は初期化後固定。ホストはジョブ中にmemoryを変更しない。
2. CASにより各演算の書込み担当者は一人。結果を書いた後にREADYを公開する。
3. READYを読んだ依存先は、SC順でその前に書かれた正しい値を読む。READYはこのジョブ中に戻らない。
4. DAG順の帰納法で、各READY値は元SSA値と一致。有限のDAGをworkerが公平に走査すれば完了する。停止済みworkerが取得中のnodeを永久保持する場合など、進行性は保証しない。
5. ホストは全worker完了後に結果を読み、次のinitを行う。各workerのinstantiateはactive data segmentを再書込みするため、全instanceのready確認前にジョブを始めてはならない。

これはアルゴリズムの説明上の論証であり、Python変換器、生成Wasm、V8、ホストadapterを一括した機械証明ではない。正当性テストと2演算のSCモデル探索は別に保存する。入力プログラムのmemory副作用・trap・I/O・共有状態は非対応なので、その保存を主張しない。追加memoryの内部状態や実行時間は元プログラムと一致しない。

## 方式既知の回復

`recover.py`は入力Wasmのみを読む。公開VM仕様から無関係な定数関数のraw/O3、atomic/non-atomicの4種類を生成し、data/custom以外のsection fingerprintを登録する。対象の型・import・export・codeがその範囲に一致しなければunsupported。これは未知VM一般を理解する解析器ではない。

data sectionを実メモリ初期像に復元し、header・各record・初期状態・境界・opcode・循環の有無を検査する。Kahnのトポロジカル順で依存先を置換し、通常のWasm命令へ戻す。入力原本・生成seed・実験manifest・期待式を回復器へ渡さない。原本との比較は回復後の評価段階だけで行う。

この範囲では回復はO(V+E)のグラフ処理とバイナリ読取りで足りる。worker数はグラフを変えず、解析者に全合法実行順の列挙を要求しない。動的順序の多さをそのまま解析費用と数えるのは誤り。有限の解析費用増自体は否定しないが、対照VMとの差を測る必要がある。
