# ArchSynth Thesis Research Package Manifest

**Archive File**: `ArchSynth_Thesis_Research_Package.zip`  
**Project**: ArchSynth v2.0 — Evidence-Grounded ROS 2 Architecture Recovery & Auto-Documentation  
**Academic Degree**: Master of Technology in Automation & Robotics  
**Host Institution**: Defence Institute of Advanced Technology (DIAT), Pune  
**Packaging Date**: November 2026  

---

## 1. Overview of Package Contents

This research archive contains the complete, reproducible source code, benchmarking suite, case-study repositories, verified experimental results, architecture models, ISO/IEC/IEEE 42010 documentation, and thesis preparation materials for ArchSynth v2.0.

---

## 2. Inclusions (What is Packed in the ZIP)

### Core Software Architecture Recovery Engine (`src/`)
- `src/ingestor.py`: Repository cloning, path validation, and ROS 2 `package.xml` manifest verification.
- `src/repo_identity.py`: Git commit SHA pinning, cryptographic provenance, and artifact isolation (`.provenance.json`).
- `src/build_analyzer.py`: CMakeLists.txt and package.xml build system analysis.
- `src/cpp_analyzer.py`: LibClang C++ AST symbol extraction and class inheritance analysis.
- `src/node_analyzer.py`: Static node discovery across Python AST and C++ sources with line-number evidence.
- `src/launch_analyzer.py`: Hierarchical launch file evaluation, substitutions, and `ComposableNodeContainer` mapping.
- `src/interface_extractor.py`: Source-grounded topic, service, action, TF broadcaster/listener extraction with QoS deduction.
- `src/communication_builder.py`: Pairwise communication graph construction and traffic matrix synthesis.
- `src/subsystem_synthesizer.py`: Newman's graph modularity optimization and cohesive subsystem clustering.
- `src/lifecycle_analyzer.py`: ROS 2 `LifecycleNode` state machine tracking and orchestrator mapping.
- `src/plugin_analyzer.py`: `pluginlib` base class interface extraction and manifest parsing.
- `src/bt_analyzer.py`: BehaviorTree.CPP navigation XML decision hierarchy recovery.
- `src/view_generator.py`: ISO/IEC/IEEE 42010 multi-view architectural generator (8 viewpoints).
- `src/architecture_constructor.py`: Schema consolidation and system-level `ArchitectureModel` assembly.
- `src/doc_generator.py`: Automated Markdown documentation and Mermaid diagram compiler.
- `src/llm_client.py`: Dual-engine LLM router (Google Gemini 2.5 Flash API + local self-hosted Ollama).
- `src/schema.py`: Pydantic v2 domain schemas and data structures.
- `src/evidence_validator.py`: Source line physical existence and grounding validator.
- `src/architecture_diff.py` & `src/drift_pipeline.py`: Architecture drift detection across Git commits.

### Empirical Benchmarking & Research Workspace (`benchmarks/`)
- `benchmarks/README.md`: Index and guide to the benchmarking harness.
- `benchmarks/repositories/`: Registered case studies, pinned commits, selection rationale, and metadata.
- `benchmarks/models/`: Evaluated LLM models (Gemini 2.5 Flash, 1.5 Pro, GPT-4o, Claude 3.5 Sonnet, Llama 3.1 70B), comparison protocols, and capabilities.
- `benchmarks/experiments/`: Experimental protocols for static analysis, LLM synthesis, context memory (Exp A–F), and ablations.
- `benchmarks/comparison_matrices/`: Tabular CSV datasets (`repository_comparison.csv`, `architecture_recovery_comparison.csv`, `model_comparison.csv`, `context_memory_comparison.csv`, `token_usage_comparison.csv`, `static_vs_llm_comparison.csv`, `feature_coverage_matrix.csv`, and `evaluation_metric_definitions.md`).
- `benchmarks/statistical_analysis/`: Hypothesis testing script (`significance_tests.py`), effect size analyses, and summaries.
- `benchmarks/reports/`: In-depth narrative research reports on benchmarks, token efficiency, and validity threats.

### Web Application & UI (`web/`, `app.py`)
- `app.py`: Flask REST API server serving recovery endpoints (`/api/presets`, `/api/runs`, `/api/load_run`, `/api/analyze`, `/api/benchmarks/summary`).
- `web/index.html`: Clean glassmorphism frontend dedicated **strictly to Architecture Recovery**.
- `web/benchmarks.html`: Dedicated research benchmarking dashboard.
- `web/app.js`: Tab switching, Mermaid diagram rendering, search filtering, and live Markdown viewing.
- `web/style.css`: Glassmorphic styling system.
- `web/presentation.html`: In-browser 10-slide interactive presentation deck.

