# ArchSynth v2.2 — M.Tech Review Presentation & Benchmark Defense Guide

This folder contains the standalone M.Tech project review presentation and complete explanation guide for **ArchSynth v2.2** (*Automated Architecture Recovery & Evidence-Grounded Synthesis for ROS 2 Robotic Systems*).

> **Isolation Note:** Everything in `review_presentation/` is kept completely separate from the web application UI (`web/`, `app.py`).

## Files in This Folder
- `ArchSynth_Review_Presentation.pptx` — 21-slide widescreen (16:9) review presentation following the exact required academic sequence.
- `build_presentation.py` — Reproducible `python-pptx` generator script used to build the deck.
- `README.md` — This guide: slide-by-slide speaker notes, mathematical backing for every benchmark score, v2.0 vs. v2.2 score reconciliation, and anticipated guide/external examiner Q&A.

---

## 1. Slide-by-Slide Speaker Notes & Talking Points (Slides 1–21)

### Slide 1 — Title Slide
- **Title:** ArchSynth v2.2: Automated Architecture Recovery & Evidence-Grounded Synthesis for ROS 2 Robotic Systems
- **Presenter:** Aman Singh (M.Tech in Automation & Robotics, Department of Robotics & Autonomous Systems, DIAT Pune).
- **Opening Pitch (30 seconds):**
  - "Good morning/afternoon to my guide and the external examiner. My project, **ArchSynth v2.2**, is a deterministic, evidence-grounded architecture recovery engine for ROS 2 robotic systems. Instead of relying on manual diagrams that go stale or ungrounded LLMs that hallucinate components, ArchSynth parses C++/Python ASTs, launch files, and package manifests into a verified system graph, and uses an LLM strictly for bounded semantic synthesis."

### Slide 2 — Content (Agenda)
- Walk through the two-part structure matching the evaluation rubric:
  - **Part I (Slides 3–8):** Introduction, Literature Review, Research Gap, and Objectives.
  - **Part II (Slides 9–21):** Methodology, Results & Benchmark Defense, Publications, Conclusion & Future Work, References, and Q&A.

### Slide 3 — Introduction (Part 1: The Architectural Drift Problem)
- Explain **why** ROS 2 systems suffer from architectural drift:
  - Production stacks like **Navigation2 (Nav2)** span dozens of packages, **75** discovered nodes (**28** production, **47** test), **41** launch files, **120** launch instances, and **288** source interfaces.
  - Documentation diagrams are manually drawn and become outdated within weeks of refactoring.
  - Static architecture cannot be captured by `ros2 node list` alone because runtime inspection misses inactive lifecycle nodes, conditional launch branches, and unlaunched packages.

### Slide 4 — Introduction (Part 2: What ArchSynth v2.2 Does)
- Highlight the core design philosophy:
  1. **Zero-Hallucination Structural Truth:** Deterministic AST, launch, and manifest parsing establishes nodes, interfaces, and dependencies with exact `file:line` citations.
  2. **Evidence-Grounded Synthesis:** The LLM (Gemini) operates *only* on the verified structural JSON to assign human-readable subsystem names and descriptions — it never invents nodes or edges.
  3. **Standards-Aligned Views:** Outputs ISO/IEC/IEEE 42010:2011 architectural views and C4-style decomposition alongside interactive graph exploration and reproducible benchmarks.

### Slide 5 — Literature Review (Part 1: ROS 2 Static & Launch Analysis)
- Contrast foundational ROS / ROS 2 works:
  - **Quigley et al. (2009) & Macenski et al. (2022):** Established ROS / ROS 2 computation graphs, lifecycle nodes, and DDS middleware, making static recovery nontrivial due to dynamic remapping and parameters.
  - **Maruyama et al. (2016):** Analyzed ROS 2 DDS communication characteristics (QoS, latency, throughput), showing why interface semantics matter.
  - **Santos et al. (2016) / HAROS:** Static verification and quality analysis for ROS, but oriented toward model checking / C++ rules rather than full launch-aware multi-view architecture recovery.
  - **Benchat et al. (2026) & Briechle et al. (2026):** Recent ROS 2 launch and static analysis advances highlighting the complexity of Python/XML launch trees and parameter resolution.

