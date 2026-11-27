# Node Specification: `nav2_tester`

- **Stable Unique ID**: `nav2_system_tests::NavTester#src__system__nav_through_poses_tester_node`
- **Fully Qualified Name**: `namespace/nav2_tester`
- **Class / Executable**: `NavTester`
- **Package**: `nav2_system_tests`
- **Namespace**: `namespace`
- **Source File**: `nav2_system_tests/src/system/nav_through_poses_tester_node.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/system/nav_through_poses_tester_node.py` | `L34–L273` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `10` | `nav_through_poses_tester_node.py:38` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `amcl_pose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `self.poseCallback` | `nav_through_poses_tester_node.py:49` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `node_service` | `GetState` | `client` | `nav_through_poses_tester_node.py:213` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `nav_through_poses_tester_node.py:237` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `nav_through_poses_tester_node.py:252` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `navigate_through_poses` | `NavigateThroughPoses` | `client` | `nav_through_poses_tester_node.py:59` |

## Parameters

*No parameters declared.*