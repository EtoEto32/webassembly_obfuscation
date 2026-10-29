"""Check manuscript integration against saved evidence, without running Wasm."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/followup-evaluation-20261016'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
tex = (ROOT / 'paper/main.tex').read_text(encoding='utf-8')
prior = ROOT / 'paper/revisions/before-followup-integration-20261017'
old = (prior / 'main.tex').read_text(encoding='utf-8')
bib = (ROOT / 'paper/references.bib').read_text(encoding='utf-8')
labels = re.findall(r'\\label\{([^}]+)\}', tex)
assert len(labels) == len(set(labels))
assert set(re.findall(r'\\(?:ref|pageref)\{([^}]+)\}', tex)) <= set(labels)
keys = set(re.findall(r'@\w+\s*\{\s*([^,\s]+)', bib))
assert {k.strip() for group in re.findall(r'\\cite\{([^}]+)\}', tex) for k in group.split(',')} <= keys
assert sha(ROOT / 'paper/references.bib') == sha(prior / 'references.bib')
assert '\\item[RQ1]' in tex and '\\item[RQ2]' in tex

def tables(source):
    return {re.search(r'\\label\{([^}]+)\}', block)[1]: block
            for block in re.findall(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', source, re.S)}

old_tables, new_tables = tables(old), tables(tex)
assert len(old_tables) == 4
assert all(new_tables[k] == v for k, v in old_tables.items())
figures = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex)
assert set(re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', old)) <= set(figures)
assert all((ROOT / 'paper' / path).is_file() for path in figures)
assert sha(ROOT / 'scripts/normalize_wat_local.py') == '01af604b04e54026c9b53c5b70e6cb89ee9e8e2424890c28305b5bd62cad58d9'

perf = load(OUT / 'confirmatory-summary.json')
structure = {r['id']: r for r in load(OUT / 'confirmatory-structure.json')['records']}
assert perf['timed_blocks'] == 272 and perf['paired_contrasts'] == 108
speed = {(r['artifact_id'], r['mode']): r for r in perf['summaries']}
assert len(speed) == 18 and all(r['repetitions'] == 6 for r in speed.values())
for family, baseline in [('swamped', 'swamped-baseline'), ('xmr-wasm', 'xmr-wasm-baseline'),
                         ('webminerpoolhashcn', 'webminerpoolhashcn-baseline')]:
    for transform in ['nop', 'constsplit']:
        artifact = f'{family}-{transform}'
        values = [structure[artifact]['instruction_count'] / structure[baseline]['instruction_count']]
        values += [speed[artifact, mode]['geometric_mean_ratio'] for mode in ['liftoff', 'turbofan']]
        assert ' & '.join(f'{v:.4f}' for v in values) in new_tables['tab:followup-performance']
for artifact in ['restore-xor8', 'restore-xor16', 'restore-both']:
    for mode in ['liftoff', 'turbofan']:
        assert f"{speed[artifact, mode]['geometric_mean_ratio']:.4f}" in tex

normal = load(OUT / 'normalization-output-audit.json')
assert (normal['labels'], normal['unique_sha256'], normal['output_checks'],
        normal['public_expected_checks'], normal['reference_derived_checks']) == (77, 42, 2793, 945, 1848)
assert '2,793' in tex and '1,848' in tex and '公表945' in tex
matching = load(OUT / 'normalization-matching-results.json')
for row in matching['summaries']:
    assert row['fixed_function_queries'] == 644
    o = row['outcomes']
    values = [o.get(k, 0) for k in ['correct_unique', 'ambiguous_with_correct', 'unmatched', 'query_origin_not_retained']]
    assert sum(values) == 644, row['method']
    assert ' & '.join(str(v) for v in values) in new_tables['tab:followup-matching']
assert '計138回測定' in tex and '19,398' in tex and '144条件中21条件' in tex
assert '26.55--32.08' in tex and '固定76バイト読出しと残存末尾' in tex

log = (ROOT / 'paper/main.log').read_text(encoding='utf-8', errors='replace')
assert not re.search(r'Overfull|LaTeX Warning:.*(?:undefined|multiply)|^!', log, re.M)
info = subprocess.check_output(['pdfinfo', str(ROOT / 'paper/main.pdf')]).decode(errors='replace')
pages = int(re.search(r'Pages:\s+(\d+)', info)[1])
assert pages == 11
pdftext = (ROOT / 'tmp/pdfs/paper-followup-20261017/main.txt').read_text(encoding='utf-8')
assert len(pdftext.split('\f')) >= pages and '0.9077' in pdftext and '536' in pdftext
rendered = sorted((ROOT / 'tmp/pdfs/paper-followup-20261017').glob('page-*.png'))
assert len(rendered) == pages

evidence = ['confirmatory-summary.json', 'confirmatory-structure.json',
            'normalization-output-audit.json', 'normalization-matching-results.json',
            'input-audit.json', 'callsite-summary.json', 'completion-audit.json']
report = dict(
    status='manuscript-integrated-and-build-checked', date='2026-10-17',
    pages=pages, submission_page_range=[6, 8], within_submission_page_range=False,
    submission_status='Expanded manuscript; shortening is still required for the previous submission limit.',
    inherited_tables_preserved_verbatim=list(old_tables),
    inherited_figures_preserved=True, bibliography_unchanged=True,
    normalizer_unchanged=True, experiments_rerun=False,
    checks=['citation keys, unique labels, references and figure files',
            'all six new performance rows and six helper speed ratios against saved JSON',
            'all seven matching rows and 77-condition output counts against saved JSON',
            'all four preceding tables preserved verbatim and original figures retained',
            'successful pLaTeX/pBibTeX/dvipdfmx build; no undefined references or overfull boxes'],
    visual_review=dict(status='all-11-pages-reviewed',
                       findings='No clipped figures or tables, overlaps, missing glyphs, or broken captions observed.',
                       rendered_pages=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in rendered]),
    files={str(p.relative_to(ROOT)): sha(p) for p in [ROOT / 'paper/main.tex', ROOT / 'paper/main.pdf',
           ROOT / 'paper/main.log', ROOT / 'paper/references.bib', ROOT / 'paper/followup-integration-build-20261017.log',
           prior / 'main.tex', prior / 'main.pdf', prior / 'references.bib']},
    evidence_sha256={name: sha(OUT / name) for name in evidence},
    historical_audits='Previous compilation and goal audits remain records for the manuscript at their recorded time; they were not overwritten.',
    scope='Selected numeric and preservation checks plus layout review; no new semantic-equivalence proof, independent scientific review, or detector-performance claim.')
(OUT / 'paper-integration-20261017.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: report[k] for k in ['status', 'pages', 'within_submission_page_range', 'inherited_tables_preserved_verbatim']}, ensure_ascii=False))
