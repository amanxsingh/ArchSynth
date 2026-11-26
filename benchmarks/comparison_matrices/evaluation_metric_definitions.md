# ArchSynth Evaluation Metric Definitions & Mathematical Formulations

**Project**: ArchSynth v2.0 Research Evaluation  
**Document**: `benchmarks/comparison_matrices/evaluation_metric_definitions.md`  

---

## 1. Information Retrieval & Extraction Accuracy Metrics

For all architectural entities (Nodes, Publishers, Subscribers, Service Servers, Service Clients, Action Servers, Action Clients, and Deployment Instances), extraction performance is evaluated against an authoritative reference ground-truth inventory:

### 1.1 Precision
The proportion of recovered architectural entities that genuinely exist in the reference codebase:
$$\text{Precision} = \frac{TP}{TP + FP}$$
- **$TP$ (True Positives)**: Correctly discovered entities matching the reference ground truth in name, package, and interface signature.
- **$FP$ (False Positives)**: Erroneously claimed entities not present in the source codebase (hallucinations or spurious detections).

### 1.2 Recall
The proportion of existing architectural entities that were successfully recovered by the pipeline:
$$\text{Recall} = \frac{TP}{TP + FN}$$
- **$FN$ (False Negatives)**: True architectural entities present in the codebase that were missed by static AST parsing or launch resolution.

### 1.3 F1-Score
The harmonic mean of Precision and Recall, balancing false alarms against omissions:
$$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = \frac{2 \cdot TP}{2 \cdot TP + FP + FN}$$

---

## 2. Evidence Grounding & Traceability Metrics

### 2.1 Evidence Coverage Rate ($\text{Cov}_{\text{ev}}$)
The percentage of recovered architectural entities backed by verifiable, line-number grounded source code evidence:
$$\text{Cov}_{\text{ev}} = \frac{\sum_{i=1}^{N} \mathbb{I}(\text{len}(e_i.\text{evidence}) > 0)}{N} \times 100\%$$
Where:
- $N$ is the total number of recovered entities.
- $\mathbb{I}(\cdot)$ is the indicator function.
- $e_i.\text{evidence}$ represents the set of line-grounded evidence items associated with entity $e_i$.

### 2.2 Unsupported Entity Rate ($\text{Rate}_{\text{unsupported}}$)
The fraction of synthesized entities that cannot be traced to any physical file or AST declaration in the repository (direct measure of LLM hallucination):
$$\text{Rate}_{\text{unsupported}} = \frac{|\mathcal{E}_{\text{unsupported}}|}{|\mathcal{E}_{\text{total}}|} \times 100\%$$
- Under strict Pydantic v2 schema-constrained execution, ArchSynth targets $\text{Rate}_{\text{unsupported}} = 0.0\%$.

---

## 3. Subsystem Clustering Quality Metrics

### 3.1 Newman's Graph Modularity ($Q$)
Measures the density of communication edges inside synthesized subsystems compared to edges between different subsystems:
$$Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$
Where:
- $A_{ij}$ is the communication edge weight between node $i$ and node $j$.
- $k_i = \sum_j A_{ij}$ is the total communication degree of node $i$.
- $m = \frac{1}{2} \sum_{i,j} A_{ij}$ is the total edge weight across the graph.
- $c_i$ is the subsystem cluster assigned to node $i$.
- $\delta(u, v) = 1$ if $u = v$, and $0$ otherwise.
- High $Q$ ($Q > 0.4$) indicates high intra-subsystem cohesion and low inter-subsystem coupling.

### 3.2 Adjusted Rand Index (ARI)
Evaluates clustering agreement between LLM-synthesized subsystems $\mathcal{U} = \{u_1, \dots, u_R\}$ and expert reference subsystems $\mathcal{V} = \{v_1, \dots, v_C\}$, corrected for chance:
$$\text{ARI} = \frac{\sum_{ij} \binom{n_{ij}}{2} - \left[ \sum_i \binom{a_i}{2} \sum_j \binom{b_j}{2} \right] / \binom{n}{2}}{\frac{1}{2} \left[ \sum_i \binom{a_i}{2} + \sum_j \binom{b_j}{2} \right] - \left[ \sum_i \binom{a_i}{2} \sum_j \binom{b_j}{2} \right] / \binom{n}{2}}$$
Where $n_{ij} = |u_i \cap v_j|$, $a_i = \sum_j n_{ij}$, and $b_j = \sum_i n_{ij}$.

---

## 4. Token Efficiency and Computational Performance Metrics

### 4.1 Token Efficiency Ratio ($\eta_{\text{token}}$)
The number of valid, ground-truth confirmed architectural entities recovered per 1,000 processed LLM tokens:
$$\eta_{\text{token}} = \frac{TP}{\text{Tokens}_{\text{total}}} \times 1000$$

### 4.2 Latency ($T_{\text{exec}}$)
The wall-clock duration of pipeline execution:
$$T_{\text{exec}} = t_{\text{end}} - t_{\text{start}} \quad [\text{seconds}]$$

### 4.3 Analysis Throughput ($\Theta_{\text{file}}$)
The number of source and launch files ingested and parsed per second:
$$\Theta_{\text{file}} = \frac{|\mathcal{F}_{\text{analyzed}}|}{T_{\text{exec}}} \quad [\text{files/second}]$$
