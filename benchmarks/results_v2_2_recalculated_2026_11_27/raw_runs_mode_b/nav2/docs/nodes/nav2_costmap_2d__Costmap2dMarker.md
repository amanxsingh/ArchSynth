# Node Specification: `costmap_2d_marker`

- **Stable Unique ID**: `nav2_costmap_2d::Costmap2dMarker`
- **Fully Qualified Name**: `costmap_2d_marker`
- **Class / Executable**: `Costmap2dMarker`
- **Package**: `nav2_costmap_2d`
- **Namespace**: `/`
- **Source File**: `nav2_costmap_2d/src/costmap_2d_markers.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_costmap_2d/src/costmap_2d_markers.cpp` | `L152` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L154` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `visualization_marker` | `visualization_msgs/msg/Marker` | `MessageType.UNKNOWN` | `default` | `costmap_2d_markers.cpp:156` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `voxel_grid` | `nav2_msgs/msg/VoxelGrid` | `MessageType.UNKNOWN` | `default` | `costmap_2d_markers.cpp:159` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*