# Node Specification: `nav2_tester`

- **Stable Unique ID**: `nav2_system_tests::RouteTester`
- **Fully Qualified Name**: `namespace/nav2_tester`
- **Class / Executable**: `RouteTester`
- **Package**: `nav2_system_tests`
- **Namespace**: `namespace`
- **Source File**: `nav2_system_tests/src/route/tester_node.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/route/tester_node.py` | `L35–L422` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `10` | `tester_node.py:39` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `amcl_pose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `self.poseCallback` | `tester_node.py:50` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `route_server/ReroutingService/reroute` | `Trigger` | `client` | `tester_node.py:200` |
| `node_service` | `GetState` | `client` | `tester_node.py:361` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `tester_node.py:386` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `tester_node.py:401` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `compute_route` | `ComputeRoute` | `client` | `tester_node.py:60` |
| `compute_and_track_route` | `ComputeAndTrackRoute` | `client` | `tester_node.py:65` |

## Parameters

*No parameters declared.*