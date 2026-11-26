# ArchSynth Benchmarking & Empirical Research Evaluation Workspace

**Project**: ArchSynth v2.0 — Evidence-Grounded ROS 2 Architecture Recovery  
**Academic Degree**: Master of Technology (Automation & Robotics)  
**Institution**: Defence Institute of Advanced Technology (DIAT), Pune  
**Workspace Identity**: `benchmarks/`  
**Evaluation Scope**: 5 Diverse ROS 2 Repositories, 5 LLM Architectures, 6 Context-Memory Paradigms, 7-Stage Architectural Ablation  

---

## 1. Overview and Workspace Role

This directory contains the complete empirical evaluation suite for the ArchSynth research dissertation. Per the strict architectural isolation requirement of ArchSynth:
- The **Main Application** (`/`) is dedicated exclusively to **Architecture Recovery** (node extraction, launch resolution, communication topologies, lifecycle tracking, ISO 42010 multi-view generation).
- This **Benchmarking Workspace** (`benchmarks/` and `/benchmarks`) isolates all experimental protocols, model comparison metrics, token efficiency measurements, statistical hypothesis tests, and ablation studies.

---

## 2. Directory Layout

```text
benchmarks/
├── README.md                              # This file: Guide and index to evaluation harness
├── repositories/                          # Target case-study definitions and selection rationale
│   ├── repository_registry.yaml           # Pinned commit registry, branches, and distributions
│   ├── repository_selection_rationale.md  # Architectural complexity and criteria
│   └── repository_metadata/               # Detailed per-repository JSON metadata
│       ├── nav2_metadata.json
│       ├── slam_toolbox_metadata.json
│       ├── ros2_control_metadata.json
│       ├── jaco2_sim_devkit_metadata.json
│       └── behaviortree_cpp_metadata.json
│
├── models/                                # LLM specifications, pricing, and comparison protocol
│   ├── model_registry.yaml                # Exact model IDs, version tags, context limits
│   ├── model_capabilities.md              # Reasoning, token limits, schema adherence
│   ├── model_comparison_protocol.md       # Standardized prompt and evaluation protocol
│   └── model_metadata/                    # Per-model JSON capabilities
│       ├── gemini_2_5_flash.json
│       ├── gemini_1_5_pro.json
│       ├── gpt_4o.json
│       ├── claude_3_5_sonnet.json
│       └── llama_3_1_70b.json
│
├── experiments/                           # Experimental protocols & execution scripts
│   ├── experiment_registry.yaml           # Complete experiment catalog
│   ├── experiment_protocol.md             # Ground truth comparison methodology
│   ├── static_analysis_experiments/       # AST & build system experiments
│   ├── llm_architecture_recovery/         # LLM synthesis runs
│   ├── context_memory_experiments/        # Exp A through Exp F implementations
│   ├── token_usage_experiments/           # Token counting and cost analysis
│   ├── ablation_studies/                  # 7-level pipeline ablation
│   └── reproducibility/                   # Environment specifications and seed controls
│
├── raw_results/                           # Unaltered output logs and JSONs
│   ├── repository_results/                # Per-repository full analysis results
│   ├── model_results/                     # Per-model raw synthesis outputs
│   ├── context_memory_results/            # Per-memory strategy responses
│   ├── token_usage_results/               # Provider token accounting logs
│   └── experiment_logs/                   # Raw shell execution traces
│
├── comparison_matrices/                   # Machine-readable tabular datasets (CSV & MD)
│   ├── repository_comparison.csv          # 5-repository structural metrics
│   ├── architecture_recovery_comparison.csv# Precision, recall, F1 across repos
│   ├── model_comparison.csv               # 5-model quality, latency, token, and cost matrix
│   ├── context_memory_comparison.csv      # Exp A–F accuracy vs token trade-offs
│   ├── token_usage_comparison.csv         # Input, output, cached, reasoning token breakdown
│   ├── static_vs_llm_comparison.csv       # 7-level ablation breakdown
│   ├── feature_coverage_matrix.csv        # Support across ROS 2 language & deployment features
│   └── evaluation_metric_definitions.md   # Mathematical definitions of all metrics
│
├── statistical_analysis/                  # Significance testing and effect sizes
│   ├── significance_tests.py              # Wilcoxon / Paired t-test scripts
│   ├── effect_sizes.md                    # Cohen's d and confidence intervals
│   └── statistical_summary.md             # Empirical findings summary
│
├── visualizations/                        # Chart generation scripts
│   └── generate_benchmark_charts.py       # Generates SVG / Markdown benchmark diagrams
│
└── reports/                               # In-depth narrative research reports
    ├── benchmark_summary.md               # Executive benchmark findings
    ├── repository_comparison_report.md    # Analysis of the 5 case studies
    ├── model_comparison_report.md         # Multi-model evaluation and trade-offs
    ├── context_memory_report.md           # Context memory analysis (Exp A–F)
    ├── token_efficiency_report.md         # Cost, latency, and token efficiency
    └── limitations_and_validity.md        # Threats to validity and limitations
```

