"""Retrieve primary reference evidence for the final candidate availability audit."""
import concurrent.futures
import json
from urllib.parse import urlencode
from acquire import ROOT
from discover_artifacts import fetch


SOURCES = [
    ('minesweeper', 'https://download.vusec.net/papers/minesweeper_ccs18.pdf', 'paper.pdf'),
    ('outguard', 'https://faculty.cc.gatech.edu/~mbailey/publications/www19_cryptojacking.pdf', 'paper.pdf'),
    ('proof-of-theft', 'https://drops.dagstuhl.de/storage/05darts/darts-vol012/darts-vol012-issue001_ecoop2026/DARTS.12.1.19/DARTS.12.1.19.pdf', 'artifact-description.pdf'),
    ('proof-of-theft', 'https://drops.dagstuhl.de/storage/00lipics/lipics-vol372-ecoop2026/LIPIcs.ECOOP.2026.25/LIPIcs.ECOOP.2026.25.pdf', 'paper.pdf'),
    ('wasmizer', 'https://qstievenart.gitlab.io/pdfs/msr2023.pdf', 'paper.pdf'),
    ('jwbinder', 'https://arxiv.org/html/2310.17304v2', 'paper.html'),
    ('first-look', 'https://par.nsf.gov/servlets/purl/10334207', 'paper.pdf'),
    ('first-look', 'https://abbasacar.github.io/publication/wasm-obfuscation/', 'author-page.html'),
    ('minos', 'https://www.ndss-symposium.org/wp-content/uploads/2021-444-paper.pdf', 'paper.pdf'),
    ('wild2019', 'https://www.intellisec.org/pubs/2019a-dimva.pdf', 'paper.pdf'),
    ('llm-deobfuscation2026', 'https://api.crossref.org/works?'+urlencode({
        'query.title':'A Systematic LLM-Based Procedure for the Deobfuscation of WebAssembly',
        'rows':3}), 'crossref-search.json'),
]


def one(source):
    name, url, filename = source
    dest = ROOT/'data/catalog'/name/filename
    try:
        result = {'candidate':name, 'status':'ok', **fetch(url,dest)}
        if filename.endswith('.pdf'):
            try:
                from pypdf import PdfReader
                reader = PdfReader(dest)
                output = dest.with_suffix('.txt')
                output.write_text('\n\n'.join(f'PAGE {i+1}\n'+(p.extract_text() or '')
                                               for i,p in enumerate(reader.pages)),encoding='utf-8')
                result['pages'] = len(reader.pages)
                result['text_file'] = output.relative_to(ROOT).as_posix()
                result['text_extraction_status'] = 'ok'
            except ImportError as exc:
                result['text_extraction_status'] = 'unavailable_dependency'
                result['text_extraction_error'] = repr(exc)
        return result
    except Exception as exc:
        return {'candidate':name,'url':url,'file':dest.relative_to(ROOT).as_posix(),
                'status':'failed','error':repr(exc)}


if __name__ == '__main__':
    log = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(one,SOURCES):
            log.append(row)
            print(json.dumps(row),flush=True)
    (ROOT/'results/catalog/literature-followup-receipts.json').write_text(
        json.dumps(log,indent=2),encoding='utf-8')
