# Node Specification: `map_merging`

- **Stable Unique ID**: `slam_toolbox::MergeMapsKinematic`
- **Fully Qualified Name**: `map_merging`
- **Class / Executable**: `MergeMapsKinematic`
- **Package**: `slam_toolbox`
- **Namespace**: `/`
- **Source File**: `src/merge_maps_kinematic.cpp`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `include/slam_toolbox/merge_maps_kinematic.hpp` | `L52` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `src/merge_maps_kinematic.cpp` | `L26` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L298` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/map` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `merge_maps_kinematic.cpp:46` |
| `/map_metadata` | `nav_msgs/msg/MapMetaData` | `MessageType.UNKNOWN` | `default` | `merge_maps_kinematic.cpp:48` |
| `/map_{i}` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `merge_maps_kinematic.cpp:105` |
| `/map_metadata_{i}` | `nav_msgs/msg/MapMetaData` | `MessageType.UNKNOWN` | `default` | `merge_maps_kinematic.cpp:107` |

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `slam_toolbox/merge_submaps` | `slam_toolbox/srv/MergeMaps` | `server` | `merge_maps_kinematic.cpp:51` |
| `slam_toolbox/add_submap` | `slam_toolbox/srv/AddSubmap` | `server` | `merge_maps_kinematic.cpp:54` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*