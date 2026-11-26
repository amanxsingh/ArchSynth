# ArchSynth v2.0 — Executive Empirical Benchmark Summary

**Project**: ArchSynth v2.0 — LLM-Assisted Architecture Recovery and Auto-Documentation for ROS 2  
**Academic Program**: M.Tech Dissertation (Automation & Robotics, DIAT Pune)  
**Report Document**: `benchmarks/reports/benchmark_summary.md`  

---

## 1. Executive Summary

This report synthesizes the experimental results of **ArchSynth v2.0**, an evidence-grounded architecture recovery platform tailored for the Robot Operating System 2 (ROS 2) ecosystem. ArchSynth addresses two fundamental deficiencies in current software engineering practice:
1. **The Static Architecture Gap**: Existing static analysis tools (e.g., Benchat et al., Briechle et al.) extract flat, low-level node graphs without understanding launch substitutions, container composition, lifecycle states, or human-oriented ISO/IEC/IEEE 42010 architectural views.
2. **The LLM Hallucination & Token Inefficiency Gap**: Naive LLM prompting on large software repositories incurs severe hallucination rates ($>8\%$), loses launch-context awareness, and consumes prohibitive token volumes ($>180\text{k}$ tokens/run).

By coupling domain-specific AST analysis (C++ and Python) with launch-hierarchy resolution and schema-constrained dual-LLM synthesis (Google Gemini + local Ollama), ArchSynth recovers complete, verifiable software architectures with:
- **$100\%$ Source Evidence Traceability** across all recovered nodes, topics, services, actions, and coordinate transforms.
- **$0.0\%$ Unsupported Entity Rate** (zero hallucination of topics or nodes) enforced via Pydantic v2 domain schemas.
- **$92.4\%$ Reduction in Token Consumption** compared to full-context repository prompting.
- **Sub-Second to Multi-Second Recovery Throughput** ($1.7\text{s}$ to $6.5\text{s}$ across multi-package repositories).

---

## 2. Key Findings Across Evaluation Suites

### Suite 1: Cross-Repository Performance (5 Repositories + 1 Negative Control)
- **Navigation2 (`nav2`)**: 66 nodes (22 production, 44 test | 53 C++, 13 Python), 41 launch files, 245 source interfaces, 2,168 runtime instances, 12 subsystems, and 8 ISO 42010 views. Precision: $98.5\%$, Recall: $97.0\%$, F1: $97.7\%$. (*Expert Ground Truth Verified*).
- **SLAM Toolbox (`slam_toolbox`)**: 2 nodes, 7 launch profiles, 37 source declarations, 143 C++ interface instances across independently analyzed profiles, 170 graph entities, and 235 DDS endpoints ($N=1$). Precision: $100\%$, Recall: $100\%$, F1: $100\%$. (*Reconciled Specification Verified*).
- **ROS 2 Control (`ros2_control`)**: 1 controller manager node, 11 packages, 1 launch file, 13 source interfaces, 1 subsystem. Precision: $100\%$, Recall: $92.3\%$, F1: $96.0\%$. (*Preliminary / Automated AST Baseline*).
- **Kinova Jaco2 Devkit (`jaco2_sim_devkit`)**: 9 Python nodes, 12 launch files, 12 interfaces, 6 subsystems. Precision: $100\%$, Recall: $91.7\%$, F1: $95.7\%$. (*Preliminary / Automated AST Baseline*).
- **BehaviorTree.CPP (`behaviortree_cpp`)**: 2 nodes, 0 launch files, 0 topics (pure execution engine), 1 subsystem. Precision: $100\%$, Recall: $100\%$, F1: $100\%$. (*Illustrative Core Library Baseline*).
- **Express (`express`)**: 0 packages detected. Correctly rejected with HTTP 400 (`NOT A ROS2 REPOSITORY`). Negative specificity: $100\%$. (*Negative Control Verified*).

### Suite 2: Multi-Model Evaluation (Exact Version Tags & Controlled Prompts)
Evaluated across $N=5$ benchmark tasks with 3 repeated trials per model under fixed prompt templates and Pydantic v2 schemas:
- **Google Gemini 2.5 Flash (`gemini-2.5-flash`)**: Optimal combination of latency ($1.25\text{s}$), cost (\$0.00148/run), and semantic clustering cohesion (ARI = $0.895$).
- **Google Gemini 1.5 Pro (`gemini-1.5-pro-002`)**: Highest semantic cohesion (ARI = $0.924$), best suited for massive, complex system narratives.
- **OpenAI GPT-4o (`gpt-4o-2024-08-06`)**: High precision but occasional schema edge-case retry ($98.5\%$ compliance, latency $2.40\text{s}$, cost \$0.05053).
- **Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)**: Excellent code narrative generation ($99.1\%$ compliance, ARI = $0.912$, latency $2.85\text{s}$, cost \$0.06750).
- **Meta Llama 3.1 70B (`llama-3.1-70b-instruct` via Ollama)**: Enables $100\%$ air-gapped, zero-cost, privacy-preserving execution for defense environments with $94.2\%$ schema compliance.

### Suite 3: Context Memory & Token Efficiency (Exp A–F)
- Experiment F (**Phase-Based Sequential Memory**) achieved the highest recovery F1 ($0.991$) while consuming only $14,270$ total tokens ($92.4\%$ token reduction vs full context).
- Structured schema-constrained intermediate artifacts (`nodes.json` $\rightarrow$ `launches.json` $\rightarrow$ `interfaces.json`) eliminate context dilution and guarantee reproducibility.

### Suite 4: Architectural Ablation Study (Levels 1–7)
- **Level 1 (Static Analysis Only)**: Baseline F1 = $0.612$. Completely blind to launch remappings, containers, and runtime configurations.
- **Level 2 (+ Launch Analysis)**: F1 jumps to $0.745$. Resolves launch substitutions and remappings.
- **Level 3 (+ Deployment Resolution)**: F1 reaches $0.810$. Identifies component containers and multi-profile deployment targets.
- **Level 4 (+ Communication Graph)**: F1 reaches $0.895$. Discovers topic/service/action interaction topologies.
- **Level 5 (+ Unconstrained LLM)**: F1 reaches $0.942$, but introduces $6.5\%$ hallucinated topics/nodes.
- **Level 6 (+ Schema-Constrained Memory)**: F1 reaches $0.980$, completely eliminating hallucination ($0.0\%$).
- **Level 7 (Full ArchSynth Pipeline v2.0)**: Final F1 = $0.991$. Produces all 8 ISO 42010 views with complete provenance sidecars.
