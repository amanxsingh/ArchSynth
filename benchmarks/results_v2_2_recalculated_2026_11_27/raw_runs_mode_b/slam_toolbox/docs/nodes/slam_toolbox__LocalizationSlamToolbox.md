# Node Specification: `slam_toolbox`

- **Stable Unique ID**: `slam_toolbox::LocalizationSlamToolbox`
- **Fully Qualified Name**: `slam_toolbox/slam_toolbox`
- **Class / Executable**: `slam_toolbox::LocalizationSlamToolbox`
- **Package**: `slam_toolbox`
- **Namespace**: `slam_toolbox`
- **Source File**: `src/slam_toolbox_localization.cpp`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `include/slam_toolbox/slam_toolbox_localization.hpp` | `L29` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `src/slam_toolbox_localization.cpp` | `L27` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `src/slam_toolbox_localization.cpp` | `L296` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L271` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L313` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `default` | `slam_toolbox_common.cpp:475` |
| `/map` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `slam_toolbox_common.cpp:477` |
| `/map_metadata` | `nav_msgs/msg/MapMetaData` | `MessageType.UNKNOWN` | `default` | `slam_toolbox_common.cpp:479` |
| `slam_toolbox/pose_graph` | `slam_toolbox/msg/PoseGraph` | `MessageType.UNKNOWN` | `default` | `slam_toolbox_common.cpp:502` |
| `slam_toolbox/new_node_event` | `slam_toolbox/msg/NewNodeEvent` | `MessageType.UNKNOWN` | `default` | `slam_toolbox_common.cpp:505` |
| `slam_toolbox/loop_closure_event` | `slam_toolbox/msg/LoopClosureEvent` | `MessageType.UNKNOWN` | `default` | `slam_toolbox_common.cpp:507` |
| `slam_toolbox/scan_visualization` | `sensor_msgs/msg/LaserScan` | `MessageType.UNKNOWN` | `default` | `loop_closure_assistant.cpp:62` |
| `slam_toolbox/graph_visualization` | `visualization_msgs/msg/MarkerArray` | `MessageType.UNKNOWN` | `default` | `loop_closure_assistant.cpp:76` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `default` | `slam_toolbox_localization.cpp:82` |
| `/scan` | `sensor_msgs/msg/LaserScan` | `MessageType.UNKNOWN` | `default` | `slam_toolbox_common.cpp:511` |
| `/map` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `map_saver.cpp:46` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `slam_toolbox/clear_localization_buffer` | `std_srvs/srv/Empty` | `server` | `slam_toolbox_localization.cpp:87` |
| `slam_toolbox/dynamic_map` | `nav_msgs/srv/GetMap` | `server` | `slam_toolbox_common.cpp:482` |
| `slam_toolbox/pause_new_measurements` | `slam_toolbox/srv/Pause` | `server` | `slam_toolbox_common.cpp:485` |
| `slam_toolbox/serialize_map` | `slam_toolbox/srv/SerializePoseGraph` | `server` | `slam_toolbox_common.cpp:490` |
| `slam_toolbox/deserialize_map` | `slam_toolbox/srv/DeserializePoseGraph` | `server` | `slam_toolbox_common.cpp:494` |
| `slam_toolbox/reset` | `slam_toolbox/srv/Reset` | `server` | `slam_toolbox_common.cpp:498` |
| `slam_toolbox/save_map` | `slam_toolbox/srv/SaveMap` | `server` | `map_saver.cpp:34` |
| `slam_toolbox/clear_changes` | `slam_toolbox/srv/Clear` | `server` | `loop_closure_assistant.cpp:54` |
| `slam_toolbox/manual_loop_closure` | `slam_toolbox/srv/LoopClosure` | `server` | `loop_closure_assistant.cpp:58` |
| `slam_toolbox/toggle_interactive_mode` | `slam_toolbox/srv/ToggleInteractive` | `server` | `loop_closure_assistant.cpp:71` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*