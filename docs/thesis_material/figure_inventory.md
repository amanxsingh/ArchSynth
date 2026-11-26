# ArchSynth v2.0 — Comprehensive Thesis Figure & Diagram Inventory

**Project**: ArchSynth v2.0 Dissertation Material  
**Document**: `docs/thesis_material/figure_inventory.md`  
**Diagram Format**: Editable Mermaid.js Syntax  

---

## Figure 1: Overall ArchSynth Architecture

- **Figure Number**: Figure 1.1 (or Figure 4.1)
- **Title**: High-Level System Architecture and Dual-Engine Synthesis Pipeline of ArchSynth v2.0
- **Purpose**: Illustrate the complete architectural flow from source ingestion through static AST extraction, launch resolution, schema-constrained dual-LLM synthesis, and ISO 42010 documentation generation.
- **Suggested Thesis Chapter**: Chapter 1 (Introduction) or Chapter 4 (System Design)
- **Relevant Implementation Files**: `src/main.py`, `src/schema.py`, `src/architecture_constructor.py`

```mermaid
flowchart TD
    subgraph InputLayer ["1. Input & Provenance Layer"]
        Repo[Target ROS 2 Git Repository] --> Ingestor[Ingestor: package.xml Validation]
        Ingestor --> Prov[RepoIdentity: Commit SHA & .provenance.json]
    end

    subgraph StaticCore ["2. Static Domain Analysis Engine"]
        Prov --> AST[NodeAnalyzer: Python AST & C++ Clang Visitors]
        AST --> Launch[LaunchAnalyzer: Symbolic Substitution & Profile Engine]
        Launch --> Extract[InterfaceExtractor: Topics, Services, Actions, TF & QoS]
        Extract --> Comm[CommunicationBuilder: Pairwise Topology & Matrix]
    end

    subgraph DualEngine ["3. Schema-Constrained Dual-LLM Synthesis"]
        Comm --> Synth[Subsystem & Views Synthesizer]
        Synth <--> Pydantic[Pydantic v2 Schema Enforcement Gate]
        Pydantic <--> LLMClient{LLMClient Engine}
        LLMClient -->|Primary| Gemini[Google Gemini 2.5 Flash API]
        LLMClient -->|Fallback / Air-Gap| Ollama[Local Ollama: Llama 3.1 70B]
    end

    subgraph PresentationLayer ["4. Delivery & Reporting Layer"]
        Synth --> DocGen[DocGenerator: ISO 42010 Markdown Manuals]
        DocGen --> WebUI[Web Dashboard: Architecture Recovery]
        DocGen --> Benchmarks[Benchmarks Workspace: Research Evaluation]
    end
```

---

## Figure 2: Complete Architecture Recovery Pipeline

- **Figure Number**: Figure 3.1
- **Title**: Multi-Stage Architecture Recovery and Provenance Pipeline
- **Purpose**: Depict the step-by-step data transformations between physical files and abstract architectural models.
- **Suggested Thesis Chapter**: Chapter 3 (Research Methodology)
- **Relevant Implementation Files**: `src/main.py`, `src/node_analyzer.py`, `src/launch_analyzer.py`

```mermaid
flowchart LR
    S1[Stage 1: Ingest & Validate] -->|nodes.json| S2[Stage 2: Node Discovery]
    S2 -->|launches.json| S3[Stage 3: Launch Analysis]
    S3 -->|interfaces.json| S35[Phase 3.5: Interface Extraction]
    S35 -->|subsystem_model.json| S4[Stage 4: Multi-View Synthesis]
    S4 -->|README.md| S5[Stage 5: ISO 42010 DocGen]
```

---

## Figure 3: Repository Ingestion & ROS 2 Validation Workflow

- **Figure Number**: Figure 3.2
- **Title**: Repository Ingestion, Manifest Validation Gate, and Isolation Protocol
- **Purpose**: Show how ArchSynth enforces the ROS 2 package rule and isolates outputs.
- **Suggested Thesis Chapter**: Chapter 3 (Methodology)
- **Relevant Implementation Files**: `src/ingestor.py`, `src/repo_identity.py`

