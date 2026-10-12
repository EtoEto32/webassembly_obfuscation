"""Inspect archive members and ingest standalone Wasm without executing them."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from acquire import ROOT

SEVEN = Path(r'C:\Program Files\7-Zip\7z.exe')
OBJECTS = ROOT/'data/objects'
MAX_DEPTH = 5
MAX_NESTED_BYTES = 8 * 1024**3


def safe_member(name, virtual_zip_name=False):
    normalized = name.replace('\\','/')
    p = PurePosixPath(normalized)
    if p.is_absolute() or (':' in normalized and not virtual_zip_name) or '..' in p.parts:
        raise ValueError('Unsafe archive member: '+name)
    return normalized


def save_binary(data, item, name):
    sha = hashlib.sha256(data).hexdigest()
    obj = OBJECTS/(sha+'.bin')
    row = {'dataset':item['dataset'], 'artifact':item['id'], 'path':name,
           'archive_url':item['url'], 'archive_sha256':item['sha256'],
           'bytes':len(data),'sha256':sha,'wasm_magic':data[:4]==b'\0asm',
           'object':obj.relative_to(ROOT).as_posix(),'acquisition_status':'stored_verified',
           'hash_evidence':'computed_from_archive_member'}
    try:
        if not obj.exists():
            obj.write_bytes(data)
        if hashlib.sha256(obj.read_bytes()).hexdigest()!=sha:
            raise ValueError('cached object mismatch')
    except OSError as exc:
        row.update(acquisition_status='local_io_failed',acquisition_error=str(exc))
    return row


def inspect_file(source, name, size, item, rows, inventory, failures, depth=0):
    """Read bytes only. Nested ZIP/APK members are never installed or run."""
    try:
        first = source.read(8)
        if first[:4] == b'\0asm' or name.lower().endswith('.wasm'):
            data = first + source.read()
            if len(data) != size:
                raise ValueError('member size mismatch')
            rows.append(save_binary(data, item, name))
        elif first[:4] in (b'PK\x03\x04', b'PK\x05\x06') or name.lower().endswith(('.zip', '.apk', '.jar')):
            if depth >= MAX_DEPTH or size > MAX_NESTED_BYTES:
                failures.append({'stage':'nested_archive_limit','path':name,'bytes':size,'depth':depth})
                return
            with tempfile.TemporaryFile(mode='w+b') as nested:
                nested.write(first)
                shutil.copyfileobj(source, nested, length=1024*1024)
                if nested.tell() != size:
                    raise ValueError('nested archive size mismatch')
                nested.seek(0)
                with zipfile.ZipFile(nested) as child:
                    walk_zip(child, item, rows, inventory, failures, prefix=name+'!/', depth=depth+1)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        failures.append({'stage':'inspect_member','path':name,'error':str(exc)})
        if name.lower().endswith('.wasm'):
            rows.append({'dataset':item['dataset'],'artifact':item['id'],'path':name,
                         'archive_url':item['url'],'archive_sha256':item['sha256'],
                         'bytes':size,'sha256':None,'acquisition_status':'member_read_failed',
                         'acquisition_error':str(exc)})


def walk_zip(z, item, rows, inventory, failures, prefix='', depth=0):
    for member in z.infolist():
        # ZIP names are metadata, never extracted to these paths. A colon in
        # an original filename is valid here; native 7z extraction retains
        # the stricter Windows rule.
        name = prefix + safe_member(member.filename, virtual_zip_name=True)
        if member.is_dir():
            continue
        inventory.append({'path':name,'bytes':member.file_size,'crc32':member.CRC,'depth':depth})
        try:
            with z.open(member) as source:
                inspect_file(source,name,member.file_size,item,rows,inventory,failures,depth)
        except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
            failures.append({'stage':'open_zip_member','path':name,'error':str(exc)})


def ingest(item):
    archive = ROOT/'data/archives'/item['filename']
    receipt = json.loads(archive.with_suffix(archive.suffix+'.receipt.json').read_text())
    item = {**item, **receipt}
    output = ROOT/'data/catalog'/(item['id']+'-archive')
    output.mkdir(parents=True,exist_ok=True); OBJECTS.mkdir(parents=True,exist_ok=True)
    rows, inventory, failures = [], [], []
    if archive.suffix == '.zip':
        with zipfile.ZipFile(archive) as z:
            walk_zip(z,item,rows,inventory,failures)
    elif archive.name.endswith(('.tar.xz','.tar.bz2','.tar.gz','.tar')):
        with tarfile.open(archive,mode='r|*') as tar:
            for member in tar:
                # TAR members are streamed and never extracted. Preserve URL-like
                # names containing ':' as metadata, while still rejecting absolute
                # paths and traversal components.
                try:
                    name = safe_member(member.name, virtual_zip_name=True)
                except ValueError as exc:
                    inventory.append({'path':member.name,'bytes':member.size,
                                      'directory':member.isdir(),'regular_file':member.isfile(),
                                      'unsafe_name':True})
                    failures.append({'stage':'unsafe_tar_member_not_read',
                                     'path':member.name,'error':str(exc)})
                    continue
                inventory.append({'path':name,'bytes':member.size,'directory':member.isdir(),
                                  'regular_file':member.isfile()})
                if member.isfile():
                    with tar.extractfile(member) as source:
                        inspect_file(source,name,member.size,item,rows,inventory,failures)
                elif not member.isdir():
                    failures.append({'stage':'tar_nonregular_not_followed','path':name,'type':repr(member.type)})
    elif archive.suffix == '.7z':
        listing = subprocess.run([str(SEVEN),'l','-slt','-ba','-sccUTF-8',str(archive)],
                                 check=True,capture_output=True).stdout.decode('utf-8')
        (output/'archive-listing.txt').write_text(listing,encoding='utf-8')
        for block in re.split(r'\r?\n\r?\n',listing.strip()):
            fields=dict(line.split(' = ',1) for line in block.splitlines() if ' = ' in line)
            if not fields.get('Path'):
                continue
            name = safe_member(fields['Path'])
            link = bool(any(k in fields for k in ('Symbolic Link','Hard Link')) or re.search(r'\bl[rwx-]{9}', fields.get('Attributes','')))
            inventory.append({'path':name,'bytes':int(fields.get('Size',0)),
                              'directory':fields.get('Attributes','').startswith('D'),'link':link})
        links = [m['path'] for m in inventory if m.get('link')]
        for name in links:
            if '*' in name or '?' in name:
                raise ValueError('Cannot safely express link exclusion')
            failures.append({'stage':'archive_link_not_followed','path':name})
        if any(m['path'].startswith(link+'/') for m in inventory for link in links):
            raise ValueError('Archive has members below a link')
        extracted = ROOT/'data/extracted'/item['id']
        extracted.mkdir(parents=True,exist_ok=True)
        # Every member was checked before native extraction; no scripts run.
        run = subprocess.run([str(SEVEN),'x','-y','-sccUTF-8',str(archive),'-o'+str(extracted)]+['-x!'+name for name in links],
                             capture_output=True)
        (output/'extraction.log').write_bytes(run.stdout+b'\n'+run.stderr)
        if run.returncode:
            failures.append({'stage':'7z_extract','returncode':run.returncode})
        for member in list(inventory):
            name=member['path']
            if member['directory'] or member.get('link'):
                continue
            source=extracted/Path(name)
            source.resolve().relative_to(extracted.resolve())
            try:
                with source.open('rb') as f:
                    inspect_file(f,name,member['bytes'],item,rows,inventory,failures)
            except OSError as exc:
                failures.append({'stage':'read_extracted','path':name,'error':str(exc)})
                if name.lower().endswith('.wasm'):
                    rows.append({'dataset':item['dataset'],'artifact':item['id'],'path':name,
                                 'archive_url':item['url'],'archive_sha256':item['sha256'],
                                 'bytes':member['bytes'],'sha256':None,'acquisition_status':'extraction_read_failed',
                                 'acquisition_error':str(exc)})
    else:
        raise ValueError('unsupported archive type')
    (output/'inventory.json').write_text(json.dumps(inventory),encoding='utf-8')
    (output/'acquisition.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    summary={'dataset':item['dataset'],'artifact':item['id'],'archive_members':len(inventory),
             'candidate_wasm_members':len(rows),'unique_downloaded_sha256':len({r['sha256'] for r in rows if r['sha256']}),
             'stored_verified_paths':sum(r['acquisition_status']=='stored_verified' for r in rows),
             'failures':failures,'scope':'all regular members inspected for core-Wasm magic or .wasm suffix; nested ZIP/APK/JAR inspected through depth 5; JS and native-binary embeddings not yet included'}
    (output/'acquisition-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('ids',nargs='+'); args=ap.parse_args()
    for item in json.loads((ROOT/'experiments/archive-registry.json').read_text()):
        if item['id'] in args.ids:
            ingest(item)
