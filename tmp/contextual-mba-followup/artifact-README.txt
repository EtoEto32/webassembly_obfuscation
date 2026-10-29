# Replicated Computational Results Artifact for Simplifying Mixed Boolean-Arithmetic Obfuscation by Program Synthesis and Equality Saturation

This artifact reproduces the empirical results of the TOSEM paper "Simplifying Mixed Boolean-Arithmetic Obfuscation by Program Synthesis and Equality Saturation". Please refer to the RCR Report for detailed information.


## Installation

The artifact ships as a self-contained Docker image. Either pull the prebuilt image:

```bash
docker pull ghcr.io/astean1001/promba-rcr:latest
docker tag ghcr.io/astean1001/promba-rcr:latest promba-rcr
```

or build it yourself from the artifact root (ProMBA and all external tools are fetched at build time):

```bash
docker build -t promba-rcr .
```

See `INSTALL` for details.


## What is reproduced

| Experiments                                   | Command             | Main Outputs                           |
|-----------------------------------------------|---------------------|----------------------------------------|
| Table 2 / Figure 4 (RQ1, RQ2)                 | `rcr.py table2`     | `table2.*`, `fig4_cactus.*`            |
| Table 3 (per-task component time & reduce)    | `rcr.py metrics`    | `table3.*`, `per_task_metrics.csv`     |
| Table 4 (RQ4, OnTheFly / Offline / NoLearn)   | `rcr.py learn`      | `table4.*`                             |
| Table 5 (RQ5, w/EqSat / NoEqSat)              | `rcr.py eqsat`      | `eqsat.*`                              |
| Table 6 (RQ5, Scoped / Full)                  | `rcr.py scoped`     | `table6.*`, `eqsat_subtasks.csv`       |
| Table 7 (RQ3, w/SimbaS / w/Duet / w/EUSolver) | `rcr.py synth`      | `table7.*`                             |
| Table 8 (RQ6, w/Opt / NoOpt)                  | `rcr.py opt`        | `opt.*`                                |
| Everything at once                            | `rcr.py all`        | all of the above                       |
| Custom benchmark                              | `rcr.py custom`     |`custom_results.csv`,`custom_summary.*` |

Outputs are written under `rcr-results/`. 

### Benchmarks
- 4,011 non-linear MBA expressions
  - MBA-Solver (polynomial 1008 + non-polynomial 1003)
  - QSynth (500)
  - Loki (loki 1000 + floki 500)

### Baselines

- [MBA-Solver](https://github.com/astean1001/MBA-Solver)
- [GAMBA](https://github.com/astean1001/GAMBA)
- [Syntia](https://github.com/RUB-SysSec/syntia)
- [GooMBA](https://github.com/HexRaysSA/goomba) : appears in the paper but is excluded from the image, as it is a closed-source IDA Pro plugin. To reproduce it, run `goomba/run_goomba.py` manually on a Windows machine with IDA Pro 9.1 and the GooMBA plugin installed.


## How to reproduce

```bash
# reproduce one experiment
mkdir -p rcr-results
docker run --rm -v "$PWD/rcr-results:/experiment/ProMBA/rcr/rcr-results" \
    promba-rcr python3 rcr.py table2 -j 8

# reproduce everything
docker run --rm -v "$PWD/rcr-results:/experiment/ProMBA/rcr/rcr-results" \
    promba-rcr python3 rcr.py all -j 8
```

Replace `table2` with any command above. Runs are checkpointed to `rcr-results/<exp>_runs.csv` and resume automatically. `--sample N` / `--datasets D` give a quick partial reproduction. See `python3 rcr.py -h` for all options.


## Run with your own benchmark

A 10-line sample benchmark (`sample-custom.txt`) is included:

```bash
docker run --rm promba-rcr python3 rcr.py custom --from-backup /experiment/ProMBA/rcr/sample-custom.txt
```

It auto-generates the required C benchmark from the `#complex,groundtruth` list and runs
ProMBA on it; ProMBA should reach the ground-truth size on all ten tasks. `INSTALL` shows the
expected output and how to add the baselines.


## License

The artifact itself (the RCR harness and documents) is released under the **MIT license** —
see [LICENSE](LICENSE). The image builds modified ProMBA source (the instrumentation used to
collect the metrics), which remains under ProMBA's **GNU GPL v3.0**. The third-party tools the
image builds (SimbaS, Duet, EUSolver, Omelet, MBA-Solver, GAMBA, Syntia) are fetched at build
time and retain their own upstream licenses.


## Layout

```
README  REQUIREMENTS  STATUS  INSTALL  LICENSE   # RCR document set
Dockerfile                                       # builds ProMBA + all external tools
requirements.txt                                 # Python deps for the harness
outputs/                                         # sample results from our own runs
rcr/
  rcr.py            # single entry point
  sample-custom.txt # 10-line example benchmark
  harness/          # experiment drivers, runner
  docker/           # in-image runner scripts for the baselines (GAMBA, Syntia)
  goomba/           # GooMBA runner (run manually under IDA Pro on Windows)
```

## Paper

This is the RCR artifact for the registered report published in TOSEM.

If you use this artifact, please cite:

```bibtex
@article{promba2026,
  title={Simplifying Mixed Boolean-Arithmetic Obfuscation by Program Synthesis and Equality Saturation},
  author={Lee, Jaehyung and Lee, Seoksu and Cho, Eunsun and Lee, Woosuk},
  journal={ACM Transactions on Software Engineering and Methodology},
  year={2026},
}
```
