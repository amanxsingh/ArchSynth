# Limitations and Validity (2026-11-27 Update)

1. `behaviortree_cpp` has no ground-truth dataset and remains marked `N/A`; `express` is evaluated strictly as a negative control (`0` nodes/interfaces/launches).
2. `slam_toolbox` and `ros2_control` ground-truth files validate entity inventories (`nodes`, `topics`, `services`, `actions`) but do not define independent cluster partitions, so subsystem `ARI`/`NMI` for those two repos are marked `N/A`.
3. `nav2` `topics` (`GT = 15`) and `services` (`GT = 6`) still compare full 44-package extraction (`40` prod topics, `26` prod services) against the core Nav2 bringup ground-truth subset, so Nav2 topic/service Precision remains `0.2500`/`0.2308` even when Recall is `0.6667`/`1.0000`.
4. `google-generativeai` and `ollama` remain absent in this environment (`LLM-only` / `Mode B` unavailable).
5. `runtime_observation_available = False` on this Windows host.
