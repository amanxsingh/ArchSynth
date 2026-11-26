# ArchSynth v2.0 — M.Tech Defense Presentation Deck & Talking Points

**Project Title**: Evidence-Grounded ROS 2 Software Architecture Recovery, Hierarchical Deployment Resolution, and Standards-Based Auto-Documentation  
**Academic Degree**: Master of Technology in Automation & Robotics  
**Institution**: Defence Institute of Advanced Technology (DIAT), Pune  
**Document**: `docs/presentation/slide_content.md`  

---

## Slide 1: Title & Candidacy Details

- **Slide Title**: ArchSynth v2.0: Evidence-Grounded ROS 2 Architecture Recovery & Auto-Documentation
- **Subtitle**: M.Tech Dissertation Defense (Automation & Robotics)
- **Candidate**: M.Tech Research Scholar
- **Department**: Department of Robotics & Autonomous Systems
- **Institution**: Defence Institute of Advanced Technology (DIAT), Pune
- **Talking Points**:
  - "Respected members of the examination board, I present ArchSynth v2.0, an evidence-grounded architecture recovery and auto-documentation framework engineered specifically for the Robot Operating System 2 ecosystem."
  - "This research bridges the fundamental divide between low-level static analysis and high-level architectural documentation in complex robotics codebases."

---

## Slide 2: Real-World Motivation & The Architectural Drift Crisis

- **Slide Title**: Motivation: The Architecture Documentation Crisis in Robotics
- **Key Bullet Points**:
  - Component-based robotics stacks (autonomous ground vehicles, UAVs, mobile manipulators) comprise dozens to hundreds of asynchronous nodes.
  - **The Drift Problem**: Rapid engineering iterations cause hand-drawn architectural diagrams (draw.io, PPT) to become obsolete within weeks.
  - **Safety & Onboarding Costs**: Tracing sensor-to-actuator data pipelines in defense and mission-critical applications requires months of manual code reading.
  - **No Architecture Manuals**: While function-level docstrings exist, systems lack cohesive, system-level documentation.
- **Talking Points**:
  - "In robotics, a node rarely operates in isolation. Nodes communicate over topics, services, actions, and coordinate frames. As software evolves, documentation drifts, posing significant certification and onboarding risks."

---

## Slide 3: The Research Gap & Proposed Novelty

- **Slide Title**: Bridging the Divide: Static Extraction vs. Generative AI
- **Key Bullet Points**:
  - **Prior Line 1 (ROS Static Analyzers)**: Benchat et al. (2026), Briechle et al. (2026) produce abstract node connection graphs without narrative, subsystem clustering, or standards-based documentation.
  - **Prior Line 2 (General LLMs)**: CIAO (De Luca et al., 2024) treats code as generic text, hallucinating topics ($>8\%$ error rate) because it lacks ROS 2 client library and launch hierarchy awareness.
  - **ArchSynth Novelty**: Unifies domain-specific AST parsing (C++/Python), symbolic launch evaluation, and Pydantic schema-constrained dual-LLM synthesis to produce verified ISO/IEC/IEEE 42010 multi-view documentation.

---

## Slide 4: Overall System Architecture (5-Stage Pipeline)

- **Slide Title**: ArchSynth v2.0 System Architecture Blueprint
- **Key Elements**:
  - Stage 1: Ingestion, `package.xml` Manifest Validation Gate, and Git Provenance Sidecars (`.provenance.json`).
  - Stage 2: Node Discovery via Python AST and C++ Clang Visitors with line-number evidence.
  - Stage 3: Launch Analysis resolving substitutions, nested includes, and component containers.
  - Stage 3.5: Interface Extraction & DDS Endpoint Topology.
  - Stage 4: Multi-View Synthesis (Subsystems, Lifecycles, Plugins, Behavior Trees, 8 ISO 42010 Views).
  - Stage 5: Documentation Generation and Glassmorphism Recovery UI.

---

## Slide 5: Methodology 1 — Static AST Node Discovery

- **Slide Title**: Static Node Discovery: Python AST & C++ Clang Extraction
- **Key Bullet Points**:
  - Python AST visitor detects `rclpy.node.Node` subclasses and constructor parameters.
  - C++ scanner parses LibClang AST for `rclcpp::Node` and `rclcpp_lifecycle::LifecycleNode`.
  - CMakeLists.txt parser identifies executable targets and component registrations.
  - Automatic test node classification (`is_test = True`) isolates production nodes from mock fixtures.
  - Captures exact file paths and 1-based line ranges for $100\%$ evidence traceability.

---

## Slide 6: Methodology 2 — Hierarchical Launch Resolution

- **Slide Title**: Launch Hierarchy, Substitutions, and Container Resolution
- **Key Bullet Points**:
  - Evaluates nested launch trees: `IncludeLaunchDescription` and `GroupAction`.
  - Symbolically evaluates launch substitutions: `LaunchConfiguration`, `PythonExpression`, `PathJoinSubstitution`.
  - Discovers `ComposableNodeContainer` instances and dynamically maps contained components loaded via `LoadComposableNodes`.
  - Synthesizes distinct **Deployment Profiles** (standalone vs. composable vs. conditional).

