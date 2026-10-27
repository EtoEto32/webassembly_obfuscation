import argparse,copy,json,subprocess
from pathlib import Path
import prototype as p
def main(data,out):
    data=Path(data);out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=json.loads((data/'manifest.json').read_text());manifest=[]
    for r in [r for r in rows if r['opt']=='raw']:
        m=p.read(data/r['file']);fi=0
        for e in m[1:]:
            if e[0]=='memory':e[:]=['memory','2','2']
            if e[0]=='func':
                decl=[x for x in e[1:] if x[0] in p.DECL];body=[x for x in e[1:] if x[0] not in p.DECL];cnt=0 if r['mode']=='plain' else r['plans'][fi]['selected'];at=2+cnt*2
                body.insert(at,['memory.copy',p.c(65536),p.g(3),p.c(r['n']*16)]);e[:]=['func',*decl,*body];fi+=1
        m.append(['export','"memory"',['memory','0']]);dst=out/r['file'];p.compile(p.w.emit(m),dst)
        source=p.profile(p.read(data/r['source']),r['n'],r['records']);manifest.append(dict(file=dst.name,n=r['n'],depth=r['depth'],mode=r['mode'],initial=str((data/r['initial']).resolve()),profiles=source))
    p.save(out/'manifest.json',manifest)
    script='''const fs=require('fs'),path=require('path'),d=process.argv[1];const rows=JSON.parse(fs.readFileSync(path.join(d,'manifest.json'))),out=[];for(const r of rows){const ref=JSON.parse(fs.readFileSync(r.initial));let i=0;for(const name of ['bump','coupled','spread','peek']){const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(d,r.file)))).exports;e[name](0,17,-1);const snap=new Uint32Array(e.memory.buffer,65536,r.n*4);let matches=0;for(let j=0;j<snap.length;j++)if(snap[j]===ref[j])matches++;for(const chunk of r.profiles[i].reads)for(let lane=0;lane<4;lane++)if(snap[chunk*4+lane]!==ref[chunk*4+lane])throw Error('required read not decoded');out.push({file:r.file,n:r.n,depth:r.depth,mode:r.mode,kernel:name,matching_words:matches,total_words:snap.length});i++;}}fs.writeFileSync(path.join(d,'exposure.json'),JSON.stringify(out,null,2));console.log(JSON.stringify({snapshots:out.length,required_reads_decoded:true}));'''
    result=json.loads(subprocess.check_output(['node','-e',script,str(out)],text=True,timeout=60));p.save(out/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
