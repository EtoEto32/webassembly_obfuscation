"""Extract one existing helper without the ordinary SHA implementation."""
import copy,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('fr_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q)

def isolate(src,dst):
    m=q.read(src);ix=int(next(x[2][1] for x in m[1:] if x[:2]==['export','"t2"']))
    fs=[x for x in m[1:] if x[0]=='func'];f=copy.deepcopy(fs[ix]);f=[x for x in f if not isinstance(x,list) or x[0]!='type']
    assert not any(x[0] in ('call','return_call','call_indirect') for x in q.walk(f))
    result=['module',*[copy.deepcopy(x) for x in m[1:] if x[0] in ('memory','global')],f,['export','"run"',['func','0']],['export','"memory"',['memory','0']],['export','"evaluations"',['global','0']]]
    q.compile(q.w.emit(result),dst)
    return dict(source_sha256=q.digest(src),helper_index=ix,isolated_sha256=q.digest(dst),functions=1,source_functions=len(fs),data_segments=0)
if __name__=='__main__':
    src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
    f=out/'isolated-raw.wasm';info=isolate(src,f);q.tool('wasm-opt',[f,'--enable-bulk-memory','-O3','-o',out/'isolated-O3.wasm'])
    q.save(out/'isolation.json',info);print(json.dumps(info))
