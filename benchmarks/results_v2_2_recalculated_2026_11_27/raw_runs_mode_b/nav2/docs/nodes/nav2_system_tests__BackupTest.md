# Node Specification: `backup_tester`

- **Stable Unique ID**: `nav2_system_tests::BackupTest`
- **Fully Qualified Name**: `backup_tester`
- **Class / Executable**: `BackupTest`
- **Package**: `nav2_system_tests`
- **Namespace**: `/`
- **Source File**: `nav2_system_tests/src/behaviors/backup/backup_tester.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/behaviors/backup/backup_tester.py` | `L34–L319` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `local_costmap/costmap_raw` | `Costmap` | `MessageType.UNKNOWN` | `self.costmap_qos` | `backup_tester.py:49` |
| `local_costmap/published_footprint` | `PolygonStamped` | `MessageType.UNKNOWN` | `10` | `backup_tester.py:51` |

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `transition_service` | `ManageLifecycleNodes` | `client` | `backup_tester.py:297` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `backup` | `BackUp` | `client` | `backup_tester.py:48` |

## Parameters

*No parameters declared.*