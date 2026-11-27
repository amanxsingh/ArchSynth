# Node Specification: `costmap_2d_cloud`

- **Stable Unique ID**: `nav2_costmap_2d::Costmap2dCloud`
- **Fully Qualified Name**: `costmap_2d_cloud`
- **Class / Executable**: `Costmap2dCloud`
- **Package**: `nav2_costmap_2d`
- **Namespace**: `/`
- **Source File**: `nav2_costmap_2d/src/costmap_2d_cloud.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_costmap_2d/src/costmap_2d_cloud.cpp` | `L217` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L169` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `voxel_marked_cloud` | `sensor_msgs/msg/PointCloud2` | `MessageType.UNKNOWN` | `default` | `costmap_2d_cloud.cpp:221` |
| `voxel_unknown_cloud` | `sensor_msgs/msg/PointCloud2` | `MessageType.UNKNOWN` | `default` | `costmap_2d_cloud.cpp:223` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `voxel_grid` | `nav2_msgs/msg/VoxelGrid` | `MessageType.UNKNOWN` | `default` | `costmap_2d_cloud.cpp:225` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*