"""Plot saved preprocessing measurements, not mining throughput."""
import os
from pathlib import Path
import json
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1]/'data/matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from benchmark_normalization_processing import OUT, METHODS


def main():
    report = json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    names = list(dict.fromkeys(x['source'] for x in report['summaries']))
    labels = ['WAT roundtrip', 'Dedicated rules', 'Binaryen local', 'Binaryen O2']
    colors = ['#737373', '#0072B2', '#009E73', '#D55E00']
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), constrained_layout=True)
    titles = ['SWAMPED baseline', 'SWAMPED NOP', 'SWAMPED constant splitting',
              'xmr arithmetic substitution', 'A-Star instrumentation', 'CreaturePack ordinary']
    for ax, name, title in zip(axes.flat, names, titles):
        rows = [next(x for x in report['summaries'] if x['source'] == name and x['method'] == method) for method in METHODS]
        medians = [x['median_ms'] for x in rows]
        ax.barh(range(4), medians, color=colors)
        ax.errorbar(medians, range(4), xerr=[[x['median_ms']-x['min_ms'] for x in rows], [x['max_ms']-x['median_ms'] for x in rows]], fmt='none', color='black', capsize=3)
        ax.set_yticks(range(4), labels)
        ax.invert_yaxis()
        ax.set_title(title)
        ax.set_xlabel('Preprocessing time (ms)')
        ax.grid(axis='x', alpha=.25)
        ax.set_axisbelow(True)
    fig.suptitle('Implemented static pipelines: median and min-max of six repetitions\nIncludes input/output, tool startup and validation; each panel uses its own scale', fontsize=13)
    fig.savefig(OUT/'processing-times.png', dpi=160)
    fig.savefig(OUT/'processing-times.svg')
    plt.close(fig)


if __name__ == '__main__':
    main()