```mermaid
flowchart TD
    Start[User Repository Input] --> CheckType{Git URL or Local Path?}
    CheckType -->|Git URL| Clone[git clone at Pinned Commit]
    CheckType -->|Local Path| Resolve[Resolve Path on Filesystem]
    Clone --> ScanManifest[Scan for package.xml Manifests]
    Resolve --> ScanManifest
    ScanManifest --> HasPackages{Found >= 1 package.xml?}
    HasPackages -->|No| Reject[HTTP 400: NOT A ROS2 REPOSITORY]
    HasPackages -->|Yes| GitProv[Extract Commit SHA, Branch, Remote URL]
    GitProv --> SetupDir[Create output/repo_pipeline/ Directory]
    SetupDir --> AttachSidecar[Attach .provenance.json Sidecars]
```

---

## Figure 4: Static Node Discovery Workflow

- **Figure Number**: Figure 3.3
- **Title**: Dual Python AST and C++ Clang Static Node Extraction
- **Purpose**: Explain how Python and C++ node definitions are extracted with line-number evidence.
- **Suggested Thesis Chapter**: Chapter 3 (Methodology) or Chapter 5 (Implementation)
- **Relevant Implementation Files**: `src/node_analyzer.py`, `src/cpp_analyzer.py`

```mermaid
flowchart TD
    SourceFiles[Source Files: .cpp, .hpp, .py] --> BranchLang{Language?}
    BranchLang -->|Python| PyAST[ast.parse -> ast.NodeVisitor]
    BranchLang -->|C++| CppAST[LibClang AST & Header Scanning]
    PyAST --> CheckPySub[Detect rclpy.node.Node Subclass]
    CppAST --> CheckCppSub[Detect rclcpp::Node or LifecycleNode]
    CheckPySub --> ExtractEvidence[Extract Class, Executable, File & Line Range]
    CheckCppSub --> ExtractEvidence
    ExtractEvidence --> FilterTests{Is Test / Mock?}
    FilterTests -->|Yes| FlagTest[Tag is_test=True]
    FilterTests -->|No| FlagProd[Tag is_test=False]
    FlagTest --> GenInventory[Generate nodes.json with EvidenceItem]
    FlagProd --> GenInventory
```

---

## Figure 5: Launch Analysis & Deployment Hierarchy Workflow

- **Figure Number**: Figure 3.4
- **Title**: Hierarchical Launch Resolution, Substitutions, and Container Mapping
- **Purpose**: Detail how nested launch trees and component containers are symbolically resolved.
- **Suggested Thesis Chapter**: Chapter 3 (Methodology)
- **Relevant Implementation Files**: `src/launch_analyzer.py`

```mermaid
flowchart TD
    LaunchFile[.launch.py / .launch.xml] --> ParseLaunch[Parse AST / XML Tree]
    ParseLaunch --> ResolveSubs[Symbolic Substitution Engine]
    ResolveSubs --> NestedInclude{IncludeLaunchDescription?}
    NestedInclude -->|Yes| Recurse[Recursively Evaluate Child Launch]
    NestedInclude -->|No| CheckContainers{ComposableNodeContainer?}
    CheckContainers -->|Yes| HostContainer[Register Container Host]
    CheckContainers -->|No| NodeAction[Extract Node Declaration]
    HostContainer --> LoadComp[Map LoadComposableNodes Components]
    LoadComp --> SynthProfiles[Synthesize Deployment Profiles]
    NodeAction --> SynthProfiles
    SynthProfiles --> OutLaunch[Generate launch_instances.json & deployment_profiles.json]
```

---

## Figure 6: ROS 2 Interface Extraction Workflow

- **Figure Number**: Figure 3.5
- **Title**: Communication Interface Extraction & QoS Profile Deduction
- **Purpose**: Show extraction of publishers, subscribers, services, actions, and coordinate transforms.
- **Suggested Thesis Chapter**: Chapter 3 (Methodology)
- **Relevant Implementation Files**: `src/interface_extractor.py`

