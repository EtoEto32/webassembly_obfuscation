"""Plot existing repeated measurements against static growth; no hashing runs."""

import csv

import hashlib

import json

import os

from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]

OUT = ROOT / 'results/runtime-mining/cross-dataset'

os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'data/matplotlib-cache'))

import matplotlib

matplotlib.use('Agg')

from matplotlib import font_manager

font_manager.fontManager.addfont('C:/Windows/Fonts/meiryo.ttc')

matplotlib.rcParams.update({'font.family':'Meiryo','pdf.fonttype':42,'axes.unicode_minus':False})

import matplotlib.pyplot as plt

import numpy as np



inputs = ['proof-of-theft/xmr-repeated-summary.json', 'swamped/controlled-pair-summary.json']

sources = []

groups = []

records = []

order_path = OUT / 'repetition-order-review.json'

order_data = order_path.read_bytes()

orders = json.loads(order_data)['experiments']

sources.append(dict(file='repetition-order-review.json', sha256=hashlib.sha256(order_data).hexdigest()))

round_ratios = {}

for experiment in orders:

    raw_bytes = (OUT / experiment['raw_report']).read_bytes()

    assert hashlib.sha256(raw_bytes).hexdigest() == experiment['raw_sha256']

    sources.append(dict(file=experiment['raw_report'], sha256=experiment['raw_sha256']))

    raw = json.loads(raw_bytes)

    field = 'method' if experiment['experiment'] == 'xmr' else 'name'

    reference = 'xmr-wasm' if field == 'method' else '046dc081-roundtrip'

    baseline = {s['repetition']:s for s in raw['samples'] if s[field] == reference}

    for comparison in experiment['comparisons']:

        samples = sorted([s for s in raw['samples'] if s[field] == comparison['method']], key=lambda s:s['repetition'])

        assert [s['repetition'] for s in samples] == [1,2,3]

        ratios = [(s['count']*1000/s['elapsed_ms']) / (baseline[s['repetition']]['count']*1000/baseline[s['repetition']]['elapsed_ms']) for s in samples]

        assert all(abs(a-b)<1e-12 for a,b in zip(ratios,comparison['within_round_ratios']))

        round_ratios[comparison['method']] = ratios

for file, family in zip(inputs, ['xmr-wasm', 'SWAMPED input controlled derivatives']):

    data = (OUT / file).read_bytes()

    rows = json.loads(data)

    sources.append(dict(file=file, sha256=hashlib.sha256(data).hexdigest()))

    base = rows[0]

    selected = rows[1:4] if family == 'xmr-wasm' else rows[1:]

    labels = ['平坦化', '基本ブロック\n分割（設定名）', '命令置換'] if family == 'xmr-wasm' else ['nop挿入', '整数定数の分割']

    group = []

    for row, label in zip(selected, labels):

        assert row['repetitions'] == 3

        ratio = row['median_hps'] / base['median_hps']

        assert abs(ratio - row.get('descriptive_throughput_ratio', row.get('throughput_ratio'))) < 1e-12

        r = dict(family=family, label=label, sha256=row['sha256'], baseline_sha256=base['sha256'],

            file_size_ratio=row['bytes']/base['bytes'], instruction_ratio=row['instructions']/base['instructions'],

            throughput_median_ratio=ratio,

            throughput_min_over_baseline_median=row['min_hps']/base['median_hps'],

            throughput_max_over_baseline_median=row['max_hps']/base['median_hps'],

            baseline_median_hps=base['median_hps'], baseline_min_hps=base['min_hps'], baseline_max_hps=base['max_hps'])

        assert abs(r['file_size_ratio']-row['size_ratio']) < 1e-12

        assert abs(r['instruction_ratio']-row['instruction_ratio']) < 1e-12

        method = row.get('method', row.get('name'))

        r.update({f'round_{i+1}_rate_ratio':v for i,v in enumerate(round_ratios[method])})

        group.append(r);records.append(r)

    groups.append(group)



fig, axes = plt.subplots(1, 2, figsize=(8.7, 3.5), gridspec_kw={'width_ratios':[3,2]}, layout='constrained')

styles = [('file_size_ratio', 'ファイルサイズ', '#4477AA', ''),

          ('instruction_ratio', '命令数', '#66CCEE', '///'),

          ('throughput_median_ratio', 'ハッシュ計算速度', '#228833', '')]

for ax, group, title in zip(axes, groups, ['xmr-wasm：公開バイナリ', 'SWAMPED：同じ条件で作成した変換版']):

    x = np.arange(len(group)); width = .23

    for j, (key, label, color, hatch) in enumerate(styles):

        values = [r[key] for r in group]; positions = x + (j-1)*width

        ax.bar(positions, values, width=width, label=label, color=color, hatch=hatch, edgecolor='#333333', linewidth=.4)

        if key == 'throughput_median_ratio':

            for round_ in range(1,4):

                ax.scatter(positions+(round_-2)*.045, [r[f'round_{round_}_rate_ratio'] for r in group],

                    marker='o', s=17, facecolor='white', edgecolor='black', linewidth=.7, zorder=4,

                    label='各測定回の基準版に対する速度の比' if round_ == 1 else None)

    ax.axhline(1, color='#666666', linestyle='--', linewidth=.8)

    ax.set_xticks(x, [r['label'] for r in group], fontsize=9)

    ax.set_title(title, fontsize=10)

    ax.set_ylim(0, 1.85); ax.set_axisbelow(True); ax.grid(axis='y', alpha=.2)

    ax.spines[['top','right']].set_visible(False)

axes[0].set_ylabel('基準版に対する比')

axes[0].legend(fontsize=7.5, loc='upper left', ncol=2)

fig.savefig(OUT / 'hash-structure-comparison.pdf')

fig.savefig(OUT / 'hash-structure-comparison.png', dpi=180)

plt.close(fig)

with (OUT / 'hash-structure-comparison.csv').open('w', newline='') as f:

    writer = csv.DictWriter(f, fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)

report = dict(sources=sources, plotted=records,

    omitted='xmr-wasm boguscf specimen: distinct explicit -O2 optimization condition; retained in the results table, excluded from this figure.',

    interpretation='Descriptive within-implementation ratios; not causal estimates. Static growth and measured throughput need not rank variants identically.',

    markers='Three individual within-round ratios: variant rate divided by the reference rate in the SAME recorded repetition group. Green bars remain ratios of separate medians. These differ in general. Points are not confidence intervals; blocks were measured sequentially, not simultaneously.',

    limitations='Different transformations and implementations occupy separate panels. No inference of independence, statistical significance, performance equivalence or cross-algorithm speed ranking.',

    executed_hashes=0)

(OUT / 'hash-structure-comparison.json').write_text(json.dumps(report, indent=2) + '\n')

print('Plotted five variants from existing summaries; no hash execution.')

