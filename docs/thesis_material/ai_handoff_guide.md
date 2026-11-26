# ArchSynth v2.0 — AI Handoff & Thesis Generation Master Guide

> **IMPORTANT NOTICE FOR DOWNSTREAM AI SYSTEMS / LLMs**:  
> You have received the complete `ArchSynth_Thesis_Research_Package.zip`. This document is your primary instruction manual. Read it completely before generating any thesis chapters, presentations, research papers, diagrams, or viva voce answers.  
> **RULE #1**: All claims, numbers, node counts, and formulas must be strictly grounded in the verified evidence contained in this repository. Never hallucinate node counts, never fabricate token consumption figures, and never describe statically predicted internal matches as live hardware telemetry.

---

## 1. Project Identity & Academic Context

- **System Name**: ArchSynth (Version 2.0)
- **Full Project Title**: Evidence-Grounded ROS 2 Software Architecture Recovery, Hierarchical Deployment Resolution, and Standards-Based Auto-Documentation
- **Candidate Program**: Master of Technology (M.Tech) in Automation & Robotics
- **Academic Department**: Department of Robotics & Autonomous Systems
- **Host Institution**: Defence Institute of Advanced Technology (DIAT), Deemed to be University under Department of Defence R&D, Ministry of Defence, Pune, India
- **Academic Year**: 2025 – 2026

### Recommended Thesis Titles:
1. *Evidence-Grounded Architecture Recovery and ISO/IEC/IEEE 42010 Auto-Documentation for Robot Operating System 2 Codebases*
2. *LLM-Assisted Reverse Engineering and Hierarchical Deployment Resolution for Component-Based Robotics Software Systems*
3. *A Dual-Engine Static Analysis and Schema-Constrained Synthesis Framework for ROS 2 Architectural Recovery and Drift Detection*

---

## 2. Research Objectives & Core Questions

### Core Research Questions:
1. **RQ1 (Architectural Fidelity)**: To what extent can domain-specific static analysis (AST parsing and symbolic launch evaluation) reconstruct the true computational topology of ROS 2 systems compared to human expert ground truth?
2. **RQ2 (Hallucination Elimination)**: Does schema-constrained Pydantic generation eliminate unsupported entities and topic hallucinations compared to unconstrained LLM prompting?
3. **RQ3 (Context Memory & Token Efficiency)**: How does phase-based sequential context memory affect recovery accuracy, latency, and token consumption relative to full-repository context ingestion?
4. **RQ4 (Multi-View Standards Compliance)**: Can automated recovery synthesize all 8 distinct viewpoints of the ISO/IEC/IEEE 42010 architectural standard directly from source code and launch configurations?

---

## 3. Directory & File Navigation for Thesis Preparation

When writing specific thesis chapters or presentation slides, draw your evidence directly from these files:

| Thesis Component | Primary Source Files to Read |
|---|---|
| **Abstract & Introduction** | `docs/project_overview/project_overview.md`, `docs/project_overview/problem_statement.md` |
| **Literature Review & Related Work** | `docs/project_overview/research_gap.md`, `docs/thesis_material/references_and_citations.md` |
| **Methodology & Static AST Extraction** | `docs/methodology/research_methodology.md`, `src/cpp_analyzer.py`, `src/launch_analyzer.py`, `src/interface_extractor.py` |
| **System Architecture & Dual-LLM Engine** | `docs/system_architecture/overall_architecture.md`, `src/architecture_constructor.py`, `src/llm_client.py`, `src/schema.py` |
| **Experimental Design & Benchmarks** | `benchmarks/README.md`, `benchmarks/reports/benchmark_summary.md`, `benchmarks/comparison_matrices/` |
| **Results, Tables & Statistical Analysis** | `docs/evaluation/results_and_discussion.md`, `benchmarks/comparison_matrices/*.csv`, `benchmarks/statistical_analysis/` |
| **Case Study 1: Navigation2** | `docs/case_studies/nav2_case_study.md`, `output/nav2_pipeline/architecture.json` |
| **Case Study 2: SLAM Toolbox** | `docs/case_studies/slam_toolbox_case_study.md`, `step3c_runtime_endpoint_accounting_report.md` |
| **Case Studies 3, 4, 5** | `benchmarks/repositories/repository_registry.yaml`, `output/*_pipeline/` |
| **Midterm vs. Final Contributions** | `docs/project_history/midterm_vs_post_midterm.md`, `docs/project_history/phase_wise_development.md` |
| **Thesis Diagrams (Mermaid)** | `docs/thesis_material/figure_inventory.md` |
| **Viva Voce Defense Preparation** | `docs/presentation/viva_questions_and_answers.md`, `docs/presentation/slide_content.md` |

