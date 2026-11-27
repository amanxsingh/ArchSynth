# Node Specification: `mtc_pickplace`

- **Stable Unique ID**: `jaco2_moveit_task_constructor::MtcPickplace`
- **Fully Qualified Name**: `mtc_pickplace`
- **Class / Executable**: `MtcPickplace`
- **Package**: `jaco2_moveit_task_constructor`
- **Namespace**: `/`
- **Source File**: `jaco2_moveit_task_constructor/jaco2_moveit_task_constructor/pickplace.py`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `jaco2_moveit_task_constructor/jaco2_moveit_task_constructor/pickplace.py` | `L14` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | `client` | `pickplace.py:124` |

## Parameters

*No parameters declared.*