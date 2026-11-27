# Node Specification: `nav2_tester`

- **Stable Unique ID**: `nav2_system_tests::NavTester#src__system__nav_to_pose_tester_node`
- **Fully Qualified Name**: `namespace/nav2_tester`
- **Class / Executable**: `NavTester`
- **Package**: `nav2_system_tests`
- **Namespace**: `namespace`
- **Source File**: `nav2_system_tests/src/system/nav_to_pose_tester_node.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/system/nav_to_pose_tester_node.py` | `L39–L389` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `10` | `nav_to_pose_tester_node.py:43` |
| `goal_pose` | `PoseStamped` | `MessageType.UNKNOWN` | `10` | `nav_to_pose_tester_node.py:46` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `amcl_pose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `self.poseCallback` | `nav_to_pose_tester_node.py:55` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `node_service` | `GetState` | `client` | `nav_to_pose_tester_node.py:319` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `nav_to_pose_tester_node.py:343` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `nav_to_pose_tester_node.py:358` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `navigate_to_pose` | `NavigateToPose` | `client` | `nav_to_pose_tester_node.py:66` |

## Parameters

*No parameters declared.*