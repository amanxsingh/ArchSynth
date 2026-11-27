# Node Specification: `costmap_filter_info_server`

- **Stable Unique ID**: `nav2_map_server::CostmapFilterInfoServer`
- **Fully Qualified Name**: `nav2_map_server/costmap_filter_info_server`
- **Class / Executable**: `nav2_map_server::CostmapFilterInfoServer`
- **Package**: `nav2_map_server`
- **Namespace**: `nav2_map_server`
- **Source File**: `nav2_map_server/src/costmap_filter_info/costmap_filter_info_server.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_map_server/include/nav2_map_server/costmap_filter_info_server.hpp` | `L28` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_map_server/src/costmap_filter_info/costmap_filter_info_server.cpp` | `L27` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_map_server/src/costmap_filter_info/costmap_filter_info_server.cpp` | `L115` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L119` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L198` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `costmap_filter_info` | `nav2_msgs/msg/CostmapFilterInfo` | `MessageType.UNKNOWN` | `default` | `costmap_filter_info_server.cpp:45` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*