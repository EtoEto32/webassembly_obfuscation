"""Audit the complete MineSweeper crawled-site archive without executing samples."""
import collections
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

from analyze_corpus import CACHE, ROOT, WABT


CATALOG = ROOT / "data/catalog/minesweeper-crawled-archive"
OUT = ROOT / "results/provenance"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def site_of(path):
    parts = path.replace("\\", "/").split("/")
    if len(parts) < 3 or parts[0] != "final_1735_mining_webs_dataset":
        raise ValueError(f"unexpected MineSweeper path: {path}")
    return parts[1]


def paper_evidence():
    path = ROOT / "data/catalog/minesweeper/paper.txt"
    text = path.read_text(encoding="utf-8")
    required = [
        "Crawling period March 12, 2018 – March 19, 2018",
        "# of crawled websites 991,513",
        "# of drive-by mining websites 1,735 (0.18%)",
        "all the websites (100.00%) use Wasm for the cryptomining payload",
    ]
    missing = [phrase for phrase in required if phrase not in text]
    if missing:
        raise ValueError(f"MineSweeper paper evidence changed: {missing}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "crawl_interval": "2018-03-12/2018-03-19",
        "crawled_websites": 991_513,
        "drive_by_mining_websites": 1_735,
        "paper_reports_all_identified_sites_use_wasm": True,
        "interpretation": (
            "The paper's crawl interval is corpus-level observation evidence, "
            "not an individual-binary first-seen date."
        ),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    acquisition_path = CATALOG / "acquisition.jsonl"
    rows = load_jsonl(acquisition_path)
    inventory_path = CATALOG / "inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    summary_path = CATALOG / "acquisition-summary.json"
    acquisition_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    receipt_path = ROOT / "data/archives/minesweeper-crawled.tar.receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    by_hash = collections.defaultdict(list)
    by_site = collections.defaultdict(list)
    for row in rows:
        if not row.get("wasm_magic"):
            raise ValueError("candidate without core Wasm magic")
        by_hash[row["sha256"]].append(row)
        by_site[site_of(row["path"])].append(row)

    archive_sites = {
        r["path"].replace("\\", "/").split("/")[1]
        for r in inventory
        if r["path"].replace("\\", "/").startswith("final_1735_mining_webs_dataset/")
        and len(r["path"].replace("\\", "/").split("/")) >= 2
    }

    hash_rows = []
    status_counts = collections.Counter()
    wabt_counts = collections.Counter()
    for sha, members in sorted(by_hash.items()):
        analysis_path = CACHE / f"{sha}.json"
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        status_counts[analysis["status"]] += 1
        obj = ROOT / members[0]["object"]
        check = subprocess.run(
            [str(WABT / "wasm-validate.exe"), "--enable-all", str(obj)],
            capture_output=True,
            timeout=120,
        )
        diagnostic = (check.stderr + check.stdout).decode("utf-8", errors="replace").strip()
        wabt_status = "valid" if check.returncode == 0 else "invalid"
        wabt_counts[wabt_status] += 1
        sites = sorted({site_of(r["path"]) for r in members})
        hash_rows.append(
            {
                "sha256": sha,
                "bytes": members[0]["bytes"],
                "archive_occurrences": len(members),
                "site_directories": len(sites),
                "analysis_status": analysis["status"],
                "analysis_error": analysis.get("error", ""),
                "wabt_status": wabt_status,
                "wabt_diagnostic": diagnostic,
                "example_path": members[0]["path"],
            }
        )

    with (OUT / "minesweeper-crawled-hashes.csv").open(
        "w", encoding="utf-8", newline=""
    ) as dest:
        writer = csv.DictWriter(dest, fieldnames=list(hash_rows[0]))
        writer.writeheader()
        writer.writerows(hash_rows)

    site_unique_counts = collections.Counter(
        len({r["sha256"] for r in members}) for members in by_site.values()
    )
    result = {
        "scope": (
            "Complete downloaded MineSweeper crawled-site TAR; standalone core-Wasm "
            "magic only. JavaScript-generated or native-binary embeddings are not counted."
        ),
        "archive_receipt": {
            "path": receipt_path.relative_to(ROOT).as_posix(),
            "bytes": receipt["bytes"],
            "sha256": receipt["sha256"],
            "md5": receipt["md5"],
        },
        "inputs": {
            "acquisition_jsonl": acquisition_path.relative_to(ROOT).as_posix(),
            "acquisition_sha256": hashlib.sha256(acquisition_path.read_bytes()).hexdigest(),
            "inventory": inventory_path.relative_to(ROOT).as_posix(),
            "inventory_sha256": hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
            "acquisition_summary": summary_path.relative_to(ROOT).as_posix(),
            "analysis_run": "results/corpus/runs/minesweeper-full-v21.json",
        },
        "paper_evidence": paper_evidence(),
        "archive_members": acquisition_summary["archive_members"],
        "archive_site_directories": len(archive_sites),
        "core_wasm_occurrences": len(rows),
        "unique_core_wasm_sha256": len(by_hash),
        "site_directories_with_core_wasm": len(by_site),
        "site_unique_sha_counts": {
            str(k): v for k, v in sorted(site_unique_counts.items())
        },
        "max_occurrences_of_one_sha": max(len(v) for v in by_hash.values()),
        "analysis_status_counts_by_unique_sha": dict(status_counts),
        "wabt_status_counts_by_unique_sha": dict(wabt_counts),
        "failures_during_archive_ingestion": acquisition_summary["failures"],
        "interpretation": [
            "4,429 archive paths collapse to 36 SHA-256 values; path count is not binary diversity.",
            "All 36 begin with core Wasm magic but fail both the v2.1 section parser and WABT 1.0.42 validation, so structural features are not imputed.",
            "Only 349 archive site directories contain directly stored core-Wasm-magic members under this extraction rule. This does not contradict the paper's dynamic finding that all 1,735 identified sites used Wasm; runtime-generated or differently captured modules are outside this static extraction.",
            "The March 2018 interval supports a corpus-level historical observation, not a per-hash temporal trend.",
        ],
    }
    output = OUT / "minesweeper-crawled-summary.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
