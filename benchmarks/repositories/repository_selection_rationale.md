# Repository Selection Rationale & Case-Study Complexity Matrix

**Project**: ArchSynth v2.0 Research Evaluation  
**Document**: `benchmarks/repositories/repository_selection_rationale.md`  

---

## 1. Selection Criteria for Empirical Benchmarking

To rigorously validate ArchSynth's evidence-grounded architecture recovery across heterogeneous robotics architectures, five production ROS 2 repositories were selected alongside one non-ROS control baseline.

Repositories were chosen according to eight objective architectural criteria:
1. **Architectural Heterogeneity**: Encompassing mobile navigation, simultaneous localization and mapping (SLAM), real-time manipulation/hardware control, multi-robot simulation, and discrete behavioral orchestration.
2. **Implementation Language Diversity**: Spanning pure modern C++ (`rclcpp`), hybrid C++/Python, pure Python (`rclpy`), and declarative XML/YAML launch and behavior models.
3. **Launch System Complexity**: Nested launch files, launch substitutions (`LaunchConfiguration`, `PythonExpression`, `PathJoinSubstitution`), conditional evaluations (`IfCondition`, `UnlessCondition`), and `GroupAction`.
4. **Execution Paradigm Variety**: Standalone executable nodes vs. composable component containers (`ComposableNodeContainer`, `LoadComposableNodes`).
5. **Lifecycle State Management**: Native `LifecycleNode` implementations, state machine callbacks, and external orchestrators (`nav2_lifecycle_manager`).
6. **Plugin Architecture Depth**: `pluginlib`-based base class polymorphism (planners, controllers, costmap layers, hardware interfaces).
7. **Ground-Truth Availability & Verifiability**: Repositories with stable, well-maintained documentation, clear node boundaries, and reproducible upstream Git revisions.
8. **Negative Boundary Validation**: Ability to reject non-ROS codebases and prevent false-positive architecture generation.

---

## 2. Comprehensive Architectural Complexity Comparison

| Criterion | Navigation2 (`nav2`) | SLAM Toolbox (`slam_toolbox`) | ROS 2 Control (`ros2_control`) | Jaco2 Devkit (`jaco2_sim_devkit`) | BehaviorTree.CPP (`behaviortree_cpp`) | Express (Negative Baseline) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Domain** | Mobile Navigation | 2D LiDAR SLAM | Real-time Robot Hardware | Arm Simulation & MoveIt | Decision Orchestration | Web Application |
| **Pinned Commit** | `6dbf4549` | `eee0cd5e` | `4052b56d` | `993a6e3d` | `365b2e49` | `c031be5d` |
| **Primary Language** | C++ (75%), Py (25%) | C++ (95%), Py (5%) | C++ (98%) | Python (90%) | C++ (100%) | JavaScript |
| **Packages Analyzed** | 44 | 1 | 11 | 11 | 1 | 0 (Non-ROS) |
| **Nodes Discovered** | 66 (22 prod, 44 test) | 2 (prod) | 1 (prod) | 9 (prod) | 2 (prod) | 0 |
| **Launch Files** | 41 | 7 | 1 | 12 | 0 | 0 |
| **Deployment Profiles** | 18 | 7 | 4 | 15 | 3 | 0 |
| **Source Interfaces** | 245 | 37 | 13 | 12 | 0 | 0 |
| **Lifecycle Nodes** | 12 | 1 | 1 | 0 | 0 | 0 |
| **Plugin Systems** | Extensive (nav2_core) | Minimal | Extensive (hardware) | Intermediate (MoveIt) | Native BT Plugins | None |
| **Behavior Trees** | Core Engine User | None | None | None | Engine Origin | None |
| **Boundary Role** | Multi-robot | Single / Multi-map | Hardware bus | Simulation bus | Subsystem tree | N/A |

---

## 3. Five-Tier Architectural Classification & Justification

To ensure comprehensive coverage of the diverse architectural patterns across the robotics software engineering spectrum, the evaluated repositories are categorized into **five distinct architectural tiers**:

### Tier 1: Production Multi-Package ROS 2 Stacks
1. **Navigation2 (`nav2`) — Autonomous Mobile Navigation**
   - **Why Mandatory**: The premier reference stack in ROS 2. Features 44 distinct packages, 66 discovered nodes (22 production, 44 test), 41 launch files, and 245 source interfaces.
   - **Architectural Stress-Test**: Validates Behavior Tree navigation orchestration, `ComposableNodeContainer` dynamic loading, `LifecycleNode` state management, and nested launch substitutions.
2. **SLAM Toolbox (`slam_toolbox`) — 2D LiDAR SLAM & Dynamic Mapping**
   - **Why Mandatory**: Formally reconciled under Step 3A/3B/3C with 100% ground-truth verification on pinned commit `eee0cd5e4a161bb10f8334b5420c93876b31ca99` (ROS 2 Jazzy).
   - **Architectural Stress-Test**: Validates separation of C++ application interface instances (143 at $N=1$) from dependency-generated endpoints (`interactive_markers` 2.5.5, `geometry2` 0.36.4 `TransformBroadcaster` and `TransformListener` hidden node expansion).

### Tier 2: Reusable Frameworks & Hardware Abstraction Libraries
3. **ROS 2 Control (`ros2_control`) — Real-Time Hardware Abstraction & Control Loops**
   - **Why Selected**: The standardized real-time actuation and sensor layer in ROS 2.
   - **Architectural Stress-Test**: Validates `pluginlib` hardware component loading (`SystemInterface`, `ActuatorInterface`, `SensorInterface`) and real-time controller manager lifecycle state machines without regular topic dependencies.

### Tier 3: Simulation Environments & Robotic Devkits
4. **Kinova Jaco2 Devkit (`jaco2_sim_devkit`) — Manipulator Simulation & Trajectory Control**
   - **Why Selected**: Represents a complete end-to-end manipulator stack combining MoveIt 2 configuration, Gazebo simulation, URDF robot descriptions, and Python trajectory control.
   - **Architectural Stress-Test**: Validates pure-Python node analysis (`rclpy`), nested Gazebo launch inclusion, and multi-package simulation coordination.

### Tier 4: Decision Orchestration Engines
5. **BehaviorTree.CPP (`behaviortree_cpp`) — Execution Engine & Custom Tree Nodes**
   - **Why Selected**: The fundamental engine powering autonomous decision-making across Nav2, Autoware, and industrial robotics.
   - **Architectural Stress-Test**: Validates C++ class inheritance for decision nodes (`ActionNode`, `ConditionNode`, `DecoratorNode`, `SubtreeNode`), XML parsing, and zero false-positive topic inference for a non-node architectural library.

### Tier 5: Non-ROS Negative Control Baseline
6. **Express (`express`) — Web Application Framework**
   - **Why Selected**: Prevents confirmation bias by evaluating whether ArchSynth correctly rejects non-ROS codebases.
   - **Validation**: Verifies that ArchSynth returns HTTP 400 (`NOT A ROS2 REPOSITORY: No package.xml found`), producing 0 false-positive nodes, topics, or architecture views (100% negative specificity).
