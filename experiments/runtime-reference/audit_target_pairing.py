"""Trace input pairing and upstream collection branches; no execution."""
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / 'data/upstream/wasm_evasion/malware_reproduction/rq3'
OUT = ROOT / 'results/runtime-mining'


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    inputs = [r for r in rows(ROOT / 'results/mining-methods/input-manifest.csv')
              if r['method'] != 'wasm-mutate/iteration-series']
    normals = {(r['program'], r['release']):r for r in inputs if r['method'] == 'unobfuscated'}
    pairs = []
    for row in inputs:
        if row['method'] == 'unobfuscated':
            continue
        normal = normals[(row['program'], row['release'])]
        if row['baseline_sha256'] != normal['sha256'] or row['baseline_object'] != normal['object']:
            raise ValueError('Pairing conflict: ' + row['path'])
        pairs.append({key:row[key] for key in ('program','release','method','sha256','baseline_sha256',
                                             'object','baseline_object','pairing_basis','source_commit')})
    reconstructed = rows(OUT / 'reference-reconstruction.csv')
    originals = json.loads((OUT / 'paper-original-manifest.json').read_text(encoding='utf-8'))
    reference_pairs = []
    for item in reconstructed:
        if item['role'] != 'variant':
            continue
        parents = [r for r in originals if r['sha256'].startswith(item['parent_prefix'])]
        if len(parents) != 1:
            raise ValueError('Ambiguous original prefix: ' + item['parent_prefix'])
        parent = parents[0]
        reference_pairs.append({
            'original_sha256':parent['sha256'], 'original_object':parent['object'],
            'variant_source':item['source'], 'reconstructed_object':item['object'],
            'reconstructed_sha256':item['actual_sha256'],
            'collection_branch':item['algorithm_group'], 'sigma':item['sigma'],
            'pairing_evidence':'Unique distributed parent-directory prefix matched to original SHA-256',
            'original_variant_binary_identity_confirmed':item['matches_named_binary'] == 'True',
            'mining_semantics_confirmed':False
        })
    reference_counts = collections.Counter((r['parent_prefix'],r['algorithm_group'],r['sigma'])
        for r in reconstructed if r['role'] == 'variant')
    source_files = ['README.md', 'plot.sh', 'plot_distributions.py', 'get_table.v2.py',
                   'replace_experiments/coinhive-32bits/collect.sh',
                   'replace_experiments/coinhive-32bits/collect_mcmc.sh']
    report = {
        'scope':'Manifest and pinned source audit; no mining execution or performance selection',
        'cryptic_bytes':{'normal_program_release_groups':len(normals),
            'paired_variants':len(pairs), 'pairs':pairs,
            'limitation':'These are another dataset, not the original paper baseline/MCMC sample groups.'},
        'reference_distribution':{
            'pairs':reference_pairs,
            'groups':[{'parent_prefix':p,'collection_branch':g,'sigma':s,'wat_count':n}
                      for (p,g,s),n in sorted(reference_counts.items())],
            'complete_paper_groups_confirmed':False,
            'mcmc_named_binary_sha256':'Not supplied by sigma-based filenames; reconstruction identity is unknown'},
        'source_sha256':{p:hashlib.sha256((UPSTREAM / p).read_bytes()).hexdigest() for p in source_files},
        'source_code_differences':[
            'collect.sh lists five original prefixes, while the paper reports six runnable programs.',
            'collect_mcmc.sh uses -0 rather than -o in the proxy command; this is not copied into the runner.',
            'collect_mcmc.sh hardcodes server.py fbdd1e for originals inside a loop over different prefixes; baseline identity must be checked explicitly.',
            'collect_mcmc.sh writes one log path per sigma and original, rather than uniquely labeling ten variants.',
            'plot_distributions.py fills missing beta distributions using np.random.normal. No such fabricated distributions will be used.',
            'get_table.v2.py and plot_distributions.py filter rates strictly inside mean plus/minus two standard deviations. Raw observations must be retained separately; zero or empty distributions must not be hidden.'
        ]
    }
    (OUT / 'target-pairing-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'paired_variants':len(pairs), 'normal_groups':len(normals),
                      'paper_groups_complete':False, 'reference_groups':len(reference_counts)}))


if __name__ == '__main__':
    main()
