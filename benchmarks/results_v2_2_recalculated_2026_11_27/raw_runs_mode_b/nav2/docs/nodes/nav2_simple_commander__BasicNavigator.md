# Node Specification: `basic_navigator`

- **Stable Unique ID**: `nav2_simple_commander::BasicNavigator`
- **Fully Qualified Name**: `namespace/basic_navigator`
- **Class / Executable**: `BasicNavigator`
- **Package**: `nav2_simple_commander`
- **Namespace**: `namespace`
- **Source File**: `nav2_simple_commander/nav2_simple_commander/robot_navigator.py`
- **Architectural Classification**: `client`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_simple_commander/nav2_simple_commander/robot_navigator.py` | `L72–L1294` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `10` | `robot_navigator.py:146` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `amcl_pose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `self._amclPoseCallback` | `robot_navigator.py:140` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `map_server/load_map` | `LoadMap` | `client` | `robot_navigator.py:150` |
| `global_costmap/clear_entirely_global_costmap` | `ClearEntireCostmap` | `client` | `robot_navigator.py:151` |
| `local_costmap/clear_entirely_local_costmap` | `ClearEntireCostmap` | `client` | `robot_navigator.py:155` |
| `local_costmap/clear_costmap_except_region` | `ClearCostmapExceptRegion` | `client` | `robot_navigator.py:159` |
| `local_costmap/clear_costmap_around_robot` | `ClearCostmapAroundRobot` | `client` | `robot_navigator.py:163` |
| `local_costmap/clear_costmap_around_pose` | `ClearCostmapAroundPose` | `client` | `robot_navigator.py:167` |
| `global_costmap/clear_costmap_around_pose` | `ClearCostmapAroundPose` | `client` | `robot_navigator.py:171` |
| `global_costmap/get_costmap` | `GetCostmap` | `client` | `robot_navigator.py:175` |
| `local_costmap/get_costmap` | `GetCostmap` | `client` | `robot_navigator.py:179` |
| `collision_monitor/toggle` | `Toggle` | `client` | `robot_navigator.py:183` |
| `srv_name` | `ManageLifecycleNodes` | `client` | `robot_navigator.py:1189` |
| `srv_name` | `ManageLifecycleNodes` | `client` | `robot_navigator.py:1214` |
| `node_service` | `GetState` | `client` | `robot_navigator.py:1229` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `navigate_through_poses` | `NavigateThroughPoses` | `client` | `robot_navigator.py:104` |
| `navigate_to_pose` | `NavigateToPose` | `client` | `robot_navigator.py:106` |
| `follow_waypoints` | `FollowWaypoints` | `client` | `robot_navigator.py:107` |
| `follow_gps_waypoints` | `FollowGPSWaypoints` | `client` | `robot_navigator.py:110` |
| `follow_path` | `FollowPath` | `client` | `robot_navigator.py:113` |
| `compute_path_to_pose` | `ComputePathToPose` | `client` | `robot_navigator.py:114` |
| `compute_path_through_poses` | `ComputePathThroughPoses` | `client` | `robot_navigator.py:117` |
| `smooth_path` | `SmoothPath` | `client` | `robot_navigator.py:120` |
| `compute_route` | `ComputeRoute` | `client` | `robot_navigator.py:121` |
| `compute_and_track_route` | `ComputeAndTrackRoute` | `client` | `robot_navigator.py:122` |
| `spin` | `Spin` | `client` | `robot_navigator.py:127` |
| `backup` | `BackUp` | `client` | `robot_navigator.py:129` |
| `drive_on_heading` | `DriveOnHeading` | `client` | `robot_navigator.py:130` |
| `assisted_teleop` | `AssistedTeleop` | `client` | `robot_navigator.py:133` |
| `dock_robot` | `DockRobot` | `client` | `robot_navigator.py:136` |
| `undock_robot` | `UndockRobot` | `client` | `robot_navigator.py:137` |
| `follow_object` | `FollowObject` | `client` | `robot_navigator.py:138` |

## Parameters

*No parameters declared.*