import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import ingest_archives as ingest
from ingest_split_zip import LocalParts


class ArchiveTests(unittest.TestCase):
    def test_nested_apk_and_extensionless_magic(self):
        nested=io.BytesIO()
        with zipfile.ZipFile(nested,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('assets/module',b'\0asm\1\0\0\0')
            z.writestr('classes.dex',b'dex\n035\0')
        outer=io.BytesIO()
        with zipfile.ZipFile(outer,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('application.apk',nested.getvalue())
            z.writestr('top.wasm',b'\0asm\1\0\0\0')
        rows,inventory,failures=[],[],[]
        item={'dataset':'fixture','id':'fixture','url':'fixture','sha256':'fixture'}
        with tempfile.TemporaryDirectory(dir=ingest.ROOT/'data') as folder:
            with patch.object(ingest,'OBJECTS',Path(folder)),zipfile.ZipFile(outer) as z:
                ingest.walk_zip(z,item,rows,inventory,failures)
            self.assertEqual([r['path'] for r in rows],['application.apk!/assets/module','top.wasm'])
            self.assertEqual(len({r['sha256'] for r in rows}),1)
            self.assertEqual(len(inventory),4)
            self.assertEqual(failures,[])

    def test_local_split_zip_boundary(self):
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('hello.txt','known payload')
        data=payload.getvalue()
        with tempfile.TemporaryDirectory() as folder:
            paths=[Path(folder)/str(i) for i in range(3)]
            for p,chunk in zip(paths,[data[:5],data[5:41],data[41:]]): p.write_bytes(chunk)
            with LocalParts(paths) as parts,zipfile.ZipFile(parts) as z:
                self.assertEqual(z.read('hello.txt'),b'known payload')

    def test_unsafe_paths_rejected(self):
        for path in ['../escape','/absolute','C:/windows','safe/../../escape','..\\escape']:
            with self.assertRaises(ValueError): ingest.safe_member(path)

    def test_invalid_nested_archive_recorded(self):
        rows,inventory,failures=[],[],[]
        ingest.inspect_file(io.BytesIO(b'invalid'),'broken.apk',7,{},rows,inventory,failures)
        self.assertEqual(rows,[])
        self.assertEqual(failures[0]['stage'],'inspect_member')

    def test_colon_in_virtual_zip_member_not_native_path(self):
        self.assertEqual(ingest.safe_member('Spyware:AndroidOS.GetFiles/a.wasm',virtual_zip_name=True),
                         'Spyware:AndroidOS.GetFiles/a.wasm')
        self.assertEqual(ingest.safe_member('links.php?go=http:example.test',virtual_zip_name=True),
                         'links.php?go=http:example.test')
        with self.assertRaises(ValueError): ingest.safe_member('Spyware:AndroidOS.GetFiles/a.wasm')
        with self.assertRaises(ValueError): ingest.safe_member('../escape',virtual_zip_name=True)


if __name__=='__main__': unittest.main()
