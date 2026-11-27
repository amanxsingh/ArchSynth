# Node Specification: `controller_server`

- **Stable Unique ID**: `nav2_controller::ControllerServer`
- **Fully Qualified Name**: `nav2_controller/controller_server`
- **Class / Executable**: `nav2_controller::ControllerServer`
- **Package**: `nav2_controller`
- **Namespace**: `nav2_controller`
- **Source File**: `nav2_controller/src/controller_server.cpp`
- **Architectural Classification**: `control`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_controller/include/nav2_controller/controller_server.hpp` | `L52` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_controller/src/controller_server.cpp` | `L38` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_controller/src/controller_server.cpp` | `L989` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L56` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L249` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `transformed_global_plan` | `nav_msgs/msg/Path` | `MessageType.UNKNOWN` | `default` | `controller_server.cpp:193` |
| `tracking_feedback` | `nav2_msgs/msg/TrackingFeedback` | `MessageType.UNKNOWN` | `default` | `controller_server.cpp:194` |
| `cmd_vel` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `controller_server.cpp:192` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `params_->speed_limit_topic` | `nav2_msgs/msg/SpeedLimit` | `MessageType.UNKNOWN` | `default` | `controller_server.cpp:213` |

## Services

*No services declared.*

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `follow_path` | `unknown/action/Action` | `server` | `controller_server.cpp:199` |

## Parameters

*No parameters declared.*