```mermaid
flowchart TD
    ASTTree[Node AST & Source Code] --> ScanAPIs[Scan ROS 2 Client Library Invocations]
    ScanAPIs --> PubSub[create_publisher / create_subscription]
    ScanAPIs --> SrvCli[create_service / create_client]
    ScanAPIs --> ActCli[rclcpp_action::create_server / client]
    ScanAPIs --> TFInt[TransformBroadcaster / TransformListener]
    PubSub --> ExtractQoS[Deduce QoS: Reliability, Durability, History, Depth]
    SrvCli --> ExtractQoS
    ActCli --> ExtractQoS
    TFInt --> ExpandTF[Expand TransformListener into /tf and /tf_static hidden node]
    ExtractQoS --> GroundEvidence[Map 1-based Line Evidence & Boundary Role]
    ExpandTF --> GroundEvidence
    GroundEvidence --> SaveInterfaces[Save interfaces.json with EvidenceItem]
```

---

## Figure 7: Communication Graph Construction

- **Figure Number**: Figure 3.6
- **Title**: Deterministic Communication Graph Matching & Traffic Matrix
- **Purpose**: Illustrate how source potential edges and deployment runtime edges are matched.
- **Suggested Thesis Chapter**: Chapter 3 (Methodology)
- **Relevant Implementation Files**: `src/communication_builder.py`

```mermaid
flowchart LR
    Pubs[Published Topic Interfaces] --> Matcher{Topic Name & QoS Matcher}
    Subs[Subscribed Topic Interfaces] --> Matcher
    Matcher --> PotentialEdges[Compute Potential Source Edges]
    PotentialEdges --> DeployFilter{In Same Deployment Profile?}
    DeployFilter -->|Yes| RuntimeEdges[Resolved Runtime Graph Edges]
    DeployFilter -->|No| ExternalEdges[External System Edges]
    RuntimeEdges --> TrafficMatrix[Construct Communication Interaction Matrix M_ij]
```

---

## Figure 8: Deployment Architecture & Container Mapping

- **Figure Number**: Figure 4.2
- **Title**: Runtime Deployment Architecture: Standalone Nodes vs. Composable Containers
- **Purpose**: Visualize how physical processes and thread containers host logical ROS 2 components.
- **Suggested Thesis Chapter**: Chapter 4 (System Design)
- **Relevant Implementation Files**: `src/schema.py`, `src/launch_analyzer.py`

```mermaid
graph TD
    subgraph OSProcess1 ["OS Process: Standalone Executable"]
        AMCL[amcl_node: Standalone Node]
    end

    subgraph OSProcess2 ["OS Process: ComposableNodeContainer"]
        Container[nav2_container Host Process]
        Container --> Comp1[controller_server Component]
        Container --> Comp2[planner_server Component]
        Container --> Comp3[behavior_server Component]
    end

    subgraph OSProcess3 ["OS Process: Lifecycle Manager"]
        LM[lifecycle_manager: Orchestration Process]
    end

    LM -.->|ROS Service: State Transitions| OSProcess1
    LM -.->|ROS Service: State Transitions| OSProcess2
```

---

## Figure 9: Evidence & Provenance Workflow

- **Figure Number**: Figure 4.3
- **Title**: Cryptographic Provenance and Source-Level Traceability Flow
- **Purpose**: Illustrate the provenance pipeline guaranteeing artifact reproducibility.
- **Suggested Thesis Chapter**: Chapter 4 (System Design)
- **Relevant Implementation Files**: `src/repo_identity.py`, `src/evidence_validator.py`

```mermaid
flowchart TD
    GitRepo[Git Repository @ Commit SHA] --> Inspect[repo_identity: Extract Commit & URL]
    Inspect --> GenArtifact[Pipeline Generates Artifact: e.g. nodes.json]
    GenArtifact --> HashCheck[Compute File Digest & Metadata]
    HashCheck --> AttachSidecar[Write nodes.json.provenance.json]
    AttachSidecar --> ValidateEvidence[evidence_validator: Verify Physical Lines on Disk]
    ValidateEvidence --> ValidReport[ValidationReport: 100% Grounded, 0% Unsupported]
```

---

## Figure 10: LLM-Assisted Synthesis Workflow

