# Node Specification: `spin_tester`

- **Stable Unique ID**: `nav2_system_tests::SpinTest`
- **Fully Qualified Name**: `spin_tester`
- **Class / Executable**: `SpinTest`
- **Package**: `nav2_system_tests`
- **Namespace**: `/`
- **Source File**: `nav2_system_tests/src/behaviors/spin/spin_tester.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/behaviors/spin/spin_tester.py` | `L34–L309` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `local_costmap/costmap_raw` | `Costmap` | `MessageType.UNKNOWN` | `self.costmap_qos` | `spin_tester.py:47` |
| `local_costmap/published_footprint` | `PolygonStamped` | `MessageType.UNKNOWN` | `10` | `spin_tester.py:49` |

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `transition_service` | `ManageLifecycleNodes` | `client` | `spin_tester.py:287` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `spin` | `Spin` | `client` | `spin_tester.py:45` |

## Parameters

*No parameters declared.*