---

## 3. Case Study Repositories

| Repository | GitHub URL | Branch | Pinned Commit SHA | ROS 2 Distro | Packages | Nodes | Interfaces |
|---|---|---|---|---|:---:|:---:|:---:|
| **Navigation2 (nav2)** | `ros-planning/navigation2` | `main` | `6dbf4549ae1914188916b06dcc19dd3a8115d0a5` | Humble / Jazzy | 44 | 66 | 245 |
| **SLAM Toolbox** | `SteveMacenski/slam_toolbox` | `ros2` | `eee0cd5e4a161bb10f8334b5420c93876b31ca99` | Jazzy | 1 | 2 | 37 |
| **ROS 2 Control** | `ros-controls/ros2_control` | `master` | `4052b56d53bdcb562653935255d118f203398b22` | Rolling / Jazzy | 11 | 1 | 13 |
| **Kinova Jaco2 Devkit** | `VibhuSharma19/jaco2_sim_devkit` | `main` | `993a6e3de05e50fec4ce40c65a5b1d3a9d8ca9cc` | Humble | 11 | 9 | 12 |
| **BehaviorTree.CPP** | `BehaviorTree/BehaviorTree.CPP` | `master` | `365b2e499d34ba1220588188a7aa045158909b0f` | Agnostic / ROS 2 | 1 | 2 | 0 |
| *Express (Negative Control)* | `expressjs/express` | `master` | `c031be5d5b7782b3d11b22e1a38f32230230fd29` | Non-ROS | 0 | 0 | 0 |

---

## 4. Evaluated LLM Models

All models were evaluated using identical Pydantic v2 JSON output schemas, identical domain prompts, and the same source-grounded evidence inputs:
1. **Google Gemini 2.5 Flash** (`gemini-2.5-flash`): Primary production reasoning model.
2. **Google Gemini 1.5 Pro** (`gemini-1.5-pro`): High-capacity 2M context reasoning model.
3. **OpenAI GPT-4o** (`gpt-4o-2024-08-06`): Multi-modal frontier baseline.
4. **Anthropic Claude 3.5 Sonnet** (`claude-3-5-sonnet-20241022`): Code comprehension baseline.
5. **Meta Llama-3.1-70B-Instruct** (`llama-3.1-70b-instruct` via Ollama): Air-gapped / local inference baseline.

---

## 5. Execution and Reproducibility

To re-run benchmark evaluations or recalculate comparison matrices:
```bash
# 1. Run all 155 unit & integration tests
python -m unittest tests.test_phase1_node_discovery tests.test_phase2_launch_analysis tests.test_phase3_interface_extraction tests.test_repository_isolation tests.test_slam_toolbox_launch tests.test_slam_toolbox_interfaces -v

# 2. Run statistical analysis scripts
python benchmarks/statistical_analysis/significance_tests.py

# 3. Regenerate benchmark visualization diagrams
python benchmarks/visualizations/generate_benchmark_charts.py
```