### Slide 6 — Literature Review (Part 2: Software Architecture, Modularity & LLMs)
- Connect classical software engineering and AI:
  - **Ducasse & Pollet (2009), Garcia et al. (2013), Kazman et al. (2000):** Architecture recovery taxonomies (ARCADE, ATAM) showing why ground-truth comparison and structural clustering are hard.
  - **ISO/IEC/IEEE 42010:2011 & Brown (2018) C4 Model:** Multi-viewpoint architecture description standards (Context, Container, Component, Deployment).
  - **Newman (2006) & Blondel et al. (2008):** Modularity optimization and Louvain community detection for unsupervised subsystem clustering.
  - **Hou et al. (2024), Feng et al. (2020), Chen et al. (2021), De Luca et al. (2024):** LLMs/CodeBERT excel at semantic summarization but suffer hallucination when asked to recover structure directly from raw codebases.

### Slide 7 — Research Gap
- Present the 3-way gap matrix clearly:
  - **Pure Static / Launch Tools:** High structural precision, but lack multi-view ISO/C4 synthesis, semantic subsystem naming, and unified reconciliation across C++/Python/YAML/Launch.
  - **Unconstrained LLMs:** Good at fluent summaries, but fail token/context budgets on 75-node repos, hallucinate non-existent topics/nodes, and have unquantified unsupported entity rates.
  - **ArchSynth v2.2:** Bridges both — 100% deterministic structural recovery (`0.0` unsupported entity rate, `1.0` evidence coverage) + bounded LLM semantic enrichment + strict ground-truth benchmarking.

### Slide 8 — Objectives
- Five concrete, verifiable objectives:
  1. **O1 — Multi-Language & Launch Extraction:** Recover ROS 2 nodes, parameters, TF2 frames, and lifecycle states from C++ (`tree-sitter`), Python (`ast`), and XML/YAML/Python launch files.
  2. **O2 — Interface & Communication Graph Synthesis:** Extract publishers, subscribers, services, and actions (including YAML-configured & API-inferred endpoints) with `file:line` provenance.
  3. **O3 — Unsupervised Subsystem Recovery & ISO Views:** Cluster nodes into functional subsystems and generate ISO 42010 / C4 architectural views.
  4. **O4 — Evidence-Grounded LLM Enrichment:** Integrate Gemini (`Mode B`) without sacrificing structural determinism (`Mode A` vs. `Mode B` invariant F1).
  5. **O5 — Rigorous Ground-Truth Benchmarking:** Evaluate Precision, Recall, F1, Evidence Coverage, Unsupported Entity Rate, and Ablation across 6 repositories (including non-ROS negative control).

### Slide 9 — Methodology: End-to-End 5-Stage Pipeline
- Walk left-to-right across the architecture diagram:
  - **Stage 1 (Ingestion & Isolation):** Repo cloning/commit pinning, non-ROS negative-control gate (rejects Express.js cleanly).
  - **Stage 2 (AST & Manifest Parsing):** C++ `tree-sitter` + Python `ast` + `package.xml` + `CMakeLists.txt` -> verified nodes + provenance.
  - **Stage 3 (Launch & Deployment Graph):** Python/XML/YAML launch resolution, node instances, remappings, YAML parameter files.
  - **Stage 4 (Interface, TF2 & Comm Graph):** Topics, services, actions, TF2 broadcasters/listeners, QoS profiles, and cross-node edges.
  - **Stage 5 (Clustering, ISO Views & Reconciliation):** Louvain/modularity clustering, optional Gemini semantic naming (`Mode B`), ISO 42010 views, and Ground-Truth Evaluator.

### Slide 10 — Methodology: Stages 1–2 (AST Extraction & Provenance)
- Explain how nodes are discovered accurately:
  - C++ classes inheriting `rclcpp::Node` or `rclcpp_lifecycle::LifecycleNode` via `tree-sitter` queries.
  - Python classes subclassing `rclpy.node.Node` via Python's built-in `ast` module.
  - Every discovered entity carries `source_file`, `line_number`, `kind` (`production` vs `test`), and `package`.
  - Separation of `production` vs `test` nodes is essential so test harnesses don't pollute architecture views (e.g., Nav2 has **28** production and **47** test nodes = **75** total).

