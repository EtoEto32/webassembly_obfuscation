"""Review helper dispatch and structural call context in saved WAT."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
core=(OUT/'xmr-original-f111-complete.wat.txt').read_text().splitlines()
contexts=[];stack=[]
for n,line in enumerate(core,1):
    token=line.strip()
    if token.startswith(('block ','loop ','if ')):stack.append(dict(line=n,construct=token))
    elif token=='end':stack.pop()
    elif token in ('call $f112','call $f118'):
        contexts.append(dict(line=n,callee=token.split()[1],enclosing_constructs=stack.copy()))
before=(OUT/'xmr-original-f118-reviewed.wat.txt').read_text()
after=(OUT/'xmr-flattening-f118-reviewed.wat.txt').read_text()
assert all(x in before for x in ['i32.const 16','i32.xor','i32.store8','loop $L1','br $L1'])
assert all(x in after for x in ['i32.const 16','i32.xor','i32.store8','i32.store offset=16',
    'i32.load offset=16','i32.store offset=12','i32.load offset=12',
    'i32.const -1944965114','i32.const -1749425722','i32.const -1178374432',
    'i32.const -266051066','loop $L0','br $L0','select'])
assert 'br_table' not in after
report=dict(function='$f118',caller_chain=['$hash','$f35','$f111','$f118'],
    reference_function_digest=hashlib.sha256(before.encode()).hexdigest(),
    flattened_function_digest=hashlib.sha256(after.encode()).hexdigest(),
    mechanism='State dispatcher around a 16-byte in-place XOR loop.',
    transitions=[dict(state=-1944965114,operation='Compare index < 16',next_if_true=-1749425722,next_if_false=-266051066),
                 dict(state=-1749425722,operation='XOR byte and store',next=-1178374432),
                 dict(state=-1178374432,operation='Increment index',next=-1944965114),
                 dict(state=-266051066,operation='Return')],
    reference_index_offset=4,flattened_index_offset=20,state_offset=16,state_pointer_offset=12,
    reference_call_contexts=contexts,
    interpretation='Calls at reference lines 1725 and 23284 are directly within main loop L17; other call sites have additional enclosing blocks. This is lexical structured-control context, not a complete CFG reachability or dynamic call-frequency proof.',
    f112_first_call_caveat='Reference f112 call at line 286 is inside the variant==1 initialization block. Its presence cannot alone explain cn/0 timing.',
    limitations='Dynamic execution coverage not measured; no new hash computation or causal attribution of overhead.')
(OUT/'xmr-helper-path-review.json').write_text(json.dumps(report,indent=2)+'\n')
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8')
old='ただし静的な呼出しの存在は，v0の速度測定でこの補助関数が実行されたことを証明しない．'
new='同様に16バイトのXORを行う補助関数118にも状態による選択を確認した．その呼出しのうち2箇所は通常版の主ループに直接含まれる．一方，関数112の最初の呼出しはvariantが1の初期化条件内にある．従って補助関数がモジュール内にあることと，v0測定でその箇所を通ることを区別する．これらは構造化された命令列での呼出し位置の確認であり，完全な到達可能性や動的呼出し回数の証明ではない．'
assert old in s;s=s.replace(old,new,1)
s=s.replace('平坦化の機構はhashラッパとXOR補助関数112で確認したが，', '平坦化の機構はhashラッパとXOR補助関数112・118で確認したが，',1)
p.write_text(s,encoding='utf-8')
with (OUT/'resume-state.txt').open('a',encoding='utf-8') as f:
    f.write('\n呼出し範囲レビュー：f118の16byteXOR helperもstate化を全文確認。元f111の呼出し1725/23284は主loopL17直下，他は追加block内。f112最初の286callはvariant==1初期化条件内。xmr-helper-path-review.jsonに全f112/f118直接呼出しの構造化コンテキストと4状態を保存。これは語彙的block位置でありCFG/動的頻度証明ではない。paperRQ1/RQ2更新，新規ハッシュ実行なし。\n')
print('Saved 16-byte helper mechanism and call-context caveats; no execution.')