### Complete Thesis & Research Documentation (`docs/`)
- `docs/README.md`: Master documentation index.
- `docs/thesis_material/ai_handoff_guide.md`: Master handoff instructions for downstream AI agents.
- `docs/thesis_material/thesis_chapter_outline.md`: 8-chapter M.Tech dissertation outline.
- `docs/thesis_material/figure_inventory.md`: 16 editable Mermaid diagrams with captions.
- `docs/thesis_material/table_inventory.md`: Complete catalog of thesis tables.
- `docs/thesis_material/references_and_citations.md`: Academic bibliography.
- `docs/project_overview/`: Problem statement, research gap, objectives, scope, and contributions.
- `docs/system_architecture/`: Overall architecture, module descriptions, data flow, and provenance design.
- `docs/methodology/`: Detailed scientific methodology for AST, launch, interface, and synthesis stages.
- `docs/project_history/`: Chronological phase-wise development (Phases 0–9), initial repository audit, and midterm vs. post-midterm demarcation.
- `docs/case_studies/`: Dedicated research reports on Nav2, SLAM Toolbox, ROS 2 Control, Jaco2 Devkit, and BehaviorTree.CPP.
- `docs/evaluation/`: Results and discussion, metric formulations, statistical tests, and validity threats.
- `docs/presentation/`: Slide-by-slide talking points and top 20 defense viva voce Q&As.
- `docs/reproducibility/`: Execution and testing guide.
- `docs/archive/historical_reports/`: Safely preserved historical notes and milestone documents.

### Verified Target Case Studies (`case_studies/`)
- `case_studies/nav2`: Pinned at commit `6dbf4549ae1914188916b06dcc19dd3a8115d0a5`.
- `case_studies/slam_toolbox`: Pinned at commit `eee0cd5e4a161bb10f8334b5420c93876b31ca99`.
- `case_studies/ros2_control`: Pinned at commit `4052b56d53bdcb562653935255d118f203398b22`.
- `case_studies/jaco2_sim_devkit`: Pinned at commit `993a6e3de05e50fec4ce40c65a5b1d3a9d8ca9cc`.
- `case_studies/behaviortree_cpp`: Pinned at commit `365b2e499d34ba1220588188a7aa045158909b0f`.
- `case_studies/express`: Pinned at commit `c031be5d5b7782b3d11b22e1a38f32230230fd29` (negative control).

### Test Suite (`tests/`)
- 155 automated unit and integration tests passing at $100\%$ across all phases.

### Precomputed & Isolated Pipeline Artifacts (`output/`)
- `output/nav2_pipeline/`: Complete verified Nav2 architecture models, views, and documentation.
- `output/slam_toolbox_pipeline/`: Complete verified SLAM Toolbox architecture models, views, and documentation.
- `output/ros2_control_pipeline/`: Complete verified ROS 2 Control architecture models, views, and documentation.
- `output/jaco2_sim_devkit_pipeline/`: Complete verified Jaco2 Devkit architecture models, views, and documentation.
- `output/behaviortree_cpp_pipeline/`: Complete verified BehaviorTree.CPP architecture models, views, and documentation.

### Presentation Artifacts
- `ArchSynth_Project_Presentation.pptx`: 10-slide PowerPoint presentation deck.

---

## 3. Exclusions (What is Intentionally Excluded from the ZIP)

To keep the research package clean, secure, and compliant with privacy rules:
1. **Virtual Environments (`.venv/`)**: Excluded to avoid OS-specific binary bloat. Can be recreated via `pip install -r requirements.txt`.
2. **Build Caches & Bytecode (`__pycache__/`, `*.pyc`)**: Excluded across all directories.
3. **Private Configuration & API Keys (`.env`)**: Excluded to protect private credentials. A sanitized `.env.example` with clear instructions is included instead.
4. **Temporary & Scratch Files (`scratch/`, `*.tmp`)**: Excluded.
5. **Root Git History of ArchSynth (`.git/`)**: Excluded to prevent repository nesting bloat, while preserving Git repositories inside `case_studies/` to ensure `git rev-parse HEAD` functions for provenance verification.
6. **The ZIP File Itself (`ArchSynth_Thesis_Research_Package.zip`)**: Excluded from self-recursion.

---

## 4. Package Verification Checksums (Option B — Slim Research Package)

- **Total Packed Files**: 3,537 files
- **Uncompressed Size**: 133.61 MB (complete ROS 2 sources, launch hierarchies, models, tests, benchmarks, views)
- **Compressed Archive**: `ArchSynth_Thesis_Research_Package.zip`
- **Archive File Size**: 42.57 MB
- **SHA-256 Checksum**: `b7f1b088433d5b935f5c22022ab98c6adb076a5fa87e2f497ddf2d4c86dcd630`
