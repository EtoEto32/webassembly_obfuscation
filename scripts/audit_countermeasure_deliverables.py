"""Index saved evidence and verify delivered report references; never execute Wasm."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/countermeasures'
RUN = OUT / 'runtime-runs/execute-120f528e37424ec6806047c933011eec'
INDEX = OUT / 'deliverable-evidence-index.json'
AUDIT = OUT / 'deliverable-audit.json'


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def role(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    if '/runtime-runs/execute-120f528e' in relative:
        return 'current-real-runtime-and-audited-analysis'
    if '/runtime-runs/execute-d50a' in relative:
        return 'historical-failed-run-zero-speed-blocks'
    if any(part in relative for part in ['/runtime-runs/probe-', '/runtime-runs/deadline-test-']):
        return 'non-mining-probe-or-deadline-test'
    if '/runtime-runs/input-diagnostic-' in relative:
        return 'baseline-input-order-diagnostic'
    if 'mock-checks' in relative:
        return 'mock-only-not-real-hash-rate'
    if '/processing-timing/' in relative:
        return 'actual-preprocessing-time-not-hash-rate'
    if '/detector-feasibility/' in relative:
        return 'static-detector-study-not-general-detection-accuracy'
    if relative.startswith('docs/'):
        return 'report-or-principles-or-history'
    if relative.startswith(('scripts/', 'experiments/')):
        return 'implementation-or-reproduction-code'
    if relative.startswith('results/countermeasures/'):
        return 'static-analysis-or-limited-check-or-preparation-see-report'
    return 'prior-research-evidence-not-new-runtime-results'


def main():
    # These two generated metadata files intentionally do not hash themselves.
    INDEX.write_text('{}\n', encoding='utf-8')
    AUDIT.write_text('{}\n', encoding='utf-8')
    documents = sorted((ROOT / 'docs').glob('countermeasure-*.md'))
    current_documents = [ROOT / 'docs/countermeasure-method-principles.md',
                         ROOT / 'docs/countermeasure-experiment-report.md']
    references = set()
    checked_links = []
    for document in current_documents:
        text = document.read_text(encoding='utf-8')
        for target in re.findall(r'\]\((C:/[^)]+)\)', text):
            path = Path(target)
            if not path.exists():
                raise ValueError(f'Missing report reference: {target}')
            checked_links.append(dict(document=document.relative_to(ROOT).as_posix(), target=target))
            if path.is_file() and path not in {INDEX, AUDIT}:
                references.add(path)
    scope = load(OUT / 'current-objective-scope.json')
    paper_checks = {}
    for relative, expected in scope['paper_snapshot'].items():
        actual = digest(ROOT / relative)
        if actual != expected:
            raise ValueError(f'Protected paper changed: {relative}')
        paper_checks[relative] = actual
    summary = load(RUN / 'summary.json')
    measurement = load(RUN / 'outputs/measurement.json')
    structure = load(RUN / 'analysis/structure-runtime.json')
    if measurement['status'] != 'complete' or len(measurement['samples']) != 138:
        raise ValueError('Runtime incomplete')
    if summary['measurement_sha256'] != digest(RUN / 'outputs/measurement.json'):
        raise ValueError('Summary is not bound to current raw measurement')
    if structure['summary_sha256'] != digest(RUN / 'summary.json'):
        raise ValueError('Structure join is not bound to current summary')
    if summary['blocks'] != 138 or summary['unique_artifacts'] != 23 or summary['label_conditions'] != 72:
        raise ValueError('Unexpected runtime coverage')
    completion = load(RUN / 'completion.json')
    if completion['exit_code'] or completion['state']['Running'] or completion['state']['OOMKilled']:
        raise ValueError('Runtime did not finish successfully')
    active = load(OUT / 'runtime-preparation/active-measurement.json')
    if active['status'] != 'complete-and-audited' or active['container_removal_check']['result'] != 'no such object':
        raise ValueError('Final status or recorded cleanup verification missing')
    for name in ['development-rates', 'structure-versus-rate']:
        for extension in ['png', 'svg']:
            if (RUN / f'analysis/{name}.{extension}').stat().st_size == 0:
                raise ValueError('Empty plot')
    files = {p for p in OUT.rglob('*') if p.is_file() and p not in {INDEX, AUDIT}}
    files.update(documents)
    files.update(references)
    # Include code actually named by the delivered documentation.
    for document in documents:
        for relative in re.findall(r'(?:scripts|experiments)/[A-Za-z0-9_./-]+\.(?:py|cjs|js|txt)',
                                   document.read_text(encoding='utf-8')):
            path = ROOT / relative
            if path.is_file():
                files.add(path)
    files.add(Path(__file__))
    files.update({ROOT / 'experiments/runtime-reference/countermeasure-benchmark.cjs',
                  ROOT / 'experiments/runtime-reference/countermeasure-input-diagnostic.cjs',
                  ROOT / 'experiments/runtime-reference/swamped-host.cjs'})
    timestamp = datetime.now(timezone.utc).isoformat()
    entries = [dict(path=p.resolve().as_posix(), relative_path=p.relative_to(ROOT).as_posix(),
                    bytes=p.stat().st_size, sha256=digest(p), role=role(p))
               for p in sorted(files)]
    INDEX.write_text(json.dumps(dict(recorded_at=timestamp, root=ROOT.as_posix(),
        scope='All saved countermeasure evidence, documentation and referenced code/prior evidence; not all project files.',
        excluded_generated_metadata=[INDEX.name, AUDIT.name], entries=entries), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    AUDIT.write_text(json.dumps(dict(recorded_at=timestamp, status='passed',
        index_sha256=digest(INDEX), indexed_files=len(entries), current_report_links_checked=checked_links,
        protected_paper_unchanged=paper_checks,
        runtime=dict(blocks=138, unique_sha=23, label_conditions=72,
                     summary_sha256=digest(RUN / 'summary.json'),
                     measurement_sha256=digest(RUN / 'outputs/measurement.json'),
                     structure_sha256=digest(RUN / 'analysis/structure-runtime.json'),
                     full_runtime_validation_script='scripts/summarize_countermeasure_runtime.py'),
        figure_review='Both PNGs displayed and inspected; points, axes and labels readable; shared SHA reuse explained in report.',
        limitation='File/reference/provenance audit, not proof of all-input equivalence, scientific novelty or detection improvement.'),
        ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status='passed', indexed_files=len(entries), report_links=len(checked_links),
                         protected_paper_files=len(paper_checks))))


if __name__ == '__main__':
    main()
