"""Reject synthetic/missing measurements. No mining measurement is fabricated."""
import csv
import json
import tempfile
from pathlib import Path
from compare_reference import compare


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        normal = root / 'normal'
        normal.mkdir()
        (normal / 'run-metadata.json').write_text(json.dumps({'input_sha256':'a'*64,'synthetic':True}))
        manifest = root / 'runs.csv'
        fields = ['run_id','run_directory','input_sha256','baseline_sha256','program','release','method']
        with manifest.open('w',newline='') as handle:
            writer = csv.DictWriter(handle,fieldnames=fields)
            writer.writeheader()
            writer.writerow(dict(run_id='normal',run_directory='normal',input_sha256='a'*64,
                baseline_sha256='a'*64,program='cn-0',release='binaries',method='unobfuscated'))
            writer.writerow(dict(run_id='missing',run_directory='missing',input_sha256='b'*64,
                baseline_sha256='a'*64,program='cn-0',release='binaries',method='llvm/cffobf'))
        table, runs = compare(manifest)
        assert all(item['summary'] is None for item in runs.values())
        assert all(item['speed_ratio_to_baseline'] is None for item in table)
        assert all(item['accepted'] is None for item in table)
        assert all(item['pool_correctness'] == 'not established' for item in table)
        assert 'real measurement' in runs['normal']['error']
        assert runs['missing']['error']
    print(json.dumps({'status':'passed','wasm_executed':False,'external_connection':False,
        'synthetic_input_rejected':True,'missing_input_not_imputed':True,
        'measurement_figure_generated':False}))


if __name__ == '__main__':
    main()
