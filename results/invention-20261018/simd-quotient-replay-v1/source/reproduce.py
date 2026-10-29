"""Cross-platform one-command reproduction, no shell policy changes."""
import argparse
from pathlib import Path
import subprocess
import sys

ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);a=ap.parse_args()
root=Path(__file__).resolve().parents[2]
subprocess.run([sys.executable,str(Path(__file__).with_name('run.py')),str(a.output)],cwd=root,check=True)
cmd=[sys.executable,str(Path(__file__).with_name('finish.py')),str(a.output)]
if a.compare:cmd+=['--compare',str(a.compare)]
subprocess.run(cmd,cwd=root,check=True)
