# ArchSynth Research Package & Documentation Index

**Project**: ArchSynth v2.0 — Evidence-Grounded ROS 2 Architecture Recovery & Auto-Documentation  
**Degree**: Master of Technology in Automation & Robotics  
**Institution**: Defence Institute of Advanced Technology (DIAT), Pune  
**Document**: `docs/README.md`  

---

## 1. Welcome to the ArchSynth Knowledge Base

This documentation base serves as the authoritative, comprehensive research archive for **ArchSynth v2.0**. It is organized so that researchers, examination committees, or an AI system receiving the research ZIP can thoroughly understand, reproduce, evaluate, and generate the complete dissertation thesis, slide presentations, architectural figures, and viva defense material.

---

## 2. Reading Roadmap

Depending on your objective, consult the following entry points:

### For an AI System Generating Thesis / Presentations:
👉 **Start with**: [`docs/thesis_material/ai_handoff_guide.md`](file:///docs/thesis_material/ai_handoff_guide.md)  
Contains explicit thesis title options, verified numerical inventories, chapter mapping, cautions against hallucination, and citation rules.

### For Academic Examiners & Faculty Guides:
1. **Research Overview & Novelty**: [`docs/project_overview/project_overview.md`](file:///docs/project_overview/project_overview.md)
2. **Phase-Wise Evolution & Midterm Distinction**: [`docs/project_history/midterm_vs_post_midterm.md`](file:///docs/project_history/midterm_vs_post_midterm.md)
3. **Empirical Evaluation & Results**: [`docs/evaluation/results_and_discussion.md`](file:///docs/evaluation/results_and_discussion.md)
4. **Formal System Architecture**: [`docs/system_architecture/overall_architecture.md`](file:///docs/system_architecture/overall_architecture.md)

### For Robotics Engineers & Reproducibility Testers:
1. **Quickstart & Test Execution**: [`docs/reproducibility/execution_guide.md`](file:///docs/reproducibility/execution_guide.md)
2. **Benchmarking Harness**: [`benchmarks/README.md`](file:///benchmarks/README.md)
3. **Architecture Recovery UI**: Open `http://localhost:5000` via `python app.py`

---

## 3. Master Table of Contents

```text
docs/
├── README.md                              # This file
│
├── project_overview/                      # Problem, gap, objectives, contributions
│   ├── project_overview.md                # Comprehensive project manifesto
│   ├── problem_statement.md               # The architectural drift crisis in ROS 2
│   ├── research_gap.md                    # Prior work vs. ArchSynth novelty
│   ├── objectives_and_scope.md            # Research scope & boundary constraints
│   ├── research_questions.md              # Core empirical research questions
│   └── contributions.md                   # Formal list of M.Tech thesis contributions
│
├── system_architecture/                   # Internal engine design & modules
│   ├── overall_architecture.md            # Full pipeline diagram & design principles
│   ├── module_architecture.md             # File-by-file module responsibilities
│   ├── data_flow.md                       # Data transformations from AST to ISO views
│   └── provenance_and_evidence.md         # Cryptographic sidecars & evidence models
│
├── methodology/                           # Static analysis & synthesis techniques
│   ├── research_methodology.md            # Step-by-step scientific methodology
│   ├── node_discovery.md                  # Python AST & C++ LibClang analysis
│   ├── launch_analysis.md                 # Hierarchical symbolic launch evaluation
│   ├── interface_extraction.md            # Topic, service, action, TF & QoS extraction
│   └── llm_assisted_synthesis.md          # Schema-constrained dual-engine synthesis
│
├── project_history/                       # Development chronology & provenance
│   ├── major_corrections_and_improvements.md # Research integrity pass & chronological changelog
│   ├── phase_wise_development.md          # Phases 0 through 9 complete history
│   ├── midterm_vs_post_midterm.md         # Midterm review vs. post-midterm achievements
│   └── initial_repository_audit.md        # Baseline repository state audit
│
├── case_studies/                          # Grounded case study evaluations
│   ├── nav2_case_study.md                 # Navigation2 (66 nodes, 41 launches)
│   ├── slam_toolbox_case_study.md         # SLAM Toolbox (37 declarations, 235 DDS endpoints)
│   ├── ros2_control_case_study.md         # ROS 2 Control (Real-time hardware interfaces)
│   ├── jaco2_sim_devkit_case_study.md     # Kinova Jaco2 Devkit (Python simulation stack)
│   └── behaviortree_cpp_case_study.md     # BehaviorTree.CPP (Execution engine)
│
├── evaluation/                            # Scientific benchmark findings
│   ├── evaluation_framework.md            # Multi-dimensional benchmark design
│   ├── evaluation_metrics.md              # Mathematical formulations of all metrics
│   ├── results_and_discussion.md          # Complete experimental tables and analysis
│   └── limitations.md                     # Threats to validity and engineering constraints
│
├── thesis_material/                       # Thesis drafts and figure inventories
│   ├── ai_handoff_guide.md                # Master prompt guide for external AI systems
│   ├── thesis_chapter_outline.md          # 8-chapter M.Tech dissertation structure
│   ├── figure_inventory.md                # 16 editable Mermaid diagrams with captions
│   ├── table_inventory.md                 # Master catalog of all dissertation tables
│   └── references_and_citations.md        # Complete academic bibliography
│
├── presentation/                          # Defense slides and viva preparation
│   ├── presentation_outline.md            # 12-slide M.Tech defense structure
│   ├── slide_content.md                   # Verbatim slide talking points & bullet points
│   └── viva_questions_and_answers.md      # Top 20 rigorous examiner viva Q&As
│
├── reproducibility/                       # Environment, dependencies, execution
│   └── execution_guide.md                 # End-to-end setup and test execution
│
└── archive/                               # Preserved historical milestone documents
    └── historical_reports/                # Preserved midterm guide, notes, and progress reports
```
