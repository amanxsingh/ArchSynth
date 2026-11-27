# Node Specification: `map_server`

- **Stable Unique ID**: `nav2_map_server::MapServer`
- **Fully Qualified Name**: `nav2_map_server/map_server`
- **Class / Executable**: `nav2_map_server::MapServer`
- **Package**: `nav2_map_server`
- **Namespace**: `nav2_map_server`
- **Source File**: `nav2_map_server/src/map_server/map_server.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_map_server/include/nav2_map_server/map_server.hpp` | `L37` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_map_server/src/map_server/map_server.cpp` | `L65` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_map_server/src/map_server/map_server.cpp` | `L256` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L119` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L200` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `map` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `map_server.cpp:115` |

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `map_server/service_name_` | `nav_msgs/srv/GetMap` | `server` | `map_server.cpp:110` |
| `map_server/load_map_service_name_` | `nav2_msgs/srv/LoadMap` | `server` | `map_server.cpp:120` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*