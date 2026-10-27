"""Freeze three bounded correctness batches using the unchanged checked host."""
import json
from pathlib import Path
from evaluate_followup_normalization import ROOT,OUT,sha,read_plan


def main():
    target=OUT/'normalization-check-plans.json';assert not target.exists()
    pp,protocol=read_plan();sp=OUT/'normalization-static.json';static=json.loads(sp.read_text(encoding='utf-8'))
    assert static['status']=='static-validation-complete' and len(static['records'])==77 and static['plan_sha256']==sha(pp)
    base=json.loads((OUT/'controlled-check-plan.json').read_text(encoding='utf-8'));plans=[]
    for family,wanted in protocol['batches'].items():
        plan=json.loads(json.dumps(base));rows=[r for r in static['records'] if r['family']==family];assert len(rows)==wanted
        needed={'host-original.cjs','glue-loader.cjs','webminerpoolhashcn.wasm','webminerpoolhashcn.js','controlled.cjs'}
        if family=='xmr-wasm':needed.add('xmr-wasm.js')
        plan['assets']=[a for a in plan['assets'] if a['name'] in needed];assert {a['name'] for a in plan['assets']}==needed
        cases=[]
        for row in rows:
            assert sha(ROOT/row['path'])==row['sha256']
            identifier=row['input_id']+'--'+row['method'];name=identifier+'.wasm'
            plan['assets'].append(dict(name=name,path=row['path'],sha256=row['sha256']))
            cases.append(dict(id=identifier,family=family,file=name,sha256=row['sha256'],
                glue=family+'.js' if family!='swamped' else None))
        plan['controlled'].update(artifacts=cases,normalization_applied=True,
            normalization_plan_sha256=sha(pp),static_result_sha256=sha(sp),
            scope='Finite normalized-output checks; original host and public/reference-derived inputs retained. No throughput evaluation.')
        plan['maximum_wall_seconds']=900
        path=OUT/('normalization-check-'+family+'-plan.json');assert not path.exists()
        path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        plans.append(dict(family=family,path=str(path.relative_to(ROOT)).replace('\\','/'),sha256=sha(path),labels=len(cases)))
    target.write_text(json.dumps(dict(plans=plans,labels=77,unique_sha256=static['unique_output_sha256'],
        frozen_before_execution=True,runner='Unchanged followup-controlled-check.cjs; new plans carry normalized artifacts.',
        no_independent_success_inflation=True),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(plans=plans,labels=77),indent=2))


if __name__=='__main__':main()
