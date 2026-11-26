# ArchSynth v2.0 — Top 20 M.Tech Defense Viva Voce Questions & Answers

**Project**: ArchSynth v2.0 — Evidence-Grounded ROS 2 Architecture Recovery & Auto-Documentation  
**Academic Degree**: Master of Technology in Automation & Robotics  
**Institution**: Defence Institute of Advanced Technology (DIAT), Pune  
**Document**: `docs/presentation/viva_questions_and_answers.md`  

---

### Q1. What is the core academic problem your M.Tech dissertation addresses?
**Answer**:  
My dissertation addresses the **Architectural Drift and Documentation Crisis** in component-based robotics systems built on ROS 2. Modern robotics stacks (such as autonomous vehicles or mobile robots) consist of dozens of asynchronously communicating nodes. In practice, codebases evolve rapidly, rendering static architecture diagrams obsolete within weeks. Furthermore, robotics systems lack comprehensive, standards-compliant system architecture manuals. Prior static analysis tools extract only low-level, abstract computation graphs without human-oriented explanations, while general-purpose LLMs hallucinate non-existent topics (exceeding an $8\%$ error rate) because they lack domain-specific knowledge of ROS 2 client libraries and launch hierarchies. ArchSynth bridges this gap by unifying domain-specific static analysis, symbolic launch evaluation, and schema-constrained LLM synthesis into verifiable ISO/IEC/IEEE 42010 architectural documentation.

---

### Q2. Why is static analysis of ROS 2 nodes alone insufficient to recover system architecture?
**Answer**:  
In ROS 2, inspecting node source code alone does not reveal how the system is actually deployed. Four critical architectural factors are decided entirely at launch time:
1. **Topic Remappings**: A node may subscribe to `/scan` in C++, but launch scripts remap it to `/lidar_front/scan`.
2. **Namespace Scoping**: Launch files encapsulate nodes in namespaces (e.g., `/robot1/planner`).
3. **Execution Composition**: Launch scripts dictate whether a node runs as an independent OS process or as a lightweight, in-process component inside a `ComposableNodeContainer` (`rclcpp_components`).
4. **Conditional Branching**: Features such as simulation time (`use_sim_time`) or secondary sensors are toggled via launch arguments.  
Without hierarchical launch analysis, static node extraction yields only a disconnected catalog of classes rather than the true runtime system topology.

---

### Q3. How does ArchSynth guarantee 0% hallucination of topics and nodes during LLM synthesis?
**Answer**:  
ArchSynth enforces strict **Pydantic v2 Schema Constraints** on all LLM inputs and outputs. The pipeline never asks the LLM to invent topics or discover nodes. Instead, Python AST and LibClang visitors extract the verified set of nodes and interfaces from physical source code into structured JSON schemas. The LLM is restricted to performing **semantic clustering, architectural narrative synthesis, and cohesion rationalization**, strictly referencing the pre-extracted entity IDs. If an LLM response contains an unrecognized node ID or invalid schema structure, Pydantic validation fails, triggering an automated exponential backoff retry. This guarantees an **Unsupported Entity Rate of 0.0%**.

---

### Q4. Explain the difference between source declarations, application instances, graph entities, and DDS transport endpoints in SLAM Toolbox.
**Answer**:  
This distinction was a major scientific contribution of our Step 3C post-midterm research. They represent different levels of abstraction:
1. **Source Declarations (37)**: Unique C++ interface declarations written in the source code (13 publishers, 5 subscribers, 15 services, 3 TF broadcasters, 1 TF listener).
2. **C++ Application Interface Instances (143 at $N=1$)**: The instantiated interface objects across SLAM Toolbox's 7 independently analyzed deployment profiles (sync, async, lifelong, etc.).
3. **ROS Graph Entities (170 at $N=1$)**: Active graph entities visible to the ROS 2 graph (73 topic publishers, 32 topic subscriptions, 65 service servers).
4. **DDS Transport Endpoints (235 at $N=1$)**: The underlying Data Distribution Service (DDS) entities:
   - 73 topic publishers become **73 DDS DataWriters**.
   - 32 topic subscriptions become **32 DDS DataReaders**.
   - Each of the 65 service servers creates **1 DataReader** (request) and **1 DataWriter** (reply), contributing 130 endpoints.
   - Total = $73 + 32 + 130 = \mathbf{235}$ transport endpoints (138 DataWriters, 97 DataReaders).

---

### Q5. How does `TransformListener` expand into DDS endpoints in ROS 2 Jazzy?
**Answer**:  
In `geometry2` (0.36.4), a `tf2_ros::TransformListener` does not merely create a single topic subscription. Its constructor unconditionally instantiates an internal, dedicated hidden node prefixed with `transform_listener_impl_...`. This internal node registers two distinct topic subscriptions:
1. Dynamic transforms on `/tf`: `RELIABLE`, `VOLATILE`, `KEEP_LAST`, Depth 100.
2. Static transforms on `/tf_static`: `RELIABLE`, `TRANSIENT_LOCAL`, `KEEP_LAST`, Depth 100.  
Both subscriptions run inside the same OS process and DDS participant as the host node.

