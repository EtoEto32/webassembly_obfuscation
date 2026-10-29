"""Rebuild the three drivers, then reproduce smith comparisons locally."""
import argparse,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def command(args):subprocess.run(list(map(str,args)),cwd=ROOT,check=True)
def main(out,offline):
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    os.environ['CARGO_HOME']=str(ROOT/'.tools/wasm-migrate-cargo')
    assert (ROOT/'.tools/gc-witness-smith-patched/patch-provenance.json').exists(),'run fetch-smith.py and prepare-smith.py once first'
    for mode in ['stock','zero','pristine']:
        project='smith-pristine' if mode=='pristine' else 'smith-driver'
        cmd=['cargo','build','--manifest-path',HERE/project/'Cargo.toml','--release','--locked','--target-dir',ROOT/'.tools/gc-witness-smith-target']
        if offline:cmd+=['--offline']
        if mode=='zero':cmd+=['--features','zero']
        command(cmd)
        if mode!='pristine':shutil.copy2(ROOT/'.tools/gc-witness-smith-target/release/gc-witness-smith-driver.exe',ROOT/('.tools/gc-witness-smith-'+mode+'.exe'))
    cmd=['cargo','build','--manifest-path',HERE/'checker/Cargo.toml','--release','--locked','--target-dir',ROOT/'.tools/gc-witness-target']
    if offline:cmd+=['--offline']
    command(cmd)
    jobs=[('smith-cap-controls.py',[out/'caps']),('smith-experiment.py',[out/'generation','--seeds','64']),('smith-baseline-check.py',[out/'generation',out/'baseline']),('smith-input-experiment.py',[out/'generation',out/'inputs']),('smith-audit.py',[out/'generation',out/'inputs',out/'audit'])]
    for script,args in jobs:command([sys.executable,HERE/script,*args])
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--offline',action='store_true');a=ap.parse_args();main(a.out,a.offline)
