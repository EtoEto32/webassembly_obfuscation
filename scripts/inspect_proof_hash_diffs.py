"""Normalize temporary-local naming only, preserving the reviewed instruction order."""
import difflib
import re
from pathlib import Path
from audit_proof_runtime_mechanisms import function_excerpt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'

def normalize(text):
    mapping = {}
    def replace(match):
        key = match.group()
        return mapping.setdefault(key, '$v'+str(len(mapping)))
    lines = [l for l in text.splitlines() if not l.lstrip().startswith('(local ')]
    return [re.sub(r'\$l\d+', replace, l) for l in lines]

base, _ = function_excerpt(OUT/'xmr-original.wat', 'hash')
for name in ['substitution', 'split']:
    modified, first = function_excerpt(OUT/f'xmr-{name}.wat', 'hash')
    (OUT/f'xmr-hash-{name}-excerpt.wat.txt').write_text(modified+'\n')
    diff = '\n'.join(difflib.unified_diff(normalize(base), normalize(modified),
                        fromfile='reference hash', tofile=name+' hash', n=8))+'\n'
    (OUT/f'xmr-hash-{name}-local-normalized.diff.txt').write_text(diff)
    print(name, 'first WAT line', first, 'diff lines', diff.count('\n'))