---

## Slide 7: Methodology 3 — Interface Extraction & DDS Endpoints

- **Slide Title**: Interface Extraction & Decomposed DDS Endpoint Accounting
- **Key Bullet Points**:
  - Extracts publishers, subscribers, service servers/clients, action servers/clients, and TF interfaces with exact QoS profiles.
  - **DDS Endpoint Decomposition**: In SLAM Toolbox ($N=1$):
    - 37 Source-Level Declarations
    - 143 C++ Application Interface Instances across 7 deployment profiles
    - 170 Active ROS Graph Entities
    - 235 DDS Transport Endpoints (138 DataWriters, 97 DataReaders)
  - Modeled `TransformListener` hidden node expansion (`transform_listener_impl_...`) into dynamic `/tf` and static `/tf_static`.
  - Reconciled `interactive_markers` 2.5.5 native ROS 2 service-based refactoring.

---

## Slide 8: Methodology 4 — Schema-Constrained Synthesis & ISO Views

- **Slide Title**: Schema-Constrained Synthesis & 8 ISO/IEC/IEEE 42010 Views
- **Key Bullet Points**:
  - Newman's Graph Modularity $Q$ over communication traffic identifies cohesive subsystem clusters.
  - Pydantic v2 schemas strictly bound LLM outputs, enforcing **$0.0\%$ unsupported entity rate**.
  - Dual-LLM architecture: Google Gemini 2.5 Flash API with seamless failover to local self-hosted Ollama (Meta Llama 3.1 70B).
  - Synthesizes 8 standardized architectural viewpoints: Context, Functional, Component, Deployment, Lifecycle, Communication, Plugin, and Behavior Tree.

---

## Slide 9: Case Studies — Navigation2 & SLAM Toolbox

- **Slide Title**: Production Case Studies: Nav2 and SLAM Toolbox
- **Key Findings**:
  - **Navigation2**: 44 packages, 66 nodes, 41 launch files, 245 source interfaces, 2,168 runtime instances, 12 subsystems. Recovery F1 = **$97.7\%$**.
  - **SLAM Toolbox**: Pinned commit `eee0cd5e` (ROS 2 Jazzy). 7 launch profiles, 37 declarations, 143 C++ app instances, 235 DDS endpoints. Recovery F1 = **$100.0\%$**.
  - Grounding: 32 `SOURCE_CONFIRMED`, 5 `DEPENDENCY_CONFIRMED`, `RUNTIME_OBSERVED = 0` (no live hardware).

---

## Slide 10: Multi-Model Parity & Context Memory Experiments

- **Slide Title**: Multi-Model Benchmarking & Context Memory Paradigms
- **Key Experimental Findings**:
  - **Gemini 2.5 Flash**: Optimal efficiency ($1.25\text{s}$ latency, \$0.00148 cost, ARI = $0.895$, $0\%$ hallucination).
  - **Local Llama 3.1 70B**: Enables $100\%$ air-gapped, zero-cost execution for defense installations ($94.2\%$ schema compliance).
  - **Context Memory (Exp A–F)**: Phase-Based Sequential Memory (Exp F) achieved **$0.991$ F1 with $92.4\%$ fewer tokens** ($14,270$ tokens) compared to full-context ingestion ($188,600$ tokens, F1 = $0.865$).

---

## Slide 11: Statistical Significance & Pipeline Ablation

- **Slide Title**: Statistical Significance & Stage-by-Stage Ablation
- **Key Empirical Evidence**:
  - **Structured Memory vs. No Memory**: Cohen's $d = 18.39$, $t = 52.30$, $p < 0.001$.
  - **Phase-Based Memory vs. Full Ingestion**: Cohen's $d = 10.67$, $t = 22.01$, $p < 0.001$.
  - **Ablation Progression**: Overall F1 increases from $0.612$ (Static Only) $\rightarrow$ $0.745$ (+Launch) $\rightarrow$ $0.810$ (+Deployment) $\rightarrow$ $0.895$ (+Comm Graph) $\rightarrow$ $0.980$ (+Schema) $\rightarrow$ **$0.991$ (Full ArchSynth v2.0)**.
  - Regression Suite: **155 / 155 unit & integration tests passing (100%)**.

---

## Slide 12: Major Contributions & Dissertation Conclusion

- **Slide Title**: Summary of Contributions & Future Work
- **Contributions**:
  1. Automated, evidence-grounded architecture recovery for modern ROS 2 systems.
  2. Symbolic launch evaluation and container resolution.
  3. Decomposed DDS transport endpoint accounting.
  4. Schema-constrained dual-engine synthesis with $0\%$ hallucination and $92\%$ token reduction.
  5. 8 ISO/IEC/IEEE 42010 architecture views with interactive web dashboard and provenance sidecars.
- **Future Work**: Integration of live eBPF dynamic kernel tracing and compiler symbol table execution for obfuscated runtime C++ macros.
