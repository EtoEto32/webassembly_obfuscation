"""Check the expanded manuscript against frozen results, without executing Wasm."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/followup-evaluation-20261016'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
backup = ROOT / 'paper/revisions/before-methods-expansion-20261017'
tex = (ROOT / 'paper/main.tex').read_text(encoding='utf-8')
old = (backup / 'main.tex').read_text(encoding='utf-8')
prior = load(OUT / 'paper-condensation-20261017.json')
files = {k.replace('\\', '/'): v for k, v in prior['files'].items()}
assert sha(backup / 'main.tex') == files['paper/main.tex']
assert sha(backup / 'main.pdf') == files['paper/main.pdf']
assert sha(ROOT / 'paper/references.bib') == sha(backup / 'references.bib')
assert sha(ROOT / 'scripts/normalize_wat_local.py') == '01af604b04e54026c9b53c5b70e6cb89ee9e8e2424890c28305b5bd62cad58d9'
assert sha(OUT / 'normalization-plan.json') == '9f5d90bb3ac2f23866cf32d9f3b4fcb38d5d6864946e85f755569f1342653d14'
assert tex[:tex.index('\\begin{abstract}')] == old[:old.index('\\begin{abstract}')]

def section(source, a, b):
    return source[source.index(a):source.index(b)]

assert section(tex, '\\section{関連研究', '\\section{対象と分析方法}') == section(old, '\\section{関連研究', '\\section{対象と分析方法}')
def tables(source):
    return {re.search(r'\\label\{([^}]+)\}', b)[1]: b for b in re.findall(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', source, re.S)}

now, before = tables(tex), tables(old)
assert now['tab:xmr-runtime'] == before['tab:xmr-runtime']
assert now['tab:followup-matching'] == before['tab:followup-matching']
perf = load(OUT / 'confirmatory-summary.json')
static = {r['id']: r for r in load(OUT / 'confirmatory-structure.json')['records']}
speeds = {(r['artifact_id'], r['mode']): r for r in perf['summaries']}
code = {(r['artifact_id'], r['mode']): r['code_bytes_minimum'] for r in perf['compiled_code_summaries']}
assert all(r['code_bytes_minimum'] == r['code_bytes_maximum'] for r in perf['compiled_code_summaries'])
for family in ['swamped', 'xmr-wasm', 'webminerpoolhashcn']:
    baseline = family + '-baseline'
    for transform in ['nop', 'constsplit']:
        artifact = family + '-' + transform
        values = [static[artifact]['instruction_count'] / static[baseline]['instruction_count']]
        values += [code[artifact, mode] / code[baseline, mode] for mode in ['liftoff', 'turbofan']]
        values += [speeds[artifact, mode]['geometric_mean_ratio'] for mode in ['liftoff', 'turbofan']]
        assert ' & '.join(f'{v:.4f}' for v in values) in now['tab:followup-performance'], artifact
assert perf['timed_blocks'] == 272 and perf['paired_contrasts'] == 108
for artifact in ['restore-xor8', 'restore-xor16', 'restore-both']:
    for mode in ['liftoff', 'turbofan']:
        assert f"{speeds[artifact, mode]['geometric_mean_ratio']:.4f}" in tex
normal = load(OUT / 'normalization-output-audit.json')
assert (normal['labels'], normal['unique_sha256'], normal['output_checks'], normal['public_expected_checks'], normal['reference_derived_checks']) == (77, 42, 2793, 945, 1848)
for r in load(OUT / 'normalization-matching-results.json')['summaries']:
    values = [r['outcomes'].get(k, 0) for k in ['correct_unique', 'ambiguous_with_correct', 'unmatched', 'query_origin_not_retained']]
    assert sum(values) == r['fixed_function_queries'] == 644
    assert ' & '.join(map(str, values)) in now['tab:followup-matching']
for phrase in ['1,179,648', '1,048,576', '全272ブロック', 'コンパイルは0件', '公表945', '1,848',
               '27条件', '81条件', '83.2', '0.8438～1.2029', '多重比較調整はしない',
               '設計上の候補', '計138回測定', '144条件中21条件', '\\widehat H_B(t_V)',
               '--liftoff-only', '--no-liftoff', '--no-wasm-dynamic-tiering']:
    assert phrase in tex, phrase
labels = re.findall(r'\\label\{([^}]+)\}', tex)
assert len(labels) == len(set(labels))
assert set(re.findall(r'\\(?:ref|pageref)\{([^}]+)\}', tex)) <= set(labels)
bib = (ROOT / 'paper/references.bib').read_text(encoding='utf-8')
assert {k.strip() for g in re.findall(r'\\cite\{([^}]+)\}', tex) for k in g.split(',')} <= set(re.findall(r'@\w+\s*\{\s*([^,\s]+)', bib))
for figure in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex):
    assert (ROOT / 'paper' / figure).is_file()
log = (ROOT / 'paper/main.log').read_text(encoding='utf-8', errors='replace')
assert not re.search(r'Overfull|LaTeX Warning:.*(?:undefined|multiply)|^!', log, re.M)
info = subprocess.check_output(['pdfinfo', str(ROOT / 'paper/main.pdf')]).decode(errors='replace')
pages = int(re.search(r'Pages:\s+(\d+)', info)[1])
assert pages == 8
rendered = sorted((ROOT / 'tmp/pdfs/paper-methods-expansion-20261017').glob('page-*.png'))
assert len(rendered) == pages
pdftext = (ROOT / 'tmp/pdfs/paper-methods-expansion-20261017/main.txt').read_text(encoding='utf-8')
assert all(x in pdftext for x in ['0.9077', '1.4692', '536', '参考文献'])
report = dict(status='expanded-explanation-manuscript-verified', date='2026-10-17', pages=pages,
              within_eight_page_limit=True, official_style_and_related_work_unchanged=True,
              previous_paper_pages=6, backup=str(backup.relative_to(ROOT)),
              checks=['six expanded performance rows checked against static, native-code-size and speed JSON',
                      'seven function-matching rows and output-count claims checked against saved JSON',
                      'six helper speed ratios retained; original runtime table retained',
                      'input contract, baseline interpolation, compiler flags, limitations, and module-design scope retained',
                      'citation keys, cross references, figure files, successful build, and eight-page limit'],
              visual_review='All eight final pages reviewed; no clipped content, overlaps, missing glyphs, or unreadable figure/table labels observed.',
              frozen_protocol_and_normalizer_unchanged=True, experiments_executed=False,
              files={str(p.relative_to(ROOT)): sha(p) for p in [ROOT / 'paper/main.tex', ROOT / 'paper/main.pdf',
                     ROOT / 'paper/main.log', ROOT / 'paper/references.bib', ROOT / 'paper/methods-expansion-build-20261017.log',
                     backup / 'main.tex', backup / 'main.pdf', OUT / 'paper-condensation-20261017.json']},
              evidence_sha256={n: sha(OUT / n) for n in ['confirmatory-summary.json', 'confirmatory-structure.json',
                               'normalization-output-audit.json', 'normalization-matching-results.json', 'normalization-plan.json']},
              rendered_pages=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in rendered],
              scope='Evidence and layout checks for manuscript editing; not an independent scientific review or a proof of semantic equivalence.')
(OUT / 'paper-methods-expansion-20261017.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: report[k] for k in ['status', 'pages', 'within_eight_page_limit']}, ensure_ascii=False))
