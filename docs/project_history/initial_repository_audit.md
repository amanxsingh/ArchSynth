# ArchSynth v2.0 — Initial Repository Audit & Architectural Inventory

**Project**: ArchSynth v2.0 — Evidence-Grounded ROS 2 Architecture Recovery & Auto-Documentation  
**Author**: M.Tech Dissertation Research Candidate (Automation & Robotics, DIAT Pune)  
**Audit Date**: November 2026  
**Document Identity**: `docs/project_history/initial_repository_audit.md`  

---

## 1. Executive Summary

This audit establishes the baseline inventory of the ArchSynth v2.0 repository prior to final thesis consolidation. It comprehensively inspects the core source engine (`src/`), evaluation and benchmarking harness (`eval/`), web application frontend/backend (`web/`, `app.py`), case study repositories (`case_studies/`), test suites (`tests/`), output artifacts (`output/`), and documentation.

### Primary Objectives of Audit:
1. Catalog existing working functionality across all pipeline stages.
2. Verify repository provenance and isolation mechanisms.
3. Identify all existing Markdown reports and classify them for archival or thesis inclusion.
4. Establish the boundary separation between the primary **Architecture Recovery Engine** and the **Benchmarking / Research Evaluation Suite**.

---

## 2. Directory Structure and Component Breakdown

```text
archy/
├── src/                          # Core ArchSynth Static Analysis & Synthesis Engine
│   ├── ingestor.py               # Repository cloning, validation (package.xml), path resolution
│   ├── repo_identity.py          # Git provenance, commit SHA pinning, artifact isolation (.provenance.json)
│   ├── build_analyzer.py         # CMakeLists.txt & package.xml build system analysis
│   ├── cpp_analyzer.py           # C++ AST analysis, node discovery, component registration
│   ├── node_analyzer.py          # ROS 2 node extraction (Python AST + C++ heuristics)
│   ├── launch_analyzer.py        # Hierarchical launch file resolution, substitutions, profiles
│   ├── interface_extractor.py    # C++ and Python interface declaration extractor (Pub/Sub/Srv/Act/TF)
│   ├── communication_builder.py  # Graph edge builder, QoS analysis, deployment-predicted edges
│   ├── subsystem_synthesizer.py  # Graph modularity and spectral subsystem clustering
│   ├── lifecycle_analyzer.py     # LifecycleNode state machine and transition recovery
│   ├── plugin_analyzer.py        # pluginlib declaration and base class interface extraction
│   ├── bt_analyzer.py            # BehaviorTree.CPP XML tree structure and node recovery
│   ├── view_generator.py         # ISO/IEC/IEEE 42010 multi-view architecture generator
│   ├── architecture_constructor.py# System-level ArchitectureModel aggregator
│   ├── doc_generator.py          # Markdown manual and Mermaid diagram generator
│   ├── llm_client.py             # Dual-engine LLM provider (Google Gemini API + local Ollama)
│   ├── schema.py                 # Pydantic v2 domain schemas and data models
│   ├── evidence_validator.py     # Source traceability and unsupported entity validator
│   ├── architecture_diff.py      # Architecture drift detection across Git commits
│   └── drift_pipeline.py         # Multi-commit comparative analysis runner
│
├── eval/                         # Research Evaluation & Historical Benchmarking Harness
│   ├── metrics.py                # Precision, recall, F1, ARI/NMI clustering metrics
│   ├── evaluator.py              # Ground truth comparison engine
│   ├── comparator.py             # Cross-run architectural comparison
│   ├── build_ground_truth.py     # Ground truth generation utilities
│   ├── generate_benchmark_snapshots.py # Snapshot generator for evaluation
│   ├── ablation.py               # 5-stage ablation study runner
│   ├── subsystem_eval.py         # Clustering quality evaluation
│   ├── ground_truth/             # Reference architectural specifications (Nav2)
│   └── raw_runtime_logs/         # Historical ros2 cli runtime inspection logs
│
├── web/                          # Frontend Dashboard (Glassmorphism UI)
│   ├── index.html                # Main architecture recovery interface
│   ├── app.js                    # UI event handlers, REST client, Mermaid renderer
│   ├── style.css                 # Dark glassmorphic design system
│   └── presentation.html         # In-browser 10-slide research presentation deck
│
├── app.py                        # Flask REST API Server
├── case_studies/                 # Target ROS 2 Repositories (Pinned Commits)
│   ├── nav2/                     # Navigation2 (commit: 6dbf4549ae1914188916b06dcc19dd3a8115d0a5)
│   ├── slam_toolbox/             # SLAM Toolbox (commit: eee0cd5e4a161bb10f8334b5420c93876b31ca99)
│   ├── ros2_control/             # ros2_control (commit: 4052b56d53bdcb562653935255d118f203398b22)
│   ├── jaco2_sim_devkit/         # Kinova Jaco2 Simulation (commit: 993a6e3de05e50fec4ce40c65a5b1d3a9d8ca9cc)
│   ├── behaviortree_cpp/         # BehaviorTree.CPP (commit: 365b2e499d34ba1220588188a7aa045158909b0f)
│   └── express/                  # Non-ROS negative control baseline
│
├── tests/                        # 155-Test Verification & Regression Suite
│   ├── test_phase1_node_discovery.py
│   ├── test_phase2_launch_analysis.py
│   ├── test_phase3_interface_extraction.py
│   ├── test_phase4_architecture_recovery.py
│   ├── test_phase5_runtime_evaluation.py
│   ├── test_repository_isolation.py
│   ├── test_slam_toolbox_launch.py
│   ├── test_slam_toolbox_interfaces.py
│   ├── test_evidence_schema.py
│   ├── test_evidence_validator.py
│   ├── test_metrics_extended.py
│   └── test_architecture_diff.py
│
└── output/                       # Isolated Analysis Runs & Generated Documentation
    ├── nav2_pipeline/
    ├── slam_toolbox_pipeline/
    └── web_runs/
```

