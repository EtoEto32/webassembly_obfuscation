"""Aggregate Cryptic Bytes features by 22 source programs, not variant count."""
import collections
import csv
import hashlib
import json
import statistics

from analyze_corpus import CACHE, ROOT


OUT = ROOT / "results/provenance"
EVIDENCE = OUT / "cryptic-bytes-parent-evidence.json"
METRICS = (
    "bytes",
    "instruction_count",
    "br_table_in_loop_count",
    "nop_count",
    "data_section_entropy",
)


def load_feature(sha, memo):
    if sha not in memo:
        feature = json.loads((CACHE / f"{sha}.json").read_text(encoding="utf-8"))
        feature["nop_count"] = feature.get("opcodes", {}).get("nop", 0)
        memo[sha] = feature
    return memo[sha]


def median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def main():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    memo = {}
    rows = []
    for path, item in evidence.items():
        feature = load_feature(item["sha256"], memo)
        baseline = load_feature(item["comparison_baseline_sha256"], memo)
        method = item["declared_transformation"].split("/", 1)[0]
        row = {
            "path": path,
            "sha256": item["sha256"],
            "release_variant": item["release_variant"],
            "program": item["program"],
            "program_category": item["program_category"],
            "method": method,
            "declared_transformation": item["declared_transformation"],
            "analysis_status": feature["status"],
            "baseline_status": baseline["status"],
            "exact_bytes_equal_baseline": item["exact_bytes_equal_baseline"],
        }
        if feature["status"] == baseline["status"] == "ok":
            for metric in METRICS:
                value = feature.get(metric)
                base = baseline.get(metric)
                row[metric] = value
                row[f"baseline_{metric}"] = base
                if metric in ("bytes", "instruction_count"):
                    row[f"{metric}_ratio"] = value / base if base else None
                elif metric != "data_section_entropy":
                    row[f"{metric}_delta"] = value - base
            row["name_section"] = feature.get("name_section")
            row["baseline_name_section"] = baseline.get("name_section")
        rows.append(row)

    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / "cryptic-bytes-feature-pairs.csv").open(
        "w", encoding="utf-8", newline=""
    ) as dest:
        writer = csv.DictWriter(dest, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # First average within each source program; then summarize 22 program means.
    program_groups = collections.defaultdict(list)
    for row in rows:
        program_groups[
            (
                row["release_variant"],
                row["method"],
                row["program_category"],
                row["program"],
            )
        ].append(row)
    program_rows = []
    for key, members in sorted(program_groups.items()):
        release, method, category, program = key
        ok = [r for r in members if r["analysis_status"] == r["baseline_status"] == "ok"]
        program_rows.append(
            {
                "release_variant": release,
                "method": method,
                "program_category": category,
                "program": program,
                "variants": len(members),
                "analyzed_pairs": len(ok),
                "exact_bytes_equal_baseline": sum(
                    bool(r["exact_bytes_equal_baseline"]) for r in members
                ),
                "median_bytes_ratio": median([r.get("bytes_ratio") for r in ok]),
                "median_instruction_count_ratio": median(
                    [r.get("instruction_count_ratio") for r in ok]
                ),
                "mean_br_table_in_loop_delta": (
                    statistics.mean(r["br_table_in_loop_count_delta"] for r in ok)
                    if ok
                    else None
                ),
                "mean_nop_delta": (
                    statistics.mean(r["nop_count_delta"] for r in ok) if ok else None
                ),
            }
        )
    with (OUT / "cryptic-bytes-program-features.csv").open(
        "w", encoding="utf-8", newline=""
    ) as dest:
        writer = csv.DictWriter(dest, fieldnames=list(program_rows[0]))
        writer.writeheader()
        writer.writerows(program_rows)

    aggregate_groups = collections.defaultdict(list)
    for row in program_rows:
        aggregate_groups[
            (row["release_variant"], row["method"], row["program_category"])
        ].append(row)
    aggregate_rows = []
    for key, programs in sorted(aggregate_groups.items()):
        release, method, category = key
        aggregate_rows.append(
            {
                "release_variant": release,
                "method": method,
                "program_category": category,
                "source_programs": len(programs),
                "variant_occurrences": sum(r["variants"] for r in programs),
                "analyzed_pairs": sum(r["analyzed_pairs"] for r in programs),
                "program_median_bytes_ratio": median(
                    [r["median_bytes_ratio"] for r in programs]
                ),
                "program_median_instruction_count_ratio": median(
                    [r["median_instruction_count_ratio"] for r in programs]
                ),
                "program_mean_br_table_in_loop_delta": statistics.mean(
                    r["mean_br_table_in_loop_delta"] for r in programs
                ),
                "program_mean_nop_delta": statistics.mean(
                    r["mean_nop_delta"] for r in programs
                ),
            }
        )
    with (OUT / "cryptic-bytes-feature-summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as dest:
        writer = csv.DictWriter(dest, fieldnames=list(aggregate_rows[0]))
        writer.writeheader()
        writer.writerows(aggregate_rows)

    result = {
        "input": EVIDENCE.relative_to(ROOT).as_posix(),
        "input_sha256": hashlib.sha256(EVIDENCE.read_bytes()).hexdigest(),
        "pair_occurrences": len(rows),
        "unique_variant_sha256": len({r["sha256"] for r in rows}),
        "source_programs": len({r["program"] for r in rows}),
        "program_categories": dict(
            collections.Counter(
                {r["program"]: r["program_category"] for r in rows}.values()
            )
        ),
        "analysis_status_counts": dict(
            collections.Counter(r["analysis_status"] for r in rows)
        ),
        "aggregation": (
            "Variant metrics are paired to the author-path baseline. Medians are "
            "computed within each source program before source-program summaries; "
            "variant count does not weight source programs."
        ),
        "limitations": [
            "Author path labels establish declared transformations, not malicious deployment.",
            "Static feature changes do not independently prove semantics or obfuscation intent.",
            "Data-section entropy is not differenced when either member lacks data.",
        ],
    }
    (OUT / "cryptic-bytes-feature-summary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
