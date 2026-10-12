"""Verify frozen inputs and save narrowly scoped, reviewed evidence excerpts."""
import hashlib
import json
from analyze_corpus import ROOT
from measure_rq_validation import OUT, functions, normalized, increments, strip_increments


def main():
    plan=json.loads((ROOT/'experiments/rq-validation-selection.json').read_text(encoding='utf-8'))
    rows=plan['selected']; prior=set(plan['prior_review_sha256'])
    assert len(rows)==len({r['sha256'] for r in rows})==28
    assert not prior.intersection(r['sha256'] for r in rows)
    for r in rows:
        obj=ROOT/r['memberships'][0]['object']
        assert hashlib.sha256(obj.read_bytes()).hexdigest()==r['sha256']
    def row(program,role):
        return next(r for r in rows if r['program_unit']==program and r['stratum'].endswith(role))
    findings=[]
    for program in ('A-Star','CreaturePack'):
        a,b=row(program,'original'),row(program,'profiled')
        af,bf=functions(a['sha256']),functions(b['sha256'])
        assert all(i in bf and normalized(f)==normalized(strip_increments(bf[i])) for i,f in af.items())
        extras={i:f for i,f in bf.items() if i not in af}
        assert len(extras)==11
        reset=max(extras)
        assert sum(x['op']=='global.set' for x in extras[reset]['ops'])==5
        findings.append(dict(program=program,origin=a['sha256'],variant=b['sha256'],
            datasets=sorted({m['dataset'] for m in b['memberships']}),
            mechanism='research_instrumentation',unit='paired original defined functions and appended interface',
            evidence=dict(original_defined_functions=len(af),
                restored_decoded_functions=len(af),increment_sites=sum(len(increments(f)) for f in bf.values()),
                added_functions=[dict(index=i,**f) for i,f in extras.items()]),
            reasoning='Removing matched unit-increment quadruples restores every original function; ten readout functions and a five-global reset are appended.',
            limits='Decoded instruction equality only; no execution or whole-module equivalence. Public CoinHive script has analogous mechanism but different global indices.',
            reviewer='Codex static inspection; independent human review pending'))
    # Short ordinary-processing counterexample selected during exploratory site review.
    r=row('CreaturePack','original'); f=functions(r['sha256'])[400]
    assert ('i32.const','74') in normalized(f)
    assert not any(x['op'] in ('loop','local.set','global.set') for x in f['ops'])
    findings.append(dict(program='CreaturePack',sha256=r['sha256'],function_index=400,
        mechanism='ordinary_numeric_base_selection',evidence=f,
        reasoning='Selector is argument-address load at offset 4 AND 74. Branches return 8,16,0,10; no state write or loop. Symbol names num_get_base/get_base support interpretation.',
        scope='This function only, not absence of obfuscation elsewhere.',
        site_selection='Exploratory inspection of short branch-table functions, not random function sampling.',
        reviewer='Codex static inspection; independent human review pending'))
    a,b=row('base64-cli.wasm','origin'),row('base64-cli.wasm','flatten')
    af,bf=functions(a['sha256'])[515],functions(b['sha256'])[515]
    original=normalized(af)[:-1]
    changed=normalized(bf)
    start=changed.index(original[0],changed.index(('br_table','0 1 0')))
    assert changed[start:start+len(original)]==original
    assert ('local.set','3') in changed and ('br','1') in changed
    findings.append(dict(program='base64-cli.wasm',origin=a['sha256'],variant=b['sha256'],function_index=515,
        mechanism='control_flow_flattening',evidence=dict(origin=af,variant=bf),
        reasoning='Original three stores survive as a contiguous sequence. State local3 initialized 0 dispatches to that sequence, is updated to 1, branches back to loop, then exits via second dispatch arm.',
        site_selection='Shortest transformed branch-table function lacking br_table at same original index; matching mangled name and retained operations checked.',
        limits='One function; transformation adds dispatch even though original body has no branch. No claim of measurable analysis difficulty.',
        reviewer='Codex static inspection; independent human review pending'))
    for program in ('random.wasm','sumrec.wasm','decimaltohex.wasm'):
        a,b=row(program,'origin'),row(program,'nameOB')
        af,bf=functions(a['sha256']),functions(b['sha256'])
        assert af.keys()==bf.keys()
        assert all(normalized(af[i])==normalized(bf[i]) for i in af)
        # Compare symbol text rather than binary offsets.
        symbols=[dict(index=i,origin=af[i]['header'],variant=bf[i]['header']) for i in af
                 if af[i]['header'].split('func[',1)[1]!=bf[i]['header'].split('func[',1)[1]]
        assert symbols
        findings.append(dict(program=program,origin=a['sha256'],variant=b['sha256'],
            mechanism='renaming',decoded_functions_equal=len(af),changed_symbols=symbols,
            reasoning='Decoded instructions, numeric operands and local declarations match at every function index; symbol annotations differ.',
            limits='Does not establish whole-module semantic equivalence; raw byte differences alone were not used.',
            reviewer='Codex static inspection; independent human review pending'))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'reviewed-controls-initial.json').write_text(json.dumps(findings,indent=2),encoding='utf-8')
    (OUT/'input-verification.json').write_text(json.dumps(dict(verified_objects=len(rows),
        prior_exact_overlap=0,scope='SHA disjointness does not prove unknown-parent corpus independence',
        controls_verified=len(findings)),indent=2),encoding='utf-8')
    print(json.dumps(dict(verified_objects=len(rows),reviewed_findings=len(findings))))


if __name__=='__main__': main()
