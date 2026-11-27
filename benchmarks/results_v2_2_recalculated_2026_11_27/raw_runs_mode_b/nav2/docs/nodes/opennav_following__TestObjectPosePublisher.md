# Node Specification: `test_object_pose_publisher`

- **Stable Unique ID**: `opennav_following::TestObjectPosePublisher`
- **Fully Qualified Name**: `test_object_pose_publisher`
- **Class / Executable**: `TestObjectPosePublisher`
- **Package**: `opennav_following`
- **Namespace**: `/`
- **Source File**: `nav2_following/opennav_following/test/test_following_server.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_following/opennav_following/test/test_following_server.py` | `L102` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `topic_name` | `geometry_msgs/msg/PoseStamped` | `MessageType.UNKNOWN` | `default` | `test_following_server.py:103` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `cmd_vel` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `test_following_server.py:305` |

## Services

*No services declared.*

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `follow_object` | `nav2_msgs/action/FollowObject` | `client` | `test_following_server.py:302` |

## Parameters

*No parameters declared.*