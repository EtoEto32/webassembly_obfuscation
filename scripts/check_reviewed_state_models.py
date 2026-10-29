"""Read-only interpretation of manually reviewed four-state XOR models.

Graph input is prior analyst evidence, not automatic extraction from arbitrary
Wasm. This checks a bounded behavior abstraction, not executable normalization.
"""
import json
import re
import time
from pathlib import Path
from evaluate_local_normalization import ROOT,sha

SOURCE=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
OUT=ROOT/'results/countermeasures/flattening-xor'


def run_model(review,case):
    graph={row['state']:row for row in review['transitions']}
    assert len(graph)==4
    start=next(state for state,row in graph.items() if row['operation'].startswith('Compare index'))
    bound=int(re.search(r'< (\d+)',graph[start]['operation'])[1])
    assert bound==case['length']
    memory=dict(case['initial']);index=0;state=start;trace=[];states=[]
    for _ in range(256):
        row=graph[state];operation=row['operation'];states.append(state)
        if operation.startswith('Compare index'):
            trace.append('condition');state=row['next_if_true'] if index<bound else row['next_if_false']
        elif operation=='XOR byte and store':
            trace.append('xor-byte');a=case['destination']+index;b=case['source']+index
            memory[a]=memory.get(a,0)^memory.get(b,0);state=row['next']
        elif operation.startswith('Increment index'):
            trace.append('increment');index+=1;state=row['next']
        elif operation=='Return':
            trace.append('return');return memory,trace,states
        else:
            raise ValueError('Unsupported reviewed operation')
    raise ValueError('Model step bound exceeded')


def main():
    cases=json.loads((OUT/'cases.json').read_text(encoding='utf-8'))
    reviews={8:SOURCE/'xmr-helper-flattening-review.json',16:SOURCE/'xmr-helper-path-review.json'}
    models={n:json.loads(path.read_text(encoding='utf-8')) for n,path in reviews.items()}
    start=time.perf_counter();results=[]
    for ordinal,case in enumerate(cases):
        memory,trace,states=run_model(models[case['length']],case)
        expected=dict(case['initial'])
        for index in range(case['length']):
            a=case['destination']+index;b=case['source']+index
            expected[a]=expected.get(a,0)^expected.get(b,0)
        expected_trace=['condition','xor-byte','increment']*case['length']+['condition','return']
        assert memory==expected and trace==expected_trace
        results.append(dict(case=ordinal,length=case['length'],trace=trace,state_trace=states,matched=True))
    report=dict(passed=True,cases=len(cases),records=results,model_elapsed_ms=(time.perf_counter()-start)*1000,
                review_sources=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in reviews.values()],
                cases_sha256=sha(OUT/'cases.json'),evaluator_sha256=sha(Path(__file__)),
                scope='Manually reviewed state graphs have the same role trace and sequential XOR effect as the ordinary loop model. This is not automatic recovery, dynamic instrumentation or all-input/full-module proof.',
                binary_rewritten=False,mining_executed=False,
                limitations=['Review graph selection supplies semantic operation labels; unsuitable as an automatic detector evaluation.',
                             'Temporary stack writes differ and are outside this abstract model.',
                             'State machines and XOR also occur in ordinary code; correspondence is not proof of maliciousness.',
                             'No cryptonight hash call path, timing, JIT or detector improvement measured.'])
    (OUT/'state-model-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,cases=len(cases),trace_steps={n:3*n+2 for n in models},automatic_recovery=False)))


if __name__=='__main__':
    main()
