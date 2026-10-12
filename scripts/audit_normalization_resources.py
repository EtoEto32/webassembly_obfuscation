"""Static resource-type audit. No Wasm instantiation or mining execution.

Supports core32 memory/table limits and simple global constant expressions.
Unsupported encodings fail closed; this is not a general Wasm validator.
"""
import json
from pathlib import Path
from analyze_corpus import Reader
from audit_corpora import sections
from audit_normalization_signatures import TYPES
from evaluate_local_normalization import ROOT, sha


def limits(r):
    flags = r.uint()
    if flags not in (0, 1, 3):
        raise ValueError('Unsupported limits flags (including memory64/table64)')
    minimum = r.uint()
    maximum = r.uint() if flags & 1 else None
    if maximum is not None and maximum < minimum:
        raise ValueError('Invalid limits')
    return dict(minimum=minimum, maximum=maximum, shared=bool(flags & 2))


def resource_type(r, kind):
    if kind == 1:
        element = r.byte()
        if element not in (0x70, 0x6f):
            raise ValueError('Unsupported table reference type')
        value = limits(r)
        if value['shared']:
            raise ValueError('Unsupported shared table')
        return dict(element_type=TYPES[element], **value)
    if kind == 2:
        return limits(r)
    if kind == 3:
        value = TYPES[r.byte()]
        mutable = r.byte()
        if mutable not in (0, 1):
            raise ValueError('Invalid global mutability')
        return dict(value_type=value, mutable=bool(mutable))
    raise ValueError('Unsupported resource kind')


def skip_initializer(r):
    # Only skip encodings whose immediate length is known. Never scan for 0x0b.
    while True:
        op = r.byte()
        if op == 0x0b:
            return
        if op in (0x41, 0x42, 0x23, 0xd2, 0xd0):
            r.leb()
        elif op in (0x43, 0x44):
            for _ in range(4 if op == 0x43 else 8):
                r.byte()
        else:
            raise ValueError(f'Unsupported initializer opcode {op:#x}')


def resources(data):
    imported = []
    defined = {1: [], 2: [], 3: []}
    exports = []
    for sec in sections(data):
        ident = sec['id']
        if ident not in (2, 4, 5, 6, 7):
            continue
        r = Reader(sec['payload'])
        for _ in range(r.uint()):
            if ident == 2:
                module, name, kind = r.text(), r.text(), r.byte()
                if kind == 0:
                    r.uint()
                elif kind in (1, 2, 3):
                    imported.append(dict(module=module, name=name, kind=kind,
                                         type=resource_type(r, kind)))
                else:
                    raise ValueError('Unsupported import kind')
            elif ident == 7:
                exports.append(dict(name=r.text(), kind=r.byte(), index=r.uint()))
            else:
                kind = {4: 1, 5: 2, 6: 3}[ident]
                defined[kind].append(resource_type(r, kind))
                if kind == 3:
                    skip_initializer(r)
        if r.pos != len(r.data):
            raise ValueError('Section not completely consumed')
    exported = []
    for item in exports:
        kind = item['kind']
        if kind == 0:
            continue
        if kind not in defined:
            raise ValueError('Unsupported export kind')
        types = [x['type'] for x in imported if x['kind'] == kind] + defined[kind]
        exported.append(dict(name=item['name'], kind=kind, type=types[item['index']]))
    return dict(imported_resources=imported, exported_resources=exported,
                defined_resource_types=defined)


def canonical(value):
    return sorted(json.dumps(x, sort_keys=True) for x in value)


def main():
    records, cache = [], {}
    for group, filename in [('local-normalization', 'static-comparison.json'),
                            ('transfer', 'comparison.json'),
                            ('seeded-normalization', 'comparison.json')]:
        rows = json.loads((ROOT/'results/countermeasures'/group/filename).read_text(encoding='utf-8'))['records']
        for row in rows:
            source = next(x for x in rows if x['source'] == row['source'] and x['variant'] == 'unmodified')
            values = []
            for item in (source, row):
                path = ROOT/item['path']
                digest = sha(path)
                assert digest == item['sha256']
                if digest not in cache:
                    cache[digest] = resources(path.read_bytes())
                values.append(cache[digest])
            a, b = values
            imported_equal = canonical(a['imported_resources']) == canonical(b['imported_resources'])
            exported_equal = canonical(a['exported_resources']) == canonical(b['exported_resources'])
            defined_equal = all(canonical(a['defined_resource_types'][k]) == canonical(b['defined_resource_types'][k]) for k in (1, 2, 3))
            records.append(dict(group=group, source=row['source'], variant=row['variant'],
                                sha256=row['sha256'], imported_resources_equal=imported_equal,
                                exported_resources_equal=exported_equal,
                                defined_resource_types_equal=defined_equal,
                                original=a, processed=b))
    report = dict(records=records, evaluator_sha256=sha(Path(__file__)), runtime_executed=False,
                  specification_sources=['https://webassembly.github.io/spec/core/binary/types.html',
                                         'https://webassembly.github.io/spec/core/binary/modules.html'],
                  scope='Imported/exported memory and table type/limits, global type/mutability, and defined resource type multisets. Not initial values, memory/data contents, table elements, start function behavior, host effects, traps or whole-module equivalence.')
    out = ROOT/'results/countermeasures/interface-resource-audit.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(records=len(records), imported_mismatches=sum(not r['imported_resources_equal'] for r in records), exported_mismatches=sum(not r['exported_resources_equal'] for r in records), defined_type_mismatches=sum(not r['defined_resource_types_equal'] for r in records))))


if __name__ == '__main__':
    main()
