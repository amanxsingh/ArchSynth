# Node Specification: `collision_monitor`

- **Stable Unique ID**: `nav2_collision_monitor::CollisionMonitor`
- **Fully Qualified Name**: `nav2_collision_monitor/collision_monitor`
- **Class / Executable**: `nav2_collision_monitor::CollisionMonitor`
- **Package**: `nav2_collision_monitor`
- **Namespace**: `nav2_collision_monitor`
- **Source File**: `nav2_collision_monitor/src/collision_monitor_node.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_collision_monitor/include/nav2_collision_monitor/collision_monitor_node.hpp` | `L54` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_collision_monitor/src/collision_monitor_node.cpp` | `L32` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_collision_monitor/src/collision_monitor_node.cpp` | `L774` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L104` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L130` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `state_topic` | `nav2_msgs/msg/CollisionMonitorState` | `MessageType.UNKNOWN` | `default` | `collision_monitor_node.cpp:75` |
| `~/collision_points_marker` | `visualization_msgs/msg/MarkerArray` | `MessageType.UNKNOWN` | `default` | `collision_monitor_node.cpp:79` |
| `~/triggering_points` | `visualization_msgs/msg/MarkerArray` | `MessageType.UNKNOWN` | `default` | `collision_monitor_node.cpp:82` |
| `cmd_vel` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `collision_monitor_node.cpp:72` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `cmd_vel_smoothed` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `collision_monitor_node.cpp:65` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `~/toggle` | `nav2_msgs/srv/Toggle` | `server` | `collision_monitor_node.cpp:86` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*