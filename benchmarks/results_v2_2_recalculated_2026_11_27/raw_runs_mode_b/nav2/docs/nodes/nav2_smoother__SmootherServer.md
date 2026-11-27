# Node Specification: `smoother_server`

- **Stable Unique ID**: `nav2_smoother::SmootherServer`
- **Fully Qualified Name**: `nav2_smoother/smoother_server`
- **Class / Executable**: `nav2_smoother::SmootherServer`
- **Package**: `nav2_smoother`
- **Namespace**: `nav2_smoother`
- **Source File**: `nav2_smoother/src/nav2_smoother.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_smoother/include/nav2_smoother/nav2_smoother.hpp` | `L46` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_smoother/src/nav2_smoother.cpp` | `L33` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_smoother/src/nav2_smoother.cpp` | `L381` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L54` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L130` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `plan_smoothed` | `nav_msgs/msg/Path` | `MessageType.UNKNOWN` | `default` | `nav2_smoother.cpp:91` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `smooth_path` | `unknown/action/Action` | `server` | `nav2_smoother.cpp:94` |

## Parameters

*No parameters declared.*