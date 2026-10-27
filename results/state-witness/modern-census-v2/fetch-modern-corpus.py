"""Fetch two pinned public npm artifacts, verify integrity, run no package code."""
import argparse,base64,hashlib,io,json,tarfile,urllib.parse,urllib.request
from pathlib import Path


def fetch(url,limit):
    request=urllib.request.Request(url,headers={'User-Agent':'Wasm-research-artifact-fetch/1.0'})
    with urllib.request.urlopen(request,timeout=45) as response:
        chunks=[];total=0
        while True:
            chunk=response.read(1024*1024)
            if not chunk:break
            total+=len(chunk)
            if total>limit:raise ValueError('download size limit')
            chunks.append(chunk)
    return b''.join(chunks)


def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for package in ('core','core-mt'):
        name='@ffmpeg/'+package;version='0.12.10';url='https://registry.npmjs.org/'+urllib.parse.quote(name,safe='')+'/'+version
        meta_bytes=fetch(url,2*1024*1024);meta=json.loads(meta_bytes)
        assert meta['name']==name and meta['version']==version
        dist=meta['dist'];integrity=dist['integrity'];assert integrity.startswith('sha512-')
        tarball=fetch(dist['tarball'],64*1024*1024);assert hashlib.sha512(tarball).digest()==base64.b64decode(integrity[7:])
        folder=out/package;folder.mkdir();(folder/'metadata.json').write_bytes(meta_bytes);files=[]
        with tarfile.open(fileobj=io.BytesIO(tarball),mode='r:gz') as archive:
            for membername,targetname in [('package/dist/umd/ffmpeg-core.wasm','ffmpeg-core.wasm'),('package/package.json','package.json')]:
                member=archive.getmember(membername);assert member.isfile() and member.size<=40*1024*1024
                data=archive.extractfile(member).read(40*1024*1024+1);assert len(data)==member.size
                (folder/targetname).write_bytes(data);files.append({'file':package+'/'+targetname,'member':membername,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        rows.append({'package':name,'version':version,'metadataURL':url,'tarballURL':dist['tarball'],'tarballBytes':len(tarball),'integrity':integrity,'files':files})
        (out/'provenance.json').write_text(json.dumps({'rows':rows},indent=2));print(json.dumps({'package':name,'files':files}),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
