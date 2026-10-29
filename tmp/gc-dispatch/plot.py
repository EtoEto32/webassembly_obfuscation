"""Plot saved O2 paired timing ratios; does not run experiments."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent / 'artifacts'
data = json.loads((root / 'timing.json').read_text())['times']
modes = ['structured', 'int-static', 'int-rotating', 'gc-static', 'gc-rotating']
fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
for ax, kernel in zip(axes, ['mix', 'gcd']):
    for i, mode in enumerate(modes):
        rows = [r for r in data if r['kernel'] == kernel and r['mode'] == mode and r['optimization'] == 'O2']
        ratios = []
        for row in rows:
            base = next(r for r in data if r['kernel'] == kernel and r['mode'] == 'structured' and r['optimization'] == 'O2' and r['round'] == row['round'])
            ratios.append(row['ns_per_run'] / base['ns_per_run'])
        ax.scatter([i + (j - 3) * .025 for j in range(len(ratios))], ratios, s=22, alpha=.75)
        med = sorted(ratios)[len(ratios)//2]
        ax.plot([i-.17, i+.17], [med, med], color='black', linewidth=2)
    ax.axhline(1, color='gray', linestyle='--', linewidth=.8)
    ax.set_xticks(range(len(modes)), modes, rotation=25, ha='right')
    ax.set_title('Integer mixer' if kernel == 'mix' else 'Bounded subtractive GCD')
    ax.grid(axis='y', alpha=.2)
axes[0].set_ylabel('Execution time / structured baseline (paired by round)')
fig.suptitle('Binaryen -O2; 7 rounds; dots = observations, bars = medians')
fig.tight_layout()
fig.savefig(root / 'paired-timing-O2.png', dpi=160)
fig.savefig(root / 'paired-timing-O2.svg')
plt.close(fig)