---

## 4. Verified Numerical Ground Truth (Do NOT Deviate from These Numbers!)

To ensure 100% mathematical consistency throughout the dissertation:

### A. Navigation2 (`nav2`) Pinned Commit: `6dbf4549ae1914188916b06dcc19dd3a8115d0a5`
- **Total Packages Analyzed**: 44
- **Total Source Nodes**: Exactly **66** (Reconciled 2D Classification: 21 C++ prod + 1 Python prod = 22 prod; 32 C++ test + 12 Python test = 44 test; Total C++ = 53, Total Python = 13)
  - *2D Contingency*: Production: 21 C++, 1 Py (`basic_navigator`) | Test: 32 C++, 12 Py | Total: 53 C++, 13 Py (Grand Total = 66)
- **Launch Files Parsed**: 41
- **Source Interface Declarations**: 245
- **Resolved Runtime Interface Instances**: 2,168
- **Deployment Profiles Resolved**: 18
- **Synthesized Subsystems**: 12
- **Recovered Architecture Views**: 8 (Context, Functional, Component, Deployment, Lifecycle, Communication, Plugin, Behavior Tree)
- **Precision / Recall / F1**: Precision = $98.5\%$, Recall = $97.0\%$, F1 = $97.7\%$

### B. SLAM Toolbox (`slam_toolbox`) Pinned Commit: `eee0cd5e4a161bb10f8334b5420c93876b31ca99` (ROS 2 Jazzy)
- **Total Packages Analyzed**: 1
- **Total Source Nodes**: 2 (`slam_toolbox::SlamToolbox`, `map_merging`)
- **Launch Profiles**: 7 independently analyzed deployment profiles
- **Source-Level Interface Declarations**: Exactly **37**
  - 13 Publishers
  - 5 Subscribers
  - 15 Services
  - 3 TransformBroadcasters
  - 1 TransformListener
- **Evidence Breakdown for 37 Declarations**:
  - `SOURCE_CONFIRMED`: 32
  - `DEPENDENCY_CONFIRMED`: 5 (3 TF broadcasters, 1 TF listener, 1 `/scan` subscriber using `rclcpp::SensorDataQoS()`)
- **C++ Application Interface Instances across 7 profiles ($N=1$)**: **143**
- **ROS Graph Entities ($N=1$)**: **170** (73 topic publishers, 32 topic subscriptions, 65 service servers)
- **DDS Transport Endpoints ($N=1$)**: **235** (138 DataWriters, 97 DataReaders)
- **InteractiveMarkerServer (Jazzy 2.5.5)**: Unconditionally creates:
  1. `<ns>/get_interactive_markers` service server (`RELIABLE`, `VOLATILE`, Depth 10)
  2. `<ns>/update` publisher (`RELIABLE`, `VOLATILE`, Depth 100)
  3. `<ns>/feedback` subscription (`RELIABLE`, `VOLATILE`, Depth 1)
  *(Notice: Native ROS 2 does NOT use the legacy ROS 1 latched `update_full` publisher!)*
- **TransformListener Behavior**: Spawns internal hidden node `transform_listener_impl_...` registering dynamic `/tf` (`VOLATILE`) and static `/tf_static` (`TRANSIENT_LOCAL`).
- **Precision / Recall / F1**: Precision = $100\%$, Recall = $100\%$, F1 = $100\%$

### C. Cross-Repository Totals (5 Case Studies)
- Repositories: 5 production (`nav2`, `slam_toolbox`, `ros2_control`, `jaco2_sim_devkit`, `behaviortree_cpp`) + 1 negative control (`express`).
- Automated Regression Test Suite: **155 / 155 tests passing** in ~5.97 seconds (100% pass rate).

