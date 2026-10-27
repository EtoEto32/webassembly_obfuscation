"""Public-template hash catalog: amortize template recognition across artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time
import prototype as p
from run import save

def key(path):
    sec=p.sections(path.read_bytes());sec.pop(11,None);sec.pop(12,None)
    # read_data permits active segments only and catalog code has no memory.init
    # or data.drop. Their count is irrelevant after initial memory is materialized.
    # Explicit lengths prevent ambiguities in concatenated section payloads.
    return hashlib.sha256(b''.join(bytes([k])+len(v).to_bytes(8,'little')+v for k,v in sorted(sec.items()))).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('inputs',type=Path,nargs='+');o=ap.parse_args();out=o.output;out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();shutil.copyfile(Path(__file__),out/'sources/indexed-attack.py')
    catalog={};build=[];results=[]
    # Manifest supplies a list of files only. No original values, modes, seeds or
    # expected results are passed into extraction/lookup/decoding.
    for folder in o.inputs:
        files=[folder/q['path'] for q in json.loads((folder/'manifest.json').read_text())['files'] if not q['recovered']]
        for src in files:
            t=time.perf_counter();data=p.read_data(src);read_ms=(time.perf_counter()-t)*1000;n=len(data)
            if n not in catalog:
                t=time.perf_counter();table={};loc=out/('catalog-'+str(n));loc.mkdir()
                for mode in p.MODES:
                    raw=loc/(mode+'.raw.wasm');p.c.compile_wat(p.wat(bytes(n),mode),raw)
                    for level in ('raw','O3'):
                        path=raw if level=='raw' else loc/(mode+'.O3.wasm')
                        if level=='O3':p.w.tool('wasm-opt',[raw,'-O3','--all-features','-o',path])
                        table.setdefault(key(path),[]).append(dict(mode=mode,opt=level))
                catalog[n]=table;build.append(dict(n=n,build_ms=(time.perf_counter()-t)*1000,profiles=10,unique_keys=len(table)))
            samples=[];entry=None;plain=None
            for _ in range(11):
                t=time.perf_counter();candidates=catalog[n].get(key(src))
                if not candidates:raise ValueError('Unsupported code profile: '+str(src))
                mode=candidates[0]['mode'];plain=p.decode(data,mode)
                assert all(p.decode(data,q['mode'])==plain for q in candidates)
                samples.append((time.perf_counter()-t)*1000)
                entry=candidates
            target=out/(folder.name+'.'+src.stem+'.wasm');p.c.compile_wat(p.wat(plain,'plain'),target)
            # Compare after recovery to the already executed recovered artifact,
            # not to input provided to the recovery algorithm.
            expected=src.with_name(src.stem+'.recovered.wasm');assert target.read_bytes()==expected.read_bytes()
            results.append(dict(input=str(src),output=target.name,n=n,status='recovered',matches=entry,read_validate_ms=read_ms,lookup_decode_samples_ms=samples,median_ms=statistics.median(samples),recovered_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),matches_previously_tested=True))
    save(out/'catalog.json',catalog);save(out/'results.json',dict(status='completed',build=build,results=results))
    print(json.dumps(dict(status='completed',recovered=len(results),catalog_sizes=len(catalog),build=build)))

if __name__=='__main__':main()