- **Figure Number**: Figure 4.4
- **Title**: Schema-Constrained Dual-Engine LLM Architecture Synthesis
- **Purpose**: Show how Pydantic v2 schemas prevent LLM hallucinations during subsystem clustering.
- **Suggested Thesis Chapter**: Chapter 4 (System Design)
- **Relevant Implementation Files**: `src/llm_client.py`, `src/subsystem_synthesizer.py`

```mermaid
flowchart TD
    Inputs[Extracted Nodes & Traffic Matrix M_ij] --> Modularity[Compute Graph Modularity Q]
    Modularity --> PromptGen[Construct Structured JSON Prompt]
    PromptGen --> LLMClient{LLM Client Router}
    LLMClient -->|Primary API| Gemini[Google Gemini 2.5 Flash]
    LLMClient -->|Failover / Air-Gap| Ollama[Local Ollama: Llama 3.1 70B]
    Gemini --> JSONResponse[Raw JSON Output]
    Ollama --> JSONResponse
    JSONResponse --> PydanticGate{Pydantic v2 Schema Validation}
    PydanticGate -->|Schema Valid| VerifiedModel[Verified SubsystemModel]
    PydanticGate -->|Schema Invalid| Retry[Exponential Backoff Retry]
    Retry --> LLMClient
```

---

## Figure 11: Context Memory Strategy Comparison (Exp A–F)

- **Figure Number**: Figure 6.1
- **Title**: Context Memory Paradigms in LLM-Assisted Architecture Recovery
- **Purpose**: Contrast unconstrained memory (Exp A, B) with structured and phase-based memory (Exp C, F).
- **Suggested Thesis Chapter**: Chapter 6 (Evaluation) or Chapter 7 (Results)
- **Relevant Implementation Files**: `benchmarks/experiments/context_memory_experiments/`

```mermaid
graph TD
    ExpA[Exp A: No Memory<br>3.9k Tokens | F1=0.724 | 8.4% Hallucination]
    ExpB[Exp B: Full Ingestion<br>188.6k Tokens | F1=0.865 | 4.2% Hallucination]
    ExpC[Exp C: Structured Memory<br>16.4k Tokens | F1=0.978 | 0% Hallucination]
    ExpD[Exp D: RAG Semantic<br>21.2k Tokens | F1=0.892 | 2.8% Hallucination]
    ExpE[Exp E: Hierarchical Memory<br>18.9k Tokens | F1=0.985 | 0% Hallucination]
    ExpF[Exp F: Phase-Based Sequential<br>14.2k Tokens | F1=0.991 | 0% Hallucination]

    ExpA -.->|Add Context| ExpB
    ExpB -.->|Apply Structure| ExpC
    ExpC -.->|Add Hierarchy| ExpE
    ExpE -.->|Pipeline Stages| ExpF
```

---

## Figure 12: Empirical Benchmarking Methodology

- **Figure Number**: Figure 6.2
- **Title**: Multi-Dimensional Empirical Benchmarking Framework
- **Purpose**: Outline the multi-dimensional benchmark architecture.
- **Suggested Thesis Chapter**: Chapter 6 (Evaluation)
- **Relevant Implementation Files**: `benchmarks/README.md`

```mermaid
flowchart TD
    BenchSuite[ArchSynth Empirical Benchmark Suite] --> Repos[Dim 1: 5 Repositories + Control]
    BenchSuite --> Models[Dim 2: 5 Frontier & Local LLMs]
    BenchSuite --> Memory[Dim 3: 6 Context Memory Paradigms]
    BenchSuite --> Ablations[Dim 4: 7-Level Pipeline Ablation]
    Repos --> EvalMetrics[Metrics: Precision, Recall, F1, Modularity Q, ARI, Latency, Cost]
    Models --> EvalMetrics
    Memory --> EvalMetrics
    Ablations --> EvalMetrics
```

---

## Figure 13: Cross-Repository Recovery Accuracy

- **Figure Number**: Figure 7.1
- **Title**: Recovery Precision, Recall, and F1-Score Across 5 Production Case Studies
- **Purpose**: Summarize extraction fidelity across Navigation2, SLAM Toolbox, ROS 2 Control, Jaco2 Devkit, and BehaviorTree.CPP.
- **Suggested Thesis Chapter**: Chapter 7 (Results and Discussion)
- **Relevant Implementation Files**: `benchmarks/comparison_matrices/architecture_recovery_comparison.csv`

