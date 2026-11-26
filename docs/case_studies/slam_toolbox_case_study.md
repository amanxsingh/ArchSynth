# Case Study 2: SLAM Toolbox — Architecture Recovery & Endpoint Reconciliation

**Repository**: `https://github.com/SteveMacenski/slam_toolbox`  
**Branch**: `ros2`  
**Pinned Commit**: `eee0cd5e4a161bb10f8334b5420c93876b31ca99`  
**Target ROS Distribution**: ROS 2 Jazzy  
**Audited Upstream Dependencies**: `geometry2` 0.36.4, `interactive_markers` 2.5.5  
**Document**: `docs/case_studies/slam_toolbox_case_study.md`  

---

## 1. Architectural Overview & Context

SLAM Toolbox is the standard 2D Simultaneous Localization and Mapping solution in ROS 2. It implements lifelong mapping, synchronous and asynchronous laser scan processing, submap merging, and pose-graph optimization using Ceres Solver.

Prior analysis of SLAM Toolbox suffered from a massive under-recovery (identifying only 4 topics and 2 services attributed to map_merging, and reporting 0 interfaces for the main SlamToolbox node). ArchSynth v2.0 audited the source repository at commit `eee0cd5`, recovering the complete set of C++ application interface objects, launch mappings, lifecycle transitions, and DDS transport endpoints.

---

## 2. Reconciled Architectural Accounting Matrix

| Metric Category | Source Declarations | C++ App Instances ($N=1$) | ROS Graph Entities ($N=1$) | DDS Transport Endpoints ($N=1$) |
|---|:---:|:---:|:---:|:---:|
| **Topic Publishers** | 13 | 53 | **73** (53 app + 13 tf + 7 ims) | **73** DataWriters |
| **Topic Subscriptions** | 5 | 13 | **32** (13 app + 12 tf + 7 ims) | **32** DataReaders |
| **Service Servers** | 15 | 58 | **65** (58 app + 7 ims) | **65** DataWriters + **65** DataReaders |
| **Transform Broadcasters** | 3 | 13 | *(expanded into pubs)* | *(expanded into DataWriters)* |
| **Transform Listeners** | 1 | 6 | *(expanded into subs)* | *(expanded into DataReaders)* |
| **Total** | **37** | **143** | **170** | **235** (138 Writers, 97 Readers) |

### Parameterized Dynamic Submap Formulation (`MergeMapsKinematic`)
For $N \ge 0$ added submaps:
$$\text{ROS Graph Entities} = 8 + 2N \qquad (\text{Baseline } N=0: 8, \quad N=1: 10)$$
$$\text{DDS Transport Endpoints} = 11 + 2N \qquad (\text{Baseline } N=0: 11, \quad N=1: 13)$$
*(At baseline $N=0$, the cross-profile aggregate is 168 graph entities and 233 DDS endpoints).*

---

## 3. Upstream Dependency Verification & Architectural Grounding

### 3.1 `interactive_markers` 2.5.5 Native ROS 2 Refactoring
Direct inspection of upstream source code (`ros-visualization/interactive_markers` v2.5.5, `src/interactive_marker_server.cpp:55-95`) revealed the exact constructor behavior and QoS profiles:
1. **Service Server (`<ns>/get_interactive_markers`)**:
   - Type: `visualization_msgs/srv/GetInteractiveMarkers`
   - QoS: `rmw_qos_profile_services_default` (`RELIABLE`, `VOLATILE`, `KEEP_LAST`, Depth 10)
2. **Update Publisher (`<ns>/update`)**:
   - Type: `visualization_msgs/msg/InteractiveMarkerUpdate`
   - QoS: `rclcpp::QoS(100)` (`RELIABLE`, `VOLATILE`, `KEEP_LAST`, Depth 100)
3. **Feedback Subscription (`<ns>/feedback`)**:
   - Type: `visualization_msgs/msg/InteractiveMarkerFeedback`
   - QoS: `rclcpp::QoS(1)` (`RELIABLE`, `VOLATILE`, `KEEP_LAST`, Depth 1)
4. **Deprecation of `update_full`**:
   - In ROS 1, `update_full` was a latched topic (`InteractiveMarkerInit`). In native ROS 2 (2.5.5), `update_full` was refactored and replaced by the `get_interactive_markers` service server. Durability across all interactive marker endpoints in ROS 2 Jazzy is strictly `VOLATILE`.

### 3.2 `TransformListener` Hidden Node Expansion (`geometry2` 0.36.4)
- Each `TransformListener` constructor unconditionally spawns an internal dedicated hidden node (`transform_listener_impl_...`) that registers:
  1. Dynamic `/tf` subscription: `RELIABLE`, `VOLATILE`, `KEEP_LAST`, Depth 100.
  2. Static `/tf_static` subscription: `RELIABLE`, `TRANSIENT_LOCAL`, `KEEP_LAST`, Depth 100.
- Single-argument constructor `TransformListener(*tf_)` defaults `spin_thread = true`.
- Executes within the same OS process and DDS participant context as the host node.

---

## 4. Evidence Classification & Terminology Grounding

- **Evidence Status Breakdown across 37 Source Declarations**:
  - `SOURCE_CONFIRMED`: **32** (all direct application interface declarations)
  - `DEPENDENCY_CONFIRMED`: **5** (3 TF broadcasters, 1 TF listener, 1 `/scan` subscriber using `rclcpp::SensorDataQoS()`)
- **Connectivity Precision**:
  - `INTERNAL_MATCHED`: Strictly designates **statically predicted, source-and-QoS-compatible local intra-stack matches** (e.g. `/tf` publisher $\leftrightarrow$ local `/tf` listener subscriber).
  - `RUNTIME_OBSERVED`: Strictly **0** across all entities, as no hardware or live rosbag replay was executed.
  - `MergeMapsKinematic`'s TF broadcaster is strictly `EXTERNAL_FACING` in its launch profile (no local listener exists in `merge_maps_kinematic`).
