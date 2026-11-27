# Node Specification: `nav2_gps_waypoint_tester`

- **Stable Unique ID**: `nav2_system_tests::GpsWaypointFollowerTest`
- **Fully Qualified Name**: `nav2_gps_waypoint_tester`
- **Class / Executable**: `GpsWaypointFollowerTest`
- **Package**: `nav2_system_tests`
- **Namespace**: `/`
- **Source File**: `nav2_system_tests/src/gps_navigation/tester.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/gps_navigation/tester.py` | `L33–L161` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `/waypoint_follower/set_parameters` | `SetParameters` | `client` | `tester.py:50` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `tester.py:135` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `follow_gps_waypoints` | `FollowGPSWaypoints` | `client` | `tester.py:42` |

## Parameters

*No parameters declared.*