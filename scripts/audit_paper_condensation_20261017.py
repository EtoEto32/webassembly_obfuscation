"""Verify the condensed paper and its binding to the audited detailed paper."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/followup-evaluation-20261016'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
texpath = ROOT / 'paper/main.tex'
tex = texpath.read_text(encoding='utf-8')
backup = ROOT / 'paper/revisions/before-eight-page-condensation-20261017'
old = (backup / 'main.tex').read_text(encoding='utf-8')
prior = json.loads((OUT / 'paper-integration-20261017.json').read_text(encoding='utf-8'))
prior['files'] = {k.replace('\\', '/'): v for k, v in prior['files'].items()}
assert prior['status'] == 'manuscript-integrated-and-build-checked'
assert prior['files']['paper/main.tex'] == sha(backup / 'main.tex')
assert prior['files']['paper/main.pdf'] == sha(backup / 'main.pdf')
for name, digest in prior['evidence_sha256'].items():
    assert sha(OUT / name) == digest, name
assert sha(ROOT / 'paper/references.bib') == sha(backup / 'references.bib')
assert sha(ROOT / 'scripts/normalize_wat_local.py') == '01af604b04e54026c9b53c5b70e6cb89ee9e8e2424890c28305b5bd62cad58d9'

def tables(source):
    return {re.search(r'\\label\{([^}]+)\}', block)[1]: block
            for block in re.findall(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', source, re.S)}

current_tables, previous_tables = tables(tex), tables(old)
assert set(current_tables) == {'tab:xmr-runtime', 'tab:followup-performance', 'tab:followup-matching'}
assert all(previous_tables[k] == v for k, v in current_tables.items())
figure = re.search(r'\\begin\{figure\*\}.*?\\end\{figure\*\}', tex, re.S)[0]
assert figure in old
for path in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex):
    assert (ROOT / 'paper' / path).is_file()
labels = re.findall(r'\\label\{([^}]+)\}', tex)
assert len(labels) == len(set(labels))
assert set(re.findall(r'\\(?:ref|pageref)\{([^}]+)\}', tex)) <= set(labels)
bib = (ROOT / 'paper/references.bib').read_text(encoding='utf-8')
assert {k.strip() for g in re.findall(r'\\cite\{([^}]+)\}', tex) for k in g.split(',')} <= set(re.findall(r'@\w+\s*\{\s*([^,\s]+)', bib))
assert tex[:tex.index('\\begin{abstract}')] == old[:old.index('\\begin{abstract}')]
for a, b in [('\\subsection{追加77条件の出力保持と関数対応付け}', '\\subsection{正規化モジュールの適用条件と開発課題}'),
             ('\\subsection{正規化モジュールの適用条件と開発課題}', '\\subsection{限界と再現性}')]:
    original_end = b if b in old else '\\subsection{測定の解釈と限界}'
    assert tex[tex.index(a):tex.index(b)].strip() == old[old.index(a):old.index(original_end)].strip()
for phrase in ['1,179,648', '1,048,576', '0.9077', '1.4692', '1.3857', '0.8438～1.2029',
               '27条件', '81条件', '先頭76バイト', '全272ブロック', 'コンパイルは0件',
               '多重比較調整はしない', '物理CPUの排他的使用ではない',
               '23バイナリ各6反復', '計138回測定', '144条件中21条件', '19,398']:
    assert phrase in tex, phrase
assert tex.index('\\section{RQ2：') < tex.index('\\section{性能評価を踏まえたコード正規化の検討}') < tex.index('\\section{まとめ}')
log = (ROOT / 'paper/main.log').read_text(encoding='utf-8', errors='replace')
assert not re.search(r'Overfull|LaTeX Warning:.*(?:undefined|multiply)|^!', log, re.M)
info = subprocess.check_output(['pdfinfo', str(ROOT / 'paper/main.pdf')]).decode(errors='replace')
pages = int(re.search(r'Pages:\s+(\d+)', info)[1])
assert 1 <= pages <= 8
rendered = sorted((ROOT / 'tmp/pdfs/paper-eight-page-20261017').glob('page-*.png'))
assert len(rendered) == pages
pdftext = (ROOT / 'tmp/pdfs/paper-eight-page-20261017/main.txt').read_text(encoding='utf-8')
assert all(value in pdftext for value in ['0.9077', '1.4692', '536', '参考文献'])
report = dict(status='condensed-paper-verified', date='2026-10-17', pages=pages,
              within_eight_page_limit=True, official_style_unchanged=True,
              previous_detailed_paper_pages=11, detailed_paper_backup=str(backup.relative_to(ROOT)),
              retained_tables_verbatim=list(current_tables), retained_additional_speed_figure_verbatim=True,
              retained_normalization_evaluation_and_development_discussion_verbatim=True,
              evidence_binding='Current tables and normalization text are identical to the numerically audited detailed manuscript; source, PDF, and saved evidence hashes were checked.',
              layout_review='All final pages visually reviewed; no clipped text, overlapping elements, or illegible table/figure labels observed.',
              historical_audits_preserved=True, data_and_normalizer_unchanged=True, wasm_executed=False,
              files={str(p.relative_to(ROOT)): sha(p) for p in [texpath, ROOT / 'paper/main.pdf',
                     ROOT / 'paper/main.log', ROOT / 'paper/eight-page-build-20261017.log',
                     ROOT / 'paper/references.bib', backup / 'main.tex', backup / 'main.pdf',
                     OUT / 'paper-integration-20261017.json']},
              rendered_pages=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in rendered],
              scope='Content retention, evidence binding, compilation, page limit and visual review; not independent scientific or semantic-equivalence verification.')
(OUT / 'paper-condensation-20261017.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: report[k] for k in ['status', 'pages', 'within_eight_page_limit']}, ensure_ascii=False))
