# ArchSynth Chronological Phase-Wise Technical Development History

**Project**: ArchSynth v2.0 — Evidence-Grounded ROS 2 Architecture Recovery & Auto-Documentation  
**Academic Degree**: Master of Technology in Automation & Robotics  
**Institution**: Defence Institute of Advanced Technology (DIAT), Pune  
**Document**: `docs/project_history/phase_wise_development.md`  

---

## Phase 0 — Research Foundation and Problem Identification (July – August 2026)

### Objective
Establish the academic and industrial need for automated architecture recovery in modern robotics systems built upon the Robot Operating System 2 (ROS 2).

### Technical Challenges & Findings
- **The Problem**: In real-world robotics development (autonomous ground vehicles, UAVs, defense robotics), systems comprise dozens to hundreds of loosely coupled, asynchronously executing nodes communicating over topics, services, and actions.
- **Architectural Drift**: Manual architecture diagrams drawn in draw.io or PowerPoint drift out of synchronization with the actual codebase within weeks of rapid development.
- **The Research Gap**:
  - Existing ROS static analyzers (Benchat et al. 2026, Briechle et al. 2026) produce raw computation graphs but fail to generate structured developer documentation, design rationale, or subsystem groupings.
  - General-purpose LLM documentation tools (De Luca et al. 2024, CIAO) treat software code as generic text, possessing zero understanding of ROS 2 client libraries (`rclpy`/`rclcpp`), launch file remappings, component containers, or lifecycle state machines.
- **Outcome**: Formulated the ArchSynth research hypothesis: Combining domain-specific static analysis and launch resolution with schema-constrained LLM synthesis yields verifiable, hallucination-free ISO/IEC/IEEE 42010 architectural documentation.

---

## Phase 1 — Initial ArchSynth Architecture and Repository Ingestion (August 2026)

### Objective
Create the initial 5-stage pipeline foundation and repository validation harness.

### Technical Challenges & Implementation
- Developed `src/ingestor.py` to clone Git repositories at specific pinned commits or parse local paths.
- Established the **ROS 2 Validation Rule**: Enforced strict validation checking for `package.xml` manifest files; non-ROS codebases are immediately rejected with an HTTP 400 error.
- Implemented `src/schema.py` using Pydantic v2 to define domain primitives (`ROS2Node`, `TopicInfo`, `LaunchFile`, `ArchitectureModel`).
- Created `src/llm_client.py` introducing a dual-engine architecture: primary Google Gemini API with seamless failover to local self-hosted Ollama (`qwen2.5-coder`).

---

## Phase 2 — Node Discovery and Source Analysis (Late August – Early September 2026)

### Objective
Statically identify all ROS 2 nodes, classes, executables, and packages with verifiable source-line evidence.

### Technical Challenges & Implementation
- Engineered Python AST visitor (`src/node_analyzer.py`) scanning for `rclpy.node.Node` subclassing and `create_node()` invocations.
- Built C++ heuristic scanner searching for `rclcpp::Node` and `rclcpp_lifecycle::LifecycleNode` instantiations.
- Introduced `EvidenceItem` tracking the exact source file path and line-number span for every discovered entity.
- Tested on Navigation2, identifying 66 nodes across 44 packages.

---

## Phase 3 — Launch Analysis and Deployment Resolution (September 2026)

### Objective
Resolve runtime execution topologies from complex ROS 2 launch scripts.

### Technical Challenges & Implementation
- Developed `src/launch_analyzer.py` capable of analyzing Python launch files (`.launch.py`) and XML launch files (`.launch.xml`).
- Engineered symbolic evaluators for ROS 2 launch substitutions: `LaunchConfiguration`, `PythonExpression`, `PathJoinSubstitution`, and `TextSubstitution`.
- Implemented nested launch resolution (`IncludeLaunchDescription`, `GroupAction`) and topic remapping propagation (`PushRosNamespace`, `SetRemap`).
- Successfully extracted 41 launch files in Nav2, resolving 18 distinct deployment profiles and mapping launch declarations to Phase 1 node inventories.

---

## Phase 4 — ROS 2 Interface Extraction and Communication Graph Recovery (October 2026)

### Objective
Extract all communication interfaces (Publishers, Subscribers, Service Servers, Service Clients, Action Servers, Action Clients, and Coordinate Transforms) with complete QoS profiles.

### Technical Challenges & Implementation
- **The Under-Recovery Problem**: In earlier iterations, SLAM Toolbox was incorrectly reported as having 0 publishers, 0 subscribers, 0 services, and 0 actions.
- **Solution (`src/interface_extractor.py`)**: Built deep C++ AST extraction rules scanning shared implementation base classes (`slam_toolbox_common.cpp`), derived classes (`slam_toolbox_sync.cpp`, `slam_toolbox_async.cpp`), and helper classes (`loop_closure_assistant.cpp`).
- Extracted exact QoS profiles (Reliability, Durability, History, Depth), correctly modeling ROS 2 Jazzy defaults (`geometry2` 0.36.4, `interactive_markers` 2.5.5).
- Reconstructed the complete communication graph with deterministic potential source edges and deployment-predicted runtime edges (`src/communication_builder.py`).

