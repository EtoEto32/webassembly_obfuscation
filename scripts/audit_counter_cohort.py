"""Directly measure increment motifs in the 124 exact-body-positive modules.

This is a selected-cohort audit, not an exhaustive instrumentation detector.
"""
import concurrent.futures
import csv
import hashlib
import json
import subprocess
from analyze_corpus import ROOT, CACHE, WABT, FUNC, OP
from analyze_malware_sensitivity import OUT, reference_counter_bodies


def audit(row):
    sha=row['sha256'];raw=(CACHE/(sha+'.json')).read_bytes();data=json.loads(raw)
    result={'sha256':sha,'author_label':row['author_label'],'status':'pending',
            'exact_body_sequences':int(row['counter_reference_sequences']),
            'instruction_count':data['instruction_count'],'cache_sha256':hashlib.sha256(raw).hexdigest()}
    try:
        obj=ROOT/data['object']
        if hashlib.sha256(obj.read_bytes()).hexdigest()!=sha:raise ValueError('object SHA mismatch')
        if data.get('disassembly_input','original')!='original':raise ValueError('nonoriginal disassembly input unsupported in this audit')
        case=ROOT/'results/cases'/sha/'disassembly.txt'
        if case.exists():dis=case.read_bytes()
        else:dis=subprocess.run([str(WABT/'wasm-objdump.exe'),'-d',str(obj)],capture_output=True,check=True,timeout=120).stdout
        text=dis.decode('utf-8');_,sites=reference_counter_bodies(data,text)
        functions={};current=None
        for line in text.splitlines():
            fm=FUNC.match(line.strip())
            if fm:current=int(fm[2]);functions[current]=[];continue
            m=OP.match(line)
            if m and m[2]!='local':functions[current].append((m[2],m[3].strip().split(' <')[0]))
        # A narrow supporting check: named low-word getters must actually
        # retrieve the expected global, and reset must zero all five globals.
        exports={e['name']:e['index'] for e in data['exports'] if e['kind']==0}
        getters={}
        for op,g in zip(('Add','And','Shl','Shru','Xor'),range(11,16)):
            name=f'_getI32{op}CountLo';index=exports.get(name)
            getters[name]=functions.get(index)==[('global.get',str(g)),('i32.wrap_i64',''),('return',''),('end','')]
        exceptions={name:{'function_index':exports.get(name),'instructions':functions.get(exports.get(name))}
                    for name,matched in getters.items() if not matched}
        reset=[entry for g in range(11,16) for entry in [('i64.const','0'),('global.set',str(g))]]+[('end','')]
        reset_verified=functions.get(exports.get('_resetInstCounters'))==reset
        n=sum(map(len,sites.values()))
        if n<result['exact_body_sequences']:raise ValueError('direct motif count below exact-body lower bound')
        result.update(status='ok',disassembly_sha256=hashlib.sha256(dis).hexdigest(),
                      direct_motif_sequences=n,direct_motif_instructions=4*n,
                      direct_motif_instruction_share=4*n/data['instruction_count'],
                      functions_with_motif=len(sites),five_named_low_getters_match=all(getters.values()),
                      named_reset_zeros_five_globals=reset_verified,
                      counter_support_checks_json=json.dumps(getters),
                      counter_support_exceptions_json=json.dumps(exceptions),
                      example_sites_json=json.dumps([{'function_index':i,**s} for i,ss in sites.items() for s in ss[:1]][:10]))
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        result.update(status='audit_failed',error=str(exc))
    return result


def main():
    input_path=OUT/'wasmmal-module-audit.csv'
    rows=[r for r in csv.DictReader(input_path.open(encoding='utf-8',newline='')) if r['counter_reference_body_present']=='True']
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(audit,rows))
    with (OUT/'counter-cohort-direct.csv').open('w',encoding='utf-8',newline='') as dst:
        writer=csv.DictWriter(dst,fieldnames=list(dict.fromkeys(k for r in results for k in r)))
        writer.writeheader();writer.writerows(results)
    summary={'input_sha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),
             'selected_modules':len(rows),'successful_audits':sum(r['status']=='ok' for r in results),
             'selection':'Every successful WasmMal module with a byte-identical function containing the reviewed increment motif.',
             'motif':'global.get g; i64.const 1; i64.add; global.set g, g in 11..15',
             'limits':['Does not search modules without an exact reference body.',
                       'Static instruction share, not runtime or size overhead.',
                       'Named getter/reset checks support interpretation but do not prove provenance or exclude other obfuscation.']}
    (OUT/'counter-cohort-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
