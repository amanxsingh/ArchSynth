# Node Specification: `nav2_tester`

- **Stable Unique ID**: `nav2_system_tests::NavTester#src__costmap_filters__tester_node`
- **Fully Qualified Name**: `namespace/nav2_tester`
- **Class / Executable**: `NavTester`
- **Package**: `nav2_system_tests`
- **Namespace**: `namespace`
- **Source File**: `nav2_system_tests/src/costmap_filters/tester_node.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/costmap_filters/tester_node.py` | `L77–L424` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `10` | `tester_node.py:86` |
| `goal_pose` | `PoseStamped` | `MessageType.UNKNOWN` | `10` | `tester_node.py:89` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `amcl_pose` | `PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `self.poseCallback` | `tester_node.py:105` |
| `local_costmap/clearing_endpoints` | `PointCloud2` | `MessageType.UNKNOWN` | `self.clearingEndpointsCallback` | `tester_node.py:111` |
| `plan` | `Path` | `MessageType.UNKNOWN` | `self.planCallback` | `tester_node.py:125` |
| `voxel_marked_cloud` | `PointCloud2` | `MessageType.UNKNOWN` | `self.voxelMarkedCallback` | `tester_node.py:128` |
| `voxel_unknown_cloud` | `PointCloud2` | `MessageType.UNKNOWN` | `self.voxelUnknownCallback` | `tester_node.py:131` |
| `cost_cloud` | `PointCloud2` | `MessageType.UNKNOWN` | `self.dwbCostCloudCallback` | `tester_node.py:134` |
| `speed_limit` | `SpeedLimit` | `MessageType.UNKNOWN` | `self.speedLimitCallback` | `tester_node.py:143` |
| `filter_mask` | `OccupancyGrid` | `MessageType.UNKNOWN` | `self.maskCallback` | `tester_node.py:148` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `node_service` | `GetState` | `client` | `tester_node.py:364` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `tester_node.py:388` |
| `transition_service` | `ManageLifecycleNodes` | `client` | `tester_node.py:403` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `navigate_to_pose` | `NavigateToPose` | `client` | `tester_node.py:157` |

## Parameters

*No parameters declared.*