### D. Multi-Model Findings (Identical Task & Prompt)
- Gemini 2.5 Flash: Latency = $1.25\text{s}$, Cost = \$0.00148/run, ARI = $0.895$, Unsupported Rate = $0.0\%$.
- Gemini 1.5 Pro: Latency = $3.80\text{s}$, Cost = \$0.02631/run, ARI = $0.924$, Unsupported Rate = $0.0\%$.
- GPT-4o: Latency = $2.40\text{s}$, Cost = \$0.05053/run, ARI = $0.880$, Unsupported Rate = $1.2\%$.
- Claude 3.5 Sonnet: Latency = $2.85\text{s}$, Cost = \$0.06750/run, ARI = $0.912$, Unsupported Rate = $0.8\%$.
- Llama 3.1 70B (Ollama): Latency = $7.40\text{s}$, Cost = \$0.00 (Self-hosted), ARI = $0.815$, Unsupported Rate = $3.5\%$.

### E. Context Memory Strategy Experiments (Exp A through Exp F)
- **Exp A (No Persistent Memory)**: 3,950 tokens, F1 = $0.724$, Unsupported Rate = $8.4\%$.
- **Exp B (Full Repository Context)**: 188,600 tokens, F1 = $0.865$, Unsupported Rate = $4.2\%$.
- **Exp C (Structured Architecture Memory)**: 16,400 tokens, F1 = $0.978$, Unsupported Rate = $0.0\%$.
- **Exp D (RAG Retrieval Context)**: 21,200 tokens, F1 = $0.892$, Unsupported Rate = $2.8\%$.
- **Exp E (Hierarchical Context Memory)**: 18,900 tokens, F1 = $0.985$, Unsupported Rate = $0.0\%$.
- **Exp F (Phase-Based Sequential Memory - ArchSynth v2.0)**: **14,270 tokens**, **F1 = 0.991**, **Unsupported Rate = 0.0%**, **92.4% token reduction**.

---

## 5. Claims Requiring Caution & Anti-Hallucination Rules

When authoring thesis text, adhere to these strict academic integrity principles:
1. **Never claim live dynamic execution where none was run**:
   - For SLAM Toolbox and Nav2 static recovery, state clearly that static AST analysis and symbolic launch evaluation were used.
   - Set **`RUNTIME_OBSERVED = 0`** when reporting empirical findings where live robot hardware telemetry was not captured.
   - Use the term **`INTERNAL_MATCHED`** to mean **statically predicted, source-and-QoS-compatible local match**, not an instrumented runtime trace.
2. **Never claim LLMs discovered nodes independently**:
   - Give credit where credit is due: Python AST and Clang heuristics discover the physical nodes, line numbers, and interface objects.
   - The LLM's contribution is **semantic subsystem clustering, architectural narrative synthesis, and ISO 42010 documentation generation**.
3. **Preserve the Midterm Distinction**:
   - State clearly that basic Python AST extraction and flat Mermaid graphs were presented at midterm.
   - Attribute Clang C++ symbol parsing, nested launch resolution, component containers, lifecycle recovery, pluginlib analysis, ISO 42010 multi-view generation, repository isolation sidecars, and the 155-test harness to the **Post-Midterm (ArchSynth v2.0)** phase.

---

## 6. Recommended Structure for the M.Tech Dissertation

Follow this 8-chapter structure:
- **Chapter 1: Introduction** — Background, problem statement, research gap, objectives, scope, and thesis contributions.
- **Chapter 2: Literature Review** — ROS 2 architecture, static analysis, reverse engineering, C4 modeling, ISO/IEC/IEEE 42010, LLM code comprehension, and RAG limitations.
- **Chapter 3: Research Methodology** — End-to-end ArchSynth pipeline, AST visitor design, launch substitution resolution, interface typing, QoS deduction, and Pydantic schema validation.
- **Chapter 4: System Design and Architecture** — Modular architecture of ArchSynth v2.0, dual-engine LLM design, repository provenance sidecars, and web dashboard separation.
- **Chapter 5: Implementation Details** — LibClang visitor, Python AST, XML launch engine, component container mapping, lifecycle state machines, and Mermaid generation.
- **Chapter 6: Empirical Evaluation and Case Studies** — Detailed experimental analysis of Navigation2, SLAM Toolbox, ROS 2 Control, Jaco2 Devkit, and BehaviorTree.CPP.
- **Chapter 7: Results and Discussion** — Multi-model comparison, context memory experiments (Exp A–F), token efficiency, ablation study (Levels 1–7), statistical hypothesis testing, and threats to validity.
- **Chapter 8: Conclusion and Future Work** — Summary of research contributions, defense viva takeaways, and future work (live eBPF telemetry, dynamic macro tracing).
