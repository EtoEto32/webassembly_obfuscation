"""Check a saved integer expression, not a mining computation."""
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
baseline = (OUT/'xmr-original-f111-complete.wat.txt').read_text().splitlines()
variant = (OUT/'xmr-substitution-f111-complete.wat.txt').read_text().splitlines()
# Exact first address-calculation replacement after load offset=1048.
before = baseline[780:786]
after = variant[780:828]
assert before[0].strip() == 'i32.const 4'
assert after[0].strip() == 'i32.const -1'
assert after[-1].strip().startswith('local.set ')
input_local = variant[779].strip().split()[1]
assert variant[778].strip() == 'i32.load offset=1048'

def evaluate(lines, value):
    locals_ = {input_local: value & 0xffffffff}
    stack = []
    for line in lines:
        parts = line.strip().split()
        op = parts[0]
        if op == 'i32.const': stack.append(int(parts[1]) & 0xffffffff)
        elif op == 'local.get': stack.append(locals_[parts[1]])
        elif op == 'local.set': locals_[parts[1]] = stack.pop()
        else:
            b, a = stack.pop(), stack.pop()
            operations = {'i32.xor': lambda: a ^ b, 'i32.and': lambda: a & b,
                          'i32.or': lambda: a | b, 'i32.mul': lambda: a*b,
                          'i32.add': lambda: a+b}
            assert op in operations, op
            stack.append(operations[op]() & 0xffffffff)
    assert not stack
    return locals_[lines[-1].strip().split()[1]]

rng = random.Random(20261008)
inputs = list(range(8)) + [0xffffffff, 0x80000000, 0x7fffffff, 16, 128] + [rng.getrandbits(32) for _ in range(2048)]
assert all(evaluate(after, x) == ((x << 4) & 0xffffffff) for x in inputs)
report = dict(function='$f111', caller_chain=['$hash','$f35','$f111'],
              source_scope='Saved WAT address expression inside nested loops, counters at frame offsets 1052 and 1048, bounds 16384 and 8.',
              reference_lines=[781,786],variant_lines=[781,828],
              expression='(x & ~16) * (~x & 16) + (x | 16) * (x & 16)',
              reference_expression='x << 4',integer_semantics='modulo 2^32',
              derivation='Let u=x&~16 and v=x&16. v is 0 or 16; u*(16-v)+(u+16)*v=16*x.',
              tested_integer_inputs=len(inputs),all_expression_checks_match=True,
              expression_sha256=hashlib.sha256('\n'.join(after).encode()).hexdigest(),
              dynamic_path_coverage='not measured; static caller chain and loop structure only',
              limitations='A local expression identity is not a full-module semantic proof or attribution of the measured throughput difference.')
(OUT/'xmr-core-substitution-review.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'xmr-core-substitution-reviewed.wat.txt').write_text('REFERENCE f111 lines 781--786\n'+'\n'.join(before)+'\nVARIANT f111 lines 781--828\n'+'\n'.join(after)+'\n')

p = ROOT/'paper/main.tex'
s = p.read_text(encoding='utf-8')
old='ハッシュ本体の他の式の確認は継続中である．'
new='さらに公開hashから関数35を介して呼ぶ関数111でも置換を確認した．通常版ではオフセット1048のループ添字$x$を4ビット左シフトしてアドレス計算に用いるが，置換版では$(x\\mathbin{\\&}\\mathord{\\sim}16)(\\mathord{\\sim}x\\mathbin{\\&}16)+(x\\mathbin{|}16)(x\\mathbin{\\&}16)$を用いる．$u=x\\mathbin{\\&}\\mathord{\\sim}16$，$v=x\\mathbin{\\&}16$とおくと，$v\\in\\{0,16\\}$なので$u(16-v)+(u+16)v=16x$となり，32ビット剰余演算で元のシフトと一致する．この箇所は上限16384と8を持つ二重ループ内にあり，ラッパ以外にも機構の根拠がある．呼出し経路，命令位置，式の導出と2061入力の局所演算確認を保存した．動的な経路被覆とモジュール全体の意味保存は未確認である．'
assert old in s
s=s.replace(old,new,1)
s=s.replace('ハッシュ本体の適用範囲は未確認であり，増加した全命令が実行されたとは扱わない．', '呼出し先の関数111のループ内にも同値なシフト式の置換を確認したが，変換範囲の全体と動的経路被覆は未確認であり，増加した全命令が実行されたとは扱わない．',1)
s=s.replace('目的に合わせて選んだcn-0の一部とxmr-wasmの公開hash関数である．', '目的に合わせて選んだcn-0の一部，xmr-wasmの公開hashとその呼出し先の一部，SWAMPED入力に自生成した変換対である．',1)
p.write_text(s,encoding='utf-8')
with (OUT/'resume-state.txt').open('a',encoding='utf-8') as f:
    f.write('\n追加進捗：RQ1/RQ2対応を刷新。audit_proof_xmr_function_scope.pyで保存済みWAT全関数を照合し，hash→f35→f111を確認。f35は基準/flatten/subで文字列一致，f111は3変換版とも差があり，先頭一致だけで未変換とはしない。record_proof_xmr_core_substitution.pyでf111の二重ループ内x<<4置換を命令列から導出し2061整数入力の局所式確認。ハッシュを実行していない。原稿RQ1機構，RQ2解釈，限界へ反映。全適用範囲・動的被覆・因果帰属は未完了。\n')
print(json.dumps(report,indent=2))
