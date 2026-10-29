"""Stage the installed rustc's matching Wasm stdlib inside this workspace.

No rustup settings or system toolchains are modified. Download is hash checked
against the manifest shipped with the installed compiler, before extraction.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
target = ROOT / '.tools' / 'masters-security-rust'
sysroot = Path(subprocess.check_output(['rustc', '--print', 'sysroot'], text=True).strip())
manifest = (sysroot / 'lib/rustlib/multirust-channel-manifest.toml').read_text(encoding='utf8')
section = re.search(r'\[pkg\.rust-std\.target\.wasm32-unknown-unknown\]\n(.*?)(?=\n\[)', manifest, re.S).group(1)
url = re.search(r'^xz_url = "([^"]+)"', section, re.M).group(1)
expected = re.search(r'^xz_hash = "([^"]+)"', section, re.M).group(1)
target.mkdir(parents=True, exist_ok=True)
archive = target / 'rust-std.tar.xz'
if not archive.exists():
    with urllib.request.urlopen(url, timeout=45) as response, archive.open('xb') as output:
        shutil.copyfileobj(response, output)
actual = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual != expected:
    raise RuntimeError('Archive hash mismatch; refusing to extract')
# Extract only ordinary library files; never follow an archive link or execute
# an installer. All destinations are checked to stay within the local sysroot.
prefix = 'rust-std-nightly-wasm32-unknown-unknown/rust-std-wasm32-unknown-unknown/'
destroot = (target / 'sysroot').resolve()
count = 0
with tarfile.open(archive, 'r:xz') as tf:
    for member in tf:
        if not member.name.startswith(prefix + 'lib/') or not member.isfile():
            continue
        dest = (destroot / member.name[len(prefix):]).resolve()
        if destroot not in dest.parents:
            raise RuntimeError('Archive path escapes local sysroot')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tf.extractfile(member) as src, dest.open('wb') as output:
            shutil.copyfileobj(src, output)
        count += 1
linker = sysroot / 'lib/rustlib/x86_64-pc-windows-msvc/bin/rust-lld.exe'
if not linker.is_file():
    raise RuntimeError('Expected the installed Windows Rust LLD')
record = {'url':url, 'sha256':actual, 'archiveBytes':archive.stat().st_size,
          'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),
          'sysroot':str(destroot), 'linker':str(linker), 'libraryFiles':count}
(target/'toolchain.json').write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps(record))
