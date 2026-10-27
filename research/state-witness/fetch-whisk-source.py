"""Fetch selected source files, verifying Git blob identities against the pin."""
import argparse,hashlib,json
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('fetch_whisk',HERE/'fetch-whisk.py');f=importlib.util.module_from_spec(sp);sp.loader.exec_module(f)

def main(folder):
    meta=json.loads((folder/'provenance.json').read_text());tree={x['path']:x for x in json.loads((folder/'tree.json').read_text())['tree'] if x['type']=='blob'}
    names=['doc/WHISK.md','src/validator/proofs/full_sym_eval.ml','src/validator/proofs/uf_sym_eval.ml','src/validator/proofs/proof_types.ml',
           'src/validator/proofs/state_types.ml','src/validator/proofs/smt_ir.ml','src/validator/proofs/sym_eval_interface.ml',
           'src/validator/syntax/instr_graph.ml','src/validator/validator-api/cfg_builder.ml','src/validator/utils/wasm_utils.ml']
    if (folder/'extra-provenance.json').exists():raise ValueError('already fetched')
    rows=[]
    for name in names:
        url='https://raw.githubusercontent.com/'+meta['repository']+'/'+meta['commit']+'/'+name;data=f.get(url,1000000)
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==tree[name]['sha']
        p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);rows.append({'path':name,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'gitBlob':tree[name]['sha']})
    (folder/'extra-provenance.json').write_text(json.dumps({'repository':meta['repository'],'commit':meta['commit'],'rows':rows},indent=2));print(json.dumps({'files':len(rows)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);main(p.parse_args().folder)
