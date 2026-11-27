# Node Specification: `map_saver`

- **Stable Unique ID**: `nav2_map_server::MapSaver`
- **Fully Qualified Name**: `nav2_map_server/map_saver`
- **Class / Executable**: `nav2_map_server::MapSaver`
- **Package**: `nav2_map_server`
- **Namespace**: `nav2_map_server`
- **Source File**: `nav2_map_server/src/map_saver/map_saver.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_map_server/include/nav2_map_server/map_saver.hpp` | `L37` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_map_server/src/map_saver/map_saver.cpp` | `L44` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_map_server/src/map_saver/map_saver.cpp` | `L237` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L119` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L199` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `map` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `map_saver.cpp:198` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `map_saver/save_map_service_name_` | `nav2_msgs/srv/SaveMap` | `server` | `map_saver.cpp:74` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*