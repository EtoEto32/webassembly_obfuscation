"""Check evidence coverage and document references; judgments remain reviewable."""
import hashlib
import json
import re
from analyze_corpus import ROOT
from measure_rq_validation import OUT, functions, increments


def main():
    plan=json.loads((ROOT/'experiments/rq-validation-selection.json').read_text())
    ledger=json.loads((OUT/'review-ledger.json').read_text())
    covered=set()
    for f in ledger:
        covered.update(f[k] for k in ('sha256','origin','variant','profiled') if k in f)
        assert f['reasoning'] and f['evidence'] if 'evidence' in f else f['reasoning'] and f['changed_symbols']
        assert 'pending' in f['reviewer']
    assert covered=={r['sha256'] for r in plan['selected']}
    # Failure analysis of copying the pilot's fixed global numbers.
    fixed_index=[]
    for r in plan['selected']:
        if r['stratum']!='seismic_nonmining/profiled':continue
        hits=[h for f in functions(r['sha256']).values() for h in increments(f)]
        fixed=sum(h['global_index'] in {'11','12','13','14','15'} for h in hits)
        assert fixed==0
        fixed_index.append(dict(program=r['program_unit'],actual_increment_sites=len(hits),
            pilot_global_numbers_matches=fixed,scope='Hypothetical fixed-index shortcut; not performance of a deployed classifier'))
    (OUT/'fixed-index-failure-analysis.json').write_text(json.dumps(fixed_index,indent=2))
    text=(ROOT/'paper/main.tex').read_text(encoding='utf-8')
    bib=(ROOT/'paper/references.bib').read_text(encoding='utf-8')
    stack=[]
    for kind,env in re.findall(r'\\(begin|end)\{([^}]+)\}',text):
        if kind=='begin':stack.append(env)
        else:assert stack and stack.pop()==env,(kind,env)
    assert not stack
    labels=re.findall(r'\\label\{([^}]+)\}',text)
    assert len(labels)==len(set(labels))
    assert set(re.findall(r'\\ref\{([^}]+)\}',text))<=set(labels)
    for group in re.findall(r'\\cite\{([^}]+)\}',text):
        for key in group.split(','):assert re.search(r'@\w+\s*\{\s*'+re.escape(key)+',',bib),key
    assert 'RQ3' not in text
    for token in ('2,756','8,526','147','756','709','708','28','20261009'):
        assert token in text,token
    checks={
        'input_and_selection':'28 verified SHA-256, disjoint from pilot35; program control/exploratory distinction recorded',
        'rq1':'V01-V04 instrumentation/ordinary/flattening contrasts; V08-V10 XOR-key checks; fixed-index failure analysis',
        'rq2':'V04-V13 transformed controls, V14-V21 exploratory corpus reviews with unresolved outcomes',
        'reproducibility':'selection + input verification + smoke + mechanical comparisons + reviewed ledger and source scripts',
        'paper':'abstract/methods/RQ1/RQ2/table/discussion/limitations/conclusion integrated',
        'human_review':'explicitly pending; evidence records are provided, not independent human validation',
        'scope':'no crawling, execution of specimens, detector retraining or speed measurements',
        'compilation':'builtin compiler result must be saved separately; source-reference check is not compilation'}
    result=dict(status='evidence_coverage_checked',covered_modules=len(covered),findings=len(ledger),
        paper_sha256=hashlib.sha256((ROOT/'paper/main.tex').read_bytes()).hexdigest(),requirements=checks)
    (OUT/'completion-audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))


if __name__=='__main__':main()