### Slide 11 — Methodology: Stage 3 (Launch Resolution & Package Dependencies)
- Explain why AST parsing alone isn't enough:
  - A single C++ node class can be instantiated multiple times under different names/namespaces in launch files (e.g., Nav2 has **28** production node definitions expanding to **120** launch instances across **41** launch files).
  - Stage 3 resolves `Node(...)`, `ComposableNode(...)`, `IncludeLaunchDescription`, and YAML parameter overrides.

### Slide 12 — Methodology: Stage 4 (Interfaces, TF2 & Communication Graph)
- Explain interface extraction depth:
  - Direct API calls: `create_publisher`, `create_subscription`, `create_service`, `create_client`, `rclcpp_action::create_server/client`.
  - **v2.2 Improvement (API-Inferred & YAML-Configured Actions):** Also captures wrapper/template actions and YAML-configured plugin actions (demonstrated on `jaco2_sim_devkit`: `3` API-inferred actions and `2` YAML-configured actions recovered at **1.0 F1**).
  - TF2 static/dynamic broadcasters and listeners build the coordinate-frame dependency view.

### Slide 13 — Methodology: Stage 5 (Subsystem Clustering, ISO 42010 & LLM Grounding)
- Explain the two execution modes:
  - **Mode A (`skip_llm=True`):** 100% deterministic structural recovery + graph-based subsystem clustering (Louvain / package-informed modularity) + rule-based subsystem labels.
  - **Mode B (`skip_llm=False`, Live Gemini):** Passes the verified structural summary to Gemini to synthesize rich architectural narratives and domain-meaningful subsystem titles, followed by a **strict reconciliation guard** that rejects any entity ID not present in Stage 2–4 outputs (`unsupported_entity_rate = 0.0`).

### Slide 14 — Methodology: Ground-Truth & Evaluation Protocol
- Explain how evaluation avoids cherry-picking:
  - Every benchmark repository is pinned to an exact Git commit SHA.
  - Curated ground-truth JSON/YAML files (derived from official architecture docs, READMEs, and verified source inspection) define expected core/extended nodes, topics, services, actions, and subsystems.
  - Standard IR metrics: **Precision**, **Recall**, **F1**, plus **Evidence Coverage** (fraction of predicted entities backed by `file:line` proof) and **Unsupported Entity Rate** (fraction lacking source proof).
  - Includes **Negative Control (`express`)** to prove the tool does not hallucinate ROS 2 entities on non-ROS repositories.

### Slide 15 — Results (Part 1: 6-Repository Cross-Evaluation)
- Present the 6-repository table from `repository_comparison.csv`:
  - `nav2`: 75 nodes (28 prod, 47 test), 41 launches, 120 instances, 288 interfaces, 11 subsystems, `1.0` coverage, `0.0` unsupported, `16.197s`.
  - `slam_toolbox`: 10 prod nodes, 7 launches, 7 instances, 61 interfaces, 3 subsystems, `1.0` coverage, `3.712s`.
  - `ros2_control`: 6 nodes (1 prod, 5 test), 1 launch, 1 instance, 14 interfaces, 2 subsystems, `1.0` coverage, `5.855s`.
  - `jaco2_sim_devkit`: 11 prod nodes, 12 launches, 38 instances, 24 interfaces, 6 subsystems, `1.0` coverage, `2.03s`.
  - `behaviortree_cpp`: 2 prod nodes, 0 launches, 0 interfaces, 1 subsystem, `1.0` coverage, `7.108s` (`ground_truth_available=False`, pure C++ library without ROS 2 comms).
  - `express`: `0` everything, `negative_control_rejected=True`, `1.415s`.

