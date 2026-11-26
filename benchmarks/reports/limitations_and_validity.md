# Threats to Validity & Known Limitations

**Project**: ArchSynth v2.0 Research Evaluation  
**Document**: `benchmarks/reports/limitations_and_validity.md`  

---

## 1. Threats to Construct Validity

1. **Static Inference vs. Dynamic Runtime Truth**:
   - In ArchSynth, static AST analysis extracts declared topics, services, and actions.
   - For case studies where no physical robot hardware or live bagfile replay was executed (e.g. SLAM Toolbox commit `eee0cd5`), **`RUNTIME_OBSERVED` is strictly set to 0**.
   - Intra-process coordinate transform links (e.g., `/tf` broadcaster to `/tf` listener) are labeled **`INTERNAL_MATCHED`** (statically predicted, source-and-QoS-compatible local match), never confused with dynamically captured traffic.

2. **DDS Endpoint Expansion Accounting**:
   - ROS 2 communication endpoints do not map 1:1 to C++ application objects.
   - For example, a `TransformListener` spawns a dedicated internal node (`transform_listener_impl_...`) that subscribes to both `/tf` and `/tf_static`.
   - In ROS 2 Jazzy, `InteractiveMarkerServer` (v2.5.5) refactored the legacy ROS 1 `update_full` latched publisher into the `get_interactive_markers` service server. Counting legacy ROS 1 endpoints would introduce construct invalidity. ArchSynth inspects exact upstream source code to guarantee accurate endpoint accounting.

---

## 2. Threats to Internal Validity

1. **LLM Non-Determinism**:
   - Stochastic token sampling can introduce variability across runs.
   - **Mitigation**: Temperature was set to $T = 0.2$ across all models, and Pydantic v2 schemas were applied to constrain output keys and types strictly.

2. **Context Dilution in Large Codebases**:
   - Concatenating hundreds of source files into an LLM context window causes the "lost in the middle" phenomenon.
   - **Mitigation**: ArchSynth uses **Phase-Based Sequential Memory** (Experiment F), extracting structured JSON representations in each deterministic stage rather than relying on raw LLM text comprehension.

---

## 3. Threats to External Validity

1. **Generalizability Across ROS 2 Distributions**:
   - Codebases were evaluated on ROS 2 Humble, Jazzy, and Rolling.
   - While ArchSynth fully models Jazzy and Humble conventions (e.g., `rclcpp::QoS(100)` and `rmw_qos_profile_services_default`), systems relying on non-standard middleware or proprietary RMW implementations may require customized QoS profile definitions.

2. **Heuristic C++ Macro Extraction**:
   - Heavily obfuscated C++ macros or template metaprogramming that dynamically construct topic names at runtime cannot be completely resolved via static AST parsing without full compiler symbol table execution. ArchSynth flags such dynamic targets as `UNRESOLVED` or `CONDITIONAL` rather than fabricating static names.

---

## 4. Threats to Conclusion Validity & Statistical Limitations

1. **Ground-Truth Annotation Asymmetry**:
   - Navigation2 and SLAM Toolbox possess authoritative, expert-verified reference ground-truth specifications and exhaustive unit-test test suites (155 tests).
   - In contrast, secondary repositories (`ros2_control`, `jaco2_sim_devkit`, and `behaviortree_cpp`) were evaluated against automated package-manifest and AST symbol extraction baselines. Reported metrics for these secondary targets represent internal extraction consistency rather than manual expert consensus, and are explicitly designated as *preliminary empirical estimates*.

2. **Sample Size & Statistical Scope**:
   - Hypothesis testing was conducted on $N=5$ benchmark tasks with 3 repeated trials per condition.
   - While statistical significance ($p < 0.001$) and large effect sizes ($d > 5$) confirm the internal validity of structured schema memory and frontier model synthesis over unconstrained prompting, these findings represent a controlled pilot study. Broad statistical generalization across the broader ROS 2 ecosystem requires scaling the benchmark corpus to $N \ge 30$ community repositories.
