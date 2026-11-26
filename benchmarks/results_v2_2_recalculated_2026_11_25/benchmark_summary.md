# ArchSynth v2.2 Recalculated Benchmark Summary (2026-11-25)

This report presents the recalculated, non-fabricated benchmark results for **ArchSynth v2.2** across all six target repositories in `skip_llm=True` deterministic mode. All previous benchmark directories (`benchmarks/comparison_matrices/`, `benchmarks/reports/`) were preserved untouched.

## 1. Cross-Repository Summary

| Repository | Commit SHA | Prod / Test Nodes | Launch Files | Subsystems | Evidence Coverage | Time (s) | GT Available | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Navigation2** | `6dbf4549ae1914188916b06dcc19dd3a8115d0a5` | 30 / 47 | 41 | 12 | 100.0% | 11.464 | Yes | Completed |
| **SLAM Toolbox** | `eee0cd5e4a161bb10f8334b5420c93876b31ca99` | 10 / 0 | 7 | 3 | 100.0% | 2.608 | No | Completed |
| **ROS 2 Control** | `4052b56d53bdcb62653935255d118f203398b22` | 1 / 5 | 1 | 2 | 100.0% | 6.564 | No | Completed |
| **Kinova Jaco2 Devkit** | `993a6e3de05e50fec4ce40c65a5b1d3a9d8ca9cc` | 11 / 0 | 12 | 6 | 100.0% | 1.695 | Yes | Completed |
| **BehaviorTree.CPP** | `365b2e499d34ba1220588188a7aa045158909b0f` | 2 / 0 | 0 | 1 | 100.0% | 6.638 | No | Completed |
| **Express.js (Negative Control)** | `a3714473feb3d2908add734d340e7755fd85e0a3` | 0 / 0 | 0 | 0 | N/A (0/0) | 1.031 | N/A | Rejected as non-ROS |

## 2. Entity Extraction Accuracy (Ground-Truth Evaluated Repositories Only)

> **Invariant check**: For every row below, `TP + FN = Ground Truth` and `TP + FP = Predicted`. Repositories without an independently verified ground-truth file (`slam_toolbox`, `ros2_control`, `behaviortree_cpp`) are marked `N/A` in `entity_metrics.csv`.

| Repository | Category | GT | Pred | TP | FP | FN | Precision | Recall | F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **nav2** | `nodes_core` | 13 | 29 | 13 | 16 | 0 | 0.4483 | 1.0000 | 0.6190 |
| **nav2** | `nodes_extended` | 22 | 29 | 20 | 9 | 2 | 0.6897 | 0.9091 | 0.7843 |
| **nav2** | `topics` | 15 | 67 | 10 | 57 | 5 | 0.1493 | 0.6667 | 0.2439 |
| **nav2** | `services` | 6 | 34 | 6 | 28 | 0 | 0.1765 | 1.0000 | 0.3000 |
| **nav2** | `actions` | 14 | 18 | 13 | 5 | 1 | 0.7222 | 0.9286 | 0.8125 |
| **jaco2_sim_devkit** | `nodes` | 11 | 11 | 11 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **jaco2_sim_devkit** | `topics` (source-declared basenames) | 8 | 8 | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **jaco2_sim_devkit** | `services` (source-declared) | 3 | 3 | 3 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **jaco2_sim_devkit** | `source_actions` | 0 | 0 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **jaco2_sim_devkit** | `api_inferred_actions` | 3 | 3 | 3 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **jaco2_sim_devkit** | `yaml_configured_actions` | 2 | 2 | 2 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |

## 3. Subsystem Clustering Metrics

- **Navigation2**: `mean_jaccard_similarity = 0.705`, `ARI = 0.1984`, `NMI = 0.6203` (13 evaluated nodes).
- **Kinova Jaco2 Devkit**: `ARI = 1.0000`, `NMI = 1.0000` (11 evaluated nodes).
- **SLAM Toolbox / ROS 2 Control / BehaviorTree.CPP**: `ARI / NMI = N/A` (no ground-truth partition file).

## 4. Ablation Study Summary

| Repository | Configuration | Status | Node F1 | Topic F1 | Service F1 | Action F1 | Time (s) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **nav2** | Baseline A: Static Regex-only | Executed | 0.0000 | 0.1322 | 0.0000 | 0.0000 | 0.320 |
| **nav2** | Baseline B: Multi-language AST (Phase 1) | Executed | 0.6190 | 0.0000 | 0.0000 | 0.0000 | 3.162 |
| **nav2** | Baseline C: Static + Launch (Phase 1+2) | Executed | 0.3611 | 0.0000 | 0.0000 | 0.0000 | 5.855 |
| **nav2** | Baseline D: Static + Launch + Comm (Phase 1-3) | Executed | 0.6190 | 0.2439 | 0.3000 | 0.8125 | 7.610 |
| **nav2** | Baseline E: Full ArchSynth Mode A (`skip_llm=True`) | Executed | 0.6190 | 0.2439 | 0.3000 | 0.8125 | 11.464 |
| **jaco2_sim_devkit** | Baseline A: Static Regex-only | Executed | 0.1000 | 1.0000 | 0.0000 | 0.0000 | 0.026 |
| **jaco2_sim_devkit** | Baseline B: Multi-language AST (Phase 1) | Executed | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.177 |
| **jaco2_sim_devkit** | Baseline C: Static + Launch (Phase 1+2) | Executed | 0.5946 | 0.0000 | 0.0000 | 0.0000 | 0.534 |
| **jaco2_sim_devkit** | Baseline D: Static + Launch + Comm (Phase 1-3) | Executed | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.643 |
| **jaco2_sim_devkit** | Baseline E: Full ArchSynth Mode A (`skip_llm=True`) | Executed | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.695 |
| **nav2 / jaco2** | LLM-only / Static + LLM / Mode B | **Unavailable** | N/A | N/A | N/A | N/A | N/A |
