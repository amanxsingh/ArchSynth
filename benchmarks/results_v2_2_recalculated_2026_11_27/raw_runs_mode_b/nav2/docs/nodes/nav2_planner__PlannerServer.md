# Node Specification: `planner_server`

- **Stable Unique ID**: `nav2_planner::PlannerServer`
- **Fully Qualified Name**: `nav2_planner/planner_server`
- **Class / Executable**: `nav2_planner::PlannerServer`
- **Package**: `nav2_planner`
- **Namespace**: `nav2_planner`
- **Source File**: `nav2_planner/src/planner_server.cpp`
- **Architectural Classification**: `planning`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_planner/include/nav2_planner/planner_server.hpp` | `L52` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_planner/src/planner_server.cpp` | `L46` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_planner/src/planner_server.cpp` | `L719` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L56` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L61` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `plan` | `nav_msgs/msg/Path` | `MessageType.UNKNOWN` | `default` | `planner_server.cpp:122` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `compute_path_to_pose` | `unknown/action/ActionToPose` | `server` | `planner_server.cpp:129` |
| `compute_path_through_poses` | `unknown/action/ActionThroughPoses` | `server` | `planner_server.cpp:137` |

## Parameters

*No parameters declared.*