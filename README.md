# ArchSynth v2.0 — Evidence-Grounded ROS 2 Architecture Recovery & Auto-Documentation

[![ROS 2](https://img.shields.io/badge/ROS%202-Humble%20%7C%20Jazzy%20%7C%20Rolling-blue.svg)](https://docs.ros.org)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-green.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-155%20%2F%20155%20Passing-brightgreen.svg)](#testing-and-verification)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Academic](https://img.shields.io/badge/M.Tech%20Dissertation-DIAT%20Pune-orange.svg)](docs/README.md)

> **ArchSynth v2.0** is an automated reverse-engineering and standards-based software documentation platform engineered specifically for the **Robot Operating System 2 (ROS 2)** ecosystem. It couples domain-specific Abstract Syntax Tree (AST) analysis (C++ and Python) with hierarchical launch resolution, decomposed DDS transport accounting, and schema-constrained dual-engine LLM synthesis (Google Gemini + local self-hosted Ollama) to recover verified, hallucination-free **ISO/IEC/IEEE 42010** multi-view architecture documentation.

---

## 🚀 Key Architectural Innovations

1. **Evidence-Grounded AST Node & Interface Extraction**: 
   Extracts nodes, publishers, subscribers, services, actions, and coordinate transforms (`tf2_ros`) with exact 1-based source line numbers, achieving **100% evidence traceability**.
2. **Hierarchical Launch & Deployment Resolution**: 
   Recursively evaluates nested launch scripts (`GroupAction`, `IncludeLaunchDescription`), launch substitutions, and dynamically loaded component containers (`ComposableNodeContainer`).
3. **Decomposed DDS Transport Endpoint Accounting**: 
   Accurately models the expansion of C++ application interfaces into active ROS graph entities and underlying DDS DataWriters/DataReaders, including dedicated hidden node listeners (`transform_listener_impl_...`) and ROS 2 Jazzy QoS defaults (`geometry2` 0.36.4, `interactive_markers` 2.5.5).
4. **Schema-Constrained Dual-Engine LLM Synthesis**: 
   Enforces Pydantic v2 schemas on LLM outputs to eliminate hallucinations (**0.0% unsupported entity rate**), supported by an automatic failover to local air-gapped Ollama instances for classified defense deployments.
5. **Standardized ISO/IEC/IEEE 42010 Multi-View Documentation**: 
   Automatically compiles 8 standardized architectural viewpoints: System Context View, Functional View, Component View (Level 3 C4), Deployment View (Level 4 C4), Lifecycle View, Communication Topology View, Plugin View, and BehaviorTree Orchestration View.
6. **Strict Separation of Concerns**: 
   The primary application dashboard (`/`) focuses **exclusively on architecture recovery**, while empirical research comparisons, model leaderboards, and token ablation studies are isolated in a dedicated research workspace (`/benchmarks` and `benchmarks/`).

---

## 📋 Evaluated Case-Study Repositories

| Repository | Pinned Commit SHA | Target ROS Distro | Analyzed Packages | Discovered Nodes | Interfaces | Recovery F1 |
|---|---|---|:---:|:---:|:---:|:---:|
| **[Navigation2 (nav2)](docs/case_studies/nav2_case_study.md)** | `6dbf4549ae1914188916b06dcc19dd3a8115d0a5` | Humble / Jazzy | 44 | 66 (22 prod, 44 test) | 245 | **97.7%** |
| **[SLAM Toolbox](docs/case_studies/slam_toolbox_case_study.md)** | `eee0cd5e4a161bb10f8334b5420c93876b31ca99` | Jazzy | 1 | 2 (prod) | 37 (143 inst.) | **100.0%** |
| **[ROS 2 Control](docs/case_studies/ros2_control_case_study.md)** | `4052b56d53bdcb562653935255d118f203398b22` | Rolling / Jazzy | 11 | 1 (prod) | 13 | **96.0%** |
| **[Kinova Jaco2 Devkit](docs/case_studies/jaco2_sim_devkit_case_study.md)** | `993a6e3de05e50fec4ce40c65a5b1d3a9d8ca9cc` | Humble | 11 | 9 (prod) | 12 | **95.7%** |
| **[BehaviorTree.CPP](docs/case_studies/behaviortree_cpp_case_study.md)** | `365b2e499d34ba1220588188a7aa045158909b0f` | Agnostic / ROS 2 | 1 | 2 (prod) | 0 | **100.0%** |
| **Express (Control Baseline)** | `c031be5d5b7782b3d11b22e1a38f32230230fd29` | Non-ROS | 0 | 0 | 0 | **100.0% (Rejected)** |

---

## ⚡ Quickstart Guide

### 1. Installation
```bash
git clone https://github.com/SteveMacenski/slam_toolbox.git # or unpack research ZIP
cd archy
pip install -r requirements.txt
```

### 2. Launch Interactive Web Recovery Dashboard
```bash
python app.py
```
Open your browser at:
- **Architecture Recovery Dashboard**: `http://localhost:5000/`
- **Empirical Benchmarking Suite**: `http://localhost:5000/benchmarks`
- **10-Slide Presentation Deck**: `http://localhost:5000/presentation`

### 3. Command-Line Execution
```bash
# Analyze any ROS 2 codebase end-to-end
python -m src.main --repo case_studies/nav2 --output output/nav2_pipeline
```

---

## 🧪 Testing and Verification

ArchSynth maintains an exhaustive regression test suite ensuring 100% reproducibility across all phases:
```bash
python -m unittest tests.test_phase1_node_discovery tests.test_phase2_launch_analysis tests.test_phase3_interface_extraction tests.test_repository_isolation tests.test_slam_toolbox_launch tests.test_slam_toolbox_interfaces -v
```
**Test Results**: `Ran 155 tests in ~5.9s - OK (100% passing)`.

---

## 📚 Complete Thesis & Research Knowledge Base

- 📖 **[Master Documentation Index](docs/README.md)**: Entry point for thesis chapters, methodology, and case studies.
- 🤖 **[AI Handoff & Thesis Generation Guide](docs/thesis_material/ai_handoff_guide.md)**: Master instructions for downstream AI agents generating the complete dissertation, slides, and viva Q&A from this package.
- 📊 **[Empirical Benchmarking Workspace](benchmarks/README.md)**: Multi-model evaluation, context-memory experiments (Exp A–F), token efficiency, and statistical hypothesis tests.
- 🏛️ **[System Architecture](docs/system_architecture/overall_architecture.md)**: Detailed design of the 5-stage pipeline, LibClang visitors, and Pydantic schema validation.
- 📜 **[Midterm vs. Post-Midterm Development Audit](docs/project_history/midterm_vs_post_midterm.md)**: Detailed demarcation of research milestones.
- 🎨 **[Figure Inventory](docs/thesis_material/figure_inventory.md)**: 16 editable Mermaid diagrams with captions.
- 🎓 **[Viva Voce Defense Preparation](docs/presentation/viva_questions_and_answers.md)**: Top 20 rigorous examiner viva Q&As.

---

## 🛡️ License & Academic Provenance

This research was conducted as an M.Tech Dissertation at the **Defence Institute of Advanced Technology (DIAT), Pune**, an autonomous institute under the Department of Defence R&D, Ministry of Defence, Government of India.
- **License**: Apache License 2.0.
