"""Compare distributed mining source files without compiling or running them."""
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
TOKEN = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|(?:\d[\w.]*|\.[0-9][\w.]*)|[^\s]')


def tokens(data):
    text = data.decode('utf-8', errors='strict')
    return [t for t in TOKEN.findall(text) if not t.startswith(('//', '/*'))]


def function_bodies(data):
    """Top-level, named function body candidates; not a C preprocessor/parser."""
    ts = tokens(data)
    result = []
    i = 0
    while i < len(ts):
        if ts[i] != '{':
            i += 1
            continue
        start = i
        depth = 1
        i += 1
        while i < len(ts) and depth:
            depth += (ts[i] == '{') - (ts[i] == '}')
            i += 1
        assert depth == 0
        if start == 0 or ts[start-1] != ')':
            continue
        j, parens = start-2, 1
        while j >= 0 and parens:
            parens += (ts[j] == ')') - (ts[j] == '(')
            j -= 1
        if j < 0 or not re.fullmatch(r'[A-Za-z_]\w*', ts[j]):
            continue
        name = ts[j]
        if name in ('if', 'for', 'while', 'switch'):
            continue
        body = ts[start:i]
        if len(body) < 40:
            continue
        result.append(dict(name=name, tokens=len(body),
                           body_token_sha256=hashlib.sha256(json.dumps(body).encode()).hexdigest()))
    return result


with zipfile.ZipFile(ROOT / 'data/archives/proof-of-theft.zip') as archive:
    prefixes = {
        'webminerpoolhashcn': 'supp-materials/artifact/samples/webminerpoolhashcn/',
        'xmr-wasm': 'supp-materials/artifact/samples/xmr-wasm/src/'}
    trees = {family: {name[len(prefix):]: archive.read(name)
                     for name in archive.namelist()
                     if name.startswith(prefix) and name.endswith(('.c', '.cpp', '.h'))}
             for family, prefix in prefixes.items()}
    summaries = {family: {name: dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                                    comment_whitespace_token_sha256=hashlib.sha256(json.dumps(tokens(data)).encode()).hexdigest())
                          for name, data in files.items()} for family, files in trees.items()}
    matches = []
    for left, a in summaries['webminerpoolhashcn'].items():
        for right, b in summaries['xmr-wasm'].items():
            if a['sha256'] == b['sha256']:
                kind = 'byte-identical'
            elif a['comment_whitespace_token_sha256'] == b['comment_whitespace_token_sha256']:
                kind = 'same lexical tokens after comments/whitespace removal'
            else:
                continue
            matches.append(dict(webminerpool_file=left, xmr_file=right, match=kind,
                                webminerpool_sha256=a['sha256'], xmr_sha256=b['sha256']))
    functions = {family: {name: function_bodies(data) for name, data in files.items()}
                 for family, files in trees.items()}
    body_matches = []
    for left, entries in functions['webminerpoolhashcn'].items():
        for right, others in functions['xmr-wasm'].items():
            for a in entries:
                for b in others:
                    if a['body_token_sha256'] == b['body_token_sha256']:
                        body_matches.append(dict(webminerpool_file=left, xmr_file=right,
                            webminerpool_function=a['name'], xmr_function=b['name'],
                            body_tokens=a['tokens'], body_token_sha256=a['body_token_sha256']))
    for family, name in [('webminerpoolhashcn', 'main.c'), ('webminerpoolhashcn', 'cryptonight.c')]:
        (OUT / ('wmp-source-' + name + '.txt')).write_bytes(trees[family][name])
    reviewed = []
    for family, name, label in [('webminerpoolhashcn', 'oaes_lib.c', 'wmp'), ('xmr-wasm', 'crypto/oaes_lib.c', 'xmr')]:
        text = trees[family][name].decode('utf-8')
        match = re.search(r'\boaes_encryption_round\s*\([^;{}]*\)\s*\{', text)
        assert match
        start, end, depth = match.start(), match.end(), 1
        while depth:
            depth += (text[end] == '{') - (text[end] == '}')
            end += 1
        excerpt = text[start:end]
        path = OUT / f'{label}-oaes-encryption-round-source.txt'
        path.write_text(excerpt + '\n')
        reviewed.append(dict(family=family, file=name, line=text[:start].count('\n')+1,
            excerpt=str(path), excerpt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            lexical_tokens=tokens(excerpt.encode()),
            manually_reviewed_payload='Null checks, byte substitution, row shift, column mixing, key XOR, success return.'))
    assert reviewed[0]['lexical_tokens'] == reviewed[1]['lexical_tokens']
report = dict(scope='C/C++/header files in two distributed reference source directories; byte equality and lexical-token candidate equality only.',
              source_prefixes=prefixes, source_files=summaries, shared_files=matches,
              function_body_candidates=functions, shared_function_body_candidates=body_matches,
              reviewed_common_component=reviewed,
              interpretation='Shared cryptographic files establish source reuse in those components. Different wrappers or dataset labels do not prove independent cryptographic implementations.',
              limitations=['Lexical matching is not preprocessing, compilation, semantic equivalence, or binary provenance.',
                           'Comments removed by normalization can contain license/provenance information; raw bytes and digests are preserved.',
                           'Nonmatches do not establish independence; modified, renamed, embedded, or partially reused functions can be missed.',
                           'Distributed sources are not proven to be the historical sources used to build each binary.',
                           'SWAMPED seed ancestry and partial reuse in the main CryptoNight routine remain unresolved.'])
(OUT / 'source-reuse-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(files=matches, reviewed_component=[dict(family=r['family'],file=r['file'],line=r['line']) for r in reviewed],
                     candidate_file_pairs=sorted({(r['webminerpool_file'],r['xmr_file']) for r in body_matches})), indent=2))
