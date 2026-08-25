# False-Alarm Attribution for Multivariate Time-Series Anomaly Detection

Reference implementation and full result archive for:

> **Attributing False Alarms in Multivariate Time-Series Anomaly Detection:
> An Injection-Based Ground-Truth Protocol and a Method-Detector Matching Study**
> (manuscript under review; citation entry will be finalized upon publication)

## What this is

Code and archived results for a benchmark study of **false-alarm attribution**:
given an anomaly-detector alarm on a *process-normal* window, decide whether the
cause is **variable-level** (a drifting / stuck / noisy sensor channel) or
**mode-level** (a legitimate operating mode absent from training), and evaluate
the verdict through repair actions.

The study covers **10 attribution methods** (counterfactual replacement family,
reconstruction, gradient, Granger, exact Shapley, model-free deviation, random
control), **5 detectors** (isolation forest, PCA, one-class SVM, deep MIL,
Anomaly Transformer) and **5 public testbeds** (SWaT, SMD, MetroPT3, PSM, SMAP),
organised into **62 evaluation units** and **19 detector-data-set pairs**, plus a
**five-annotator human-reference validation** on natural alarms.

## Repository layout

```
code/       all source (fixed seeds throughout)
  common.py             shared config (window length, splits, FAR targets)
  scorers_new.py        PCA / OCSVM detectors; scorers_rescore.py  iforest rescore
  scorers_at.py         Anomaly Transformer units
  injection/            fault-injection engine (drift / stuck / variance / joint)
  rcca/                 RC-CA reference implementation + regime bank
  baselines/            CondAttr (UMAP reimplementation) and other baselines
  evaluation/           two-layer evaluation, calibration, bootstrap, gt_pool
  fa_collection/        natural false-alarm collection and probes
  regimes/              GMM mode construction
  scripts/              every experiment entry point (see below)
results/    archived JSON result tables (one per manuscript table/figure)
```

## Data acquisition (not redistributed here)

All datasets are public and must be downloaded independently:
- **SWaT** - iTrust, SUTD (attack-rows-only variant used)
- **SMD** - OmniAnomaly release, machine-1-1
- **MetroPT3** - UCI Machine Learning Repository, dataset 791
- **PSM** - eBay/Pulsar release
- **SMAP** - NASA telemetry release (channel subset)

Place them under `code/datasets_local/` following the loaders in
`code/common.py`.

## Reproducing the main results

All entry points are in `code/scripts/` and write JSON to `code/_cache/`
(the archived copies are in `results/`). Key scripts:

| Manuscript item | Script(s) |
|---|---|
| Evaluation units / protocol | `evaluation/gt_pool.py`, `run_stage0_anchor.py` |
| Ten attribution methods, main comparison | `run_full_suite.py`, `run_new_scorers.py`, `run_wilcoxon.py` |
| Bootstrap CIs | `run_bootstrap_ci.py` |
| SHAP baselines | `run_shap_attr.py`, `run_shap_top3.py`, `run_shap_cmhmil.py`, `run_new_scorers_shap.py` |
| Method-detector matching table | `build_detector_table.py` |
| DAAS / DAAS-v2 selection rule | `add_daas.py`, `update_daas_final.py`, `run_daas_v2.py` |
| Repair loop (incl. stronger baselines) | `run_repair_experiment.py`, `run_repair_guided2.py`, `run_repair_v3.py`, `run_repair_pca.py` |
| Natural-alarm probes + human annotation | `run_natural_validation.py`, `run_natext.py`, `make_label_package.py`, `run_t02b.py` |
| Assumption audit (A1/A4) | `run_proposition_checks.py`, `run_audit_ext.py`, `validate_treeshap.py` |
| Seed / robustness analyses | `analyze_seeds.py`, `analyze_seeds3.py`, `run_new_scorers_seeded.py` |
| Supplementary-table generation | `make_supplement.py`, `make_supplement_jiis.py` |

Every random component is seeded; the archived `results/*.json` are the exact
numbers reported in the manuscript and its supplementary tables (S1-S20).

## Results archive map (selection)

`main_results.json` (Tables 2/4), `bootstrap_ci.json` (Table S3),
`repair_guided2.json` / `repair_v3.json` / `repair_pca.json` (Tables S6/S19 and
the PCA replication), `natural_validation.json` (natural-alarm section),
`t02b_results.json` + `label_windows_meta.json` (Table S20 human-reference check),
`daas_v2.json` (Table S18), `seed_stability_3seed.json` (Table S17),
`at_ext_all.json` (transformer variable-level units),
`validate_treeshap.json` (SHAP fidelity probe).

## License

MIT (see `LICENSE`). The datasets remain under their respective licenses.

## Contact

Lei An (corresponding author) - Department of Artificial Intelligence,
Baoding University - anlei@bdu.edu.cn
