# Node Specification: `costmap`

- **Stable Unique ID**: `nav2_costmap_2d::Costmap2DROS`
- **Fully Qualified Name**: `nav2_costmap_2d/costmap`
- **Class / Executable**: `nav2_costmap_2d::Costmap2DROS`
- **Package**: `nav2_costmap_2d`
- **Namespace**: `nav2_costmap_2d`
- **Source File**: `nav2_costmap_2d/src/costmap_2d_ros.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_costmap_2d/include/nav2_costmap_2d/costmap_2d_ros.hpp` | `L75` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_costmap_2d/src/costmap_2d_ros.cpp` | `L64` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L185` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `published_footprint` | `geometry_msgs/msg/PolygonStamped` | `MessageType.UNKNOWN` | `default` | `costmap_2d_ros.cpp:214` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `footprint` | `geometry_msgs/msg/PolygonStamped` | `MessageType.UNKNOWN` | `default` | `costmap_2d_ros.cpp:205` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `get_cost_costmap` | `nav2_msgs/srv/GetCosts` | `server` | `costmap_2d_ros.cpp:246` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*