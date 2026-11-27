# Node Specification: `zpf_second_target`

- **Stable Unique ID**: `nav2_costmap_2d::SecondTargetNode`
- **Fully Qualified Name**: `zpf_second_target`
- **Class / Executable**: `SecondTargetNode`
- **Package**: `nav2_costmap_2d`
- **Namespace**: `/`
- **Source File**: `nav2_costmap_2d/test/unit/zone_parameter_filter_test.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_costmap_2d/test/unit/zone_parameter_filter_test.cpp` | `L158` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L185` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `kInfoTopic` | `nav2_msgs/msg/CostmapFilterInfo` | `MessageType.UNKNOWN` | `default` | `zone_parameter_filter_test.cpp:70` |
| `kMaskTopic` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `zone_parameter_filter_test.cpp:92` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `topic` | `std_msgs/msg/UInt8` | `MessageType.UNKNOWN` | `default` | `zone_parameter_filter_test.cpp:109` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*