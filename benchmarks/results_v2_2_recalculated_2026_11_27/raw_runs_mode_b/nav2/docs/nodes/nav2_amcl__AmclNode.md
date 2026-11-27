# Node Specification: `amcl`

- **Stable Unique ID**: `nav2_amcl::AmclNode`
- **Fully Qualified Name**: `nav2_amcl/amcl`
- **Class / Executable**: `nav2_amcl::AmclNode`
- **Package**: `nav2_amcl`
- **Namespace**: `nav2_amcl`
- **Source File**: `nav2_amcl/src/amcl_node.cpp`
- **Architectural Classification**: `localization`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_amcl/include/nav2_amcl/amcl_node.hpp` | `L59` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_amcl/src/amcl_node.cpp` | `L57` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_amcl/src/amcl_node.cpp` | `L1650` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L127` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L139` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `particle_cloud` | `nav2_msgs/msg/ParticleCloud` | `MessageType.UNKNOWN` | `default` | `amcl_node.cpp:1420` |
| `amcl_pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `default` | `amcl_node.cpp:1424` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `map_topic_` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `amcl_node.cpp:1267` |
| `initialpose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `default` | `amcl_node.cpp:1428` |
| `scan_topic_` | `sensor_msgs/msg/LaserScan` | `MessageType.UNKNOWN` | `default` | `amcl_node.cpp:1397` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `reinitialize_global_localization` | `std_srvs/srv/Empty` | `server` | `amcl_node.cpp:1443` |
| `set_initial_pose` | `nav2_msgs/srv/SetInitialPose` | `server` | `amcl_node.cpp:1449` |
| `request_nomotion_update` | `std_srvs/srv/Empty` | `server` | `amcl_node.cpp:1455` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*