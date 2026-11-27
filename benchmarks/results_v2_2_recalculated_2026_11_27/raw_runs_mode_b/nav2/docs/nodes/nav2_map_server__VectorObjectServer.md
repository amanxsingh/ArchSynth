# Node Specification: `vector_object_server`

- **Stable Unique ID**: `nav2_map_server::VectorObjectServer`
- **Fully Qualified Name**: `nav2_map_server/vector_object_server`
- **Class / Executable**: `nav2_map_server::VectorObjectServer`
- **Package**: `nav2_map_server`
- **Namespace**: `nav2_map_server`
- **Source File**: `nav2_map_server/src/vo_server/vector_object_server.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_map_server/include/nav2_map_server/vector_object_server.hpp` | `L39` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_map_server/src/vo_server/vector_object_server.cpp` | `L34` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_map_server/src/vo_server/vector_object_server.cpp` | `L605` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L183` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L201` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `map_topic_` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `vector_object_server.cpp:59` |

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `~/add_shapes` | `nav2_msgs/srv/AddShapes` | `server` | `vector_object_server.cpp:63` |
| `~/get_shapes` | `nav2_msgs/srv/GetShapes` | `server` | `vector_object_server.cpp:67` |
| `~/remove_shapes` | `nav2_msgs/srv/RemoveShapes` | `server` | `vector_object_server.cpp:71` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*