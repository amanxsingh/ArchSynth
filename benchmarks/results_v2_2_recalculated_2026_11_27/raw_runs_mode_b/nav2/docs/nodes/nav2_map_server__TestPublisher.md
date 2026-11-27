# Node Specification: `map_publisher`

- **Stable Unique ID**: `nav2_map_server::TestPublisher`
- **Fully Qualified Name**: `map_publisher`
- **Class / Executable**: `TestPublisher`
- **Package**: `nav2_map_server`
- **Namespace**: `/`
- **Source File**: `nav2_map_server/test/component/test_map_saver_publisher.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_map_server/test/component/test_map_saver_publisher.cpp` | `L29` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `test/component/CMakeLists.txt` | `L40` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `map` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `test_map_saver_publisher.cpp:43` |
| `malformed_map` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `test_map_saver_publisher.cpp:53` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*