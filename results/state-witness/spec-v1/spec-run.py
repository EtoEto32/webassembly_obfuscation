"""Apply observers to accepted modules from pinned official WAST sources."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];other=[]
    for name in ('spec-run.py','spec-run.cjs','prototype.py','observer.cjs'):shutil.copy2(HERE/name,out/name)
    shutil.copy2(source/'provenance.json',out/'provenance.json')
    for file in ['memory_init.wast','table_init.wast']:
        folder=out/file[:-5];folder.mkdir();shutil.copy2(source/file,folder/file)
        k.p.tool('wast2json',[source/file,'--enable-all','-o',folder/'suite.json'])
        commands=json.loads((folder/'suite.json').read_text())['commands'];current=None
        for command in commands:
            if command['type']=='module':
                current={'suite':file,'source':(folder/command['filename']).relative_to(out).as_posix(),
                         'line':command['line'],'commands':[]};rows.append(current)
                src=out/current['source'];dest=src.with_name(src.stem+'-observed.wasm')
                try:
                    meta=k.transform(src,dest);current.update({'status':'accepted','observed':dest.relative_to(out).as_posix(),'manifest':meta})
                except ValueError as e:current.update({'status':'unsupported','reason':str(e)})
                except RuntimeError as e:current.update({'status':'tool-rejected','reason':str(e)})
            elif current is not None and command['type'] in ('action','assert_return','assert_trap'):
                current['commands'].append(command)
            else:other.append({'suite':file,**command})
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'otherCommands':other},indent=2),encoding='utf8')
    cmd=['node',str(HERE/'spec-run.cjs'),str(out.resolve())]
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=120)
    (out/'node-log.json').write_text(json.dumps({'command':cmd,'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({x.relative_to(out).as_posix():hashlib.sha256(x.read_bytes()).hexdigest()
        for x in out.rglob('*') if x.is_file() and x.name!='sha256.json'},indent=2))
    if run.returncode:raise RuntimeError(run.stderr)
    print(run.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
