# ArchSynth: Midterm vs. Post-Midterm Development & Novelty Audit

**Project**: ArchSynth v2.0 — Evidence-Grounded ROS 2 Architecture Recovery & Auto-Documentation  
**Academic Degree**: Master of Technology in Automation & Robotics  
**Institution**: Defence Institute of Advanced Technology (DIAT), Pune  
**Document**: `docs/project_history/midterm_vs_post_midterm.md`  
**Date**: November 2026  

---

## 1. Executive Overview

This document rigorously demarcates the research, engineering, and evaluation contributions completed prior to the **M.Tech Midterm Dissertation Review (September/October 2026)** from the substantial theoretical, architectural, and experimental advancements engineered during the **Post-Midterm Research Phase (October–November 2026, ArchSynth v2.0)**.

---

## 2. Comprehensive Midterm vs. Post-Midterm Comparison Table

| Area / Subsystem | Completed by Midterm (v1.0) | Implemented After Midterm (v2.0) | Final Dissertation Status | Concrete Source Evidence |
|---|---|---|---|---|
| **C++ AST & Symbol Extraction** | Basic regular expression heuristics matching `create_publisher` / `create_subscription`. | LibClang-based C++ AST parsing, class inheritance tracing, template type resolution, and exact line-range bounding. | **Production Ready** | `src/cpp_analyzer.py`, `src/build_analyzer.py` |
| **Launch Hierarchy & Deployment Resolution** | Basic flat parsing of `.launch.py` and `.launch.xml` files. | Recursive launch inclusion resolution, nested `GroupAction`, launch substitutions (`LaunchConfiguration`, `PathJoinSubstitution`), and multi-profile deployment synthesis (`standalone`, `composable`, `conditional`). | **Production Ready** | `src/launch_analyzer.py`, `test_phase2_launch_analysis.py` |
| **Component Containers** | Ignored or treated as regular single nodes. | Full support for `ComposableNodeContainer` as host and dynamically loaded component instances via `LoadComposableNodes`. | **Production Ready** | `src/launch_analyzer.py:650-780`, `test_composable_node_and_container` |
| **ROS 2 Communication Graph** | Preliminary topic matching between published strings and subscribed strings. | Strict topic, service, action, and TF broadcaster/listener extraction with QoS deduction (Reliability, Durability, History, Depth) aligned with ROS 2 Jazzy defaults (`geometry2` 0.36.4). | **Production Ready** | `src/communication_builder.py`, `src/interface_extractor.py`, `tests/test_slam_toolbox_interfaces.py` |
| **DDS Endpoint Accounting** | Assumed 1:1 mapping between C++ interface objects and DDS topics. | Complete decomposition: C++ interface declarations (37) $\rightarrow$ C++ application instances (143) $\rightarrow$ ROS graph entities (170) $\rightarrow$ DDS DataWriters/DataReaders (235). Hidden node expansion (`transform_listener_impl_...`) for TF. | **Mathematically Verified** | `tests/test_slam_toolbox_interfaces.py:test_72`, `step3c_runtime_endpoint_accounting_report.md` |
| **Subsystem Architecture** | Unconstrained LLM clustering based purely on node name heuristics. | Dual-strategy recovery: Graph Modularity (Louvain community detection over communication frequency matrix) + schema-constrained semantic labeling. | **Production Ready** | `src/subsystem_synthesizer.py`, `eval/metrics.py:ari_score` |
| **Lifecycle State Architecture** | Not implemented (flat node assumption). | Native `LifecycleNode` recovery: unconfigured, inactive, active, finalized state machine tracking, transition callbacks, and orchestrator mapping. | **Production Ready** | `src/lifecycle_analyzer.py`, `output/slam_toolbox_pipeline/lifecycle_graph.json` |
| **Plugin Architecture** | Not implemented. | `pluginlib` XML manifest parsing, export tags, base class interface inheritance extraction (`pluginlib::ClassLoader`). | **Production Ready** | `src/plugin_analyzer.py`, `output/ros2_control_pipeline/plugin_architecture.json` |
| **Behavior Tree Orchestration** | Not implemented. | BehaviorTree.CPP XML tree structure parsing, custom node registration (`ActionNode`, `ConditionNode`), and navigation orchestration recovery. | **Production Ready** | `src/bt_analyzer.py`, `case_studies/behaviortree_cpp` |
| **Architecture Views Standard** | Single flat Mermaid flowchart. | **8 ISO/IEC/IEEE 42010 Aligned Architecture Views**: Context, Functional, Component, Deployment, Lifecycle, Communication, Plugin, and Behavior Tree. | **Standards Compliant** | `src/view_generator.py`, `src/doc_generator.py` |
| **Repository Provenance & Isolation** | Ingestion into shared `output/` directory causing cross-repository file overwrites. | Mandatory Git provenance verification (`repo_name`, `commit_sha`, `remote_url`, `branch`), isolated output directories, and `.provenance.json` cryptographic sidecars. | **Fully Isolated** | `src/repo_identity.py`, `tests/test_repository_isolation.py` |
| **Evaluation Case Studies** | Navigation2 preliminary run only. | **5 Production Case Studies + 1 Negative Control**: Nav2, SLAM Toolbox, ROS 2 Control, Kinova Jaco2 Devkit, BehaviorTree.CPP, and Express. | **Empirically Grounded** | `benchmarks/repositories/repository_registry.yaml` |
| **Empirical Benchmarking** | Simple P/R/F1 precision script. | Dedicated `benchmarks/` workspace: 5-model evaluation (Gemini 2.5 Flash, 1.5 Pro, GPT-4o, Claude 3.5, Llama 3.1 70B), context-memory experiments (Exp A–F), token efficiency, cost analysis, and ablation study. | **Thesis Ready** | `benchmarks/`, `web/benchmarks.html` |
| **Web UI Architecture** | Basic form showing raw Mermaid text and Markdown. | Clean separation: Main Dashboard dedicated exclusively to Architecture Recovery with tabbed views and provenance; dedicated `/benchmarks` dashboard for research evaluation. | **Production UI** | `web/index.html`, `web/benchmarks.html`, `app.py` |
| **Regression Testing** | 22 basic unit tests. | **155 automated unit & integration tests** passing with 100% success rate across all pipeline phases. | **100% Passing** | `tests/` (155 tests in 5.97s) |

