# M.Tech Dissertation Thesis Chapter Outline & Structure

**Title**: Evidence-Grounded ROS 2 Software Architecture Recovery, Hierarchical Deployment Resolution, and Standards-Based Auto-Documentation  
**Candidate**: M.Tech Research Candidate (Automation & Robotics)  
**Institution**: Defence Institute of Advanced Technology (DIAT), Pune  
**Document**: `docs/thesis_material/thesis_chapter_outline.md`  

---

## Chapter 1: Introduction
- 1.1 Context and Motivation: Distributed Robotics Software & ROS 2
- 1.2 The Problem: Architectural Drift & The Documentation Crisis in Robotics
- 1.3 The Research Gap: Limitations of Static Code Analyzers vs. Unconstrained Generative AI
- 1.4 Research Objectives & Core Research Questions (RQ1–RQ4)
- 1.5 Summary of Novel Technical Contributions
- 1.6 Evolution of Research: Midterm Proof-of-Concept vs. ArchSynth v2.0
- 1.7 Dissertation Organization

## Chapter 2: Literature Review & Theoretical Foundations
- 2.1 Software Architecture Recovery & Program Comprehension
- 2.2 Robot Operating System 2 (ROS 2) Architecture & DDS Middleware
- 2.3 Static Analysis of Robotics Systems (Prior Line 1: Benchat et al., Briechle et al.)
- 2.4 Generative AI in Software Documentation (Prior Line 2: De Luca et al., CIAO)
- 2.5 Architectural Standards: The ISO/IEC/IEEE 42010 Standard & C4 Model
- 2.6 The Hallucination Phenomenon in Code LLMs & Schema Constraints
- 2.7 Context Management & Memory Trade-Offs in LLM Engineering

## Chapter 3: Research Methodology
- 3.1 Overall Research Framework & Pipeline Overview
- 3.2 Repository Ingestion, Provenance Control & The ROS 2 Validation Gate
- 3.3 Static Node Discovery: Python AST Visitors & LibClang C++ Analysis
- 3.4 Hierarchical Launch Analysis & Symbolic Substitution Evaluation
- 3.5 Interface Extraction: Topics, Services, Actions, Coordinate Transforms, and QoS Profiling
- 3.6 Communication Graph Construction & Pairwise Traffic Matrices
- 3.7 Schema-Constrained Multi-View Synthesis & Dual-LLM Integration

## Chapter 4: System Design & Architecture
- 4.1 ArchSynth v2.0 Modular Architecture
- 4.2 Separation of Concerns: Architecture Recovery vs. Empirical Benchmarking
- 4.3 Provenance Tracking & Output Artifact Isolation (`.provenance.json`)
- 4.4 Dual-Engine LLM Router: Cloud API (Gemini) vs. Air-Gapped Local Inference (Ollama)
- 4.5 Domain Schema Hierarchy (Pydantic v2 Models)
- 4.6 User Interface Architecture: Glassmorphism Web Dashboard

## Chapter 5: Implementation Details
- 5.1 Python AST Implementation & Line-Number Evidence Attachment
- 5.2 LibClang C++ Visitor, CMakeLists Parser & Lifecycle Node Scanner
- 5.3 Recursive Launch Evaluator: `GroupAction`, `ComposableNodeContainer`, Substitutions
- 5.4 Decomposed DDS Endpoint Accounting: Hidden Node Expansion (`transform_listener_impl_...`)
- 5.5 Modularity-Guided Subsystem Clustering & Graph Community Detection
- 5.6 ISO/IEC/IEEE 42010 Architecture View Generators & Mermaid.js Compiler

## Chapter 6: Empirical Evaluation & Case Studies
- 6.1 Experimental Setup, Environment, and Case Study Selection Criteria
- 6.2 Case Study 1: Navigation2 (Nav2) — Multi-Package Production Benchmark
- 6.3 Case Study 2: SLAM Toolbox — Lifecycles, TF Broadcasting & DDS Endpoint Reconciliation
- 6.4 Case Study 3: ROS 2 Control — Real-Time Hardware Abstraction & Plugins
- 6.5 Case Study 4: Kinova Jaco2 Devkit — Robotic Manipulation Simulation
- 6.6 Case Study 5: BehaviorTree.CPP — Discrete Autonomous Decision Orchestration
- 6.7 Negative Baseline Control: Express.js Boundary Validation

## Chapter 7: Results, Statistical Analysis & Discussion
- 7.1 Cross-Repository Architecture Recovery Precision, Recall, and F1
- 7.2 Multi-Model Evaluation: Frontier vs. Open-Weight Models
- 7.3 Context Memory Strategy Experiments (Exp A through Exp F): Accuracy vs. Token Efficiency
- 7.4 Architectural Pipeline Ablation Study (Levels 1 through 7)
- 7.5 Statistical Significance & Hypothesis Testing (Paired t-tests, Cohen's d)
- 7.6 Threats to Construct, Internal, and External Validity
- 7.7 Engineering Limitations & Scope Boundaries

## Chapter 8: Conclusion & Future Work
- 8.1 Summary of Research Achievements
- 8.2 Academic & Industrial Impact
- 8.3 Key Takeaways for Defense Robotics & Mission-Critical Systems
- 8.4 Future Research Directions: Dynamic eBPF Tracing & Compiler Symbol Tables
