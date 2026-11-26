# ArchSynth Project History: Major Corrections and Research Improvements

**Project**: ArchSynth v2.0 — Evidence-Grounded ROS 2 Architecture Recovery  
**Document**: `docs/project_history/major_corrections_and_improvements.md`  
**Last Updated**: November 2026 (Final Research Integrity Pass)

---

## 1. Executive Summary of Corrections

This document records the major architectural corrections, technical refinements, and research integrity audits performed on ArchSynth between the initial Midterm PoC (September 2026) and the Final Thesis Package release (November 2026).

---

## 2. Chronological Log of Major Improvements & Audits

### 2.1 SLAM Toolbox Endpoint Accounting & ROS 2 Native Reconciliation (Step 3C & Final Integrity Pass)
- **Problem**: Earlier iterations assumed a 1:1 mapping between C++ application interface objects and ROS 2 communication endpoints, and mistakenly inherited legacy ROS 1 `InteractiveMarkerServer` behaviors (`update_full` latched topic).
- **Audit & Source Grounding**:
  - Pinned commit `eee0cd5e4a161bb10f8334b5420c93876b31ca99` (ROS 2 Jazzy) and upstream `interactive_markers` 2.5.5 were audited line-by-line.
  - Verified that ROS 2 Jazzy `InteractiveMarkerServer` refactored the legacy ROS 1 `update_full` topic into the `get_interactive_markers` service server.
  - Each `InteractiveMarkerServer` creates strictly 3 endpoints: 1 update publisher (`<ns>/update`), 1 feedback subscription (`<ns>/feedback`), and 1 service server (`<ns>/get_interactive_markers`).
  - Each `tf2_ros::TransformListener` spawns a dedicated hidden node (`transform_listener_impl_...`) subscribing to dynamic `/tf` (`VOLATILE`, depth 100) and static `/tf_static` (`TRANSIENT_LOCAL`, depth 100).
- **Reconciled Numerical Totals ($N=1$)**:
  - **Source Interface Declarations**: Exactly **37** (13 pub, 5 sub, 15 srv, 3 tf_b, 1 tf_l).
  - **C++ Application Interface Instances**: **143** across 7 deployment profiles.
  - **Active ROS Graph Entities**: **170** (73 topic publishers, 32 topic subscriptions, 65 service servers).
  - **DDS Transport Endpoints**: **235** (138 DataWriters, 97 DataReaders).
  - **`MergeMapsKinematic` Dynamic Formulas**:
    $$\text{Graph Entities} = 8 + 2N \qquad (\text{Baseline } N=0: 8, \quad N=1: 10)$$
    $$\text{DDS Endpoints} = 11 + 2N \qquad (\text{Baseline } N=0: 11, \quad N=1: 13)$$
- **Regression Verification**: `tests/test_slam_toolbox_interfaces.py` updated and verified with all 155 unit tests passing.

---

### 2.2 Navigation2 Node Inventory & Orthogonal 2D Classification Reconciliation
- **Problem**: Previous reports cited two seemingly disparate node distributions for Navigation2: "53 C++ + 13 Python = 66 nodes" vs. "22 production + 44 test = 66 nodes".
- **Resolution**: Both distributions represent orthogonal classification axes of the exact same 66 discovered nodes:
  - **Production Core Nodes (22)**: 21 C++ nodes (`bt_navigator`, `planner_server`, `controller_server`, `amcl`, `map_server`, etc.) + 1 Python utility node (`basic_navigator` in `nav2_simple_commander`).
  - **Test & Validation Nodes (44)**: 32 C++ test executables + 12 Python integration fixtures.
  - **Total**: $21 + 32 = 53$ C++ nodes, $1 + 12 = 13$ Python nodes. Total = 66.
- **Artifact Updated**: Added 2D contingency table across `docs/case_studies/nav2_case_study.md`, `docs/thesis_material/ai_handoff_guide.md`, and `docs/evaluation/results_and_discussion.md`.

---

### 2.3 Ground Truth Categorization & Research Integrity Relabeling
- **Problem**: Benchmark comparison tables previously listed uniform precision/recall/F1 scores without distinguishing between manual expert ground truth and automated AST extraction baselines.
- **Resolution**:
  - Formally categorized repositories into **Five Distinct Architectural Tiers**:
    1. *Tier 1: Production Multi-Package ROS 2 Stacks* (`nav2`, `slam_toolbox`)
    2. *Tier 2: Reusable Frameworks & Hardware Abstraction Libraries* (`ros2_control`)
    3. *Tier 3: Simulation Environments & Robotic Devkits* (`jaco2_sim_devkit`)
    4. *Tier 4: Decision Orchestration Engines* (`behaviortree_cpp`)
    5. *Tier 5: Non-ROS Negative Control Baseline* (`express`)
  - Labeled `nav2` as **Expert Ground Truth Verified**.
  - Labeled `slam_toolbox` as **Reconciled Specification Verified**.
  - Explicitly relabeled `ros2_control`, `jaco2_sim_devkit`, and `behaviortree_cpp` as **Preliminary / Automated AST Baselines** (rather than claiming ungrounded manual ground truth).
  - Documented exact TP, FP, FN confusion breakdowns in `docs/evaluation/results_and_discussion.md`.

---

### 2.4 Multi-Model Benchmarking & Statistical Hypothesis Testing Rigor
- **Problem**: Model comparison claims needed explicit versioning, prompt control documentation, and qualification of sample sizes.
- **Resolution**:
  - Pinned exact model identifiers: `gemini-2.5-flash`, `gemini-1.5-pro-002`, `gpt-4o-2024-08-06`, `claude-3-5-sonnet-20241022`, and `llama-3.1-70b-instruct` (Ollama).
  - Documented experimental protocol: 3 repeated runs across $N=5$ benchmark tasks under fixed prompt instructions, low temperature ($T = 0.2$), and strict Pydantic v2 schemas.
  - Stated statistical assumptions: Paired Student's $t$-tests assuming normal distribution of paired differences on identical codebases, pooled standard deviation for Cohen's $d$.
  - Added explicit research notes qualifying that statistical significance ($p < 0.001$) reflects controlled pilot evaluations on reference repositories, recommending larger sample sizes ($N \ge 30$) for universal generalization.

---

### 2.5 Clean UI Separation (Recovery on `/` vs. Benchmarks on `/benchmarks`)
- **Problem**: Experimental research metrics must not clutter the core architectural recovery user interface.
- **Resolution**:
  - The primary landing page (`/`) is dedicated strictly to automated architecture recovery, repository ingestion, live Markdown rendering, and ISO 42010 tabbed viewpoints.
  - Research evaluation metrics, model comparisons, context memory experiments (Exp A–F), and ablation studies are cleanly isolated on `/benchmarks`.
  - Presentation and thesis preparation slides are served on `/presentation`.
