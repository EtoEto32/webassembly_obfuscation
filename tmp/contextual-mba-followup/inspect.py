"""Read-only provenance checks and extraction of selected documentation."""
import hashlib,json,zipfile
from pathlib import Path
p=Path(__file__).parent
record=json.loads((p/'zenodo-record.json').read_text(encoding='utf-8-sig'))
commit=json.loads((p/'commit.json').read_text(encoding='utf-8-sig'))
tree=json.loads((p/'tree.json').read_text(encoding='utf-8-sig'))
assert not tree['truncated']
data=(p/'promba-rcr.zip').read_bytes()
assert hashlib.md5(data).hexdigest()=='c68df8ff9fd4d19d6525f0cfb2be9837'
members=[]
with zipfile.ZipFile(p/'promba-rcr.zip') as z:
    for name,out in [('README','artifact-README.txt'),('Dockerfile','artifact-Dockerfile.txt'),
                     ('LICENSE','artifact-LICENSE.txt'),('INSTALL','artifact-INSTALL.txt'),
                     ('rcr/sample-custom.txt','sample-custom.txt')]:
        payload=z.read('promba-rcr/'+name)
        (p/out).write_bytes(payload)
        members.append(dict(member='promba-rcr/'+name,saved=out,sha256=hashlib.sha256(payload).hexdigest()))
verified=[]
for filename in ('main.ml','expr.ml','utils.ml','options.ml'):
    payload=(p/filename).read_bytes()
    oid=hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
    expected=next(t['sha'] for t in tree['tree'] if t['path']=='src/'+filename)
    assert oid==expected
    verified.append(dict(file=filename,git_blob=oid,sha256=hashlib.sha256(payload).hexdigest()))
report=dict(record=record['id'],commit=commit['sha'],commit_date=commit['commit']['committer']['date'],
            archive_sha256=hashlib.sha256(data).hexdigest(),archive_md5=hashlib.md5(data).hexdigest(),
            archive_members=members,source_files=verified,
            executed_author_code=False)
(p/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
