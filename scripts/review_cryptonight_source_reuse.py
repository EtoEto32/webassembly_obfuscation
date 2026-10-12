"""Extend lexical source-reuse review to the unexecuted cryptonight candidate."""
import ast
import hashlib
import itertools
import json
import re
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
helper=ROOT/'scripts/review_proof_source_reuse.py'
# Reuse just the tokenizer and candidate extractor, without running that
# script's top-level archive reads or replacing its existing report.
tree=ast.parse(helper.read_text(encoding='utf-8'))
selected=[n for n in tree.body if
    isinstance(n,ast.FunctionDef) and n.name in ('tokens','function_bodies') or
    isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TOKEN' for t in n.targets)]
assert len(selected)==3
namespace={'re':re,'json':json,'hashlib':hashlib}
exec(compile(ast.Module(body=selected,type_ignores=[]),str(helper),'exec'),namespace)
tokens=namespace['tokens'];function_bodies=namespace['function_bodies']
prefixes={
    'webminerpoolhashcn':'supp-materials/artifact/samples/webminerpoolhashcn/',
    'xmr-wasm':'supp-materials/artifact/samples/xmr-wasm/src/',
    'cryptonight-hash':'supp-materials/artifact/samples/cryptonight-hash/'}
sources={};bodies={};reviewed=[]
with zipfile.ZipFile(ROOT/'data/archives/proof-of-theft.zip') as archive:
    names=archive.namelist()
    for family,prefix in prefixes.items():
        sources[family]={};bodies[family]={}
        for name in names:
            if not name.startswith(prefix) or not name.endswith(('.c','.cpp','.h')):continue
            data=archive.read(name);relative=name[len(prefix):]
            sources[family][relative]={
                'archive_path':name,'bytes':len(data),
                'sha256':hashlib.sha256(data).hexdigest(),
                'token_sha256':hashlib.sha256(json.dumps(tokens(data)).encode()).hexdigest()}
            bodies[family][relative]=function_bodies(data)
            review_names={
                ('webminerpoolhashcn','cryptonight.c'):('copy_block','xor_blocks'),
                ('cryptonight-hash','cryptonightnative.c'):('copy_block','xor_blocks','sum_half_blocks'),
                ('xmr-wasm','crypto/slow-hash.c'):('sum_half_blocks',)}.get((family,relative),())
            text=data.decode('utf-8')
            for function in review_names:
                for match in re.finditer(r'\b'+function+r'\s*\([^;{}]*\)\s*\{',text):
                    end=match.end();depth=1
                    while depth:
                        depth+=(text[end]=='{')-(text[end]=='}');end+=1
                    excerpt=text[match.start():end]
                    reviewed.append({'family':family,'archive_path':name,'function':function,
                        'line':text[:match.start()].count('\n')+1,'source_excerpt':excerpt,
                        'excerpt_sha256':hashlib.sha256(excerpt.encode()).hexdigest(),
                        'lexical_tokens':tokens(excerpt.encode())})
assert len(reviewed)==7
for function,left_family,right_family,left_line,right_line in [
        ('copy_block','webminerpoolhashcn','cryptonight-hash',245,111),
        ('xor_blocks','webminerpoolhashcn','cryptonight-hash',477,126),
        ('sum_half_blocks','xmr-wasm','cryptonight-hash',1609,98)]:
    pair=[next(x for x in reviewed if x['family']==family and x['function']==function and x['line']==line)
          for family,line in [(left_family,left_line),(right_family,right_line)]]
    assert pair[0]['lexical_tokens']==pair[1]['lexical_tokens'],function
file_matches=[];function_matches=[]
for left,right in itertools.combinations(prefixes,2):
    if 'cryptonight-hash' not in (left,right):continue
    for a,ma in sources[left].items():
        for b,mb in sources[right].items():
            if ma['sha256']==mb['sha256'] or ma['token_sha256']==mb['token_sha256']:
                file_matches.append({'left_family':left,'left_file':a,'right_family':right,'right_file':b,
                    'match':'bytes' if ma['sha256']==mb['sha256'] else 'lexical tokens',
                    'left_sha256':ma['sha256'],'right_sha256':mb['sha256']})
    index={}
    for b,entries in bodies[right].items():
        for entry in entries:index.setdefault(entry['body_token_sha256'],[]).append((b,entry))
    for a,entries in bodies[left].items():
        for entry in entries:
            for b,other in index.get(entry['body_token_sha256'],[]):
                function_matches.append({'left_family':left,'left_file':a,'left_function':entry['name'],
                    'right_family':right,'right_file':b,'right_function':other['name'],
                    'body_tokens':entry['tokens'],'body_token_sha256':entry['body_token_sha256']})
report={'date':'2026-10-08','scope':'Three distributed reference source trees; new comparisons concern cryptonight-hash only.',
    'analysis_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'extractor_script_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
    'source_prefixes':prefixes,'source_files':sources,'function_body_candidates':bodies,
    'shared_files':file_matches,'shared_function_body_candidates':function_matches,
    'reviewed_helper_excerpts':reviewed,
    'interpretation':'Exact byte or lexical matches show reuse of the matched components, not equality of the whole mining implementation or binary ancestry. Absence of a match does not prove independence.',
    'limitations':['Function candidates are lexical, not a C/C++ parser or preprocessor.',
        'Macros, renaming, edits and partial reuse can escape matching.',
        'Distributed sources are not proven historical build inputs.',
        'The cryptonight-hash candidate has not been dynamically validated or timed.'],
    'executed_hashes':0}
(OUT/'cryptonight-source-reuse-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('Three source trees reviewed; shared helper excerpts verified; no hash execution.')
