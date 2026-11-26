# ArchSynth v2.2 presentation: verification notes

Deck: `ArchSynth_v2.2_Thesis_Presentation.pptx` (18 slides, project root).
Primary source: `benchmarks/results_v2_2_recalculated_2026_11_25/` (run 24–25 Nov 2026, `skip_llm=True`).

## What was checked against raw files

| Claim on slides | Verified against |
|---|---|
| Node, test, launch-file, interface, subsystem counts for all six repos | Recomputed from `raw_runs/<repo>/nodes.json`, `launches.json`, `interfaces.json`, `subsystem_model.json`; all match `repository_comparison.csv` |
| Nav2 / JACO2 precision, recall, F1 | `entity_metrics.csv`, `ground_truth_comparison.json`; TP+FN=GT and TP+FP=Pred hold in every row |
| Ablation F1 and times | `ablation_results.csv` / `.json` |
| Subsystem Jaccard / ARI / NMI | `subsystem_metrics.json`; Nav2 GT in `eval/ground_truth/nav2/subsystems.json` |
| 109 tests passed | `logs/unittest_v22.log` (UTF-16): "Ran 109 tests in 11.661s OK" |
| LLM experiments unavailable | `ablation_results.csv` reason column; `limitations_and_validity.md` |
| LLM call sites | `src/doc_generator.py` (narrative summary), `src/architecture_constructor.py` (subsystem fallback); providers in `src/llm_client.py` |

## Discrepancies found (all disclosed in the deck or its speaker notes)

1. **Nav2 launch instances: 120 vs 806.** `architecture.json` holds 120 instances (one per node declaration in the 41 launch files). `launch_instances.json` holds 806 records (one per include-chain context). Example: `controller_server` is declared twice in `navigation_launch.py` (lines 163 and 305) and expands to 32 records.
2. **Nav2 services: 8 → 6.** Basename matching collapses `manage_nodes` and `is_active` across the two lifecycle managers, so the GT used for scoring has 6 services, not the 8 in `ground_truth.json`.
3. **JACO2 actions differ between tables.** The ablation scores actions against a single deduplicated name (GT = 1). `entity_metrics.csv` splits actions into source 0 / API-inferred 3 / YAML-configured 2.
4. **0/0 convention.** `evaluation_manifest.json` says "0/0 → 1.0", so JACO2 `source_actions` is stored as F1 = 1.0. The deck shows it as N/A.
5. **JACO2 subsystem ARI = NMI = 1.0 is not independent evidence.** The GT `architectural_role` field uses `pkg_*` labels, which are exactly ArchSynth's package-fallback names (`eval/run_v22_benchmark.py`, `evaluate_jaco2_detailed`).
6. **Test coverage of the 109.** The log's command line is truncated. 109 equals the ten unittest-compatible modules, excluding `test_slam_toolbox_interfaces.py` (83) and `test_slam_toolbox_launch.py` (21). The four modules that import pytest (`test_architecture_diff`, `test_evidence_schema`, `test_evidence_validator`, `test_metrics_extended`; 42 tests) are also not in this log. No claim is made that these pass on v2.2.
7. **Express.js commit.** The manifest records `a3714473…`. Earlier reports cited `c031be5d…`.
8. **Superseded numbers.** Earlier reports quoted 22 production / 66 total Nav2 nodes and 98.5 / 97.0 / 97.7 % summary scores. v2.2 gives 30 / 77 nodes, and the summary scores have no run files behind them.
9. **File naming.** `runtime_interfaces.json` contains launch-resolved predictions, not runtime observations. `runtime_observation_available` is `false` in all six runs.

## Extraction errors cited on the limitations slide

- Nav2 false positives include records with empty names (`''`, `'_'`) and RViz panel nodes outside GT scope. In SLAM Toolbox, one RViz plugin declaration (`slam_toolbox_rviz_plugin.cpp:59`) is attributed to two node records.
- Nav2 false negatives: topics `/tf`, `/tf_static`, `/particlecloud`, `/map_metadata`, `/cmd_vel_nav`. Extended nodes `base_footprint_publisher` and `costmap_2d_ros` (recovered as `costmap`).