---

## 3. Detailed Technical Narrative

### 3.1 What Was Originally Proposed at Midterm
At the midterm evaluation, ArchSynth was presented as a proof-of-concept pipeline demonstrating that Large Language Models could assist in creating architecture diagrams for ROS 2 systems. The original proposal envisioned:
1. Ingesting ROS 2 Git repositories via `git clone`.
2. Extracting Python AST node definitions.
3. Passing raw node and launch summaries to an LLM (Gemini or local Ollama).
4. Generating Markdown documentation with embedded Mermaid diagrams.

### 3.2 What Had Actually Been Implemented at Midterm
While the midterm presentation claimed end-to-end functionality, actual codebase inspection revealed significant limitations:
- **Heuristic Over-Simplification**: Node discovery relied on regex pattern matching rather than full C++ compiler AST or Clang symbol tables. Test nodes were frequently misclassified as production nodes.
- **Launch Naivety**: The launch analyzer could not resolve launch substitutions (e.g., `LaunchConfiguration('use_sim_time')`), conditional branches (`IfCondition`), or `ComposableNodeContainer` component loading.
- **DDS Interface Under-Recovery**: Only 4 topics and 2 services were originally recovered for SLAM Toolbox, completely missing all 37 core application interfaces.
- **Unconstrained LLM Hallucinations**: Without strict Pydantic v2 schema constraints on LLM outputs, models hallucinated non-existent topic names and node relationships at an unsupported entity rate of $6.5\%$ to $8.4\%$.
- **Output Contamination**: Analyzing multiple repositories in sequence overwrote artifacts in `output/` without verifying Git commit provenance.

### 3.3 Novel Technical Contributions Introduced Post-Midterm (ArchSynth v2.0)
Between October and November 2026, the candidate executed a fundamental re-architecture of ArchSynth:
1. **Evidence-Grounded AST Interface Extraction (`src/interface_extractor.py`)**: Built LibClang and AST extraction rules capturing exact source file paths and line ranges for all publishers, subscribers, services, actions, and coordinate transforms.
2. **Hierarchical Launch & Deployment Resolution (`src/launch_analyzer.py`)**: Implemented a symbolic execution visitor capable of evaluating nested launch trees, component containers, and deployment profiles.
3. **Formal ISO/IEC/IEEE 42010 Architecture View Generator (`src/view_generator.py`)**: Replaced the single flat diagram with 8 standardized architectural viewpoints addressing distinct stakeholder concerns.
4. **Subsystem Community Detection (`src/subsystem_synthesizer.py`)**: Introduced Newman's graph modularity over communication traffic matrices to objectively evaluate clustering cohesion before LLM semantic labeling.
5. **Cryptographic Provenance & Artifact Isolation (`src/repo_identity.py`)**: Developed an automated Git provenance validator attaching `.provenance.json` sidecars to all generated artifacts.
6. **Decomposed DDS Endpoint Accounting**: Solved the discrepancy between C++ object instances and DDS transport entities, accurately modeling hidden node expansion (`transform_listener_impl_...`) and ROS 2 Jazzy QoS defaults.
7. **Rigorous Empirical Benchmarking Suite (`benchmarks/`)**: Created multi-repository matrices, multi-model parity studies, and context-memory efficiency experiments (Exp A–F).
8. **155-Test Verification Harness**: Scaled test coverage from 22 to 155 comprehensive regression tests.

### 3.4 What Remains Incomplete & Future Work
To maintain total scientific integrity:
- **Dynamic Runtime Telemetry**: Static analysis accurately predicts deployment and interface configurations, but `RUNTIME_OBSERVED` is strictly set to 0 in case studies where no physical robot hardware or live bagfiles were executed. Live eBPF tracing remains future work.
- **Dynamic C++ Macro Expansion**: Heavily obfuscated dynamic string formatting inside C++ macros that construct topic names at runtime cannot be fully resolved statically without executing the compiler symbol table. ArchSynth flags these as `CONDITIONAL` or `UNRESOLVED`.
