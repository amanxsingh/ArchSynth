# Node Specification: `nav2_tester`

- **Stable Unique ID**: `nav2_system_tests::NavTester#src__system__nav_through_poses_tester_error_msg_node`
- **Fully Qualified Name**: `namespace/nav2_tester`
- **Class / Executable**: `NavTester`
- **Package**: `nav2_system_tests`
- **Namespace**: `namespace`
- **Source File**: `nav2_system_tests/src/system/nav_through_poses_tester_error_msg_node.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/system/nav_through_poses_tester_error_msg_node.py` | `L37–L251` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `10` | `nav_through_poses_tester_error_msg_node.py:41` |
| `goal_checker_selector` | `String` | `MessageType.UNKNOWN` | `checker_qos` | `nav_through_poses_tester_error_msg_node.py:52` |
| `progress_checker_selector` | `String` | `MessageType.UNKNOWN` | `checker_qos` | `nav_through_poses_tester_error_msg_node.py:55` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `amcl_pose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `self.poseCallback` | `nav_through_poses_tester_error_msg_node.py:65` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `/controller_server/set_parameters` | `SetParameters` | `client` | `nav_through_poses_tester_error_msg_node.py:79` |
| `node_service` | `GetState` | `client` | `nav_through_poses_tester_error_msg_node.py:191` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `nav_through_poses_tester_error_msg_node.py:215` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `nav_through_poses_tester_error_msg_node.py:230` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `navigate_through_poses` | `NavigateThroughPoses` | `client` | `nav_through_poses_tester_error_msg_node.py:76` |

## Parameters

*No parameters declared.*