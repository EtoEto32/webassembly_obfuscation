"""Summarize saved experiments; does not rerun or add experimental cases."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report(main, audit, runtime, model, output):
    dirs = [Path(x).resolve() for x in (main, audit, runtime, model)]
    main, audit, runtime, model = dirs
    out = Path(output).resolve()
    if out.exists():
        raise FileExistsError(out)
    evidence = {}

    def read(directory, name):
        path = directory / name
        evidence[str(path)] = digest(path)
        return json.loads(path.read_text(encoding='utf-8'))

    verified = {}
    for directory in dirs:
        pins = read(directory, 'pins.json')
        for name, expected in pins.items():
            assert digest(directory / name) == expected, (directory, name)
        verified[directory.name] = len(pins)
    producer_checks = []
    for directory in dirs:
        for saved in directory.glob('source-*'):
            current = Path(__file__).parent / saved.name.removeprefix('source-')
            if current.suffix in ('.py', '.cjs') and current.exists():
                assert digest(saved) == digest(current), current
                producer_checks.append(str(saved))

    checks = read(main, 'checks.json')
    positive = [x for x in checks['results'] if not x['negative']]
    negative = [x for x in checks['results'] if x['negative']]
    assert all(x['mismatch'] == x['traps'] == 0 for x in positive)
    assert all(x['mismatch'] > 0 for x in negative)
    attacks = read(main, 'analysis.json')
    valid_attacks = [x for x in attacks if x['mode'] != 'bad']
    assert all(x['status'] == 'recovered' for x in valid_attacks)
    assert all(x['status'] == 'rejected' for x in attacks if x['mode'] == 'bad')
    dependency = read(main, 'dependency-attack.json')
    replay = read(audit, 'replay.json')
    assert all(x['byte_equal'] for x in replay)
    interpreter = read(audit, 'interpreter.json')
    initials = read(audit, 'initials.json')
    controls = read(audit, 'controls.json')
    assert all(x['status'] == 'rejected' for x in controls)
    measurements = read(runtime, 'runtime.json')
    summary = read(runtime, 'summary.json')
    analysis = read(runtime, 'analysis.json')
    transforms = read(main, 'transforms.json')
    model_result = read(model, 'model.json')
    assert len(measurements) == summary['processes'] == 45
    assert sum(len(x['measurement']['batches']) for x in measurements) == summary['batches'] == 405
    assert summary['short_batches'] == 0
    rows = []
    for row in summary['rows']:
        name, modes = row['name'], row['modes']
        chosen = [x for x in measurements if x['name'] == name]
        assert len({x['measurement']['verification'] for x in chosen}) == 1
        for mode, values in modes.items():
            samples = [x['measurement']['medianNs'] for x in chosen if x['mode'] == mode]
            assert len(samples) == 3 and statistics.median(samples) == values['median']
        rates = {x['mode']: x for x in analysis if x['name'] == name and x['opt'] == 'O3'}
        assert all(len(x['samples']) == 11 for x in rates.values())
        rows.append(dict(name=name, modes=modes,
            rotated_over_plain=modes['rotated']['median']/modes['plain']['median'],
            rotated_over_congruent=modes['rotated']['median']/modes['congruent']['median'],
            recovery_ms=rates['rotated']['recovery_median_ms'],
            recovery_over_congruent=rates['rotated']['recovery_median_ms']/rates['congruent']['recovery_median_ms'],
            read_ms=rates['rotated']['read_median_ms'],
            sum_of_medians_ratio=(rates['rotated']['read_median_ms']+rates['rotated']['recovery_median_ms'])/(rates['congruent']['read_median_ms']+rates['congruent']['recovery_median_ms'])))
    facts = dict(positive_conditions=len(positive), inputs=checks['inputs'],
        positive_calls=sum(x['calls'] for x in positive), negative_conditions=len(negative),
        recovered=len(valid_attacks), dependency_cycle=sum(x['status']=='cycle' for x in dependency),
        regenerated=len(replay), interpreter_calls=sum(x['calls'] for x in interpreter),
        extra_initial_calls=sum(x['calls'] for x in initials), controls=len(controls),
        pointwise_checks=model_result['pointwise_cases'], scalar_convergence_checks=model_result['convergence_cases'],
        processes=summary['processes'], batches=summary['batches'], short_batches=summary['short_batches'],
        rss_kib_range=[min(x['measurement']['maxRssKiB'] for x in measurements),max(x['measurement']['maxRssKiB'] for x in measurements)],
        transform_ms_range=[min(x['transform_ms'] for x in transforms if x['mode']!='bad'),max(x['transform_ms'] for x in transforms if x['mode']!='bad')],
        rows=rows, binaries=summary['binaries'])
    assert facts['positive_calls'] == checks['positiveCalls'] == 128016
    text = ['# 根への下降：保存済み実験の集計', '',
        '3種類の3演算マイクロベンチマーク。実アプリの結果ではない。', '',
        f"正{len(positive)}条件、{checks['inputs']:,}入力、{facts['positive_calls']:,}呼出しで不一致・追加trap 0。負{len(negative)}条件すべてで反例を得た。",
        f"適応的係数射影は{len(valid_attacks)}/{len(valid_attacks)}条件を回復。旧bit依存解析器のcycle拒否は定数対照にも発生し、新方式だけの効果ではない。",
        f"{len(replay)}本をbyte一致再生成。別WABT実行器{facts['interpreter_calls']}呼出し、追加初期値{facts['extra_initial_calls']}呼出し。",
        f"小語長の許容一段遷移{facts['pointwise_checks']:,}件と、スカラー収束{facts['scalar_convergence_checks']:,}ケースを検査。すべての関数Mの列挙ではない。", '',
        '## O3実行時間と回復費用', '',
        '実行時間は共通Wasmループ内の1反復あたりns。3 fresh Node processの中央値の中央値。各processはwarmup 16,384回、9batch。45process・405batchすべて10ms以上。API呼出し速度ではない。', '',
        '| 式 | 元式 ns | 合同保存 ns | 回転 ns（process間範囲） | 回転/元式 | 回転/合同保存 | 回復本体 ms | 回復本体比 | 読取込み中央値和の比 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        m=x['modes'];lo,hi=m['rotated']['range']
        text.append(f"| {x['name']} | {m['plain']['median']:.3f} | {m['congruent']['median']:.3f} | {m['rotated']['median']:.3f} ({lo:.3f}–{hi:.3f}) | {x['rotated_over_plain']:.2f} | {x['rotated_over_congruent']:.3f} | {x['recovery_ms']:.4f} | {x['recovery_over_congruent']:.3f} | {x['sum_of_medians_ratio']:.3f} |")
    text += ['', '回復費用の比較対象も合同保存版。各条件11回測定。読取込みの欄は二つの中央値の和の比で、total時間の中央値ではない。回転追加の解析本体費用増は小さく、読取のばらつきもある。通常版と回復版はO3後のbinaryが各式で一致した。', '',
        '定数対照は3Iであり、交差結合を持つ定数行列との同コスト比較ではない。回転の寄与は合同保存版との比較で判断する。', '',
        f"O3本体は元式48–50byte、合同保存306byte、回転333byte。全条件のlinear memoryは0。Node最大RSS範囲は{facts['rss_kib_range'][0]:,}–{facts['rss_kib_range'][1]:,}KiB（JIT等を含む）。変換時間は各条件単回で{facts['transform_ms_range'][0]:.2f}–{facts['transform_ms_range'][1]:.2f}ms。", '',
        'CPU affinity・周波数は未固定。小さな式に限られ、同コスト調整、実アプリ、汎用逆コンパイラ、人間の解析時間は未評価。有限試験を全入力の形式的同値性証明とはしない。', '',
        '## 判断', '',
        '任意の全域な状態依存係数を許す有限回収束の十分条件を保持する。一般収束理論や残差反復の発明とは主張しない。今回の構成では係数から元の式を射影でき、回転による追加の保護効果は実行費用に見合う形で示せなかった。独立した主発明として採用しない。', '']
    out.mkdir(parents=True)
    (out/'facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'report.md').write_text('\n'.join(text),encoding='utf-8')
    provenance=dict(input_hashes=evidence,verified_pin_counts=verified,producer_snapshot_checks=producer_checks,
        generator_sha256=digest(Path(__file__)),terminal_exit_code_observed=False,
        completion_evidence='All 45 runtime measurements, 18 analysis groups and final manifest present and hashes verified; original performance call exit output unavailable.')
    (out/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'pins.json').write_text(json.dumps({x.name:digest(x) for x in out.iterdir() if x.is_file()},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(positive_calls=facts['positive_calls'],recovered=facts['recovered'],verified=verified),ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    for name in ('main','audit','runtime','model','output'):
        parser.add_argument(name)
    args=parser.parse_args()
    report(**vars(args))