---

### Q6. What refactoring occurred in `InteractiveMarkerServer` between ROS 1 and ROS 2 Jazzy (v2.5.5)?
**Answer**:  
In legacy ROS 1, `InteractiveMarkerServer` published a latched topic called `<ns>/update_full` using `visualization_msgs/InteractiveMarkerInit`. In native ROS 2 (`interactive_markers` 2.5.5), this latched publisher was refactored and replaced by the `<ns>/get_interactive_markers` service server (`visualization_msgs/srv/GetInteractiveMarkers`). Therefore, counting `update_full` as an active publisher in ROS 2 Jazzy is historically inaccurate. The native ROS 2 server creates exactly 1 service server, 1 update publisher, and 1 feedback subscription.

---

### Q7. What does the term `INTERNAL_MATCHED` mean, and why is it not called `RUNTIME_OBSERVED`?
**Answer**:  
In ArchSynth, **`INTERNAL_MATCHED`** designates a **statically predicted, source-and-QoS-compatible local intra-stack match** (for instance, a local `/tf` publisher matching a local `/tf` listener subscriber inside the same stack).  
To uphold total scientific integrity, we strictly reserve **`RUNTIME_OBSERVED`** for dynamically captured traffic from running robot hardware or rosbag execution. In our static analysis case studies, because no physical robot or bagfile was executed, **`RUNTIME_OBSERVED` is strictly set to 0**. Confusing statically predicted matches with runtime telemetry would constitute a severe threat to construct validity.

---

### Q8. How does ArchSynth group flat nodes into high-level functional subsystems?
**Answer**:  
ArchSynth employs a two-tier hybrid approach:
1. **Mathematical Graph Modularity**: It constructs an interaction frequency matrix $M_{ij}$ representing communication edges between all recovered nodes. It evaluates Newman's graph modularity $Q$ to find dense intra-cluster connectivity.
2. **Schema-Constrained Semantic Labeling**: The LLM analyzes the cohesive node clusters, naming the subsystem (e.g., Perception, Path Planning, Actuation) and articulating an architectural cohesion rationale grounded in the nodes' common responsibilities.

---

### Q9. What is Newman's Graph Modularity ($Q$), and how is it used in your evaluation?
**Answer**:  
Graph modularity measures the fraction of communication edges falling within clusters minus the expected fraction if edges were distributed at random:
$$Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$
In our ablation study, static analysis without launch or interface awareness achieved a modularity of $Q = 0.210$ (near random). Incorporating full communication topologies and schema-constrained synthesis elevated modularity to $Q = 0.924$, proving that ArchSynth's synthesized subsystems possess high intra-module cohesion and low inter-module coupling.

---

### Q10. What are the 8 ISO/IEC/IEEE 42010 Architecture Views synthesized by ArchSynth?
**Answer**:  
ArchSynth generates 8 distinct viewpoints conforming to the ISO/IEC/IEEE 42010 systems architecture standard:
1. **System Context View (Level 1)**: Primary system purpose, operational boundaries, and external sensors/actors.
2. **Functional View**: Decomposition of the robot stack into functional capability groups.
3. **Component View (Level 3 C4)**: Core node-to-node computation graph.
4. **Deployment View (Level 4 C4)**: Mapping of nodes into physical executables, `ComposableNodeContainers`, and deployment profiles.
5. **Lifecycle View**: State machines for `LifecycleNode` instances, detailing transitions and callback triggers.
6. **Communication View**: Complete publish/subscribe, service, action, and TF topology matrix.
7. **Plugin View**: Extensibility interfaces, listing `pluginlib` base classes and discovered plugin implementations.
8. **Behavior Tree View**: Autonomous decision-making hierarchy mapped from BehaviorTree.CPP XML structures.

---

### Q11. What is the "Phase-Based Sequential Memory" paradigm (Exp F), and why did it outperform full repository ingestion?
**Answer**:  
In Experiment B, feeding the entire raw codebase into the LLM consumed $188,600$ tokens, incurred high latency ($14.8\text{s}$), and suffered from context dilution ($4.2\%$ hallucination rate).  
In Experiment F (ArchSynth v2.0), the pipeline operates sequentially: each deterministic stage extracts a verified, compact Pydantic JSON artifact (`nodes.json` $\rightarrow$ `launches.json` $\rightarrow$ `interfaces.json`), which serves as the memory context for the subsequent stage. This achieved an optimal recovery F1 of **$0.991$ with $92.4\%$ fewer tokens ($14,270$ tokens)** and a **$0.0\%$ unsupported entity rate**.