```mermaid
graph LR
    Nav2[Navigation2: F1 = 97.7%]
    SLAM[SLAM Toolbox: F1 = 100.0%]
    Control[ROS 2 Control: F1 = 96.0%]
    Jaco2[Jaco2 Devkit: F1 = 95.7%]
    BT[BehaviorTree.CPP: F1 = 100.0%]
    Express[Express Control: Rejection = 100.0%]
```

---

## Figure 14: Multi-Model Latency vs. Cost Trade-Off

- **Figure Number**: Figure 7.2
- **Title**: Cost vs. Latency Trade-Off Across Evaluated LLM Models
- **Purpose**: Compare API cost, latency, and clustering quality.
- **Suggested Thesis Chapter**: Chapter 7 (Results and Discussion)
- **Relevant Implementation Files**: `benchmarks/comparison_matrices/model_comparison.csv`

```mermaid
graph TD
    GeminiFlash[Gemini 2.5 Flash: Latency 1.25s | Cost $0.0015 | ARI 0.895]
    GeminiPro[Gemini 1.5 Pro: Latency 3.80s | Cost $0.0263 | ARI 0.924]
    GPT4o[GPT-4o: Latency 2.40s | Cost $0.0505 | ARI 0.880]
    ClaudeSonnet[Claude 3.5 Sonnet: Latency 2.85s | Cost $0.0675 | ARI 0.912]
    LlamaLocal[Llama 3.1 70B: Latency 7.40s | Cost $0.0000 | ARI 0.815]
```

---

## Figure 15: Chronological Development Timeline (Midterm to Final)

- **Figure Number**: Figure 1.2
- **Title**: Chronological Development Progression: Midterm PoC vs. ArchSynth v2.0 Final Thesis Release
- **Purpose**: Highlight the evolution of ArchSynth between September 2026 and November 2026.
- **Suggested Thesis Chapter**: Chapter 1 (Introduction) or Appendix
- **Relevant Implementation Files**: `docs/project_history/midterm_vs_post_midterm.md`

```mermaid
flowchart TD
    Midterm[Midterm PoC: September 2026<br>- Basic Python AST Regex<br>- Flat Launch Parsing<br>- Unconstrained LLM Hallucinations 8%<br>- 22 Unit Tests] --> PostMidterm[Post-Midterm Research: October - November 2026<br>- LibClang C++ AST Symbol Table Extraction<br>- Symbolic Launch Substitution Engine<br>- Decomposed DDS Endpoint Accounting 235 Endpoints<br>- 8 ISO 42010 Architecture Views<br>- Provenance Sidecars & Directory Isolation<br>- 155 Unit & Integration Tests Passing 100%]
```

---

## Figure 16: Final Architecture Recovery Output (ISO 42010 Viewpoint Collection)

- **Figure Number**: Figure 4.5
- **Title**: Reconstructed 8 ISO/IEC/IEEE 42010 Architecture Viewpoints
- **Purpose**: Display the complete set of architectural views generated by ArchSynth.
- **Suggested Thesis Chapter**: Chapter 4 (System Design) or Chapter 5 (Implementation)
- **Relevant Implementation Files**: `src/view_generator.py`, `output/nav2_pipeline/architecture_views.json`

```mermaid
graph TD
    Root[ArchSynth ISO/IEC/IEEE 42010 Architecture Views]
    Root --> V1[1. System Context View: External Actors & Boundaries]
    Root --> V2[2. Functional View: Robotic Capabilities & Subsystems]
    Root --> V3[3. Component View: Level 3 C4 Node Interactions]
    Root --> V4[4. Deployment View: Containers & OS Process Allocations]
    Root --> V5[5. Lifecycle View: State Machine & Transition Orchestration]
    Root --> V6[6. Communication View: Topic Pub/Sub & Service Topologies]
    Root --> V7[7. Plugin View: pluginlib Base Class Interfaces]
    Root --> V8[8. Behavior Tree View: Autonomous Navigation Decision Trees]
```
