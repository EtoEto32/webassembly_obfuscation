"""Resolve numeric function types in static artifacts; no module execution.

This audit covers imported/exported function signatures, not memory contents,
trap behavior, table elements, host semantics or whole-module equivalence.
"""
import json
from pathlib import Path
from analyze_corpus import Reader,interfaces
from audit_corpora import sections
from evaluate_local_normalization import ROOT,sha

TYPES={0x7f:'i32',0x7e:'i64',0x7d:'f32',0x7c:'f64',0x7b:'v128',0x70:'funcref',0x6f:'externref'}


def signatures(path):
    parsed=sections(path.read_bytes());types=[];defined=[]
    for sec in parsed:
        if sec['id'] not in [1,3]:
            continue
        r=Reader(sec['payload']);n=r.uint()
        if sec['id']==1:
            for _ in range(n):
                if r.byte()!=0x60:
                    raise ValueError('Unsupported GC/recursive type')
                params=[TYPES[r.byte()] for _ in range(r.uint())]
                results=[TYPES[r.byte()] for _ in range(r.uint())]
                types.append(dict(params=params,results=results))
        else:
            defined=[r.uint() for _ in range(n)]
        assert r.pos==len(r.data)
    api=interfaces(parsed)
    imported=[item for item in api['imports'] if item['kind']==0]
    function_types=[item['type_index'] for item in imported]+defined
    return dict(imported_functions=[dict(module=item['module'],name=item['name'],**types[item['type_index']]) for item in imported],
                exported_functions=[dict(name=item['name'],**types[function_types[item['index']]]) for item in api['exports'] if item['kind']==0],
                import_names_kinds=[(item['module'],item['name'],item['kind']) for item in api['imports']],
                export_names_kinds=[(item['name'],item['kind']) for item in api['exports']])


def main():
    records=[];cache={}
    for directory,filename in [('local-normalization','static-comparison.json'),('transfer','comparison.json'),('seeded-normalization','comparison.json')]:
        comparison=ROOT/'results/countermeasures'/directory/filename
        rows=json.loads(comparison.read_text(encoding='utf-8'))['records']
        for row in rows:
            source=next(r for r in rows if r['source']==row['source'] and r['variant']=='unmodified')
            values=[]
            for item in [source,row]:
                path=ROOT/item['path'];digest=sha(path)
                assert digest==item['sha256']
                if digest not in cache:
                    cache[digest]=signatures(path)
                values.append(cache[digest])
            a,b=values
            canonical=lambda items:sorted(json.dumps(item,sort_keys=True) for item in items)
            records.append(dict(group=directory,source=row['source'],variant=row['variant'],sha256=row['sha256'],
                                function_signatures_equal=canonical(a['imported_functions'])==canonical(b['imported_functions']) and canonical(a['exported_functions'])==canonical(b['exported_functions']),
                                exported_function_signatures_equal=canonical(a['exported_functions'])==canonical(b['exported_functions']),
                                ordered_function_records_equal=a['imported_functions']==b['imported_functions'] and a['exported_functions']==b['exported_functions'],
                                interface_names_kinds_equal=canonical(a['import_names_kinds'])==canonical(b['import_names_kinds']) and canonical(a['export_names_kinds'])==canonical(b['export_names_kinds']),
                                removed_imported_function_signatures=[json.loads(x) for x in sorted(set(canonical(a['imported_functions']))-set(canonical(b['imported_functions'])))],
                                original=a,processed=b))
    report=dict(records=records,evaluator_sha256=sha(Path(__file__)),runtime_executed=False,
                scope='Resolve function signatures through Type, Import, Function and Export sections; compare multisets independent of index/order, retaining duplicate multiplicity. Compare names/kinds for all interfaces. Does not check nonfunction resource types/limits, table elements, host behavior or whole-module semantics.')
    out=ROOT/'results/countermeasures/interface-signature-audit.json'
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=len(records),function_signature_mismatches=sum(not r['function_signatures_equal'] for r in records),names_kinds_mismatches=sum(not r['interface_names_kinds_equal'] for r in records))))


if __name__=='__main__':
    main()
