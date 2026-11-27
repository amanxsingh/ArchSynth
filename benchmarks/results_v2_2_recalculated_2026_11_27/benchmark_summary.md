# ArchSynth v2.2 Updated Benchmark Summary (2026-11-27)

Recalculated across all six repositories after fixing confirmed C++/Python AST & TF extraction bugs and adding manually verified ground-truth datasets for `slam_toolbox` and `ros2_control`. Earlier snapshots (`benchmarks/results_v2_2_recalculated_2026_11_25/` and `benchmarks/reports/`) remain preserved untouched.

## 1. Fixes Applied
1. Excluded anonymous placeholder `"_"` C++ standalone nodes (`src/cpp_analyzer.py`), eliminating `nav2_ros_common::_` and `nav2_rviz_plugins::_` FPs.
2. Added CamelCase → snake_case fallback when C++ `node_name` is empty (`src/node_analyzer.py`), recovering `base_footprint_publisher` (`nav2`) and `controller_manager` (`ros2_control`).
3. Extended `src/interface_extractor.py` to skip `shared_from_this()`/`get_node_base_interface()` in `create_subscription`, `create_client`, and `create_action_server`, and added `nav2::create_transform_broadcaster`, `StaticTransformBroadcaster` (`/tf_static`), and `nav2::TransformListener` support.
4. Scoped benchmark interface evaluation strictly to non-test production nodes (`not node.is_test`) and created verified ground-truth files for `slam_toolbox` and `ros2_control`.

## 2. Updated Entity Extraction Accuracy (`benchmarks/results_v2_2_recalculated_2026_11_27/entity_metrics.csv`)

| Repository | Category | GT | Pred | TP | FP | FN | Precision | Recall | F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **nav2** | `nodes_core` | 13 | 28 | 13 | 15 | 0 | 0.4643 | 1.0000 | **0.6341** |
| **nav2** | `nodes_core_pkg_scoped` | 13 | 17 | 13 | 4 | 0 | 0.7647 | 1.0000 | **0.8667** |
| **nav2** | `nodes_extended` | 22 | 28 | 21 | 7 | 1 | 0.7500 | 0.9545 | **0.8400** |
| **nav2** | `topics` (prod) | 15 | 40 | 10 | 30 | 5 | 0.2500 | 0.6667 | **0.3636** |
| **nav2** | `services` (prod) | 6 | 26 | 6 | 20 | 0 | 0.2308 | 1.0000 | **0.3750** |
| **nav2** | `actions` (prod) | 14 | 17 | 13 | 4 | 1 | 0.7647 | 0.9286 | **0.8387** |
| **slam_toolbox** | `nodes` | 4 | 4 | 4 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **slam_toolbox** | `topics` | 14 | 14 | 14 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **slam_toolbox** | `services` | 14 | 14 | 14 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **ros2_control** | `nodes` | 1 | 1 | 1 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **ros2_control** | `topics` (prod) | 2 | 2 | 2 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **ros2_control** | `services` (prod) | 11 | 11 | 11 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **jaco2_sim_devkit** | `nodes` | 11 | 11 | 11 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **jaco2_sim_devkit** | `topics` (basenames) | 8 | 8 | 8 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **jaco2_sim_devkit** | `services` | 3 | 3 | 3 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **jaco2_sim_devkit** | `api_inferred_actions` | 3 | 3 | 3 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **jaco2_sim_devkit** | `yaml_configured_actions` | 2 | 2 | 2 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **behaviortree_cpp** | *(no GT file)* | N/A | 2 / 0 / 0 / 0 | N/A | N/A | N/A | N/A | N/A | N/A |
| **express** | *(neg. control)* | N/A | 0 / 0 / 0 / 0 | N/A | N/A | N/A | N/A | N/A | Rejected (`True`) |
