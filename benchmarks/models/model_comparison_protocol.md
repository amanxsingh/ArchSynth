# Standardized Multi-Model Comparison Protocol

**Project**: ArchSynth v2.0 Research Evaluation  
**Document**: `benchmarks/models/model_comparison_protocol.md`  

---

## 1. Principles of Fair LLM Evaluation

In software architecture recovery, comparing LLMs fairly requires strict standardization to avoid confounding prompt quality, retrieval differences, or schema formatting with intrinsic model reasoning capability.

To enforce 100% parity across all evaluated models:
1. **Identical Input Grounding**: Every model receives the exact same JSON serialization of extracted Phase 1 (nodes), Phase 2 (launches & profiles), and Phase 3 (interfaces & potential communication edges).
2. **Identical Target Schema**: Every model is constrained to generate the exact same Pydantic v2 `SubsystemModel` and `ArchitectureModel` JSON structure.
3. **Identical Hyperparameters**:
   - Decoding Temperature: $T = 0.2$ (minimizes stochastic noise while preserving semantic synthesis).
   - Top-p: $0.95$.
   - Explicit JSON response mode enabled across all provider APIs.
4. **Token Accounting Isolation**:
   - Input tokens, output tokens, cached tokens, and reasoning tokens are captured directly from provider response headers and metadata objects (`usage_metadata` for Gemini, `usage` for OpenAI, `usage` for Claude, `eval_count` for Ollama).
5. **Replication Control**: Each experiment is repeated over 3 independent trials, with mean and standard deviation recorded.
6. **No Mocking or Fabrication**: Where API access is constrained or self-hosted hardware is unavailable, experiments are marked as `OFFLINE_RECORDED` or `NOT RUN` with full justification.

---

## 2. Experimental Task Definitions

### Task 1: Semantic Subsystem Clustering
- **Input**: List of extracted ROS 2 nodes, packages, executables, and pairwise communication traffic matrix.
- **Instruction**: Group nodes into 3–15 cohesive functional subsystems (e.g., Perception, Control, Planning, Infrastructure), providing a formal name, description, and architectural cohesion rationale.
- **Constraint**: Must reference only declared nodes (0 hallucinated node IDs allowed).

### Task 2: Architectural Narrative Synthesis (ISO 42010 Context View)
- **Input**: Repository identity, package inventory, launch profiles, and high-level subsystem models.
- **Instruction**: Generate an ISO/IEC/IEEE 42010 compliant System Context narrative explaining the primary purpose, external actors, operational environment, and safety-critical boundaries of the robotic system.
- **Constraint**: Must strictly reference source-confirmed ROS 2 topics and coordinate frames.

---

## 3. Evaluation Metrics for Models

| Metric | Calculation Method | Unit | Ideal Value |
|---|---|:---:|:---:|
| **Schema Compliance Rate** | $\frac{\text{Valid Pydantic Invocations}}{\text{Total Model Invocations}}$ | $\%$ | $100\%$ |
| **Unsupported Entity Rate (Hallucination)** | $\frac{\text{Entities without Source Evidence}}{\text{Total Entities Synthesized}}$ | $\%$ | $0.0\%$ |
| **Subsystem Modularity (Q)** | Newman's Graph Modularity over communication edges | $[-0.5, 1.0]$ | $> 0.50$ |
| **Adjusted Rand Index (ARI)** | Agreement with ground-truth subsystem clustering | $[-1.0, 1.0]$ | $> 0.70$ |
| **Latency** | End-to-end request duration | seconds | $< 3.0\text{ s}$ |
| **Token Efficiency** | $\frac{\text{Total Recovered Entities}}{\text{Total Ingested Tokens}} \times 1000$ | Entities/kToken | Higher |
| **API Cost per Execution** | Provider published input + output pricing | USD (\$) | Lower |
