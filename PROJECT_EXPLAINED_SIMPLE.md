# ArchSynth — Complete Beginner-to-Defense Guide (In Simple Words)

If you are opening this project fresh and want to understand **everything** from scratch — what ArchSynth is, why it exists, what every folder and file does, how our benchmark scores were calculated, and how to defend every number if a professor or reviewer asks you — this guide explains it all in plain language.

---

## 1. What Is This Project? (The Big Picture in Simple Words)

Imagine you are given a giant LEGO robot or a self-driving robot codebase (like **Navigation2** with hundreds of C++ and Python files across 44+ folders), and someone asks you:

> *"How does this robot actually work? Which program talks to which program? Which topic or service connects them? What starts when we run a launch file?"*

Normally, an engineer has to manually open dozens of C++ files, Python scripts, XML configs, YAML parameter files, and launch files, trace topic names by hand, and draw architecture diagrams themselves. And whenever developers update the code, those hand-drawn diagrams become outdated (**architectural drift**).

**ArchSynth** is an **automated software architecture recovery and documentation tool for ROS 2 (Robot Operating System 2)**.

Think of ArchSynth like an **automatic X-ray machine + blueprint maker for ROS 2 robot code**:
1. You give it a ROS 2 code repository (for example, Navigation2, SLAM Toolbox, ROS 2 Control, or Kinova JACO2).
2. Without needing to compile or run the robot first, ArchSynth reads the source code (C++ & Python), build files (`CMakeLists.txt`, `package.xml`, `setup.py`), configuration files (`.yaml`, BehaviorTree `.xml`, `pluginlib` `.xml`), and ROS 2 launch scripts (`.launch.py`, `.launch.xml`).
3. It extracts **facts with proof** (every discovered node, topic, service, and action comes with the exact `file:line_number` citation where it was found).
4. It groups nodes into logical subsystems, checks consistency, draws **8 standard architectural diagrams** (following the **ISO/IEC/IEEE 42010** international standard and **C4** model), and generates clean Markdown documentation plus a web dashboard.

---

## 2. Why Are We Doing This? (Why It Matters)

In ROS 2 robotics research and defense/industrial systems, there are two big problems:

1. **The Static Analysis Gap**: Basic code scanners can grep for `create_publisher(...)`, but they miss ROS 2 concepts:
   - What namespace or topic remapping does a launch file apply at startup?
   - Which nodes run as dynamic plugins (`pluginlib`) or inside a `ComposableNodeContainer`?
   - How do Lifecycle nodes (`Unconfigured -> Inactive -> Active`), Behavior Trees (Nav2 XML trees), and MoveIt/YAML controller configs fit together?
