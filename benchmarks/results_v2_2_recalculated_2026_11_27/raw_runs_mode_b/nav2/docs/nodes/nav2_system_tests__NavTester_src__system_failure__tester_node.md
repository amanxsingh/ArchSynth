# Node Specification: `nav2_tester`

- **Stable Unique ID**: `nav2_system_tests::NavTester#src__system_failure__tester_node`
- **Fully Qualified Name**: `namespace/nav2_tester`
- **Class / Executable**: `NavTester`
- **Package**: `nav2_system_tests`
- **Namespace**: `namespace`
- **Source File**: `nav2_system_tests/src/system_failure/tester_node.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/system_failure/tester_node.py` | `L35–L218` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `10` | `tester_node.py:39` |
| `goal_pose` | `PoseStamped` | `MessageType.UNKNOWN` | `10` | `tester_node.py:42` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `amcl_pose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `self.poseCallback` | `tester_node.py:51` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `node_service` | `GetState` | `client` | `tester_node.py:158` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `tester_node.py:182` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `tester_node.py:197` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `navigate_to_pose` | `NavigateToPose` | `client` | `tester_node.py:61` |

## Parameters

*No parameters declared.*