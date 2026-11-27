# Node Specification: `scene_publisher`

- **Stable Unique ID**: `jaco2_moveit_task_constructor::ScenePublisher`
- **Fully Qualified Name**: `scene_publisher`
- **Class / Executable**: `ScenePublisher`
- **Package**: `jaco2_moveit_task_constructor`
- **Namespace**: `/`
- **Source File**: `jaco2_moveit_task_constructor/jaco2_moveit_task_constructor/scene_publisher.py`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `jaco2_moveit_task_constructor/jaco2_moveit_task_constructor/scene_publisher.py` | `L10–L53` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/planning_scene` | `PlanningScene` | `MessageType.UNKNOWN` | `QoSProfile` | `scene_publisher.py:23` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*