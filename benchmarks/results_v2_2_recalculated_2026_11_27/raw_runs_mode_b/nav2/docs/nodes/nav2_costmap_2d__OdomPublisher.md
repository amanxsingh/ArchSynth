# Node Specification: `odom_pub`

- **Stable Unique ID**: `nav2_costmap_2d::OdomPublisher`
- **Fully Qualified Name**: `odom_pub`
- **Class / Executable**: `OdomPublisher`
- **Package**: `nav2_costmap_2d`
- **Namespace**: `/`
- **Source File**: `nav2_costmap_2d/test/unit/speed_filter_test.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_costmap_2d/test/unit/speed_filter_test.cpp` | `L133` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L185` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `INFO_TOPIC` | `nav2_msgs/msg/CostmapFilterInfo` | `MessageType.UNKNOWN` | `default` | `speed_filter_test.cpp:69` |
| `MASK_TOPIC` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `speed_filter_test.cpp:97` |
| `plan` | `nav_msgs/msg/Path` | `MessageType.UNKNOWN` | `default` | `speed_filter_test.cpp:119` |
| `odom` | `nav_msgs/msg/Odometry` | `MessageType.UNKNOWN` | `default` | `speed_filter_test.cpp:139` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `speed_limit_topic` | `nav2_msgs/msg/SpeedLimit` | `MessageType.UNKNOWN` | `default` | `speed_filter_test.cpp:167` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*