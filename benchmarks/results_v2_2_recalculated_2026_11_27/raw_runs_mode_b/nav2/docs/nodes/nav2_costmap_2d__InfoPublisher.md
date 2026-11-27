# Node Specification: `costmap_filter_info_pub`

- **Stable Unique ID**: `nav2_costmap_2d::InfoPublisher`
- **Fully Qualified Name**: `costmap_filter_info_pub`
- **Class / Executable**: `InfoPublisher`
- **Package**: `nav2_costmap_2d`
- **Namespace**: `/`
- **Source File**: `nav2_costmap_2d/test/unit/binary_filter_test.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_costmap_2d/test/unit/binary_filter_test.cpp` | `L51` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L185` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `INFO_TOPIC` | `nav2_msgs/msg/CostmapFilterInfo` | `MessageType.UNKNOWN` | `default` | `binary_filter_test.cpp:57` |
| `MASK_TOPIC` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `binary_filter_test.cpp:85` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `binary_state_topic` | `std_msgs/msg/Bool` | `MessageType.UNKNOWN` | `default` | `binary_filter_test.cpp:107` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*