2. **The LLM Hallucination Gap**: If you just paste raw robot code into an AI like ChatGPT/Gemini and say *"draw the architecture"*, LLMs often **hallucinate** (invent topic names or connections that don't actually exist in the code) and burn huge amounts of tokens.

**ArchSynth's Core Idea**: Never let an AI guess the architecture from scratch! Instead:
- Let **deterministic code analyzers (AST + C++ + Launch + YAML parsers)** extract every entity and exact `file:line` evidence first (`ArchitectureModel` validated by strict **Pydantic** schemas).
- Use the LLM (when enabled/installed) **only** to write human-friendly explanations of the verified structure — or run purely deterministically (`skip_llm=True`) with **0% hallucinated entities**.

---

## 3. How ArchSynth Works (Step-by-Step Pipeline)

When you run `python -m src.main --repo <repo_path> --output <output_dir>` (or call `ArchSynthPipeline(PipelineConfig(..., skip_llm=True))` in Python), ArchSynth executes **5 clear stages**:

```text
[ROS 2 Repository]
   │
   ▼
Stage 1: Ingest & Identity (src/ingestor.py, src/repo_identity.py)
   │  Checks if it is actually a ROS 2 repo (rejects non-ROS repos like Express.js)
   │  and records exact Git URL, branch, and commit SHA.
   ▼
Stage 2: Node & Build Discovery (src/node_analyzer.py, src/cpp_analyzer.py, src/build_analyzer.py)
   │  Reads package.xml, CMakeLists.txt, setup.py, Python AST, and C++ files.
   │  Finds every ROS 2 Node class, functional node (create_node), executable, and test node.
   │  Output: nodes.json
   ▼
Stage 3: Launch Resolution (src/launch_analyzer.py)
   │  Walks launch files in lexical order, tracks namespaces/remappings (GroupAction),
   │  resolves ComposableNodeContainer targets, and flags opaque constructs (OpaqueFunction).
   │  Outputs: launches.json, launch_instances.json, node_launch_mapping.json, deployment_profiles.json
   ▼
Phase 3: Interface & Communication Graph (src/interface_extractor.py, src/communication_builder.py)
   │  Extracts publishers, subscribers, services, actions (source-declared, API-inferred, YAML config),
   │  and matches producers to consumers across source & deployment profiles.
   │  Outputs: interfaces.json, runtime_interfaces.json, communication_graph.json, communication_matrix.json
   ▼
Phase 4 & Stage 4: Architecture Synthesis & Validation
   │  - Subsystem clustering (src/subsystem_synthesizer.py) -> subsystem_model.json
   │  - Lifecycle state machines (src/lifecycle_analyzer.py) -> lifecycle_graph.json
   │  - Pluginlib manifests (src/plugin_analyzer.py) -> plugin_architecture.json
   │  - Behavior Trees (src/bt_analyzer.py) -> behavior_tree_model.json
   │  - Package Dependency Graph (src/build_analyzer.py) -> package_dependency_graph.json
   │  - 8 ISO/IEC/IEEE 42010 Views (src/view_generator.py) -> architecture_views.json
   │  - Inventory Reconciliation & Consistency Check (src/architecture_validator.py)
   │  - Master Model Assembly (src/architecture_constructor.py) -> architecture.json
   ▼
Stage 5: Evidence Validation & Documentation (src/evidence_validator.py, src/doc_generator.py)
      Verifies citations and renders human-readable README.md + per-node docs + Mermaid diagrams.
      Also served interactively via Flask (app.py + web/).
```

---

## 4. Complete Folder & File Guide (What Every File Is Made For)

Here is what every folder and key file in `d:\Web Dev\archy\` does:

### A. Root Files
| File / Folder | Purpose in Simple Words |
| :--- | :--- |
| `app.py` | **Web Server (Flask backend)**: Powers the browser UI at `http://localhost:5000`, handles repository runs, loads recovered reports, serves `/api/download/...` Markdown exports, benchmarks, and presentation pages. |
| `requirements.txt` | Lists Python dependencies (`pydantic`, `pydantic-settings`, `python-dotenv`, `google-generativeai`, `ollama`, `scikit-learn`, `numpy`, `pytest`, `pytest-cov`, `tqdm`, `pyyaml`, `GitPython`). |
| `.gitignore` | Tells Git which heavy/private files NOT to upload to GitHub (like `.venv/`, `.env`, `output/`, `case_studies/*/`, `raw_runs/`, `__pycache__/`), while keeping source code, tests, `eval/`, and curated `benchmarks/` results tracked. |
| `.env` / `.env.example` | Stores local API keys/config (e.g., `GEMINI_API_KEY`, `OLLAMA_HOST`). `.env` is ignored by `.gitignore` so secrets never leak. |
| `README.md` | Original v2.0 project landing README. |
| `ArchSynth_v2.2_Thesis_Presentation.pptx` | Latest v2.2 thesis presentation deck (18 slides). |

### B. `src/` — The Core ArchSynth Engine
Every module here does one specific job in the recovery pipeline:

| File | Role |
| :--- | :--- |
| `src/main.py` | **Main orchestrator** (`ArchSynthPipeline`): runs Stages 1 to 5 end-to-end from CLI (`python -m src.main`) or from `app.py`. |
| `src/schema.py` | **Blueprint rules (Pydantic v2 models)**: defines exact structures (`ROS2Node`, `InterfaceDeclaration`, `EvidenceItem`, `Subsystem`, `PackageDependencyGraph`, `ArchitectureModel`, etc.) so data stays clean and type-safe. |
| `src/ingestor.py` | **Stage 1**: Clones or opens a local folder and checks if it has ROS 2 markers (`package.xml`, ROS C++/Python patterns); rejects non-ROS repos like Express.js. |
| `src/repo_identity.py` | **Provenance guard**: Verifies Git repo name/URL/commit SHA and creates `.provenance.json` sidecar files so results from Nav2 and SLAM Toolbox never mix by mistake. |
| `src/build_analyzer.py` | **Build & Dependency parser**: Reads `package.xml`, `CMakeLists.txt`, and `setup.py` to find executables, plugin exports, `console_scripts`, and builds the **Package Dependency Graph** (`resolved_internal_package`, `resolved_ros_package`, `manifest_declared_external`, `unresolved_external_library`). |
| `src/node_analyzer.py` | **Stage 2 Python+Overall Node finder**: Uses Python AST to find `Node` subclasses and functional nodes (`rclpy.create_node`, `rclcpp.Node`), separates production vs. test nodes, and calls C++ analysis. |
| `src/cpp_analyzer.py` | **Stage 2 C++ analyzer**: Parses C++ `.cpp`/`.hpp` files to find `rclcpp::Node` / `rclcpp_lifecycle::LifecycleNode` subclasses, `make_shared<rclcpp::Node>`, and `RCLCPP_COMPONENTS_REGISTER_NODE`. |
| `src/launch_analyzer.py` | **Stage 3 Launch analyzer**: Parses `.launch.py`, `.launch.xml`, `.launch.yaml` in source order with scoped namespaces (`GroupAction`), tracks unresolved dynamic expressions (`OpaqueFunction`, `ExecuteProcess`), and generates `deployment_profiles.json`. |
| `src/interface_extractor.py` | **Phase 3 Endpoint finder**: Extracts publishers, subscribers, services, actions from Python AST (both positional and keyword args) and C++ (skipping `shared_from_this()` first args), MoveIt `.execute()` inference (context-aware), and YAML controller configs (`moveit_controllers.yaml`, `ros2_controllers.yaml`), tagging `claim_type` (`source_declared`, `api_inferred`, `config_declared`). |
| `src/communication_builder.py` | **Phase 3 Graph builder**: Matches publishers to subscribers, service clients to servers, and action clients to servers, separating `source_potential_edges`, `deployment_runtime_edges`, `unmatched_endpoints`, and `external_endpoints`. |
| `src/subsystem_synthesizer.py` | **Phase 4.1 Subsystem clustering**: Groups nodes into logical subsystems using generic ROS 2 role/interface affinity, communication links, co-launch frequency, and package boundaries (separating RViz UI panels, map tools, localization, control, planning, test nodes, client APIs). Computes bounded `intra_cohesion_score`, `coupling_internal`, `coupling_external`, and `interface_density`. |
| `src/lifecycle_analyzer.py` | **Phase 4.2**: Recovers ROS 2 Managed Lifecycle nodes (`on_configure`, `on_activate`, etc.) and `LifecycleManager` supervision chains (omitting fake diagrams when no lifecycle nodes exist). |
| `src/plugin_analyzer.py` | **Phase 4.3**: Reads `PLUGINLIB_EXPORT_CLASS` and plugin XML manifests + YAML server configurations to map base classes, available plugins, and configured plugins. |
| `src/bt_analyzer.py` | **Phase 4.4**: Parses BehaviorTree.CPP XML files (`NavigateToPose`, etc.), blackboard variables, and BT leaf bindings to ROS 2 action/service servers. |
| `src/view_generator.py` | **Phase 4.5**: Generates all **8 ISO/IEC/IEEE 42010 Mermaid views** strictly from `ArchitectureModel` data (no hardcoded repository diagrams). |
| `src/architecture_validator.py` | **v2.1/v2.2 Validator**: Builds the deduplicated `structured_node_inventory`, computes `compute_inventory_reconciliation` (so plugins/nodes/launch aliases are not double-counted), and flags `Confirmed`, `Warning`, `Unresolved`, and `Potential inconsistency` findings. |
| `src/architecture_constructor.py` | **Stage 4**: Assembles everything into the final `architecture.json` and runs inventory reconciliation + consistency validation. |
| `src/llm_client.py` | **LLM Wrapper**: Connects to Gemini or Ollama if installed & configured (and falls back cleanly if unavailable or `skip_llm=True`). |
| `src/doc_generator.py` | **Stage 5**: Turns `architecture.json` into `docs/README.md` and per-node Markdown documentation pages. |
| `src/evidence_validator.py` | Checks that every recovered node, topic, service, and action actually has a real `file:line` citation inside the repository (**Evidence Coverage**). |
| `src/architecture_diff.py` & `src/drift_pipeline.py` | Compares two Git commits of a repo to detect **architectural drift** (added/removed/changed nodes and interfaces). |
| `src/runtime_validator.py` & `src/nav2_reconciler.py` | Runtime ROS 2 introspection helper (for Linux/ROS 2 environments) and Nav2-specific audit reconciliation logic from an earlier verification step. |

### C. `eval/` — Evaluation Scripts & Ground-Truth Datasets
| File | Role |
| :--- | :--- |
| `eval/ground_truth/nav2/` | Manually verified ground-truth inventory for Navigation2 (`ground_truth.json`, `nodes.json`, `topics.json`, `services.json`, `actions.json`, `subsystems.json`). |
| `eval/ground_truth/jaco2_sim_devkit/ground_truth.json` | Manually verified ground-truth inventory created in v2.2 for JACO2 (11 nodes, 9 qualified / 8 basename topics, 3 services, 3 API-inferred actions, 2 YAML-configured actions, exact file:line evidence). |
| `eval/run_v22_benchmark.py` | **The v2.2 master benchmark runner**: Runs ArchSynth v2.2 across all 6 repos, computes exact Precision/Recall/F1/TP/FP/FN, ARI/NMI, staged ablation (Baselines A–E), and writes everything to `benchmarks/results_v2_2_recalculated_2026_11_25/`. |
| `eval/evaluator.py`, `eval/metrics.py`, `eval/comparator.py`, `eval/subsystem_eval.py`, `eval/ablation.py` | Evaluation metric helpers (`compute_prf1`, `compute_fuzzy_prf1`, `calculate_ari_nmi`), runtime comparison against archived logs in `eval/raw_runtime_logs/`, and legacy ablation baselines. |

### D. `benchmarks/` — Saved Experimental Results
| Path | Role |
| :--- | :--- |
| `benchmarks/results_v2_2_recalculated_2026_11_25/` | **Our current, honest, verified v2.2 benchmark results**: `benchmark_summary.md`, `repository_comparison.csv`, `entity_metrics.csv/.json`, `ablation_results.csv/.json`, `subsystem_metrics.json`, `ground_truth_comparison.json`, `execution_times.csv`, `evaluation_manifest.json`, `limitations_and_validity.md`, `logs/unittest_v22.log`, and raw outputs in `raw_runs/`. |
| `benchmarks/comparison_matrices/` & `benchmarks/reports/` | Earlier v2.0 benchmark tables & protocol docs (kept untouched for historical comparison). |
| `benchmarks/repositories/repository_registry.yaml` | Registry of target repos, URLs, pinned commit SHAs, and selection rationale. |

### E. `tests/` — Automated Verification Suite
- **10 `unittest`-compatible test files (`109` tests, all passing in `11.661s`)**:
  - `test_v22_research_validation.py` (v2.2 SLAM clustering separation, keyword-arg Python topics, `shared_from_this()` guard, inventory deduplication, JACO2 completeness)
  - `test_archsynth_improvements.py` (v2.1 MoveIt false-positive prevention, YAML actions, launch scoping, opaque constructs, package deps, bounded cohesion, data-driven views)
  - `test_phase1_node_discovery.py` through `test_phase5_runtime_evaluation.py`
  - `test_repository_isolation.py`, `test_web_api_regression.py`, `test_nav2_accuracy_reconciliation.py`
- **Other test files**: `test_slam_toolbox_interfaces.py`, `test_slam_toolbox_launch.py`, and 4 legacy `pytest`-only files (`test_architecture_diff.py`, `test_evidence_schema.py`, `test_evidence_validator.py`, `test_metrics_extended.py` — not run in the 109 log because `pytest` is not installed in the active environment).

### F. `web/`, `case_studies/`, `output/`, `docs/`, `scripts/`
- `web/`: Frontend HTML/CSS/JS (`index.html`, `app.js`, `style.css`, `benchmarks.html`, `presentation.html`) served by `app.py`.
- `case_studies/`: Local clones of the target repositories (`nav2`, `slam_toolbox`, `ros2_control`, `jaco2_sim_devkit`, `behaviortree_cpp`, `express`, etc.) used for offline static analysis.
- `output/`: Generated pipeline runs (`jaco2_sim_devkit_pipeline`, `nav2_v22_eval`, `slam_toolbox_v22_eval`, plus earlier `nav2_pipeline`, `nav2_corrected_pipeline`, `web_runs/`).
- `docs/`: Comprehensive thesis documentation, presentation verification notes (`docs/presentation/v2_2_presentation_verification_notes.md`), viva Q&As (`docs/presentation/viva_questions_and_answers.md`), and case-study writeups.
- `scripts/`: Utility script `package_thesis_archive.py`.

---

## 5. What We Have Done So Far (Evolution from v2.0 → v2.1 → v2.2)

1. **v2.0 (Baseline Prototype + Web App)**:
   - Built the 5-stage pipeline, Flask dashboard, Evidence Validator, Pydantic schemas, and initial benchmark tables.
   - *Bugs found in audits*: Web UI had routing/download bugs, Nav2 docs had stale counts, `view_generator.py` had hardcoded Nav2 Mermaid diagrams, and legacy benchmark tables reported near-100% scores (`97.7%`–`100%`) even on repos without ground-truth datasets.
2. **v2.1 (Generalization & Research Validity Fixes)**:
   - Removed all hardcoded repository-name Mermaid branches in `view_generator.py` — all 8 views are now genuinely generated from `ArchitectureModel`.
   - Added standalone/functional node discovery (`rclpy.create_node`, `rclcpp.Node`, `setup.py` `console_scripts`), recovering JACO2 from 9 → **11 nodes**.
   - Made MoveIt `.execute()` action inference context-aware (eliminating false positives on unrelated `.execute()` calls) and separated YAML controller configs.
   - Fixed Launch AST traversal to preserve lexical scope (`GroupAction`) and track unresolved dynamic launch expressions (`OpaqueFunction`, `ExecuteProcess`).
   - Built Package Dependency Graph (separating internal ROS vs external vs unresolved) and bounded `cohesion` to `[0.0, 1.0]` (`N/A` when `N < 2`).
3. **v2.2 (Accuracy, Ground-Truth Verification & Benchmark Recalculation)**:
   - Audited SLAM Toolbox and fixed why all 10 nodes had collapsed into one subsystem (`localization_state_estimation`): separated RViz UI nodes (`visualization_operator_ui`), offline map tools (`map_management_tools`), and localization/SLAM modes (**3 subsystems** instead of 1).
   - Fixed **Python keyword-argument topic extraction** (`jsp_gui_controller.py` `msg_type=..., topic=...`), recovering JACO2's missed 3 topics (bringing JACO2 to 100% topic recall).
   - Fixed **C++ `shared_from_this()` bug** in `nav2_lifecycle_manager::LifecycleManager` so `shared_from_this()` is no longer recorded as a topic/service name.
   - Fixed **Structured Node Inventory double-counting** (case-insensitive plugin deduplication, separating internal unmapped launch instances from true external ROS nodes, separating launch composable instances from source nodes).
   - Created manually verified JACO2 ground truth and recalculated honest, non-fabricated v2.2 benchmarks across all 6 repositories into `benchmarks/results_v2_2_recalculated_2026_11_25/`.
   - Cleaned `.gitignore` for GitHub readiness.

---

## 6. How to Back & Explain Your Benchmark Scores (Viva & Reviewer Guide)

If someone asks **"How did you calculate these numbers, what did you compare, and why should I trust them?"**, here is the exact, step-by-step explanation you can give:

### 6.1 What Repositories Are We Comparing (and Why These 6?)
We selected **6 diverse targets** spanning tiny Python robots to massive C++ production stacks, plus a negative control:
1. **Navigation2 (`nav2`)** (`6dbf4549...`) — Large multi-package C++/Python ROS 2 stack (30 prod + 47 test nodes, 41 launch files, Behavior Trees, Lifecycle, Plugins). *Has expert ground truth (`eval/ground_truth/nav2/ground_truth.json`).*
2. **SLAM Toolbox (`slam_toolbox`)** (`eee0cd5e...`) — Single-package C++ SLAM stack with 6 composable mode variants, RViz UI plugin, Solver plugin, and 7 launch files. *No curated GT file -> metrics marked `N/A`.*
3. **ROS 2 Control (`ros2_control`)** (`4052b56d...`) — Hardware abstraction & real-time controller manager framework (1 prod node, 5 test nodes, 25 component plugins). *No curated GT file -> metrics marked `N/A`.*
4. **Kinova JACO2 Devkit (`jaco2_sim_devkit`)** (`993a6e3d...`) — Medium 11-package Python manipulation robot using MoveIt 2, MoveIt Task Constructor, Servo, and Gazebo (11 nodes, 12 launch files). *Has full manually verified GT (`eval/ground_truth/jaco2_sim_devkit/ground_truth.json`).*
5. **BehaviorTree.CPP (`behaviortree_cpp`)** (`365b2e49...`) — C++ orchestration library largely framework-agnostic with minimal ROS 2 nodes (2 nodes, 0 launches, 0 topics). Tests whether ArchSynth handles pure C++ libraries gracefully.
6. **Express.js (`express`)** (`a3714473...`) — Popular Node.js web framework (**Negative Non-ROS Control**). Proves ArchSynth has 100% specificity and does NOT fabricate fake ROS 2 nodes/topics on non-robotics codebases (`0` nodes, `0` launches, `0` interfaces).

### 6.2 How Entity Accuracy (Precision, Recall, F1) Is Calculated
First, we **never blindly count raw lines** or duplicate declarations. Look at `eval/run_v22_benchmark.py`:
1. **Normalization (Canonical Basename Matching)**:
   - Take the predicted item (e.g., `/amcl_pose` or `/servo_node/joy`) -> strip leading `/`, take last segment after `/`, lowercase (`amcl_pose`, `joy`). Put into a unique Python `set` so duplicates aren't counted twice.
   - Do the same for the Ground Truth (`GT`) set.
2. **Count Set Overlaps**:
   - **TP (True Positives)** = items in **both** `Predicted` and `GT` (`len(pred_set & gt_set)`).
   - **FP (False Positives)** = items ArchSynth predicted that are **not** in `GT` (`len(pred_set - gt_set)`).
   - **FN (False Negatives)** = real items in `GT` that ArchSynth **missed** (`len(gt_set - pred_set)`).
   - **Sanity Invariant Check** (automatically asserted in code!):
     - `TP + FN == Ground Truth count`
     - `TP + FP == Predicted count`
3. **Formulas**:
   - $\text{Precision} = \frac{TP}{TP + FP}$ ("Out of everything ArchSynth extracted, how much was actually in the Ground Truth?")
   - $\text{Recall} = \frac{TP}{TP + FN}$ ("Out of everything in the Ground Truth, how much did ArchSynth manage to find?")
   - $\text{F1} = \frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$ (Harmonic mean balancing Precision and Recall)
   - *Zero-denominator rule*: When both `GT = 0` and `Pred = 0` (e.g., JACO2 `source_actions`), Precision = Recall = F1 = `1.0` (some slides display `N/A`); if only one side is 0, score = `0.0`.

#### Worked Example #1: Why Is Nav2 Precision `0.4483` While Recall Is `1.0000`?
If an examiner asks *"Why is Nav2 precision lower in v2.2 than the old 98.5% number?"*, this is your **best scientific answer**:
- Look at `entity_metrics.csv`:
  - `nodes_core`: `GT = 13`, `Pred = 29`, `TP = 13`, `FP = 16`, `FN = 0`
  - $\text{Precision} = 13 / 29 = 0.4483$ (`44.83%`), $\text{Recall} = 13 / 13 = 1.0000$ (`100%`), $\text{F1} = 0.6190$.
- **Why?** Because Nav2's `core_nodes` ground-truth file **only lists the 13 main server nodes** (like `bt_navigator`, `planner_server`, `controller_server`, `amcl`). Meanwhile, ArchSynth's AST parser actually found **all 29 unique production node names** in the repository (including real auxiliary nodes like `basic_navigator`, `collision_detector`, `costmap_filter_info_server`, `loopback_simulator`, `map_saver`, `following_server`, RViz nodes, plus 1 dummy `'_'`). Because our formula strictly checks against `core_nodes`, those extra 16 nodes are counted as `FP`, pulling Precision to `0.4483`!
- When compared against Nav2's larger **22-node `extended_nodes`** ground truth: `TP = 20`, `FP = 9`, `FN = 2` -> $\text{Precision} = 20 / 29 = 0.6897$, $\text{Recall} = 20 / 22 = 0.9091$, $\text{F1} = 0.7843$. The 2 misses (`FN`) are `base_footprint_publisher` (extracted as `basefootprintpublisher`, camelCase vs snake_case) and `costmap_2d_ros` (extracted as `costmap`).
- Same thing happens on Nav2 **Topics** (`GT = 15`, `Pred = 67`, `TP = 10`, `FP = 57`, `FN = 5` -> `P = 0.1493, R = 0.6667, F1 = 0.2439`) and **Services** (`GT = 6` unique basenames out of 8 qualified, `Pred = 34`, `TP = 6`, `FP = 28`, `FN = 0` -> `P = 0.1765, R = 1.0, F1 = 0.3000`): the Nav2 GT only covers the core subset, whereas ArchSynth extracts all 44 packages.

#### Worked Example #2: Kinova JACO2 (`jaco2_sim_devkit`)
- Because JACO2 has 11 packages, we manually inspected **100% of the source files** and verified:
  - **Nodes**: `GT = 11`, `Pred = 11`, `TP = 11, FP = 0, FN = 0` -> **P = 1.0, R = 1.0, F1 = 1.0**.
  - **Source Topics**: There are **9 qualified topics** in source (`arm_controller/joint_trajectory` and `gripper_controller/joint_trajectory` + 7 others). Under basename matching, both `*/joint_trajectory` share the basename `joint_trajectory`, giving **8 unique basenames**: `TP = 8, FP = 0, FN = 0` -> **P = 1.0, R = 1.0, F1 = 1.0**.
  - **Source Services**: `GT = 3`, `Pred = 3` (`/servo_node/start_servo`, `stop_servo`, `switch_command_type`) -> **F1 = 1.0**.
  - **Actions (Strictly Separated!)**:
    - `source_actions` (explicit `ActionClient`/`ActionServer` in code): `0` in GT, `0` predicted.
    - `api_inferred_actions` (`MoveItPy.execute()` / `MTC Task.execute()`): `3` in GT, `3` predicted -> **F1 = 1.0**.
    - `yaml_configured_actions` (`/arm_controller/follow_joint_trajectory`, `/gripper_controller/follow_joint_trajectory`): `2` in GT, `2` predicted -> **F1 = 1.0**.

### 6.3 Evidence Coverage vs. Extraction Accuracy (CRITICAL Distinction!)
Never confuse these two! If a reviewer asks, make this distinction crystal clear:
- **Evidence Coverage (`100.0%` on all 5 ROS repos)** checks: *"Does every entity ArchSynth reported have a valid `file:line` citation in the source tree?"* It measures **traceability / zero fabrication**, NOT completeness!
- **Precision / Recall / F1** check: *"Did we find ALL the true entities without false alarms compared to Ground Truth?"* You can have `100%` evidence coverage while still missing 3 topics (low Recall) — which is literally what we caught and fixed in JACO2 (`jsp_gui_controller.py` keyword arguments)!

### 6.4 Subsystem & Architecture Metrics Explained
- **Jaccard Similarity (`0.705` on Nav2)**: Overlap between nodes in a recovered subsystem and the reference Nav2 functional subsystem divided by their union.
- **ARI (Adjusted Rand Index) & NMI (Normalized Mutual Information)**: Standard clustering agreement scores (`Nav2: ARI = 0.1984, NMI = 0.6203`; `JACO2: ARI = 1.0, NMI = 1.0`). *Honest caveat from `v2_2_presentation_verification_notes.md`:* JACO2's GT labels (`pkg_*`) match ArchSynth's package-based fallback names, so JACO2 ARI/NMI = `1.0` verifies pipeline consistency rather than independent clustering power.
- **Cohesion (`E_internal / (N * (N - 1))`)**: Fraction of possible node-to-node pairs inside a subsystem that have direct communication links (`[0.0, 1.0]`, reported as `N/A` if `< 2` nodes).
- **Coupling Internal / External**: Edges crossing to other in-repo subsystems vs. unmatched endpoints talking to external ROS 2 servers (like MoveIt `move_group`).
- **Interface Density**: Average ROS 2 endpoints per node inside a subsystem.

### 6.5 Ablation Study (Why Every Stage Matters)
An **ablation study** removes parts of a system one by one to prove each piece contributes value:
- **Baseline A (Simple Regex only)**: Misses inheritance/AST context -> Nav2 Node F1 = `0.0000`, JACO2 Node F1 = `0.1000`.
- **Baseline B (Multi-language AST - Phase 1)**: Recovers C++/Python node classes cleanly -> Nav2 Node F1 = `0.6190`, JACO2 Node F1 = `1.0000` (Topics/Services/Actions still `0.0`).
- **Baseline C (+ Launch Analysis - Phase 1+2)**: Resolves launch instances & remappings (note: raw launch instance names include extra aliases, temporarily dropping node-only F1 on Nav2 to `0.3611` unless reconciled with source nodes).
- **Baseline D (+ Communication Graph - Phase 1–3)**: Extracts Topics, Services, Actions -> Nav2 Topic F1 = `0.2439`, Service F1 = `0.3000`, Action F1 = `0.8125`; JACO2 Topic/Service/Action F1 = `1.0000`.
- **Baseline E (Full ArchSynth Mode A, `skip_llm=True`)**: Adds Subsystems, Lifecycle, Plugins, Behavior Trees, Package Dependencies, Consistency Validator, and 8 ISO Views in `11.464s` (Nav2) / `1.695s` (JACO2).
- **LLM-only / Static + LLM (Mode B)**: Explicitly marked **`unavailable`** in `ablation_results.csv` because `google-generativeai` and `ollama` Python packages are not installed in this environment.

---

## 7. Honest Limitations (How to Answer Tough Questions)

Being honest about limitations makes research **stronger**, not weaker:
1. **Only 2 of 6 repositories have verified Ground Truth**: `nav2` and `jaco2_sim_devkit` have manually verified GT; `slam_toolbox`, `ros2_control`, and `behaviortree_cpp` are reported as `N/A` rather than guessing numbers.
2. **Nav2 vs JACO2 GT scopes differ**: Nav2's GT covers a core/extended subset (`13`/`22` nodes), whereas JACO2's GT covers `100%` of the small repo (`11` nodes). Therefore Nav2 precision (`0.4483`) and JACO2 precision (`1.0000`) reflect different GT scopes, not a drop in Nav2 quality.
3. **No live ROS 2 runtime graph here**: This Windows machine has no live ROS 2 DDS middleware running (`runtime_observation_available = False`). Files named `runtime_interfaces.json` represent **launch-resolved static predictions** (expanded across deployment profiles), not live `ros2 node list` measurements.
4. **No live LLM runs in v2.2 environment**: `google-generativeai` and `ollama` packages are not installed in `.venv` / Python 3.11 here, so LLM hallucination / narrative comparisons (Mode B) remain `unavailable` until installed.
5. **109/109 passing tests scope**: The `109` passing `unittest` log covers 10 test modules (`logs/unittest_v22.log`); 4 legacy `pytest`-only modules and 2 older SLAM Toolbox modules were outside that `unittest` run.

---

## 8. What We Want to Do Next (Roadmap)

1. **Create Verified Ground Truth for `slam_toolbox` & `ros2_control`**: Manually curate `eval/ground_truth/slam_toolbox/ground_truth.json` and `eval/ground_truth/ros2_control/ground_truth.json` so their `N/A` scores become empirically measured P/R/F1/ARI/NMI scores.
2. **Install LLM Clients & Run Mode B Comparison**: `pip install google-generativeai python-dotenv ollama` and run `skip_llm=False` vs `skip_llm=True` to empirically measure LLM narrative quality and unsupported-claim rates.
3. **Linux / Docker ROS 2 Runtime Validation**: Run `nav2` and `jaco2_sim_devkit` inside ROS 2 Jazzy/Humble on Ubuntu/Docker and execute `src/runtime_validator.py` to compare `source_potential_edges` / `deployment_runtime_edges` against live `ros2 topic/service/action/node` output.
4. **Fix Remaining Nav2 Edge Cases**: Clean out dummy node `'_'` from Python AST test/example files and normalize camelCase vs snake_case (`basefootprintpublisher` vs `base_footprint_publisher`).
5. **Initialize & Push Clean GitHub Repo**: Run `git init` at `d:\Web Dev\archy` (where `.gitignore` is already configured), verify `git status` excludes `output/`, `.venv/`, `.env`, `case_studies/*/`, and `raw_runs/`, and commit `src/`, `eval/`, `benchmarks/results_v2_2_recalculated_2026_11_25/`, `tests/`, `web/`, and `docs/`.

---

## 9. Quick Cheat-Sheet of Useful Commands

```powershell
# 1. Start the interactive Web UI (http://localhost:5000)
python app.py

# 2. Run ArchSynth on a single repository via CLI
python -m src.main --repo case_studies/jaco2_sim_devkit --output output/jaco2_sim_devkit_pipeline

# 2b. Or run explicitly in offline deterministic Mode A via Python
python -c "from src.main import ArchSynthPipeline; from src.schema import PipelineConfig; ArchSynthPipeline(PipelineConfig(repo_path='case_studies/jaco2_sim_devkit', output_dir='output/jaco2_sim_devkit_pipeline', skip_llm=True)).run()"

# 3. Re-run the full v2.2 6-repository benchmark & ablation study
python eval/run_v22_benchmark.py

# 4. Run the verified 10-module unittest suite (109 tests)
python -m unittest tests/test_v22_research_validation.py tests/test_archsynth_improvements.py tests/test_phase1_node_discovery.py tests/test_phase2_launch_analysis.py tests/test_phase3_interface_extraction.py tests/test_phase4_architecture_recovery.py tests/test_phase5_runtime_evaluation.py tests/test_repository_isolation.py tests/test_web_api_regression.py tests/test_nav2_accuracy_reconciliation.py
```
