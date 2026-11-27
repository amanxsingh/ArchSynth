# Node Specification: `costmap_ros_lifecycle_node`

- **Stable Unique ID**: `nav2_costmap_2d::CostmapRosLifecycleNode`
- **Fully Qualified Name**: `costmap_ros_lifecycle_node`
- **Class / Executable**: `CostmapRosLifecycleNode`
- **Package**: `nav2_costmap_2d`
- **Namespace**: `/`
- **Source File**: `nav2_costmap_2d/test/integration/test_costmap_2d_publisher.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_costmap_2d/test/integration/test_costmap_2d_publisher.cpp` | `L25` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L185` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/fake_costmap/static_layer_raw` | `nav2_msgs/msg/Costmap` | `MessageType.UNKNOWN` | `default` | `test_costmap_2d_publisher.cpp:87` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*