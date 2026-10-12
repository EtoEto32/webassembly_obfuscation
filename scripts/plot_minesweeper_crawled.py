"""Plot multiplicity in the complete MineSweeper crawled-site archive."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyze_corpus import ROOT


def main():
    source = ROOT / "results/provenance/minesweeper-crawled-hashes.csv"
    summary_path = ROOT / "results/provenance/minesweeper-crawled-summary.json"
    rows = list(csv.DictReader(source.open(encoding="utf-8")))
    rows.sort(key=lambda r: int(r["archive_occurrences"]), reverse=True)
    counts = [int(r["archive_occurrences"]) for r in rows]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.5))
    axes[0].bar(range(1, len(counts) + 1), counts, color="#365f91")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("SHA-256 rank")
    axes[0].set_ylabel("Archive path occurrences (log scale)")
    axes[0].set_title("Reuse of 36 byte-distinct bodies")
    axes[0].grid(axis="y", alpha=0.25)

    labels = ["Wasm paths", "site dirs\nwith core magic", "unique SHA"]
    values = [
        summary["core_wasm_occurrences"],
        summary["site_directories_with_core_wasm"],
        summary["unique_core_wasm_sha256"],
    ]
    bars = axes[1].bar(labels, values, color=["#8faadc", "#5b9bd5", "#264478"])
    axes[1].set_yscale("log")
    axes[1].set_ylabel("Count (log scale)")
    axes[1].set_title("Counting unit changes the scale")
    axes[1].grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, values):
        axes[1].text(
            bar.get_x() + bar.get_width() / 2,
            value * 1.12,
            f"{value:,}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.tight_layout()
    out = ROOT / "results/provenance/figures"
    out.mkdir(parents=True, exist_ok=True)
    stem = out / "minesweeper-crawled-multiplicity"
    for suffix in (".png", ".svg", ".pdf"):
        fig.savefig(stem.with_suffix(suffix), dpi=220, bbox_inches="tight")
    plt.close(fig)
    receipt = {
        "inputs": {
            source.relative_to(ROOT).as_posix(): hashlib.sha256(source.read_bytes()).hexdigest(),
            summary_path.relative_to(ROOT).as_posix(): hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        },
        "outputs": [
            stem.with_suffix(s).relative_to(ROOT).as_posix()
            for s in (".png", ".svg", ".pdf")
        ],
        "note": "Counts use archive paths, site directories with directly stored core-Wasm magic, and SHA-256; log scale is explicit.",
    }
    (out / "minesweeper-crawled-generation.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
