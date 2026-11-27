# Node Specification: `nav2_waypoint_tester`

- **Stable Unique ID**: `nav2_system_tests::WaypointFollowerTest`
- **Fully Qualified Name**: `nav2_waypoint_tester`
- **Class / Executable**: `WaypointFollowerTest`
- **Package**: `nav2_system_tests`
- **Namespace**: `/`
- **Source File**: `nav2_system_tests/src/waypoint_follower/tester.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/waypoint_follower/tester.py` | `L34–L205` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `10` | `tester.py:44` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `amcl_pose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `self.poseCallback` | `tester.py:60` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `/waypoint_follower/set_parameters` | `SetParameters` | `client` | `tester.py:64` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `tester.py:163` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `tester.py:179` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `follow_waypoints` | `FollowWaypoints` | `client` | `tester.py:43` |

## Parameters

*No parameters declared.*