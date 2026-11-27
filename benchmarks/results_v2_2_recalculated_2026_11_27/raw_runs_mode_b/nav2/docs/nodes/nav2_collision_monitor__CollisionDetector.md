# Node Specification: `collision_detector`

- **Stable Unique ID**: `nav2_collision_monitor::CollisionDetector`
- **Fully Qualified Name**: `nav2_collision_monitor/collision_detector`
- **Class / Executable**: `nav2_collision_monitor::CollisionDetector`
- **Package**: `nav2_collision_monitor`
- **Namespace**: `nav2_collision_monitor`
- **Source File**: `nav2_collision_monitor/src/collision_detector_node.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_collision_monitor/include/nav2_collision_monitor/collision_detector_node.hpp` | `L50` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_collision_monitor/src/collision_detector_node.cpp` | `L29` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_collision_monitor/src/collision_detector_node.cpp` | `L477` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L117` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L132` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `collision_detector_state` | `nav2_msgs/msg/CollisionDetectorState` | `MessageType.UNKNOWN` | `default` | `collision_detector_node.cpp:49` |
| `~/collision_points_marker` | `visualization_msgs/msg/MarkerArray` | `MessageType.UNKNOWN` | `default` | `collision_detector_node.cpp:52` |
| `~/triggering_points` | `visualization_msgs/msg/MarkerArray` | `MessageType.UNKNOWN` | `default` | `collision_detector_node.cpp:55` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*