# Node Specification: `drive_tester`

- **Stable Unique ID**: `nav2_system_tests::DriveTest`
- **Fully Qualified Name**: `drive_tester`
- **Class / Executable**: `DriveTest`
- **Package**: `nav2_system_tests`
- **Namespace**: `/`
- **Source File**: `nav2_system_tests/src/behaviors/drive_on_heading/drive_tester.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/behaviors/drive_on_heading/drive_tester.py` | `L34–L328` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `local_costmap/costmap_raw` | `Costmap` | `MessageType.UNKNOWN` | `self.costmap_qos` | `drive_tester.py:49` |
| `local_costmap/published_footprint` | `PolygonStamped` | `MessageType.UNKNOWN` | `10` | `drive_tester.py:51` |

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `transition_service` | `ManageLifecycleNodes` | `client` | `drive_tester.py:306` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `drive_on_heading` | `DriveOnHeading` | `client` | `drive_tester.py:48` |

## Parameters

*No parameters declared.*