---

## 3. Existing Markdown Documents Audit & Classification

The root workspace contains several Markdown files created during previous development phases. Each is audited below:

| File Name | Size | Original Purpose | Classification | Action |
|---|---:|---|---|---|
| `README.md` | 6.1 KB | Quickstart & midterm summary | Outdated / Incomplete | Rewrite to reflect ArchSynth v2.0, architecture recovery UI, and benchmark separation. |
| `DEVELOPMENT_GUIDE.md` | 38.6 KB | Developer manual & stage explanations | Essential Project Evidence | Preserve & adapt into `docs/reproducibility/execution_guide.md` and `docs/system_architecture/`. |
| `MIDTERM_EVALUATION_MASTER_GUIDE.md` | 33.9 KB | Midterm defense guide & Q&A | Historical Midterm Artifact | Archive in `docs/archive/historical_reports/` and integrate into `docs/project_history/midterm_vs_post_midterm.md`. |
| `MIDTERM_REPORT_CONTEXT.md` | 59.7 KB | Midterm report background text | Historical Midterm Artifact | Archive in `docs/archive/historical_reports/` and synthesize into `docs/thesis_material/`. |
| `PROGRESS_AND_NOVELTY_REPORT.md` | 15.8 KB | Progress summary for advisor review | Historical Milestone | Archive in `docs/archive/historical_reports/` and reference in `phase_wise_development.md`. |
| `PROJECT_CONTEXT.md` | 12.3 KB | Early problem framing & goals | Historical Project Plan | Archive in `docs/archive/historical_reports/` and integrate into `docs/project_overview/`. |

---

## 4. Verification of Current System State

### 4.1 Test Suite Status
The test suite was executed across all test files using standard library `unittest`:
- **Total Test Cases**: 155
- **Passed**: 155
- **Failed**: 0
- **Errors**: 0
- **Execution Time**: ~5.97 seconds
- **Key Modules Tested**:
  - Python & C++ Node Discovery with Line-Number Evidence
  - Component Container Resolution (`ComposableNodeContainer`)
  - Launch Hierarchy Parsing, Remappings, and Profile Synthesis
  - C++ AST Interface Extraction & QoS Deduction (ROS 2 Jazzy defaults)
  - Lifecycle Node Analysis & Plugin Registration
  - Repository Identity & Provenance Verification (`.provenance.json`)
  - SLAM Toolbox Pinned Source & Endpoint Reconciliation (37 declarations, 143 C++ app instances, 170 graph entities, 235 DDS endpoints)

### 4.2 Case Study Status & Grounding
1. **Navigation2 (`nav2`)**: Pinned at commit `6dbf4549ae1914188916b06dcc19dd3a8115d0a5`. Verified baseline: 66 nodes, 41 launch files, 245 source interfaces, 2,168 runtime instances, 12 subsystems, 8 views.
2. **SLAM Toolbox (`slam_toolbox`)**: Pinned at commit `eee0cd5e4a161bb10f8334b5420c93876b31ca99` (ROS 2 Jazzy). Reconciled baseline: 7 profiles, 37 declarations, 143 C++ interface instances, 170 graph entities, 235 DDS transport endpoints.
3. **ros2_control (`ros2_control`)**: Pinned at commit `4052b56d53bdcb562653935255d118f203398b22`. Clean working tree.
4. **Kinova Jaco2 Simulation Devkit (`jaco2_sim_devkit`)**: Pinned at commit `993a6e3de05e50fec4ce40c65a5b1d3a9d8ca9cc`. Clean working tree.
5. **BehaviorTree.CPP (`behaviortree_cpp`)**: Pinned at commit `365b2e499d34ba1220588188a7aa045158909b0f`. Clean working tree.
6. **Express (`express`)**: Non-ROS baseline for negative validation.

---

## 5. Architectural Gap Analysis & Action Items

To satisfy the Master Prompt requirements for an M.Tech dissertation package:
1. **Frontend / Web UI Refinement**:
   - The main dashboard (`web/index.html`, `web/app.js`) currently displays an overview of nodes, launches, subsystems, and topics.
   - It must strictly represent **Architecture Recovery Only** — including Repository Identity & Provenance (URL, Branch, Commit SHA, ROS Distribution), Phase Progress (Phases 1 through 5), Subsystems, Lifecycle, Plugins, Behavior Trees, Architecture Views (Context, Functional, Component, Deployment, Lifecycle, Communication), Source Evidence, and Markdown Downloads.
   - Benchmarks must not be visible on the main page. A dedicated navigation link to a separate benchmarking view / workspace must be provided.
2. **Dedicated Benchmarking Workspace (`benchmarks/`)**:
   - Establish `benchmarks/` with standard structure: `repositories/`, `models/`, `experiments/`, `raw_results/`, `processed_results/`, `comparison_matrices/`, `statistical_analysis/`, `visualizations/`, `reports/`.
   - Populate verified comparative matrices and evaluation scripts.
3. **Dissertation Documentation Base (`docs/`)**:
   - Establish complete thesis chapters, architecture views, methodology guides, project history, AI handoff guide, and figure inventories.
4. **Final Research Package Creation**:
   - Build `ArchSynth_Thesis_Research_Package.zip` omitting virtual environments, large binary caches, and credentials.