### Slide 16 — Results (Part 2: Entity-Level Precision, Recall & F1)
- Highlight the exact numbers from `entity_metrics.csv`:
  - **Perfect 1.0000 F1** across `slam_toolbox` (nodes 4/4, topics 14/14, services 14/14), `ros2_control` (nodes 1/1, topics 2/2, services 11/11), and `jaco2_sim_devkit` (nodes 11/11, topics 8/8, services 3/3, api_inferred_actions 3/3, yaml_configured_actions 2/2).
  - **Nav2 (Scale & Granularity):**
    - `nodes_core`: Recall **1.0000** (13/13), Precision **0.4643** (13/28), F1 **0.6341**.
    - `nodes_core_pkg_scoped`: Recall **1.0000** (13/13), Precision **0.7647** (13/17), F1 **0.8667**.
    - `nodes_extended`: Recall **0.9545** (21/22), Precision **0.7500** (21/28), F1 **0.8400**.
    - `actions`: Recall **0.9286** (13/14), Precision **0.7647** (13/17), F1 **0.8387**.
    - `topics`: Recall **0.6667** (10/15), Precision **0.2500** (10/40), F1 **0.3636** (explained below in Section 2!).
    - `services`: Recall **1.0000** (6/6), Precision **0.2308** (6/26), F1 **0.3750**.
  - **Subsystem Clustering:** Nav2 `mean_jaccard = 0.7000`, `NMI = 0.8186`, `ARI = 0.2632` (`evaluated_nodes = 8`); JACO2 `ARI = 1.0`, `NMI = 1.0` (`evaluated_nodes = 11`).

### Slide 17 — Results (Part 3: Ablation Study & Live Gemini Mode B)
- Show why our architecture beats baselines:
  - **Mode A (`skip_llm=True`) vs. Live Gemini Mode B (`skip_llm=False`):**
    - Nav2: `16.197s` vs `28.559s` — **identical F1s** (`0.6341`, `0.8667`, `0.8400`, `0.8387`), `1.0` evidence coverage, `0.0` unsupported entity rate.
    - JACO2: `2.030s` vs `19.645s` (identical `1.0` F1s).
    - SLAM Toolbox: `3.712s` vs `16.424s` (identical `1.0` F1s).
    - ROS 2 Control: `5.855s` vs `17.563s` (identical `1.0` F1s).
  - **Key Takeaway:** Adding the LLM adds rich architectural synthesis without degrading precision, breaking determinism, or introducing hallucinated entities.
  - Also mention the unit test suite (`109 tests in 18.469s — OK`).

### Slide 18 — Publications & Dissemination
- Be transparent and academically honest:
  - Currently **no published journal/conference paper** yet; work is prepared as the M.Tech Thesis Dissertation at DIAT Pune.
  - Target submission venues identified: **ICSA** (International Conference on Software Architecture), **Journal of Systems and Software (JSS)**, and **IEEE/RSJ IROS** (Software Engineering for Robotics tracks).

### Slide 19 — Conclusion & Future Work
- Summarize contributions: Deterministic ROS 2 extraction + bounded LLM synthesis + 6-repo verified benchmark (`109/109` tests passing).
- Future Work:
  1. Dynamic runtime trace fusion (rosbag2 / DDS discovery) to resolve runtime-remapped topic names.
  2. Multi-robot namespace graph partitioning.
  3. Automated CI/CD architectural drift alerts on Pull Requests.

### Slide 20 — References
- 11 key peer-reviewed & standard references (Macenski 2022, Quigley 2009, Maruyama 2016, Ducasse & Pollet 2009, Garcia 2013, ISO/IEC/IEEE 42010:2011, Brown 2018, Santos 2016, De Luca 2024, Hou 2024, Blondel 2008) matching `docs/thesis_material/references_and_citations.md`.

### Slide 21 — Thank You
- Clean closing slide inviting questions from the Guide and External Examiner.

---

## 2. How to Back Every Benchmark Score (Mathematical & Technical Defense)

If the external examiner asks *"Where did this number come from?"* or *"Why is Nav2 topic precision 0.25?"*, use the exact formulas and facts below from `benchmarks/results_v2_2_recalculated_2026_11_27/`.

