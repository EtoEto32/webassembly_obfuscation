"""Reproduce evidence for authored static judgments; does not auto-label a corpus."""
import csv
import hashlib
import json
import re
import subprocess
from analyze_corpus import ROOT, CACHE, WABT
from measure_rq_validation import OUT, functions, normalized


def main():
    plan=json.loads((ROOT/'experiments/rq-validation-selection.json').read_text(encoding='utf-8'))
    rows=plan['selected']
    findings=json.loads((OUT/'reviewed-controls-initial.json').read_text())
    def row(u,t): return next(r for r in rows if r['program_unit']==u and r['stratum'].endswith(t))
    def details(r):
        folder=ROOT/'results/cases'/r['sha256']; obj=folder/'review-core.wasm'
        if not obj.exists(): obj=ROOT/r['memberships'][0]['object']
        d=subprocess.run([str(WABT/'wasm-objdump.exe'),'-x',str(obj)],capture_output=True,text=True,check=True).stdout
        (folder/'validation-details.txt').write_text(d,encoding='utf-8')
        return d
    for u in ('random.wasm','sumrec.wasm','decimaltohex.wasm'):
        a,b=row(u,'origin'),row(u,'memoryOB'); af,bf=functions(a['sha256']),functions(b['sha256'])
        helpers=sorted(bf)[-2:]
        i=min((i for i in af if any(x['op']=='call' and int(x['args'].split()[0]) in helpers for x in bf[i]['ops'])),key=lambda i:len(bf[i]['ops']))
        d=details(b); c=json.loads((CACHE/(b['sha256']+'.json')).read_text())
        assert '- global[1] i64 mutable=1 - init i64=0' in d
        assert not [x for f in bf.values() for x in f['ops'] if x['op']=='global.set' and x['args']=='1']
        assert not [x for x in c['imports']+c['exports'] if x['kind']==3]
        assert normalized(af[i])[1]==('i32.load','2 56')
        assert ('i32.const','56') in normalized(bf[i])
        findings.append(dict(program=u,origin=a['sha256'],variant=b['sha256'],function_index=i,
            mechanism='memory_access_indirection',evidence=dict(origin=af[i],variant=bf[i],helpers={k:bf[k] for k in helpers},global1='i64 mutable, init 0, no writes/imports/exports'),
            reasoning='Direct offset-56 load becomes helper call with base and offset arguments, followed by i32.wrap_i64. Helpers select address ranges and widths; XOR key remains zero.',
            baseline='XOR and branch tables suggest candidates',refined='helper indirection confirmed; nonzero-key encryption not established',
            limits='Selected access and helpers only; shared runtime functions across these three controls are not independent implementations. Core stripped of custom metadata.'))
    a,b=row('base64-cli.wasm','origin'),row('base64-cli.wasm','callindirect')
    af,bf=functions(a['sha256'])[6],functions(b['sha256'])[6]; d=details(b)
    assert normalized(af)==[('call','708'),('end','')]
    assert normalized(bf)==[('i32.const','709'),('call_indirect','0 (type 1)'),('end','')]
    elem=next(l.strip() for l in d.splitlines() if 'elem[709]' in l)
    assert 'ref.func:708 ' in elem
    findings.append(dict(program='base64-cli.wasm',origin=a['sha256'],variant=b['sha256'],function_index=6,
        mechanism='call_indirection',evidence=dict(origin=af,variant=bf,element=elem),
        reasoning='Direct call708 replaced by constant709 and call_indirect; element709 resolves to func708.',
        baseline='call_indirect present',refined='paired direct-to-indirect conversion confirmed',
        limits='One call site; target is statically recoverable.'))
    # Explicit path witness; local alpha-renaming is checked, not assumed from index.
    a,b=row('seqtk','unobfuscated'),row('seqtk','flatten'); af,bf=functions(a['sha256']),functions(b['sha256']); f=bf[43]
    path=list(range(1,11))+list(range(46,57))+list(range(32,45))
    renaming={9:3,10:4,11:5}
    witness=[]
    for j in path:
        x=f['ops'][j]; op,args=x['op'],x['args']
        if op in ('local.get','local.set','local.tee'): args=str(renaming.get(int(args),int(args)))
        witness.append((op,args))
    matches=[i for i,g in af.items() if normalized(g)[1:-1]==witness]
    assert matches==[11,45],matches
    findings.append(dict(program='seqtk',origin=a['sha256'],variant=b['sha256'],function_index=43,
        mechanism='control_flow_flattening',original_function_candidates=matches,
        evidence=dict(variant=f,original=af[11],execution_path_op_indices=path,local_renaming=renaming),
        reasoning='State at stackbase+8 starts0, dispatches to calloc(1,28), stores result at +12, changes state to1 and returns to dispatcher; state1 restores stack and returns result. Payload path matches original f11 and f45 under local renaming.',
        baseline='loop br_table present',refined='flattened payload correspondence confirmed, unique function identity unresolved',
        limits='Two identical originals prevent unique attribution. Counterpart is not original f43. Static path witness, not general equivalence proof.'))
    a,b=row('needleman_wunsch','unobfuscated'),row('needleman_wunsch','flatten'); f=functions(b['sha256'])[57]
    assert ('br_table','1 0 2') in normalized(f)
    source=ROOT/'data/upstream/source/dataset/utilities/needleman_wunsch/tigress/flatten.sh'
    findings.append(dict(program='needleman_wunsch',origin=a['sha256'],variant=b['sha256'],function_index=57,
        mechanism='flattening_structure_correspondence_unresolved',evidence=dict(variant=f,source=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()),
        reasoning='Stackbase+12 initialized0, dispatch reads it, state0 calls17 with constant95592 and writes1, state1 restores stack and returns. Public build recipe applies Flatten to all functions.',
        baseline='loop br_table present',refined='state-dispatch mechanism observed; exact original function correspondence unresolved',
        limits='Original same-index function is different; build recipe does not prove byte-level provenance. Not included as fully paired confirmation.'))
    for r in rows:
        if r['program_unit']!='unknown_ancestry': continue
        fs=functions(r['sha256']); c=json.loads((CACHE/(r['sha256']+'.json')).read_text())
        candidates=[i for i,f in fs.items() if any(x['op']=='br_table' for x in f['ops'])]
        indices=[min(candidates,key=lambda i:len(fs[i]['ops']))]
        loops=[f['function_index'] for f in c['functions'] if f['br_table_in_loop']]
        if loops: indices.append(min(loops,key=lambda i:len(fs[i]['ops'])))
        evidence=[]
        for i in dict.fromkeys(indices):
            f=fs[i];ops=f['ops'];j=next(j for j,x in enumerate(ops) if x['op']=='br_table')
            evidence.append(dict(function_index=i,header=f['header'],first_table_context=ops[max(0,j-22):j+18],
                disassembly_path=f'results/cases/{r["sha256"]}/disassembly.txt',
                full_function_line_start=ops[0]['line'],full_function_line_end=ops[-1]['line']))
        sha=r['sha256']
        if sha.startswith(('dceaf','fa6e','f181')):
            reasoning='Short function selects argument type via local1-9; loop site selects sign-extended byte with special entries0 and37. Input/type or format parsing is an alternative; state updates alone do not establish obfuscation.'
        elif sha.startswith('d453'):
            reasoning='Short function chooses store width from parameter; loop selector is input byte (load8 or call13) minus46. Numeric/string parsing is an alternative to an inserted dispatcher.'
        elif sha.startswith('c09d'):
            reasoning='Selector sign-extends low16 bits of parameter then subtracts1; no loop br_table. This is compatible with ordinary type-dependent processing.'
        else:
            reasoning='Selector loads a value, subtracts224 and rotates right5 using shifts/or. Branch bodies copy output fields. No loop br_table; algorithm/output-mode selection remains a possible explanation.'
        findings.append(dict(program='unknown_ancestry',sha256=sha,
            datasets=sorted({m['dataset'] for m in r['memberships']}),selected_dataset=r['stratum'].split('/')[0],
            mechanism='unresolved_obfuscation',evidence=evidence,
            baseline='br_table candidate',refined='no confirmed flattening at reviewed sites',reasoning=reasoning,
            pairing='none established',site_selection='shortest branch-table function plus shortest loop-table function where available',
            limits='Selected sites only; neither obfuscation absence nor ordinary whole-module behavior established. Unknown ancestry; similar sites across samples are not independent programs.'))
    bysha={r['sha256']:r for r in rows}
    for index,f in enumerate(findings,1):
        f['finding_id']=f'V{index:02d}'
        f.setdefault('reviewer','Codex static inspection; independent human review pending')
        sha=f.get('variant',f.get('profiled',f.get('sha256')))
        f.setdefault('datasets',sorted({m['dataset'] for m in bysha[sha]['memberships']}))
        f.setdefault('baseline','structural indicator or raw difference is candidate only')
        f.setdefault('refined',f['mechanism'])
    (OUT/'review-ledger.json').write_text(json.dumps(findings,indent=2),encoding='utf-8')
    fields=['finding_id','datasets','program','mechanism','baseline','refined','reviewer']
    with (OUT/'dataset-mechanism-evidence.csv').open('w',newline='',encoding='utf-8-sig') as h:
        w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
        for f in findings:w.writerow({k:';'.join(f[k]) if isinstance(f[k],list) else f[k] for k in fields})
    print(json.dumps({'findings':len(findings),'exploratory_modules':8,'human_review':'pending'}))


if __name__=='__main__':main()
