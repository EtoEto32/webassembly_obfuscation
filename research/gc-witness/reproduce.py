"""Run the bounded local R experiments in a new destination."""
import argparse,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
commands=[['experiment.py',a.out/'screen'],['controls.py',a.out/'controls'],['binaryen-probe.py',a.out/'binaryen','--seeds','32'],['execute-probe.py',a.out/'binaryen',a.out/'binaryen-execution'],['benchmark.py',a.out/'screen',a.out/'performance']]
for script,*args in commands:subprocess.run([sys.executable,str(HERE/script),*map(str,args)],check=True)