### A. Exact Metric Formulas & Accounting Invariants
Every score in `entity_metrics.csv` satisfies two strict accounting identities:
- $\text{GT} = \text{TP} + \text{FN}$ (every ground-truth item is either found or missed)
- $\text{Pred} = \text{TP} + \text{FP}$ (every predicted item is either in GT or extra)
- $\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{\text{TP}}{\text{Pred}}$
- $\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{\text{TP}}{\text{GT}}$
- $\text{F1} = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}} = \frac{2\text{TP}}{2\text{TP} + \text{FP} + \text{FN}}$

**Worked Verification Examples (from `entity_metrics.csv`):**
1. **Nav2 `nodes_core`:** $\text{GT}=13, \text{Pred}=28 \implies \text{TP}=13, \text{FP}=15, \text{FN}=0$
   - $P = 13/28 = \mathbf{0.4643}$, $R = 13/13 = \mathbf{1.0000}$, $F1 = \frac{2(13)}{2(13)+15+0} = 26/41 = \mathbf{0.6341}$
2. **Nav2 `nodes_core_pkg_scoped`:** $\text{GT}=13, \text{Pred}=17 \implies \text{TP}=13, \text{FP}=4, \text{FN}=0$
   - $P = 13/17 = \mathbf{0.7647}$, $R = 13/13 = \mathbf{1.0000}$, $F1 = 26/30 = \mathbf{0.8667}$
3. **Nav2 `nodes_extended`:** $\text{GT}=22, \text{Pred}=28 \implies \text{TP}=21, \text{FP}=7, \text{FN}=1$
   - $P = 21/28 = \mathbf{0.7500}$, $R = 21/22 = \mathbf{0.9545}$, $F1 = 42/50 = \mathbf{0.8400}$
4. **Nav2 `actions`:** $\text{GT}=14, \text{Pred}=17 \implies \text{TP}=13, \text{FP}=4, \text{FN}=1$
   - $P = 13/17 = \mathbf{0.7647}$, $R = 13/14 = \mathbf{0.9286}$, $F1 = 26/31 = \mathbf{0.8387}$
5. **Nav2 `topics`:** $\text{GT}=15, \text{Pred}=40 \implies \text{TP}=10, \text{FP}=30, \text{FN}=5$
   - $P = 10/40 = \mathbf{0.2500}$, $R = 10/15 = \mathbf{0.6667}$, $F1 = 20/55 = \mathbf{0.3636}$
6. **Nav2 `services`:** $\text{GT}=6, \text{Pred}=26 \implies \text{TP}=6, \text{FP}=20, \text{FN}=0$
   - $P = 6/26 = \mathbf{0.2308}$, $R = 6/6 = \mathbf{1.0000}$, $F1 = 12/32 = \mathbf{0.3750}$

### B. Why Is Nav2 Precision Lower on Full-Repo `topics` (0.25) and `nodes_core` (0.4643)?
- **It is NOT hallucination!** Notice that `evidence_coverage = 1.0` and `unsupported_entity_rate = 0.0` across all 28 production nodes and 288 source interfaces in Nav2. Every single "FP" has an exact C++/Python `file:line` citation!
- **Why does `entity_metrics.csv` count them as FP?** Because the curated Ground Truth only lists the **13 core architectural nodes**, **15 high-level topics**, and **6 core services** documented in Nav2's high-level overview — whereas ArchSynth's AST scanner recovers **all 28 real production nodes** (including auxiliary lifecycle/bridge/utility nodes like `nav2_map_server` helpers, route/docking/collision monitor nodes) and **all 40 real source topics** (including internal costmap updates, debug markers, and parameter/diagnostic topics).
- **Proof:** When we scope the evaluation to the core packages (`nodes_core_pkg_scoped`), Precision jumps from `0.4643` to `0.7647` (`F1 = 0.8667`), and against the 22-node `nodes_extended` GT, F1 is `0.8400` with `95.45%` recall!

