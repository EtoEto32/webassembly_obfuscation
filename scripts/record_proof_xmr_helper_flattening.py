"""Record a statically reviewed helper dispatcher without executing code."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
before=(OUT/'xmr-original-f112-reviewed.wat.txt').read_text()
after=(OUT/'xmr-flattening-f112-reviewed.wat.txt').read_text()
assert 'i32.const 8' in before and 'i32.xor' in before and 'i32.store8' in before
assert 'loop $L1' in before and 'br $L1' in before
assert all(x in after for x in ['i32.store offset=16','i32.load offset=16',
    'i32.store offset=12','i32.load offset=12','loop $L0','br $L0',
    'i32.const -644732001','i32.const -601762212','i32.const -36145701',
    'i32.const 25466191','select','i32.xor','i32.store8'])
assert 'br_table' not in after
report=dict(function='$f112',caller_chain=['$hash','$f35','$f111','$f112'],
    reference_function_digest=hashlib.sha256(before.encode()).hexdigest(),
    flattened_function_digest=hashlib.sha256(after.encode()).hexdigest(),
    mechanism='State-driven dispatch for an eight-byte in-place XOR helper.',
    correspondence='Same two pointer parameters, byte loads from pointer+index, XOR and store8, index bound 8 and increment 1. Distributed slow-hash.c has a matching xor64 byte loop; no debug symbol mapping proves its identity.',
    reference_frame_bytes=16,flattened_frame_bytes=32,
    reference_index_offset=4,flattened_index_offset=20,
    dispatcher_state_offset=16,state_pointer_offset=12,
    transitions=[dict(state=-644732001,operation='Compare index < 8',next_if_true=-601762212,next_if_false=-36145701),
                 dict(state=-601762212,operation='XOR byte and store',next=25466191),
                 dict(state=25466191,operation='Increment index by 1',next=-644732001),
                 dict(state=-36145701,operation='Return')],
    scope='Complete saved helper body reviewed; state writes use the pointer stored at frame+12 and common loop L0.',
    dynamic_path_coverage='Not measured; static call sites do not prove execution in the cn/0 benchmark.',
    limitations='Not a whole-module semantic proof, historical rebuild, or quantitative attribution of throughput loss.')
(OUT/'xmr-helper-flattening-review.json').write_text(json.dumps(report,indent=2)+'\n')
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8')
needle='命令置換版の公開hash関数にも，元の式との対応を確認した．'
paragraph='さらに関数111から呼ぶ補助関数112では，通常版の8バイトのXORループが状態による選択へ変わっていた．元の添字はオフセット4，変換版では20に保存され，状態は16，状態へのポインタは12に置かれる．状態$-644732001$で添字が8未満かを調べ，真なら$-601762212$でXORと1バイトの書込みを行い，$25466191$で添字を増やして最初の状態へ戻る．偽なら$-36145701$で終了する．2ポインタ引数，バイトの読書き，XOR，上限8と増分1が対応し，この補助関数にも\\texttt{br\\_table}はない．ただし静的な呼出しの存在は，v0の速度測定でこの補助関数が実行されたことを証明しない．\n\n'
assert needle in s
if '補助関数112では' not in s:s=s.replace(needle,paragraph+needle,1)
s=s.replace('平坦化で確認したhashラッパ以外の処理も測定時間に含まれるため，ラッパの変更だけから低下の全量を説明しない．', '平坦化の機構はhashラッパとXOR補助関数112で確認したが，各関数の動的な呼出し回数は測定していない．その他の処理も測定時間に含まれるため，これらの機構だけから低下の全量を説明しない．',1)
p.write_text(s,encoding='utf-8')
with (OUT/'resume-state.txt').open('a',encoding='utf-8') as f:
 f.write('\nRQ1範囲拡張：保存WATのf111直呼出し先のうち平坦化版で6関数に差がある。f112全文（通常版8バイトXORループ/平坦化版198行）をレビュー，state offset16，pointer12，index20，-644732001→条件→-601762212 XOR→25466191 increment→条件，false -36145701 return，br_tableなし。xmr-helper-flattening-review.json保存，paperRQ1/RQ2へ反映。実行経路は未計測，性能低下因果は断定しない。新規ハッシュ実行なし。\n')
print('Saved helper flattening mechanism and updated RQ1/RQ2 scope.')