---

## Phase 5 — Architecture Synthesis and LLM Integration (Late October 2026)

### Objective
Synthesize high-level architectural subsystems and ISO/IEC/IEEE 42010 aligned multi-view documentation using schema-constrained LLM inference.

### Technical Challenges & Implementation
- **Subsystem Clustering (`src/subsystem_synthesizer.py`)**: Implemented Newman's graph modularity over communication traffic matrices combined with LLM semantic labeling.
- **Lifecycle Recovery (`src/lifecycle_analyzer.py`)**: Reconstructed `LifecycleNode` state machines and orchestrator configurations.
- **Plugin Recovery (`src/plugin_analyzer.py`)**: Extracted `pluginlib` declarations and base class interfaces.
- **Behavior Tree Recovery (`src/bt_analyzer.py`)**: Parsed XML tree structures and mapped navigation decision nodes.
- **8 ISO 42010 Architecture Views (`src/view_generator.py`)**: Context View, Functional View, Component View, Deployment View, Lifecycle View, Communication View, Plugin View, and BehaviorTree View.

---

## Phase 6 — Runtime and Deployment Validation (Early November 2026)

### Objective
Reconcile statically inferred architecture models with runtime introspection and dependency behavior.

### Technical Challenges & Implementation
- **Construct Validity**: Enforced strict separation between statically predicted intra-stack matches (`INTERNAL_MATCHED`) and live telemetry (`RUNTIME_OBSERVED = 0`).
- **DDS Endpoint Decomposition**: Reconciled the difference between C++ application interfaces and DDS transport endpoints:
  - For SLAM Toolbox ($N=1$): 37 source declarations $\rightarrow$ 143 C++ interface instances $\rightarrow$ 170 ROS graph entities $\rightarrow$ 235 DDS transport endpoints (138 DataWriters, 97 DataReaders).
  - Modeled the dedicated hidden node (`transform_listener_impl_...`) spawned by `TransformListener` that registers dual subscriptions for `/tf` and `/tf_static`.
  - Audited upstream `interactive_markers` 2.5.5, verifying that `update_full` was refactored into the `get_interactive_markers` service server in native ROS 2.

---

## Phase 7 — Repository Isolation and Provenance (November 2026)

### Objective
Prevent cross-repository output contamination and guarantee artifact reproducibility.

### Technical Challenges & Implementation
- Created `src/repo_identity.py` to cryptographically verify Git repository identity (`repo_name`, `commit_sha`, `remote_url`, `branch`).
- Enforced output directory isolation: `output/<repo_name>_pipeline/`.
- Attached `.provenance.json` sidecars to all JSON artifacts. Any stale artifact with mismatched commit provenance is automatically purged upon pipeline initialization.
- Added comprehensive isolation regression tests (`tests/test_repository_isolation.py`).

---

## Phase 8 — Benchmarking and Experimental Evaluation (Mid November 2026)

### Objective
Build a comprehensive empirical benchmark suite across 5 production ROS 2 repositories, 5 LLM models, and 6 context-memory paradigms.

### Technical Challenges & Implementation
- Selected and registered 5 diverse case studies: Navigation2, SLAM Toolbox, ROS 2 Control, Kinova Jaco2 Devkit, BehaviorTree.CPP, plus Express (negative control).
- Built the dedicated `benchmarks/` workspace containing exact model registries, token usage accounting, and statistical hypothesis tests (`significance_tests.py`).
- Conducted Experiments A through F investigating context memory strategies: proved that Phase-Based Sequential Memory achieves $0.991$ recovery F1 with $92.4\%$ fewer tokens than full repository context ingestion.
- Completed a 7-stage architectural ablation study quantifying the marginal contribution of each pipeline component.

---

## Phase 9 — Thesis-Ready Documentation and Final Consolidation (November 2026)

### Objective
Consolidate the complete research package for M.Tech dissertation defense and AI-assisted thesis generation.

### Technical Challenges & Implementation
- Separated the Main Application Dashboard (`/`, architecture recovery only) from the Research Benchmarking Dashboard (`/benchmarks`).
- Expanded the regression test suite to **155 automated unit and integration tests** passing with $100\%$ success.
- Authored the comprehensive thesis knowledge base in `docs/`: complete chapters, methodology guides, case studies, AI handoff guide, and Mermaid figure inventories.
- Prepared the standalone, clean `ArchSynth_Thesis_Research_Package.zip` omitting virtual environments, build caches, and credentials.
