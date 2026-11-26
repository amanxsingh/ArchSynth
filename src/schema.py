"""
ArchSynth Schema - Blueprint Pydantic Models

These models define the strict schema that constrains LLM output,
reducing hallucination and ensuring structured, validatable results.
This is the key technique from Benchat/Briechle papers.

Research Extensions (M.Tech Dissertation):
    - EvidenceItem: source provenance for every recovered architectural entity
    - ValidationStatus: evidence-based validity of recovered entities
    - ValidationReport: machine-readable evidence coverage metrics
    - DriftReport: architecture evolution / commit-to-commit change tracking
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class MessageType(str, Enum):
    """ROS2 message type categories"""
    STD_MSGS = "std_msgs"
    GEOMETRY_MSGS = "geometry_msgs"
    SENSOR_MSGS = "sensor_msgs"
    NAV_MSGS = "nav_msgs"
    ACTION_MSGS = "action_msgs"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class CommunicationType(str, Enum):
    """Types of ROS2 communication"""
    PUBLISHER = "publisher"
    SUBSCRIBER = "subscriber"
    SERVICE_SERVER = "service_server"
    SERVICE_CLIENT = "service_client"
    ACTION_SERVER = "action_server"
    ACTION_CLIENT = "action_client"
    TF_BROADCASTER = "tf_broadcaster"
    TF_LISTENER = "tf_listener"
    TF_STATIC_BROADCASTER = "tf_static_broadcaster"


class EntityType(str, Enum):
    """Classification of ROS2 architectural entities"""
    ROS_NODE = "ros_node"
    LIFECYCLE_NODE = "lifecycle_node"
    COMPONENT = "component"
    EXECUTABLE = "executable"
    CLIENT_APP = "client_app"
    TEST_NODE = "test_node"
    PLUGIN = "plugin"
    UNKNOWN = "unknown"


class NodeCategory(str, Enum):
    """Architectural subsystem / functional role category"""
    NAVIGATION_SERVER = "navigation_server"
    LOCALIZATION = "localization"
    PLANNING = "planning"
    CONTROL = "control"
    BEHAVIOR = "behavior"
    INFRASTRUCTURE = "infrastructure"
    CLIENT = "client"
    TEST = "test"
    UTILITY = "utility"
    UNKNOWN = "unknown"


class ResolutionStatus(str, Enum):
    """Status of entity and name resolution"""
    RESOLVED = "resolved"
    PARTIAL = "partial"
    UNRESOLVED = "unresolved"


class LaunchMappingStatus(str, Enum):
    """Resolution status when mapping launch declarations to Phase 1 node inventory"""
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    EXTERNAL_DEPENDENCY = "external_dependency"
    UNRESOLVED = "unresolved"


class DeploymentProfileType(str, Enum):
    """Deployment configuration profile"""
    STANDALONE = "standalone"
    COMPOSABLE = "composable"
    CONDITIONAL = "conditional"
    DEFAULT = "default"


# ---------------------------------------------------------------------------
# RESEARCH EXTENSION: Evidence / Provenance Models
# ---------------------------------------------------------------------------

class EvidenceType(str, Enum):
    """
    Types of evidence that support an architectural claim.
    Used to categorize where and how an entity was discovered.

    Research motivation: Distinguishes schema validity (Pydantic structure check)
    from factual validity (actual source code grounding).
    """
    NODE_DEFINITION = "node_definition"
    PUBLISHER_CREATION = "publisher_creation"
    SUBSCRIBER_CREATION = "subscriber_creation"
    SERVICE_CREATION = "service_creation"
    ACTION_CREATION = "action_creation"
    LAUNCH_NODE = "launch_node"
    LAUNCH_INCLUDE = "launch_include"
    NAMESPACE = "namespace"
    REMAPPING = "remapping"
    PARAMETER = "parameter"
    PACKAGE_MANIFEST = "package_manifest"
    COMPONENT_REGISTRATION = "component_registration"
    CMAKE_TARGET = "cmake_target"
    ACTION_PROTOCOL = "action_protocol"
    INTERFACE_DECLARATION = "interface_declaration"
    TF_INTERFACE = "tf_interface"


class EvidenceItem(BaseModel):
    """
    A single piece of evidence supporting an architectural claim.

    Research motivation: Separates schema validity (does the JSON structure
    match Pydantic?) from factual validity (does this entity actually exist
    in the source code?).

    Every recovered node, topic, service, or action carries EvidenceItems
    linking it back to source code or launch files with exact file:line citations.
    """
    file: str = Field(..., description="Relative path to the source file")
    line_start: Optional[int] = Field(default=None, description="Starting line number (1-indexed)")
    line_end: Optional[int] = Field(default=None, description="Ending line number (1-indexed)")
    evidence_type: EvidenceType = Field(..., description="Category of evidence")
    source: str = Field(
        ...,
        description="Extractor that produced this evidence (e.g. 'python_ast_analyzer', 'launch_analyzer')"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    claim_type: Optional[str] = Field(
        default=None,
        description="source_declared | config_declared | launch_declared | api_inferred | graph_inferred | runtime_observed"
    )
    confidence_rationale: Optional[str] = Field(
        default=None,
        description="Documented justification for the assigned confidence score"
    )
    explanation: Optional[str] = Field(default=None, description="Human-readable explanation of the evidence")


class ValidationStatus(str, Enum):
    """
    Evidence-based validation status of a recovered architectural entity.

    SUPPORTED   — at least one valid EvidenceItem found and verified
    UNSUPPORTED — no EvidenceItem found, or evidence file not found on disk
    PARTIAL     — some evidence found but incomplete (e.g. file exists, line not verified)
    UNKNOWN     — validation not yet performed
    """
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class UnsupportedEntityRecord(BaseModel):
    """Record of an entity that failed evidence validation"""
    entity_type: str = Field(..., description="Type: node, topic, service, action")
    name: str = Field(..., description="Entity name")
    reason: str = Field(..., description="Why it is unsupported")
    evidence_count: int = Field(default=0, description="Number of evidence items found")


class ValidationReport(BaseModel):
    """
    Machine-readable report from EvidenceValidator.

    Research metric: Evidence Coverage = supported_entities / total_entities
    Measures how much of the recovered architecture has traceable source evidence.

    Key research metrics:
        evidence_coverage        = supported / total
        unsupported_entity_rate  = unsupported / total
        node_coverage            = node-specific coverage
        topic_coverage           = topic-specific coverage
    """
    repo_name: str = Field(default="", description="Repository name")
    analysis_timestamp: str = Field(default="", description="When validation was run")
    total_entities: int = Field(default=0, description="Total recovered entities checked")
    supported_entities: int = Field(default=0, description="Entities with valid evidence")
    unsupported_entities: int = Field(default=0, description="Entities without valid evidence")
    partial_entities: int = Field(default=0, description="Entities with partial evidence")
    evidence_coverage: float = Field(default=0.0, description="Fraction of entities with supporting evidence")
    unsupported_entity_rate: float = Field(default=0.0, description="Fraction of entities without evidence")
    unsupported_list: List[UnsupportedEntityRecord] = Field(
        default_factory=list,
        description="List of entities that failed validation"
    )
    node_coverage: float = Field(default=0.0, description="Evidence coverage for nodes specifically")
    topic_coverage: float = Field(default=0.0, description="Evidence coverage for topics specifically")
    service_coverage: float = Field(default=0.0, description="Evidence coverage for services specifically")
    action_coverage: float = Field(default=0.0, description="Evidence coverage for actions specifically")


# ---------------------------------------------------------------------------
# RESEARCH EXTENSION: Architecture Drift / Evolution Models
# ---------------------------------------------------------------------------

class NodeChange(BaseModel):
    """Describes a modification to a node between two architecture versions"""
    node_name: str
    changed_fields: List[str] = Field(default_factory=list)
    old_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)


class TopicChange(BaseModel):
    """Describes a modification to a topic between two architecture versions"""
    topic_name: str
    changed_fields: List[str] = Field(default_factory=list)
    old_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)


class SubsystemChange(BaseModel):
    """Describes a change in subsystem assignment or composition"""
    subsystem_name: str
    change_type: Literal["added", "removed", "modified"] = "modified"
    added_nodes: List[str] = Field(default_factory=list)
    removed_nodes: List[str] = Field(default_factory=list)


class DriftReport(BaseModel):
    """
    Architecture evolution report comparing two architecture snapshots.

    Research motivation: Enables commit-to-commit tracking of architectural
    changes. Supports architecture evolution analysis as a novel research
    contribution beyond static architecture recovery.
    """
    base_commit: str = Field(default="", description="Base commit hash or label")
    target_commit: str = Field(default="", description="Target commit hash or label")
    base_timestamp: str = Field(default="", description="Timestamp of base analysis")
    target_timestamp: str = Field(default="", description="Timestamp of target analysis")
    repo_name: str = Field(default="", description="Repository name")

    # Node-level changes
    added_nodes: List[str] = Field(default_factory=list)
    removed_nodes: List[str] = Field(default_factory=list)
    modified_nodes: List[NodeChange] = Field(default_factory=list)

    # Topic-level changes
    added_topics: List[str] = Field(default_factory=list)
    removed_topics: List[str] = Field(default_factory=list)
    modified_topics: List[TopicChange] = Field(default_factory=list)

    # Service-level changes
    added_services: List[str] = Field(default_factory=list)
    removed_services: List[str] = Field(default_factory=list)

    # Action-level changes
    added_actions: List[str] = Field(default_factory=list)
    removed_actions: List[str] = Field(default_factory=list)

    # Subsystem-level changes
    subsystem_changes: List[SubsystemChange] = Field(default_factory=list)

    # Summary statistics
    total_changes: int = Field(default=0, description="Total number of detected changes")
    summary: str = Field(default="", description="Human-readable drift summary")

    def compute_total(self) -> int:
        """Compute total change count"""
        self.total_changes = (
            len(self.added_nodes) + len(self.removed_nodes) + len(self.modified_nodes) +
            len(self.added_topics) + len(self.removed_topics) + len(self.modified_topics) +
            len(self.added_services) + len(self.removed_services) +
            len(self.added_actions) + len(self.removed_actions) +
            len(self.subsystem_changes)
        )
        return self.total_changes


# ---------------------------------------------------------------------------
# Core ROS2 Schema Models
# (backward-compatible — all new evidence fields are Optional with defaults)
# ---------------------------------------------------------------------------

class TopicInfo(BaseModel):
    """Information about a ROS2 topic"""
    name: str = Field(..., description="Full topic name (with namespace)")
    message_type: str = Field(..., description="ROS2 message type (e.g., geometry_msgs/msg/Twist)")
    message_category: MessageType = Field(default=MessageType.UNKNOWN, description="Category of message type")
    qos_profile: Optional[str] = Field(default=None, description="QoS profile if specified")
    # Evidence provenance (research extension — backward compatible)
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Source evidence items supporting this topic's existence"
    )


class ServiceInfo(BaseModel):
    """Information about a ROS2 service"""
    name: str = Field(..., description="Full service name (with namespace)")
    service_type: str = Field(..., description="ROS2 service type (e.g., std_srvs/srv/SetBool)")
    role: Literal["server", "client"] = Field(..., description="Whether node provides or calls service")
    # Evidence provenance (research extension — backward compatible)
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Source evidence items supporting this service's existence"
    )


class ActionInfo(BaseModel):
    """Information about a ROS2 action"""
    name: str = Field(..., description="Full action name (with namespace)")
    action_type: str = Field(..., description="ROS2 action type (e.g., nav2_msgs/action/NavigateToPose)")
    role: Literal["server", "client"] = Field(..., description="Whether node provides or calls action")
    # Evidence provenance (research extension — backward compatible)
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Source evidence items supporting this action's existence"
    )


class ParameterInfo(BaseModel):
    """Information about a ROS2 parameter"""
    name: str = Field(..., description="Parameter name")
    param_type: str = Field(..., description="Parameter type")
    default_value: Optional[Any] = Field(default=None, description="Default value if any")
    description: Optional[str] = Field(default=None, description="Parameter description")


class QoSCompatibility(str, Enum):
    """Evaluation of ROS2 QoS profile compatibility between endpoints"""
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


class RemappingRule(BaseModel):
    """An ordered ROS2 remapping rule with evidence and scope"""
    from_name: str = Field(..., description="Original topic/service/action name to match")
    to_name: str = Field(..., description="Replacement name")
    scope: Optional[str] = Field(default=None, description="Scope where remapping was declared")
    target_node: Optional[str] = Field(default=None, description="Node name if rule is node-specific")
    order: int = Field(default=0, description="Evaluation order index")
    source_file: Optional[str] = Field(default=None, description="Declaring launch file")
    line_number: Optional[int] = Field(default=None, description="Source line number")


class InterfaceDeclaration(BaseModel):
    """
    Source-level ROS2 interface declaration extracted from C++ or Python source code.
    Permanently associated with its canonical Phase 1 source node ID.
    """
    declaration_id: str = Field(..., description="Unique ID: owner_node_id::type::name#Lline")
    owner_node_id: str = Field(..., description="Canonical Phase 1 source node ID (package::ClassName)")
    interface_type: CommunicationType = Field(..., description="Interface category (publisher, subscriber, etc.)")
    name_expression: str = Field(..., description="Original raw name expression from source code")
    message_type: str = Field(..., description="Normalized ROS2 message/service/action type (e.g. geometry_msgs/msg/Twist)")
    direction: Literal["in", "out"] = Field(..., description="'out' for publishers/clients, 'in' for subscribers/servers")
    qos_reliability: Optional[str] = Field(default=None, description="Reliability QoS if specified (e.g. reliable, best_effort)")
    qos_durability: Optional[str] = Field(default=None, description="Durability QoS if specified (e.g. transient_local, volatile)")
    source_file: str = Field(..., description="Relative path to declaring source file")
    line_start: Optional[int] = Field(default=None, description="Source line number (1-indexed)")
    line_end: Optional[int] = Field(default=None, description="Ending source line number")
    discovery_method: str = Field(..., description="Extractor method (e.g. cpp_interface_extractor, python_ast_interface_extractor)")
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.RESOLVED, description="Resolution status")
    is_action_protocol_child: bool = Field(default=False, description="True if this is an internal DDS child of an Action")
    parent_action_name: Optional[str] = Field(default=None, description="Parent Action name if this is an internal protocol child")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Source evidence citations")
    repository_name: Optional[str] = Field(default=None, description="Repository name for provenance and isolation")
    owning_class: Optional[str] = Field(default=None, description="Owning C++ or Python class name")
    owning_component: Optional[str] = Field(default=None, description="Owning component name if registered")
    inheritance_path: List[str] = Field(default_factory=list, description="Class inheritance hierarchy path (e.g. ['SlamToolbox', 'AsynchronousSlamToolbox'])")
    resolved_name: Optional[str] = Field(default=None, description="Parameter-resolved default interface name")
    qos_history: Optional[str] = Field(default=None, description="QoS history policy (e.g. keep_last, keep_all)")
    qos_depth: Optional[int] = Field(default=None, description="QoS queue depth")
    qos_compatibility: Optional[str] = Field(default=None, description="QoS compatibility notes")
    lifecycle_phase: Optional[str] = Field(default=None, description="Lifecycle transition phase when interface is configured (e.g. on_configure, on_activate)")
    parameter_provenance: Optional[str] = Field(default=None, description="Parameter name and default value backing this interface")
    is_dynamic: bool = Field(default=False, description="True if interface name is dynamically computed or templated at runtime")
    dynamic_template: Optional[str] = Field(default=None, description="Template format for dynamic interface (e.g. /map_{i})")
    dynamic_prefix: Optional[str] = Field(default=None, description="Static prefix of dynamic template (e.g. /map_)")
    dynamic_unresolved_part: Optional[str] = Field(default=None, description="Dynamic unresolved part (e.g. {i} or std::to_string(...))")


class ROS2Node(BaseModel):
    """
    Blueprint for a ROS2 node - the core schema element.
    Constrains LLM output to valid, structured node information.
    """
    # Identity
    id: str = Field(default="", description="Stable unique entity identifier (e.g. package::ClassName)")
    name: str = Field(..., description="Node name (as appears in ROS graph, or empty if unresolved)")
    fully_qualified_name: str = Field(..., description="Fully qualified name with namespace")
    class_name: str = Field(..., description="C++ or Python class name")
    source_file: str = Field(..., description="Path to source file relative to repo root")
    package_name: str = Field(..., description="ROS2 package name")
    namespace: str = Field(default="", description="ROS2 namespace")

    # Entity classification (Phase 1)
    entity_type: EntityType = Field(default=EntityType.ROS_NODE, description="Type of entity")
    node_category: NodeCategory = Field(default=NodeCategory.UNKNOWN, description="Architectural role / category")
    classification_label: Optional[str] = Field(default=None, description="Explicit architectural classification label")
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.UNRESOLVED, description="Identity resolution status")
    source_language: Literal["python", "cpp", "launch_only", "unknown"] = Field(default="unknown", description="Source implementation language")
    is_test: bool = Field(default=False, description="Whether node is test code")
    is_lifecycle: bool = Field(default=False, description="Whether node uses lifecycle")
    is_abstract: bool = Field(default=False, description="Whether node is an abstract base class with pure virtual methods")
    base_class: Optional[str] = Field(default=None, description="Base class name if derived")
    executable: Optional[str] = Field(default=None, description="Mapped executable name")
    component_registered: bool = Field(default=False, description="Whether component is registered via macro/CMake")
    component_name: Optional[str] = Field(default=None, description="Registered component class/library name")

    # Communication interfaces
    publishers: List[TopicInfo] = Field(default_factory=list, description="Topics this node publishes to")
    subscribers: List[TopicInfo] = Field(default_factory=list, description="Topics this node subscribes to")
    services: List[ServiceInfo] = Field(default_factory=list, description="Services this node provides/calls")
    actions: List[ActionInfo] = Field(default_factory=list, description="Actions this node provides/calls")
    interface_declarations: List[InterfaceDeclaration] = Field(default_factory=list, description="Detailed source interface declarations")

    # Configuration
    parameters: List[ParameterInfo] = Field(default_factory=list, description="ROS2 parameters")
    remappings: Dict[str, str] = Field(default_factory=dict, description="Topic/service remappings")

    # Metadata
    docstring: Optional[str] = Field(default=None, description="Class docstring if available")
    composition: Optional[str] = Field(default=None, description="Component container if composed")

    # Evidence provenance (research extension — backward compatible)
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Source evidence items supporting this node's existence"
    )
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.UNKNOWN,
        description="Evidence-based validation status (set by EvidenceValidator)"
    )

    @field_validator('fully_qualified_name')
    @classmethod
    def validate_fqn(cls, v: str, info) -> str:
        """Ensure fully qualified name includes namespace"""
        if info.data.get('namespace') and not v.startswith(info.data['namespace']):
            return f"{info.data['namespace']}/{v.lstrip('/')}"
        return v

    def get_publisher_topics(self) -> List[str]:
        return [p.name for p in self.publishers]

    def get_subscriber_topics(self) -> List[str]:
        return [s.name for s in self.subscribers]


class LaunchNode(BaseModel):
    """Node or component as declared in a launch file"""
    node_name: str = Field(..., description="Node name in launch file")
    package: str = Field(..., description="ROS2 package containing the node")
    executable: str = Field(default="", description="Executable name (empty if composable)")
    plugin: Optional[str] = Field(default=None, description="Plugin/class name if ComposableNode")
    namespace: str = Field(default="", description="Namespace from launch file")
    remappings: Dict[str, str] = Field(default_factory=dict, description="Remappings from launch file")
    parameters: List[Any] = Field(default_factory=list, description="Parameters from launch file")
    arguments: List[str] = Field(default_factory=list, description="Command-line arguments")
    respawn: bool = Field(default=False, description="Whether node respawns")
    output: str = Field(default="screen", description="Output handling")
    is_composable: bool = Field(default=False, description="Whether declared as a composable component")
    target_container: Optional[str] = Field(default=None, description="Target component container if composable")
    condition: Optional[str] = Field(default=None, description="Launch condition expression if conditional")
    line_start: Optional[int] = Field(default=None, description="Source line where node is declared")
    action_type: str = Field(default="Node", description="Action type: Node, LifecycleNode, ComposableNode")
    is_lifecycle: bool = Field(default=False, description="Whether declared as a LifecycleNode")
    parameter_files: List[str] = Field(default_factory=list, description="Resolved or declared parameter files")
    inline_parameters: Dict[str, Any] = Field(default_factory=dict, description="Inline key-value parameters")
    lifecycle_info: Optional[Dict[str, Any]] = Field(default=None, description="Lifecycle transition or management info")
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.RESOLVED, description="Resolution status")


class LaunchInclude(BaseModel):
    """Included launch file"""
    file_path: str = Field(..., description="Path expression to included launch file")
    resolved_path: Optional[str] = Field(default=None, description="Resolved relative file path if resolved")
    package: Optional[str] = Field(default=None, description="Package if using find-pkg-share")
    launch_arguments: Dict[str, str] = Field(default_factory=dict, description="Arguments passed to included launch")
    condition: Optional[str] = Field(default=None, description="Launch condition if any")
    line_start: Optional[int] = Field(default=None, description="Source line where include is declared")
    included_by: Optional[str] = Field(default=None, description="Parent launch file")
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.UNRESOLVED, description="Path resolution status")


class LaunchInstance(BaseModel):
    """
    A runtime deployment instance of a ROS2 node (standalone executable or composed component).
    Maintains deterministic identity, source node mapping, container association, and deployment profile.
    """
    instance_id: str = Field(..., description="Deterministic unique instance ID (e.g. launch_file::node_name#L123)")
    node_id: Optional[str] = Field(default=None, description="Canonical Phase 1 ROS2Node.id if resolved")
    candidate_node_ids: List[str] = Field(default_factory=list, description="All matching candidate node IDs when ambiguous or unselected")
    mapping_status: LaunchMappingStatus = Field(default=LaunchMappingStatus.UNRESOLVED, description="Resolution status against source inventory")
    node_name: str = Field(..., description="Declared or effective runtime node name")
    package: str = Field(..., description="Package name")
    executable: Optional[str] = Field(default=None, description="Executable name if standalone or container host")
    plugin_class: Optional[str] = Field(default=None, description="Plugin/component class if composable")
    launch_file: str = Field(..., description="Path to declaring launch file relative to repo root")
    line_number: Optional[int] = Field(default=None, description="Declaration line in launch file")
    parent_inclusion_id: Optional[str] = Field(default=None, description="ID of parent inclusion if included hierarchically")
    namespace: str = Field(default="", description="Resolved ROS2 namespace")
    remappings: Dict[str, str] = Field(default_factory=dict, description="Resolved remappings")
    parameters: List[Any] = Field(default_factory=list, description="Resolved parameters or parameter files")
    arguments: List[str] = Field(default_factory=list, description="CLI arguments")
    is_composable: bool = Field(default=False, description="True if loaded into a component container")
    container_name: Optional[str] = Field(default=None, description="Target component container name if composed")
    condition: Optional[str] = Field(default=None, description="Active launch condition expression")
    deployment_profile: str = Field(default="default", description="Active deployment profile (standalone, composable, etc.)")
    launch_arguments: Dict[str, str] = Field(default_factory=dict, description="Active launch arguments passed or scoped")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Source citations for this launch instance")
    repository_name: Optional[str] = Field(default=None, description="Repository name for provenance and isolation")
    action_type: str = Field(default="Node", description="Action type: Node, LifecycleNode, ComposableNode")
    is_lifecycle: bool = Field(default=False, description="Whether declared as a LifecycleNode")
    parameter_files: List[str] = Field(default_factory=list, description="Resolved or declared parameter files")
    inline_parameters: Dict[str, Any] = Field(default_factory=dict, description="Inline key-value parameters")
    lifecycle_info: Optional[Dict[str, Any]] = Field(default=None, description="Lifecycle transition or management info")
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.RESOLVED, description="Declaration resolution status")


class LaunchContainer(BaseModel):
    """
    Host process / component container (e.g. rclcpp_components::component_container).
    Hosts ComposableNode instances but is not a functional domain node itself.
    """
    container_id: str = Field(..., description="Unique container ID")
    name: str = Field(..., description="Container name")
    package: str = Field(default="rclcpp_components", description="Package providing container executable")
    executable: str = Field(default="component_container", description="Container executable")
    launch_file: str = Field(..., description="Declaring launch file")
    line_number: Optional[int] = Field(default=None, description="Declaration line")
    namespace: str = Field(default="", description="Container namespace")
    loaded_components: List[str] = Field(default_factory=list, description="List of LaunchInstance IDs hosted in this container")
    condition: Optional[str] = Field(default=None, description="Container condition")
    deployment_profile: str = Field(default="composable", description="Deployment profile")


class NodeLaunchMapping(BaseModel):
    """
    Mapping between a Phase 1 source-grounded ROS2Node and its runtime LaunchInstances.
    """
    node_id: str = Field(..., description="Phase 1 canonical node ID (package::ClassName)")
    class_name: str = Field(..., description="Source implementation class name")
    package_name: str = Field(..., description="Source package name")
    source_file: str = Field(..., description="Source file location")
    mapping_status: LaunchMappingStatus = Field(..., description="Mapping status")
    candidate_node_ids: List[str] = Field(default_factory=list, description="Alternative matching candidate IDs if ambiguous")
    runtime_instances: List[str] = Field(default_factory=list, description="Associated LaunchInstance IDs")
    launch_files: List[str] = Field(default_factory=list, description="Launch files where this node is deployed")
    deployment_profiles: List[str] = Field(default_factory=list, description="Deployment profiles containing this node")


class DeploymentProfile(BaseModel):
    """
    A deployment configuration profile (e.g. standalone vs composable).
    """
    profile_name: str = Field(..., description="Profile name (e.g. standalone, composable, default)")
    condition: Optional[str] = Field(default=None, description="Condition defining this profile")
    description: Optional[str] = Field(default=None, description="Description of the profile")
    instance_ids: List[str] = Field(default_factory=list, description="LaunchInstance IDs active in this profile")
    container_ids: List[str] = Field(default_factory=list, description="LaunchContainer IDs active in this profile")
    configuration_args: Dict[str, Any] = Field(default_factory=dict, description="Key launch arguments defining profile")


class RuntimeInterfaceInstance(BaseModel):
    """
    Runtime deployment instance of an interface bound to a Phase 2 LaunchInstance.
    Applies namespaces, ordered remapping rules, and deployment profile context.
    """
    runtime_instance_id: str = Field(..., description="Unique runtime ID: launch_instance_id::type::resolved_name")
    declaration_id: str = Field(..., description="Reference to source InterfaceDeclaration")
    launch_instance_id: str = Field(..., description="Reference to Phase 2 LaunchInstance")
    owner_node_id: str = Field(..., description="Canonical Phase 1 source node ID")
    interface_type: CommunicationType = Field(..., description="Interface category")
    raw_name: str = Field(..., description="Original name expression before remapping/namespace")
    resolved_name: str = Field(..., description="Fully resolved runtime name with namespace and remappings")
    message_type: str = Field(..., description="Normalized ROS2 type")
    direction: Literal["in", "out"] = Field(..., description="'out' or 'in'")
    namespace: str = Field(default="", description="Resolved ROS2 namespace applied")
    applied_remappings: List[RemappingRule] = Field(default_factory=list, description="Ordered remapping rules applied")
    deployment_profile: str = Field(default="default", description="Deployment profile (standalone, composable, default)")
    container_name: Optional[str] = Field(default=None, description="Container name if composable")
    qos_reliability: Optional[str] = Field(default=None, description="Reliability QoS")
    qos_durability: Optional[str] = Field(default=None, description="Durability QoS")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Source and launch evidence citations")


class ActionProtocolDetails(BaseModel):
    """
    Internal protocol entities underlying a high-level ROS2 Action.
    Keeps Action as one semantic abstraction while recording protocol-level DDS children.
    """
    action_name: str = Field(..., description="Resolved Action name")
    action_type: str = Field(..., description="Action type (e.g. nav2_msgs/action/NavigateToPose)")
    owner_node_id: str = Field(..., description="Owner node ID")
    role: Literal["server", "client"] = Field(..., description="Server or client")
    send_goal_service: str = Field(..., description="send_goal service: <action>/_action/send_goal")
    cancel_goal_service: str = Field(..., description="cancel_goal service: <action>/_action/cancel_goal")
    get_result_service: str = Field(..., description="get_result service: <action>/_action/get_result")
    feedback_topic: str = Field(..., description="feedback topic: <action>/_action/feedback")
    status_topic: str = Field(..., description="status topic: <action>/_action/status")


class CommunicationEdge(BaseModel):
    """
    A typed communication connection between two endpoints with QoS and dual-endpoint evidence.
    """
    edge_id: str = Field(..., description="Unique edge ID: source -> target")
    graph_level: Literal["source_potential", "deployment_runtime"] = Field(..., description="Source-level potential vs Deployment runtime edge")
    communication_type: Literal["topic", "service", "action"] = Field(..., description="Channel type")
    interface_name: str = Field(..., description="Matched interface name (topic/service/action)")
    message_type: str = Field(..., description="ROS2 message/service/action type")
    source_node_id: str = Field(..., description="Caller / Publisher node ID")
    target_node_id: str = Field(..., description="Provider / Subscriber node ID")
    source_declaration_id: Optional[str] = Field(default=None, description="Source declaration ID")
    target_declaration_id: Optional[str] = Field(default=None, description="Target declaration ID")
    source_instance_id: Optional[str] = Field(default=None, description="Source launch instance ID if runtime")
    target_instance_id: Optional[str] = Field(default=None, description="Target launch instance ID if runtime")
    deployment_profile: Optional[str] = Field(default=None, description="Deployment profile if runtime edge")
    qos_status: QoSCompatibility = Field(default=QoSCompatibility.UNKNOWN, description="QoS evaluation status")
    qos_details: Optional[str] = Field(default=None, description="Explanation of QoS evaluation")
    status: Literal["matched", "external_source", "external_target", "unmatched_internal", "unknown"] = Field(default="matched")
    edge_kind: Optional[Literal["inter_node", "intra_node", "peer_instance", "cross_profile"]] = Field(
        default="inter_node", description="Category of communication connection"
    )
    source_component: Optional[str] = Field(default=None, description="Owning sub-component or host of source")
    target_component: Optional[str] = Field(default=None, description="Owning sub-component or host of target")
    evidence_source: List[EvidenceItem] = Field(default_factory=list, description="Evidence from source endpoint")
    evidence_target: List[EvidenceItem] = Field(default_factory=list, description="Evidence from target endpoint")


class CommunicationGraphModel(BaseModel):
    """Complete typed ROS2 communication graph model"""
    provenance: Optional[Dict[str, Any]] = Field(default=None, alias="_provenance", description="Artifact provenance metadata")
    repo_name: str = Field(default="", description="Repository name")
    source_potential_edges: List[CommunicationEdge] = Field(default_factory=list, description="Repository-level potential communication edges")
    deployment_runtime_edges: List[CommunicationEdge] = Field(default_factory=list, description="Deployment-specific active communication edges")
    intra_node_edges: List[CommunicationEdge] = Field(default_factory=list, description="Intra-node component communication edges")
    peer_edges: List[CommunicationEdge] = Field(default_factory=list, description="Inter-instance peer communication edges")
    cross_profile_edges: List[CommunicationEdge] = Field(default_factory=list, description="Hypothetical cross-profile edges")
    unmatched_endpoints: List[str] = Field(default_factory=list, description="Unmatched interface IDs")
    external_endpoints: List[str] = Field(default_factory=list, description="External interface IDs (backed by external evidence)")
    external_confirmed_endpoints: List[str] = Field(default_factory=list, description="Confirmed external endpoints backed by package/launch evidence")
    external_candidate_endpoints: List[str] = Field(default_factory=list, description="Candidate external endpoints without explicit launch evidence")
    internal_matched_endpoints: List[str] = Field(default_factory=list, description="Internal matched interface IDs")
    internal_peer_endpoints: List[str] = Field(default_factory=list, description="Internal peer-to-peer interface IDs")
    dependency_generated_endpoints: List[str] = Field(default_factory=list, description="Dependency-generated interface IDs")
    action_protocols: List[ActionProtocolDetails] = Field(default_factory=list, description="Detailed underlying action protocol entities")


class CommunicationMatrixModel(BaseModel):
    """N x N communication matrix between recovered nodes"""
    provenance: Optional[Dict[str, Any]] = Field(default=None, alias="_provenance", description="Artifact provenance metadata")
    nodes: List[str] = Field(default_factory=list, description="List of node IDs")
    matrix: Dict[str, Dict[str, Dict[str, int]]] = Field(default_factory=dict, description="caller -> provider -> counts")
    summary: Dict[str, int] = Field(default_factory=dict, description="Total matched connection counts by type")


class LaunchFile(BaseModel):
    """
    Parsed launch file information - Python or XML launch files.
    """
    file_path: str = Field(..., description="Path to launch file relative to repo root")
    package_name: str = Field(..., description="ROS2 package name")
    launch_type: Literal["python", "xml", "yaml"] = Field(..., description="Launch file type")

    # Nodes declared in this launch file
    nodes: List[LaunchNode] = Field(default_factory=list, description="Nodes launched by this file")

    # Included launch files (hierarchical composition)
    includes: List[LaunchInclude] = Field(default_factory=list, description="Included launch files")

    # Launch arguments
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Launch file arguments")

    # Groups/scoped elements
    groups: List[Dict[str, Any]] = Field(default_factory=list, description="Group actions with scoped namespaces")
    unresolved_expressions: List[str] = Field(default_factory=list, description="Dynamic or unsupported launch constructs (OpaqueFunction, ExecuteProcess, etc.)")

    # Resolved deployment instances and containers in this file
    instances: List[LaunchInstance] = Field(default_factory=list, description="Resolved launch deployment instances in this file")
    containers: List[LaunchContainer] = Field(default_factory=list, description="Component containers declared in this file")
    repository_name: Optional[str] = Field(default=None, description="Target repository name")
    is_cmake_installed: bool = Field(default=True, description="Whether installed via CMakeLists.txt install(DIRECTORY launch ...)")
    launch_role: Optional[str] = Field(default=None, description="Architectural role / classification of the launch file")
    is_runnable_entry_point: bool = Field(default=True, description="Whether this launch file is a runnable entry point")
    provenance: Optional[Dict[str, Any]] = Field(default=None, alias="_provenance", description="Artifact provenance metadata")


class Subsystem(BaseModel):
    """A logical subsystem grouping related nodes"""
    name: str = Field(..., description="Subsystem name")
    description: str = Field(..., description="Subsystem description")
    nodes: List[str] = Field(default_factory=list, description="Node IDs or names in this subsystem")
    launch_files: List[str] = Field(default_factory=list, description="Launch files that compose this subsystem")
    external_interfaces: List[TopicInfo] = Field(default_factory=list, description="Topics crossing subsystem boundary (legacy)")
    architectural_role: str = Field(default="production_subsystem", description="Architectural role of subsystem")
    is_test_infrastructure: bool = Field(default=False, description="Whether subsystem is test/mock infrastructure")
    is_client_application: bool = Field(default=False, description="Whether subsystem is a client-side autonomy application")
    intra_cohesion_score: float = Field(default=0.0, description="Internal edge density score [0.0, 1.0]")
    inter_coupling_score: float = Field(default=0.0, description="Inter-subsystem edge count")
    cohesion_status: str = Field(default="computed", description="'computed' or 'N/A' when fewer than 2 nodes")
    coupling_internal: float = Field(default=0.0, description="Edges to other internal repository subsystems")
    coupling_external: float = Field(default=0.0, description="Edges/interfaces connecting to external ROS 2 nodes")
    incoming_dependencies: int = Field(default=0, description="Incoming communication/dependency count")
    outgoing_dependencies: int = Field(default=0, description="Outgoing communication/dependency count")
    interface_density: float = Field(default=0.0, description="Average communication interfaces per node in subsystem")
    boundary_interfaces: List[str] = Field(default_factory=list, description="List of interface signatures crossing subsystem boundary")
    justification: Optional[str] = Field(default=None, description="Clustering justification")
    subsystem_evidence: List[EvidenceItem] = Field(default_factory=list, description="Evidence items for subsystem assignment")


class SubsystemModel(BaseModel):
    """Recovered logical subsystems model"""
    provenance: Optional[Dict[str, Any]] = Field(default=None, alias="_provenance", description="Artifact provenance metadata")
    subsystems: List[Subsystem] = Field(default_factory=list, description="Recovered subsystems")
    unassigned_nodes: List[str] = Field(default_factory=list, description="Nodes not assigned to any subsystem")
    cohesion_coupling_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Per-subsystem cohesion & coupling")
    clustering_method: str = Field(default="multi_criteria_graph_role_clustering", description="Clustering algorithm used")
    node_assignments: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-node assignment justification, primary subsystem, and alternative candidates when uncertain"
    )
    reference_comparison: Dict[str, Any] = Field(default_factory=dict, description="Comparison with reference hypothesis")


# ---------------------------------------------------------------------------
# Phase 4 Lifecycle Architecture Models
# ---------------------------------------------------------------------------

class LifecyclePrimaryState(str, Enum):
    """Primary steady states of a ROS 2 lifecycle node"""
    UNCONFIGURED = "Unconfigured"
    INACTIVE = "Inactive"
    ACTIVE = "Active"
    FINALIZED = "Finalized"


class LifecycleTransitionState(str, Enum):
    """Intermediate transition states of a ROS 2 lifecycle node"""
    CONFIGURING = "Configuring"
    CLEANING_UP = "CleaningUp"
    ACTIVATING = "Activating"
    DEACTIVATING = "Deactivating"
    SHUTTING_DOWN = "ShuttingDown"
    ERROR_PROCESSING = "ErrorProcessing"


class ManagedNodeInfo(BaseModel):
    """Details of a node managed by a lifecycle manager"""
    node_id: str = Field(..., description="Canonical Phase 1 node ID")
    launch_name: str = Field(..., description="Runtime node name in launch")
    managing_manager: str = Field(..., description="Lifecycle manager node/launch name")
    transition_order_index: int = Field(default=0, description="Order index in startup transition sequence")
    autostart: bool = Field(default=False, description="Whether autostart is enabled for manager")
    bond_enabled: bool = Field(default=True, description="Whether bond connection is enabled")
    handles_transition_callbacks: List[str] = Field(
        default_factory=list,
        description="Lifecycle callbacks implemented in source (e.g. on_configure, on_activate)"
    )
    is_lifecycle_node: bool = Field(default=True, description="Whether node inherits from rclcpp_lifecycle::LifecycleNode")
    configured_target_state: str = Field(default="Active", description="Target state configured via launch manager")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Evidence citations")


class LifecycleManagerInfo(BaseModel):
    """Details of a nav2_lifecycle_manager instance"""
    manager_name: str = Field(..., description="Lifecycle manager launch/node name")
    launch_file: str = Field(..., description="Launch file where declared")
    autostart: bool = Field(default=False, description="Autostart parameter value")
    bond_timeout: float = Field(default=4.0, description="Bond timeout parameter value")
    managed_node_names: List[str] = Field(default_factory=list, description="Node names list in order of transition")
    service_servers: List[str] = Field(default_factory=list, description="Services exposed by manager")


class LifecycleTransition(BaseModel):
    """A transition between lifecycle states"""
    transition_id: int = Field(..., description="ROS 2 transition ID (e.g. 1=configure, 3=activate)")
    transition_name: str = Field(..., description="Transition name (configure, activate, deactivate, cleanup, shutdown)")
    from_state: str = Field(..., description="Source state")
    to_state: str = Field(..., description="Destination state")
    trigger: str = Field(default="lifecycle_manager", description="Trigger source")


class LifecycleGraphModel(BaseModel):
    """Recovered ROS 2 lifecycle management architecture"""
    provenance: Optional[Dict[str, Any]] = Field(default=None, alias="_provenance", description="Artifact provenance metadata")
    lifecycle_managers: List[LifecycleManagerInfo] = Field(default_factory=list, description="Declared lifecycle managers")
    managed_nodes: List[ManagedNodeInfo] = Field(default_factory=list, description="Nodes under lifecycle management")
    unmanaged_nodes: List[str] = Field(default_factory=list, description="Nodes not managed by any lifecycle manager")
    standard_transitions: List[LifecycleTransition] = Field(default_factory=list, description="ROS 2 lifecycle state machine transitions")
    startup_sequence: List[str] = Field(default_factory=list, description="Ordered sequence of nodes brought up during autostart")
    mermaid_diagram: str = Field(default="", description="Mermaid state diagram of lifecycle architecture")


# ---------------------------------------------------------------------------
# Phase 4 Plugin Architecture Models
# ---------------------------------------------------------------------------

class PluginStatus(str, Enum):
    """Plugin status in lifecycle and build"""
    REGISTERED = "registered"         # Declared in plugins.xml
    AVAILABLE = "available"           # Compiled binary / export found
    CONFIGURED = "configured"         # Named in YAML parameters
    SELECTED = "selected"             # Set as active default in params
    RUNTIME_LOADED = "runtime_loaded" # Confirmed in deployment
    UNKNOWN = "unknown"


class PluginDeclaration(BaseModel):
    """A pluginlib plugin declared in a plugins.xml manifest"""
    plugin_name: str = Field(..., description="Lookup name of plugin (e.g. 'nav2_costmap_2d::ObstacleLayer')")
    class_type: str = Field(..., description="C++ class implementation")
    base_class_type: str = Field(..., description="Pluginlib base class interface (e.g. 'nav2_core::GlobalPlanner')")
    package_name: str = Field(..., description="Package declaring the plugin")
    manifest_file: str = Field(..., description="Path to plugins.xml manifest file")
    library_path: Optional[str] = Field(default=None, description="Library path declared in XML")
    description: Optional[str] = Field(default=None, description="Description from XML manifest")
    plugin_category: str = Field(default="unknown", description="Category: costmap_layer, planner, controller, smoother, behavior, navigator, waypoint_task")
    status: PluginStatus = Field(default=PluginStatus.REGISTERED, description="Plugin status")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Source provenance evidence")


class ServerPluginConfiguration(BaseModel):
    """Plugin configuration for a specific Nav2 server in nav2_params.yaml"""
    server_node_name: str = Field(..., description="Server node name (e.g. controller_server, planner_server)")
    plugin_slot: str = Field(..., description="Parameter key for plugin slot (e.g. FollowPath.plugin, planner_plugins)")
    plugin_names: List[str] = Field(default_factory=list, description="Configured plugin identifiers in YAML")
    plugin_types: List[str] = Field(default_factory=list, description="Configured plugin types in YAML")
    selected_plugin: Optional[str] = Field(default=None, description="Active selected plugin type")
    parameter_file: str = Field(default="", description="YAML file where configured")


class PluginArchitectureModel(BaseModel):
    """Recovered pluginlib plugin architecture"""
    provenance: Optional[Dict[str, Any]] = Field(default=None, alias="_provenance", description="Artifact provenance metadata")
    plugins: List[PluginDeclaration] = Field(default_factory=list, description="All declared pluginlib plugins")
    categories: Dict[str, List[str]] = Field(default_factory=dict, description="Category -> plugin names")
    server_configurations: List[ServerPluginConfiguration] = Field(default_factory=list, description="Plugin configurations per server")
    status_counts: Dict[str, int] = Field(default_factory=dict, description="Counts by PluginStatus")
    mermaid_diagram: str = Field(default="", description="Mermaid diagram of plugin architecture")


# ---------------------------------------------------------------------------
# Phase 4 Behavior Tree Models
# ---------------------------------------------------------------------------

class BTNodeType(str, Enum):
    """BehaviorTree.CPP node category"""
    CONTROL = "control"
    DECORATOR = "decorator"
    ACTION = "action"
    CONDITION = "condition"
    SUBTREE = "subtree"
    UNKNOWN = "unknown"


class BlackboardPort(BaseModel):
    """Input/Output port on a BehaviorTree node"""
    name: str = Field(..., description="Port name (e.g. path, goal, server_name)")
    direction: Literal["input", "output", "inout"] = Field(..., description="Dataflow direction")
    blackboard_key: Optional[str] = Field(default=None, description="Bound blackboard key expression (e.g. {path})")
    description: Optional[str] = Field(default=None, description="Port description")


class BTNodeModel(BaseModel):
    """A node in a BehaviorTree XML definition"""
    id: str = Field(..., description="Node element identifier / tag")
    node_type: BTNodeType = Field(..., description="Node type category")
    class_name: str = Field(..., description="BT class name (e.g. ComputePathToPose, RecoveryNode)")
    name: Optional[str] = Field(default=None, description="Name attribute if set")
    ports: List[BlackboardPort] = Field(default_factory=list, description="Bound blackboard ports")
    target_server: Optional[str] = Field(default=None, description="Target Nav2 server node if action/service")
    action_or_service: Optional[str] = Field(default=None, description="ROS 2 action or service interface name")
    child_ids: List[str] = Field(default_factory=list, description="Child node identifiers")
    is_hosted_in_bt_navigator: bool = Field(default=True, description="BT nodes are components hosted inside bt_navigator, never independent ROS 2 nodes")


class BehaviorTreeModel(BaseModel):
    """A recovered BehaviorTree definition"""
    tree_id: str = Field(..., description="Tree ID / filename")
    tree_name: str = Field(..., description="Tree identifier in XML")
    file_path: str = Field(..., description="Relative path to XML file")
    root_node_id: str = Field(default="", description="Root node ID")
    nodes: List[BTNodeModel] = Field(default_factory=list, description="All nodes in this tree")
    blackboard_variables: List[str] = Field(default_factory=list, description="Blackboard variables accessed in tree")
    ros2_action_bindings: Dict[str, str] = Field(default_factory=dict, description="BT node -> ROS 2 action name")
    ros2_service_bindings: Dict[str, str] = Field(default_factory=dict, description="BT node -> ROS 2 service name")
    mermaid_diagram: str = Field(default="", description="Mermaid flowchart of behavior tree")


class BehaviorTreeCollectionModel(BaseModel):
    """Collection of recovered Nav2 behavior trees"""
    provenance: Optional[Dict[str, Any]] = Field(default=None, alias="_provenance", description="Artifact provenance metadata")
    trees: List[BehaviorTreeModel] = Field(default_factory=list, description="Recovered behavior trees")
    host_node_id: str = Field(default="nav2_bt_navigator::BtNavigator", description="Host ROS 2 node ID")
    all_blackboard_variables: List[str] = Field(default_factory=list, description="All unique blackboard variables")
    total_trees: int = Field(default=0, description="Total trees recovered")
    total_bt_nodes: int = Field(default=0, description="Total BT nodes recovered")
    bt_to_ros2_bindings: List[Dict[str, str]] = Field(default_factory=list, description="Cross-system bindings")


# ---------------------------------------------------------------------------
# Phase 4 Architecture Views Models (ISO/IEC/IEEE 42010 Aligned)
# ---------------------------------------------------------------------------

class ArchitectureView(BaseModel):
    """An architectural view adhering to ISO/IEC/IEEE 42010"""
    view_id: str = Field(..., description="View identifier (e.g. system_context, lifecycle_view)")
    name: str = Field(..., description="Human-readable view name")
    description: str = Field(..., description="View description")
    architectural_concerns: List[str] = Field(default_factory=list, description="Concerns addressed by this view")
    target_stakeholders: List[str] = Field(default_factory=list, description="Target stakeholders")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Key entities represented in view")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Relationships between entities")
    mermaid_diagram: str = Field(default="", description="Mermaid.js diagram syntax")


class ArchitectureViewsModel(BaseModel):
    """Complete collection of 8 ISO/IEC/IEEE 42010 aligned architectural views"""
    provenance: Optional[Dict[str, Any]] = Field(default=None, alias="_provenance", description="Artifact provenance metadata")
    standards_alignment: str = Field(default="ISO/IEC/IEEE 42010", description="Architecture description standard")
    views: Dict[str, ArchitectureView] = Field(default_factory=dict, description="Views keyed by view_id")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics across views")


# ---------------------------------------------------------------------------
# Phase 5 Runtime Validation & Evaluation Models
# ---------------------------------------------------------------------------

class DiscrepancyType(str, Enum):
    """Classification of discrepancies between static prediction and runtime observation"""
    MATCHED = "MATCHED"
    MISSING_FROM_STATIC = "MISSING_FROM_STATIC"
    MISSING_FROM_RUNTIME = "MISSING_FROM_RUNTIME"
    UNEXPECTED_RUNTIME = "UNEXPECTED_RUNTIME"
    UNRESOLVED = "UNRESOLVED"
    CONFIGURATION_MISMATCH = "CONFIGURATION_MISMATCH"


class RuntimeNodeRecord(BaseModel):
    """Runtime node observed via ROS 2 CLI introspection"""
    name: str = Field(..., description="Node name")
    namespace: str = Field(default="/", description="Node namespace")
    fully_qualified_name: str = Field(..., description="Fully qualified name (namespace + name)")
    package: Optional[str] = Field(default=None, description="Package if identified")
    lifecycle_state: Optional[str] = Field(default=None, description="Observed lifecycle state (e.g. active, unconfigured)")
    is_component: bool = Field(default=False, description="Whether node runs as a component inside a container")
    container_name: Optional[str] = Field(default=None, description="Container name if composable")
    publishers: List[Dict[str, Any]] = Field(default_factory=list, description="Observed publisher endpoints")
    subscribers: List[Dict[str, Any]] = Field(default_factory=list, description="Observed subscriber endpoints")
    service_servers: List[Dict[str, Any]] = Field(default_factory=list, description="Observed service servers owned by node")
    service_clients: List[Dict[str, Any]] = Field(default_factory=list, description="Observed service clients owned by node")
    action_servers: List[Dict[str, Any]] = Field(default_factory=list, description="Observed action servers owned by node")
    action_clients: List[Dict[str, Any]] = Field(default_factory=list, description="Observed action clients owned by node")


class RuntimeSnapshot(BaseModel):
    """
    A reproducible runtime snapshot captured from an active ROS 2 deployment.
    Contains raw CLI outputs and parsed graph entities with complete provenance.
    """
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    scenario_name: str = Field(..., description="Experiment scenario name (e.g. standalone_navigation)")
    timestamp: str = Field(..., description="ISO 8601 capture timestamp")
    commit_hash: str = Field(..., description="Exact Git commit hash of target repository")
    ros_distribution: str = Field(..., description="ROS distribution (e.g. jazzy, humble)")
    os_version: str = Field(..., description="Operating system version (e.g. Ubuntu 24.04 LTS)")
    rmw_implementation: str = Field(..., description="Active RMW implementation (e.g. rmw_cyclonedds_cpp)")
    ros_domain_id: int = Field(default=0, description="ROS_DOMAIN_ID used during experiment")
    root_launch_file: str = Field(..., description="Root launch file executed")
    launch_arguments: Dict[str, Any] = Field(default_factory=dict, description="Launch CLI arguments passed")
    yaml_parameter_hashes: Dict[str, str] = Field(default_factory=dict, description="SHA-256 hashes of input YAML parameter files")
    nodes: List[RuntimeNodeRecord] = Field(default_factory=list, description="Observed running ROS 2 nodes")
    topics: List[Dict[str, Any]] = Field(default_factory=list, description="Observed active DDS topics")
    services: List[Dict[str, Any]] = Field(default_factory=list, description="Observed active ROS 2 services")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Observed active ROS 2 actions")
    containers: List[Dict[str, Any]] = Field(default_factory=list, description="Observed composable node containers")
    lifecycle_states: Dict[str, str] = Field(default_factory=dict, description="Observed node lifecycle states")
    raw_cli_output: Dict[str, str] = Field(default_factory=dict, description="Raw stdout from ros2 introspection commands")
    command_exit_codes: Dict[str, int] = Field(default_factory=dict, description="Exit codes of introspection commands")
    verification_status: str = Field(default="VERIFIED", description="Snapshot verification status")
    provenance_notes: Dict[str, Any] = Field(default_factory=dict, description="Detailed provenance, execution environment, and benchmark fixture metadata")


class RuntimeDiscrepancy(BaseModel):
    """A discrepancy between static prediction and runtime observation"""
    entity_type: str = Field(..., description="Category: node, topic, service, action, edge, lifecycle, qos")
    name: str = Field(..., description="Entity identifier or interface name")
    discrepancy_type: DiscrepancyType = Field(..., description="Discrepancy classification")
    static_prediction: Optional[Any] = Field(default=None, description="Static model prediction")
    runtime_observation: Optional[Any] = Field(default=None, description="Observed runtime fact")
    explanation: str = Field(..., description="Detailed architectural reason for discrepancy")


class EvaluationMetricsModel(BaseModel):
    """Comprehensive quantitative evaluation metrics across all research dimensions"""
    scenario_name: str = Field(..., description="Evaluated scenario")
    node_metrics: Dict[str, float] = Field(default_factory=dict, description="Precision, Recall, F1 for nodes")
    topic_metrics: Dict[str, float] = Field(default_factory=dict, description="Precision, Recall, F1 for topics")
    service_metrics: Dict[str, float] = Field(default_factory=dict, description="Precision, Recall, F1 for services")
    action_metrics: Dict[str, float] = Field(default_factory=dict, description="Precision, Recall, F1 for actions")
    edge_metrics: Dict[str, float] = Field(default_factory=dict, description="Precision, Recall, F1 for communication edges")
    runtime_graph_agreement: float = Field(default=0.0, description="Jaccard similarity between predicted and observed edges")
    subsystem_jaccard_similarity: float = Field(default=0.0, description="Mean Jaccard similarity across subsystems")
    subsystem_ari: float = Field(default=0.0, description="Adjusted Rand Index for subsystem clustering")
    subsystem_nmi: float = Field(default=0.0, description="Normalized Mutual Information for subsystem clustering")
    plugin_accuracy: float = Field(default=0.0, description="Accuracy of plugin selection prediction")
    behavior_tree_accuracy: float = Field(default=0.0, description="Accuracy of BT server bindings")
    evidence_coverage: float = Field(default=0.0, description="Evidence provenance coverage rate")
    processing_time_seconds: float = Field(default=0.0, description="Pipeline execution duration")



class PackageDependencyEdge(BaseModel):
    """Directed dependency edge between two ROS 2 packages"""
    source_package: str = Field(..., description="Dependent package name")
    target_package: str = Field(..., description="Dependency package name")
    dependency_type: str = Field(
        ...,
        description="build_depend, buildtool_depend, exec_depend, test_depend, depend, source_include, source_import"
    )
    origin: Literal["declared_manifest", "observed_source"] = Field(
        default="declared_manifest", description="Whether declared in package.xml/setup.py or observed in source"
    )
    is_target_internal: bool = Field(default=False, description="True if target package exists in this repository")
    resolution_category: str = Field(
        default="resolved_ros_package",
        description="resolved_internal_package | resolved_ros_package | manifest_declared_external | unresolved_external_library"
    )
    source_file: str = Field(default="", description="Declaring or observing file path")
    line_number: Optional[int] = Field(default=None, description="Line number of declaration or import/include")


class PackageNodeInfo(BaseModel):
    """Metadata for a ROS 2 package in the dependency graph"""
    name: str = Field(..., description="Package name")
    build_type: str = Field(default="unknown", description="ament_cmake, ament_python, cmake, etc.")
    package_path: str = Field(default="", description="Relative path to package directory")
    is_internal: bool = Field(default=True, description="True if defined in this repository")
    declared_dependencies: List[str] = Field(default_factory=list)
    observed_source_dependencies: List[str] = Field(default_factory=list)
    console_scripts: Dict[str, str] = Field(default_factory=dict, description="setup.py console_scripts mapping")


class PackageDependencyGraph(BaseModel):
    """Complete directed package dependency graph"""
    packages: List[PackageNodeInfo] = Field(default_factory=list)
    edges: List[PackageDependencyEdge] = Field(default_factory=list)
    internal_packages: List[str] = Field(default_factory=list)
    external_packages: List[str] = Field(default_factory=list)
    undeclared_source_dependencies: List[Dict[str, Any]] = Field(
        default_factory=list, description="Source imports/includes not declared in package.xml"
    )


class ArchitectureValidationFinding(BaseModel):
    """A structured finding from ArchitectureValidator"""
    finding_id: str
    category: str = Field(..., description="e.g. launch_node_mismatch, unmatched_interface, missing_dependency")
    severity: Literal["Confirmed", "Warning", "Unresolved", "Potential inconsistency"] = Field(...)
    entity: str = Field(..., description="Affected node, interface, package, or launch file")
    message: str = Field(..., description="Detailed explanation")
    evidence: List[EvidenceItem] = Field(default_factory=list)


class ArchitectureValidationReport(BaseModel):
    """Summary of structural & semantic architecture validation checks"""
    findings: List[ArchitectureValidationFinding] = Field(default_factory=list)
    counts_by_severity: Dict[str, int] = Field(default_factory=dict)
    inventory_reconciliation: Dict[str, Any] = Field(default_factory=dict)


class ArchitectureModel(BaseModel):
    """
    Complete hierarchical architecture model - the final output of Stage 4.
    This is validated against the blueprint schema before documentation generation.
    """
    provenance: Optional[Dict[str, Any]] = Field(default=None, alias="_provenance", description="Artifact provenance metadata")
    # Metadata
    repo_name: str = Field(..., description="Repository name")
    repo_url: str = Field(..., description="Repository URL")
    commit_hash: str = Field(..., description="Git commit hash analyzed")
    branch: str = Field(default="unavailable", description="Git branch analyzed")
    archsynth_version: str = Field(default="2.0", description="ArchSynth version")
    analysis_timestamp: str = Field(..., description="ISO timestamp of analysis")

    # Core elements
    nodes: List[ROS2Node] = Field(default_factory=list, description="All discovered ROS2 nodes")
    launch_files: List[LaunchFile] = Field(default_factory=list, description="All parsed launch files")
    subsystems: List[Subsystem] = Field(default_factory=list, description="Logical subsystem grouping")

    # Communication graph
    topic_connections: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Publisher-subscriber pairs: {topic, publisher, subscribers[]}"
    )
    service_connections: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Service client-server pairs: {service, server, clients[]}"
    )
    action_connections: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Action client-server pairs: {action, server, clients[]}"
    )

    # Mermaid diagram syntax
    mermaid_diagram: str = Field(default="", description="Mermaid.js diagram syntax")

    # Phase 2 Launch Analysis elements
    launch_instances: List[LaunchInstance] = Field(default_factory=list, description="Runtime launch deployment instances")
    launch_containers: List[LaunchContainer] = Field(default_factory=list, description="Component containers declared across launch files")
    node_launch_mappings: List[NodeLaunchMapping] = Field(default_factory=list, description="Mapping between source nodes and launch instances")
    deployment_profiles: List[DeploymentProfile] = Field(default_factory=list, description="Deployment configuration profiles")

    # Phase 3 Communication Graph elements
    interfaces: List[InterfaceDeclaration] = Field(default_factory=list, description="Extracted source interface declarations")
    runtime_interfaces: List[RuntimeInterfaceInstance] = Field(default_factory=list, description="Resolved runtime interface instances")
    communication_graph: Optional[CommunicationGraphModel] = Field(default=None, description="Complete recovered ROS2 communication graph")
    communication_matrix: Optional[CommunicationMatrixModel] = Field(default=None, description="Interaction frequency matrix between nodes")

    # Phase 4 Synthesis & Recovery elements
    subsystem_model: Optional[SubsystemModel] = Field(default=None, description="Detailed multi-criteria subsystem recovery model")
    lifecycle_graph: Optional[LifecycleGraphModel] = Field(default=None, description="Recovered ROS 2 lifecycle management architecture")
    plugin_architecture: Optional[PluginArchitectureModel] = Field(default=None, description="Recovered pluginlib plugin architecture")
    behavior_tree_model: Optional[BehaviorTreeCollectionModel] = Field(default=None, description="Recovered BehaviorTree navigation orchestration")
    architecture_views: Optional[ArchitectureViewsModel] = Field(default=None, description="Collection of 8 ISO/IEC/IEEE 42010 aligned views")

    # Statistics
    stats: Dict[str, int] = Field(default_factory=dict, description="Summary statistics")

    # Research extensions (all Optional — backward compatible with existing architecture.json)
    package_dependency_graph: Optional[PackageDependencyGraph] = Field(
        default=None,
        description="Directed package dependency graph from package.xml, setup.py, CMakeLists.txt, and source includes/imports"
    )
    structured_node_inventory: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Unified inventory distinguishing repo-defined nodes, external launch executables, composable nodes, and unresolved entries"
    )
    architecture_validation: Optional[ArchitectureValidationReport] = Field(
        default=None,
        description="Structural and semantic architecture validation findings"
    )
    unresolved_launch_constructs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Dynamic or unsupported launch constructs preserved with evidence"
    )
    validation_report: Optional[ValidationReport] = Field(
        default=None,
        description="Evidence validation report (populated when --validate-evidence is used)"
    )
    experiment_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Reproducibility metadata: LLM provider, model, commit, timing, token usage, etc."
    )
    drift_report: Optional[DriftReport] = Field(
        default=None,
        description="Architecture drift report (populated in drift detection mode)"
    )

    def compute_stats(self) -> Dict[str, int]:
        """Compute summary statistics"""
        self.stats = {
            "total_nodes": len(self.nodes),
            "total_launch_files": len(self.launch_files),
            "total_launch_instances": len(self.launch_instances),
            "total_launch_containers": len(self.launch_containers),
            "total_subsystems": len(self.subsystems),
            "total_topics": len(set().union(*[n.get_publisher_topics() for n in self.nodes], *[n.get_subscriber_topics() for n in self.nodes])),
            "total_services": len(self.service_connections),
            "total_actions": len(self.action_connections),
        }
        return self.stats

    def get_node_by_name(self, name: str) -> Optional["ROS2Node"]:
        """Find node by fully qualified name"""
        for node in self.nodes:
            if node.fully_qualified_name == name or node.name == name:
                return node
        return None

    def get_nodes_in_namespace(self, namespace: str) -> List["ROS2Node"]:
        """Get all nodes in a namespace"""
        return [n for n in self.nodes if n.namespace == namespace or n.namespace.startswith(namespace + "/")]


class AnalysisResult(BaseModel):
    """Result of a single analysis stage"""
    stage: str = Field(..., description="Stage name")
    success: bool = Field(..., description="Whether stage completed successfully")
    output_path: Optional[str] = Field(default=None, description="Path to output file")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    duration_seconds: float = Field(default=0.0, description="Time taken")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PipelineConfig(BaseModel):
    """Configuration for the analysis pipeline"""
    repo_path: str = Field(..., description="Path to ROS2 repository")
    repo_url: str = Field(default="", description="Repository URL")
    commit_hash: str = Field(default="", description="Specific commit to analyze")
    output_dir: str = Field(default="output", description="Output directory")

    # LLM settings
    primary_llm: Literal["gemini", "ollama"] = Field(default="gemini", description="Primary LLM provider")
    gemini_model: str = Field(default="gemini-1.5-flash", description="Gemini model name")
    ollama_model: str = Field(default="qwen2.5-coder", description="Ollama model name")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama host")

    # Analysis settings
    max_files_per_call: int = Field(default=10, description="Max files to send to LLM at once")
    include_cpp: bool = Field(default=False, description="Whether to analyze C++ files")
    include_test_files: bool = Field(default=False, description="Whether to analyze test files")

    # Output settings
    generate_mermaid: bool = Field(default=True, description="Generate Mermaid diagram")
    generate_markdown: bool = Field(default=True, description="Generate Markdown documentation")
    validate_schema: bool = Field(default=True, description="Validate against schema")

    # Research extension settings (all optional, backward compatible)
    validate_evidence: bool = Field(default=False, description="Run evidence validation after synthesis")
    run_ablation: bool = Field(default=False, description="Run ablation study")
    ground_truth_dir: Optional[str] = Field(default=None, description="Path to ground truth JSON directory")
    base_commit: Optional[str] = Field(default=None, description="Base commit for drift detection")
    target_commit: Optional[str] = Field(default=None, description="Target commit for drift detection")
    drift_report: bool = Field(default=False, description="Enable drift detection mode")


# Schema registry for LLM output validation
SCHEMA_REGISTRY = {
    "ros2_node": ROS2Node,
    "launch_file": LaunchFile,
    "architecture_model": ArchitectureModel,
    "subsystem": Subsystem,
    "subsystem_model": SubsystemModel,
    "lifecycle_graph": LifecycleGraphModel,
    "plugin_architecture": PluginArchitectureModel,
    "behavior_tree_collection": BehaviorTreeCollectionModel,
    "architecture_views": ArchitectureViewsModel,
    "runtime_snapshot": RuntimeSnapshot,
    "runtime_discrepancy": RuntimeDiscrepancy,
    "evaluation_metrics": EvaluationMetricsModel,
    "evidence_item": EvidenceItem,
    "validation_report": ValidationReport,
    "drift_report": DriftReport,
}


def get_schema(name: str) -> type[BaseModel]:
    """Get schema class by name"""
    if name not in SCHEMA_REGISTRY:
        raise ValueError(f"Unknown schema: {name}. Available: {list(SCHEMA_REGISTRY.keys())}")
    return SCHEMA_REGISTRY[name]