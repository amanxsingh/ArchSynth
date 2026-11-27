# Node Specification: `loopback_simulator`

- **Stable Unique ID**: `nav2_loopback_sim::LoopbackSimulator`
- **Fully Qualified Name**: `nav2_loopback_sim/loopback_simulator`
- **Class / Executable**: `nav2_loopback_sim::LoopbackSimulator`
- **Package**: `nav2_loopback_sim`
- **Namespace**: `nav2_loopback_sim`
- **Source File**: `nav2_loopback_sim/src/loopback_simulator.cpp`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_loopback_sim/include/nav2_loopback_sim/loopback_simulator.hpp` | `L59` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_loopback_sim/src/loopback_simulator.cpp` | `L34` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_loopback_sim/src/loopback_simulator.cpp` | `L551` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L56` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L61` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `odom` | `nav_msgs/msg/Odometry` | `MessageType.UNKNOWN` | `default` | `loopback_simulator.cpp:85` |
| `scan` | `sensor_msgs/msg/LaserScan` | `MessageType.UNKNOWN` | `default` | `loopback_simulator.cpp:88` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `default` | `loopback_simulator.cpp:75` |
| `cmd_vel` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `loopback_simulator.cpp:79` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `/map_server/map` | `nav_msgs/srv/GetMap` | `client` | `loopback_simulator.cpp:93` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*