### C. Why Did v2.0 Show ~97.7% While v2.2 Shows 0.6341 / 0.8667 / 0.8400?
- If the examiner asks about earlier draft numbers (`v2.0` vs `v2.2`), explain clearly:
  1. **v2.0** measured small/scoped extraction checks or internal consistency on fewer targets without full-repo strict GT matching across all 75 Nav2 nodes and 288 interfaces.
  2. **v2.2** enforces **strict commit-pinned, full-repository evaluation**, separates `production` vs `test` nodes, distinguishes `nodes_core` vs `nodes_core_pkg_scoped` vs `nodes_extended`, and explicitly penalizes extra real utility nodes/topics against minimal architectural GT rather than hiding them.
  3. On well-bounded repositories (`slam_toolbox`, `ros2_control`, `jaco2_sim_devkit`), v2.2 achieves **1.0000 (100%) F1** across nodes, topics, services, and actions.

### D. Crucial Metric Distinctions to Keep Straight
- **`Evidence Coverage (1.0)` $\neq$ `Recall`:**
  - *Evidence Coverage* = fraction of ArchSynth's **output entities** that have a verified `file:line` source citation (`1.0` = 0 hallucinations).
  - *Recall* = fraction of **Ground Truth entities** that ArchSynth successfully found (`1.0` on Nav2 core nodes & services; `0.9545` on extended nodes).
- **Why `BehaviorTree.CPP` shows `ground_truth_available = False` (`N/A`):**
  - `behaviortree_cpp` is a **pure C++ middleware/behavior-tree library**, not a ROS 2 application with launch graphs or DDS topics/services. Including it proves ArchSynth cleanly detects `2` library nodes and `0` ROS interfaces without fabricating fake topics.
- **Why `Express.js` (`express`) is in the table (`0` nodes, `negative_control_rejected = True`):**
  - It is a **Node.js web framework** used as a **negative control** to prove zero false positives on non-ROS codebases (`1.415s` fast rejection).
- **Why `Mode A` and `Live Gemini Mode B` have identical F1 scores:**
  - Because ArchSynth intentionally decouples **structural extraction (deterministic AST/Launch/YAML)** from **semantic synthesis (LLM)**. Gemini improves architectural narratives and subsystem labeling without ever altering the verified node/interface set.

---

## 3. Anticipated Guide & External Examiner Questions (Viva Prep)

1. **Q: If Mode A and Mode B have identical F1 scores, why use an LLM at all?**
   - **A:** F1 measures *structural entity recovery* (nodes, topics, services, actions), which *must* remain 100% deterministic so the tool never hallucinates components. The LLM (Mode B) adds *semantic value* — synthesizing human-readable C4/ISO 42010 architectural descriptions, domain-meaningful subsystem names, and cross-component design rationale that pure AST parsers cannot produce.

2. **Q: How do you guarantee the LLM doesn't hallucinate new nodes or edges in Mode B?**
   - **A:** Through a two-layer defense: (1) Gemini never sees raw files to guess entities — it only receives the verified Stage 2–4 JSON summary; (2) Stage 5 runs a deterministic reconciliation check verifying every referenced ID against the extracted symbol table (`unsupported_entity_rate = 0.0`).

3. **Q: Why is Nav2 `ARI = 0.2632` when `NMI = 0.8186` and `Mean Jaccard = 0.70`?**
   - **A:** `ARI` (Adjusted Rand Index) penalizes strict pair-counting disagreements when a larger architectural subsystem is split into finer-grained functional sub-clusters (11 subsystems vs. fewer coarse GT groups on the 8 evaluated core nodes), whereas `NMI = 0.8186` and `Mean Jaccard = 0.70` show strong mutual information and cluster overlap.

4. **Q: How are `jaco2_sim_devkit` actions recovered if `source_actions = 0`?**
   - **A:** Through v2.2's multi-mechanism action extractor: **3** `api_inferred_actions` (wrapper/MoveIt/control API patterns) and **2** `yaml_configured_actions` (controller YAML definitions), both achieving **1.0000 F1**.

5. **Q: What happens if someone runs ArchSynth on a non-ROS repository?**
   - **A:** Stage 1's repository gate detects the absence of ROS 2 manifests/patterns and rejects it cleanly (`negative_control_rejected = True` on `express` in `1.415s` with `0` entities).
