"""Resolve current named refs and distinguish Git commit from Git tree identities."""
import concurrent.futures
import json
from acquire import ROOT, get


def one(dataset):
    base=ROOT/'data/catalog'/dataset['id']
    tree_path=base/'tree.json'
    if not tree_path.exists():return None
    tree=json.loads(tree_path.read_text(encoding='utf-8'))
    repo=json.loads((base/'repository.json').read_text(encoding='utf-8'))
    ref=dataset.get('ref',repo['default_branch'])
    path=base/'resolved-commit.json'
    url=f"https://api.github.com/repos/{dataset['github']}/commits/{ref}"
    if not path.exists():
        with get(url) as response:raw=response.read()
        json.loads(raw);path.write_bytes(raw)
    commit=json.loads(path.read_text(encoding='utf-8'))
    matched=commit['sha']==tree['sha']
    return {'dataset':dataset['id'],'requested_ref':ref,'saved_tree_response_revision_sha':tree['sha'],
            'resolved_commit_sha':commit['sha'],'resolved_commit_tree_sha':commit['commit']['tree']['sha'],
            'saved_revision_matches_commit':matched,'saved_revision_matches_root_tree':commit['commit']['tree']['sha']==tree['sha'],
            'commit_time':commit['commit']['committer']['date'],
            'evidence_file':path.relative_to(ROOT).as_posix(),
            'interpretation':'Direct comparison distinguishes the revision SHA in the saved tree response from the root-tree SHA. Do not infer object type from the API endpoint name.'}


if __name__=='__main__':
    datasets=[d for d in json.loads((ROOT/'experiments/dataset-registry.json').read_text(encoding='utf-8'))['datasets'] if d.get('github')]
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(one,d):d for d in datasets}
        for future in concurrent.futures.as_completed(futures):
            dataset=futures[future]
            try:row= {'status':'ok',**(future.result() or {'dataset':dataset['id'],'scope':'no saved tree'})}
            except Exception as exc:row={'dataset':dataset['id'],'status':'failed','error':str(exc)[:500]}
            results.append(row);print(json.dumps(row),flush=True)
    (ROOT/'results/provenance/git-revision-identities.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