---

### Q12. How does ArchSynth handle repository provenance and prevent cross-repository contamination?
**Answer**:  
Through `src/repo_identity.py`, ArchSynth cryptographically pins every analysis to the repository's Git commit SHA, branch, and remote URL. Generated outputs are placed in dedicated isolated folders: `output/<repo_name>_pipeline/`. Every generated JSON artifact is bound to a `.provenance.json` sidecar. During initialization, any artifact with a mismatched commit hash or missing provenance is immediately purged, ensuring zero cross-repository contamination.

---

### Q13. Why did you include Express.js in your benchmark evaluation?
**Answer**:  
Express.js is a popular Node.js web framework and is completely unrelated to ROS. It serves as our **Negative Baseline Control**. In scientific evaluations, a classifier or extraction pipeline must demonstrate both high sensitivity (recovering true ROS systems) and high specificity (rejecting non-ROS software). ArchSynth's ingestion validation rule successfully scanned Express, found zero `package.xml` files, and halted with an HTTP 400 rejection, demonstrating $100\%$ negative specificity.

---

### Q14. What are the key architectural differences between Navigation2 and SLAM Toolbox?
**Answer**:  
- **Navigation2**: A large multi-package system (44 packages, 66 nodes, 41 launch files) utilizing behavior trees, multiple `ComposableNodeContainers`, and dedicated external lifecycle managers.
- **SLAM Toolbox**: A compact, algorithm-intensive C++ stack (1 package, 2 nodes, 7 launch profiles) featuring extensive C++ inheritance, intra-process transform listeners, interactive marker servers, and dual-role `/tf` broadcasting.

---

### Q15. How does ArchSynth differentiate production nodes from test nodes?
**Answer**:  
In Phase 1, `src/node_analyzer.py` applies structural heuristics and path inspection. Nodes originating within `test/` directories, nodes subclassing gtest harnesses, or nodes whose class names contain `Test` or `Mock` are tagged with `is_test = True` and categorized as `TEST_NODE`. In Nav2, this accurately distinguished the 22 production servers from the 44 system test fixtures.

---

### Q16. Can ArchSynth run in air-gapped or classified defense environments?
**Answer**:  
Yes. Through `src/llm_client.py`, ArchSynth features a built-in fallback to **Local Ollama** (e.g., Meta Llama 3.1 70B Instruct). In our benchmark evaluation, the local model ran with zero external API egress, zero operational token cost, and achieved $94.2\%$ schema compliance.

---

### Q17. What were the statistical significance findings of your research?
**Answer**:  
Using paired $t$-tests and Cohen's $d$ effect sizes across repeated experimental trials:
- **Structured Memory vs. No Memory**: Cohen's $d = 18.39$, $t = 52.30$, $p < 0.001$.
- **Phase-Based Memory vs. Full Ingestion**: Cohen's $d = 10.67$, $t = 22.01$, $p < 0.001$.  
Both demonstrated statistically significant superiority over baseline approaches.

---

### Q18. What was completed before the midterm evaluation vs. after the midterm?
**Answer**:  
At midterm (v1.0), ArchSynth had implemented basic Python AST regex scanning and flat launch parsing, suffering from unconstrained LLM hallucinations ($>8\%$).  
Post-midterm (v2.0), we implemented:
- LibClang C++ AST extraction.
- Hierarchical symbolic launch substitutions and component container resolution.
- 8 ISO/IEC/IEEE 42010 architecture views.
- Decomposed DDS endpoint accounting (235 endpoints in SLAM Toolbox).
- Provenance sidecars and directory isolation.
- The 155-test verification regression harness passing at $100\%$.

---

### Q19. What are the primary threats to validity of your research?
**Answer**:  
1. **Construct Validity**: Addressed by strictly decoupling statically predicted matches (`INTERNAL_MATCHED`) from live telemetry (`RUNTIME_OBSERVED = 0`).
2. **Internal Validity (LLM Non-Determinism)**: Mitigated by low temperature ($T = 0.2$), Pydantic schema validation, and repeated trials.
3. **External Validity (Obfuscated Dynamic C++ Macros)**: Highly obfuscated runtime macro string concatenation cannot be resolved without a live compiler runtime; ArchSynth flags such dynamic targets as `UNRESOLVED` rather than guessing.

---

### Q20. What is the primary takeaway of your M.Tech dissertation?
**Answer**:  
That automated software architecture recovery for distributed robotics systems cannot rely on static code analysis alone, nor on unconstrained generative AI alone. By coupling domain-specific AST parsing and symbolic launch evaluation with schema-constrained, phase-based sequential LLM memory, we can achieve **100% evidence-grounded, hallucination-free, standards-compliant architectural documentation** with greater than $92\%$ token efficiency.
