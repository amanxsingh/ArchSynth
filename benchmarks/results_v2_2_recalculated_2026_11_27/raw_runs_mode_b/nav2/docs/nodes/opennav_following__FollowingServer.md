# Node Specification: `following_server`

- **Stable Unique ID**: `opennav_following::FollowingServer`
- **Fully Qualified Name**: `opennav_following/following_server`
- **Class / Executable**: `opennav_following::FollowingServer`
- **Package**: `opennav_following`
- **Namespace**: `opennav_following`
- **Source File**: `nav2_following/opennav_following/src/following_server.cpp`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_following/opennav_following/include/opennav_following/following_server.hpp` | `L45` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_following/opennav_following/src/following_server.cpp` | `L32` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_following/opennav_following/src/following_server.cpp` | `L688` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L53` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L63` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `filtered_dynamic_pose` | `geometry_msgs/msg/PoseStamped` | `MessageType.UNKNOWN` | `default` | `following_server.cpp:82` |
| `cmd_vel` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `following_server.cpp:47` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `pose_topic` | `geometry_msgs/msg/PoseStamped` | `MessageType.UNKNOWN` | `default` | `following_server.cpp:221` |

## Services

*No services declared.*

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `follow_object` | `unknown/action/FollowObject` | `server` | `following_server.cpp:55` |

## Parameters

*No parameters declared.*