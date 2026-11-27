"""
Generate ArchSynth_Review_Presentation.pptx (21 slides) in review_presentation/.
Follows the exact requested sequence:
  1. Title (First slide)
  2. Content
  3-4. Introduction
  5-6. Literature Review
  7. Research Gap
  8. Objective
  9-14. Methodology
  15-17. Results
  18. Publications
  19. Conclusion and Future Work
  20. Reference
  21. Thank You
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

OUT_DIR = Path("review_presentation")
OUT_DIR.mkdir(parents=True, exist_ok=True)
PPTX_PATH = OUT_DIR / "ArchSynth_Review_Presentation.pptx"

# Color Palette (Clean Academic Dark-Header + Light-Content Theme)
NAVY = RGBColor(15, 23, 42)        # #0F172A
DARK_BLUE = RGBColor(30, 58, 138)  # #1E3A8A
CYAN = RGBColor(6, 182, 212)       # #06B6D4
TEAL = RGBColor(13, 148, 136)      # #0D9488
SLATE = RGBColor(51, 65, 85)       # #334155
MUTED = RGBColor(100, 116, 139)    # #64748B
LIGHT_BG = RGBColor(248, 250, 252) # #F8FAFC
CARD_BG = RGBColor(241, 245, 249)  # #F1F5F9
BORDER = RGBColor(203, 213, 225)   # #CBD5E1
WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(22, 163, 74)
AMBER = RGBColor(217, 119, 6)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, title_text, section_tag, slide_num):
    set_bg(slide, LIGHT_BG)
    # Top navy bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.05))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()

    # Cyan accent strip
    strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.05), Inches(13.333), Inches(0.06))
    strip.fill.solid()
    strip.fill.fore_color.rgb = CYAN
    strip.line.fill.background()

    # Section tag
    tb_tag = slide.shapes.add_textbox(Inches(0.6), Inches(0.12), Inches(6.0), Inches(0.28))
    p = tb_tag.text_frame.paragraphs[0]
    p.text = section_tag.upper()
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = CYAN

    # Title
    tb_title = slide.shapes.add_textbox(Inches(0.6), Inches(0.36), Inches(11.5), Inches(0.6))
    p2 = tb_title.text_frame.paragraphs[0]
    p2.text = title_text
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = WHITE

    # Footer
    tb_foot = slide.shapes.add_textbox(Inches(0.6), Inches(7.12), Inches(9.0), Inches(0.28))
    pf = tb_foot.text_frame.paragraphs[0]
    pf.text = "ArchSynth v2.2  |  M.Tech Dissertation Review  |  DIAT Pune"
    pf.font.size = Pt(10)
    pf.font.color.rgb = MUTED

    tb_num = slide.shapes.add_textbox(Inches(11.8), Inches(7.12), Inches(1.0), Inches(0.28))
    pn = tb_num.text_frame.paragraphs[0]
    pn.alignment = PP_ALIGN.RIGHT
    pn.text = f"{slide_num} / 21"
    pn.font.size = Pt(10)
    pn.font.bold = True
    pn.font.color.rgb = SLATE


def add_bullets(slide, left, top, width, height, items, font_size=15, space_after=8):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        if isinstance(item, tuple):
            lead, rest = item
            r1 = p.add_run()
            r1.text = f"• {lead}: "
            r1.font.bold = True
            r1.font.size = Pt(font_size)
            r1.font.color.rgb = NAVY
            r2 = p.add_run()
            r2.text = rest
            r2.font.size = Pt(font_size)
            r2.font.color.rgb = SLATE
        else:
            r = p.add_run()
            r.text = f"• {item}"
            r.font.size = Pt(font_size)
            r.font.color.rgb = SLATE
    return tb


def add_card(slide, left, top, width, height, title, body_lines, accent=DARK_BLUE):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = WHITE
    box.line.color.rgb = BORDER
    box.line.width = Pt(1)

    hdr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(0.42))
    hdr.fill.solid()
    hdr.fill.fore_color.rgb = accent
    hdr.line.fill.background()

    tb_h = slide.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.06), Inches(width - 0.3), Inches(0.34))
    ph = tb_h.text_frame.paragraphs[0]
    ph.text = title
    ph.font.size = Pt(14)
    ph.font.bold = True
    ph.font.color.rgb = WHITE

    add_bullets(slide, left + 0.12, top + 0.50, width - 0.24, height - 0.58, body_lines, font_size=13, space_after=5)


def add_table(slide, left, top, width, height, headers, rows, font_size=11):
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(left), Inches(top), Inches(width), Inches(height))
    table = shape.table
    for c_idx, h in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(font_size)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT

    for r_idx, row in enumerate(rows, start=1):
        bg = WHITE if r_idx % 2 == 1 else CARD_BG
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = str(val)
            p.font.size = Pt(font_size)
            p.font.color.rgb = SLATE
            if c_idx == 0:
                p.font.bold = True
                p.font.color.rgb = NAVY
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
    return shape


# ==============================================================================
# SLIDE 1: FIRST SLIDE (Title)
# ==============================================================================
s1 = prs.slides.add_slide(BLANK)
set_bg(s1, NAVY)
bar1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.28), Inches(7.5))
bar1.fill.solid()
bar1.fill.fore_color.rgb = CYAN
bar1.line.fill.background()

tb = s1.shapes.add_textbox(Inches(1.0), Inches(1.3), Inches(11.3), Inches(1.6))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "ArchSynth v2.2"
p.font.size = Pt(46)
p.font.bold = True
p.font.color.rgb = CYAN
p2 = tf.add_paragraph()
p2.text = "Evidence-Grounded ROS 2 Architecture Recovery & Auto-Documentation"
p2.font.size = Pt(28)
p2.font.bold = True
p2.font.color.rgb = WHITE

tb_sub = s1.shapes.add_textbox(Inches(1.0), Inches(3.6), Inches(11.0), Inches(2.5))
tfs = tb_sub.text_frame
tfs.word_wrap = True
for idx, line in enumerate([
    "M.Tech Dissertation Review — Automation & Robotics",
    "Presenter: Aman Singh",
    "Department of Robotics & Autonomous Systems",
    "Defence Institute of Advanced Technology (DIAT), Pune",
    "Review Package: v2.2 Recalculated Benchmarks & Live Mode B Validation",
]):
    ps = tfs.paragraphs[0] if idx == 0 else tfs.add_paragraph()
    ps.text = line
    ps.font.size = Pt(18 if idx == 0 else 15)
    ps.font.bold = (idx == 0)
    ps.font.color.rgb = WHITE if idx < 2 else RGBColor(203, 213, 225)
    ps.space_after = Pt(6)

# ==============================================================================
# SLIDE 2: CONTENT (Agenda)
# ==============================================================================
s2 = prs.slides.add_slide(BLANK)
add_header(s2, "Presentation Outline", "Content", 2)
add_card(s2, 0.7, 1.45, 5.8, 5.3, "Part I — Foundation & Design", [
    ("1. Introduction", "ROS 2 complexity, architectural drift, and problem statement"),
    ("2. Literature Review", "ROS static analyzers, standards (ISO 42010 / C4), and LLMs"),
    ("3. Research Gap", "Why existing static tools and unconstrained LLMs fall short"),
    ("4. Objectives", "Five measurable goals for evidence-grounded recovery"),
    ("5. Methodology", "5-stage pipeline, AST/launch/comm recovery, GT protocol"),
], accent=DARK_BLUE)
add_card(s2, 6.8, 1.45, 5.8, 5.3, "Part II — Evaluation & Closure", [
    ("6. Results", "6-repository cross-evaluation, GT accuracy, ablation & Mode B"),
    ("7. Publications", "Current status & target publication venues"),
    ("8. Conclusion & Future Work", "Key contributions, limitations, and next milestones"),
    ("9. References", "Primary academic & standards bibliography"),
    ("10. Thank You", "Q&A and live demonstration readiness"),
], accent=TEAL)

# ==============================================================================
# SLIDE 3: INTRODUCTION (Motivation)
# ==============================================================================
s3 = prs.slides.add_slide(BLANK)
add_header(s3, "Introduction: The Architectural Drift Crisis in ROS 2", "Introduction", 3)
add_bullets(s3, 0.7, 1.4, 11.9, 2.3, [
    ("Distributed Robotics Complexity", "Modern ROS 2 stacks (e.g., Navigation2) span 40+ packages, C++ & Python nodes, XML Behavior Trees, YAML configs, and hierarchical launch files."),
    ("Architectural Drift", "Manual diagrams (draw.io, PPT) become outdated within weeks of code commits, creating safety and onboarding risks."),
    ("Hidden Runtime Wiring", "In ROS 2, actual topic/service/action names depend on launch namespaces, remappings, ComposableNodeContainers, and pluginlib XML manifests."),
    ("Lack of System-Level Manuals", "Code comments explain functions, but teams lack verified end-to-end architecture blueprints."),
], font_size=16, space_after=10)
add_card(s3, 0.7, 4.3, 3.8, 2.4, "Code Reality", [
    "C++ rclcpp & LifecycleNode",
    "Python rclpy AST & console_scripts",
    "Launch substitutions & containers",
    "YAML params & pluginlib XML",
], accent=DARK_BLUE)
add_card(s3, 4.75, 4.3, 3.8, 2.4, "Manual Pain Points", [
    "Months to onboard engineers",
    "Stale hand-drawn diagrams",
    "Hidden external dependencies",
    "Hard to audit for safety/defense",
], accent=AMBER)
add_card(s3, 8.8, 4.3, 3.8, 2.4, "ArchSynth Solution", [
    "Automated static X-ray of repo",
    "100% file:line evidence proof",
    "8 ISO/IEC/IEEE 42010 views",
    "Schema-constrained AI narratives",
], accent=TEAL)

# ==============================================================================
# SLIDE 4: INTRODUCTION (What Is ArchSynth?)
# ==============================================================================
s4 = prs.slides.add_slide(BLANK)
add_header(s4, "Introduction: What ArchSynth Does", "Introduction", 4)
add_card(s4, 0.7, 1.45, 5.8, 5.2, "Inputs & Core Principle", [
    ("Input", "Any local or GitHub ROS 2 repository (C++ / Python / XML / YAML)."),
    ("No Build Required", "Analyzes source, CMakeLists.txt, package.xml, setup.py, and launch files statically."),
    ("ROS 2 Gatekeeping", "Verifies repository identity and rejects non-ROS codebases (e.g., Express.js)."),
    ("Deterministic First", "Extracts every entity with exact file:line evidence before any LLM runs."),
], accent=NAVY)
add_card(s4, 6.8, 1.45, 5.8, 5.2, "Recovered Outputs", [
    ("Structured Inventory", "Production vs. test nodes, executables, composable & pluginlib components."),
    ("Communication Graph", "Source-declared, API-inferred, YAML-configured, and launch-resolved edges."),
    ("Architectural Models", "Subsystems, Lifecycle graphs, Plugins, Behavior Trees, Package Dependencies."),
    ("Standards Docs & UI", "8 ISO/IEC/IEEE 42010 Mermaid views, README.md, and Flask dashboard."),
], accent=TEAL)

# ==============================================================================
# SLIDE 5: LITERATURE REVIEW (ROS 2 & Static Analysis)
# ==============================================================================
s5 = prs.slides.add_slide(BLANK)
add_header(s5, "Literature Review: ROS 2 & Robotics Static Analysis", "Literature Review", 5)
add_table(s5, 0.6, 1.45, 12.1, 5.1,
    ["Study / Standard", "Focus Area", "Key Contribution", "Limitation for Our Goal"],
    [
        ["Quigley et al. (2009)", "ROS 1 Architecture", "Publish-subscribe computation graph", "No lifecycle, DDS QoS, or launch AST"],
        ["Macenski et al. (2022)", "ROS 2 Design", "DDS middleware, LifecycleNodes, components", "Design spec; no automated recovery tool"],
        ["Macenski et al. (2020)", "Navigation2", "BT orchestration, costmap/planner plugins", "Complex multi-package reference target"],
        ["Santos et al. (2016)", "HAROS", "Static quality & model extraction for ROS 1", "ROS 1 only; lacks ROS 2 launch/BT/LLM views"],
        ["Benchat et al. (2026)", "ROS 2 Comm Graphs", "Static recovery of ROS 2 communication", "Flat node-topic graphs; no ISO 42010 views"],
        ["Briechle et al. (2026)", "Launch Extraction", "Deployment models from launch scripts", "Isolated deployment view; no subsystem synthesis"],
    ], font_size=12)

# ==============================================================================
# SLIDE 6: LITERATURE REVIEW (Architecture, Clustering & LLMs)
# ==============================================================================
s6 = prs.slides.add_slide(BLANK)
add_header(s6, "Literature Review: Architecture Standards, Clustering & LLMs", "Literature Review", 6)
add_table(s6, 0.6, 1.45, 12.1, 5.1,
    ["Study / Standard", "Focus Area", "Key Contribution", "Relevance to ArchSynth"],
    [
        ["Ducasse & Pollet (2009)", "Arch Reconstruction", "Process taxonomy for reverse engineering", "Guides bottom-up AST -> architectural views"],
        ["ISO/IEC/IEEE 42010:2011", "Arch Description", "Multi-viewpoint stakeholder documentation", "Defines our 8 standardized architectural views"],
        ["Brown (2018)", "C4 Model", "Context, Container, Component, Code hierarchy", "Structures C4-aligned Markdown & diagrams"],
        ["Newman (2006) / Blondel (2008)", "Graph Modularity", "Community detection & cohesion/coupling", "Basis for explainable subsystem clustering"],
        ["De Luca et al. (2024) — CIAO", "LLM Arch Docs", "Generates architecture prose using LLMs", "Treats code as text -> >8% hallucination rate"],
        ["Hou et al. (2024)", "LLMs for SE", "Survey of LLM strengths & hallucination risks", "Motivates Pydantic schema-constrained synthesis"],
    ], font_size=12)

# ==============================================================================
# SLIDE 7: RESEARCH GAP
# ==============================================================================
s7 = prs.slides.add_slide(BLANK)
add_header(s7, "Research Gap: Static Extractors vs. Generative LLMs", "Research Gap", 7)
add_table(s7, 0.6, 1.45, 12.1, 3.6,
    ["Capability", "ROS Static Analyzers", "Unconstrained LLMs (e.g., CIAO)", "ArchSynth v2.2 (Ours)"],
    [
        ["C++ & Python ROS 2 AST + Build Parsing", "Partial / ROS 1 or C++ only", "No (generic text window)", "Yes (Python AST + C++ + CMake/XML/YAML)"],
        ["Hierarchical Launch & Namespace Resolution", "Limited", "No (misses launch remappings)", "Yes (lexical-scoped GroupAction + containers)"],
        ["Source-Grounded Citations (file:line)", "Yes", "No (>8% hallucinated entities)", "Yes (100% Evidence Coverage, 0% unsupported)"],
        ["Subsystem, Lifecycle, Plugin & BT Views", "No (flat graphs)", "Unverified prose", "Yes (8 data-driven ISO/IEC/IEEE 42010 views)"],
        ["Offline / Air-Gapped Determinism", "Yes", "No (cloud API dependent)", "Yes (skip_llm=True + local Ollama fallback)"],
    ], font_size=12)
add_card(s7, 0.6, 5.3, 12.1, 1.5, "Core Gap Statement", [
    "No existing system unifies domain-specific ROS 2 AST + launch + YAML extraction with schema-constrained synthesis to guarantee 0% unsupported entities and measurable precision/recall against verified ground truth."
], accent=DARK_BLUE)

# ==============================================================================
# SLIDE 8: OBJECTIVE
# ==============================================================================
s8 = prs.slides.add_slide(BLANK)
add_header(s8, "Research Objectives", "Objective", 8)
add_bullets(s8, 0.7, 1.45, 11.9, 5.4, [
    ("Objective 1 — Multi-Language & Build Recovery", "Accurately discover C++ & Python ROS 2 nodes (subclasses, functional create_node, components), executables, and categorized package dependencies."),
    ("Objective 2 — Hierarchical Launch & Interface Resolution", "Resolve launch namespaces, remappings, MoveIt/YAML controller configs, and tf2_ros transforms while explicitly flagging dynamic/unresolved constructs."),
    ("Objective 3 — Zero-Hallucination Evidence Grounding", "Attach verifiable file:line citations to every recovered entity (100% evidence coverage) and enforce Pydantic v2 schemas on LLM synthesis (0% unsupported entities)."),
    ("Objective 4 — Standards-Based Multi-View Synthesis", "Recover explainable subsystems, lifecycle state machines, plugin architectures, Behavior Trees, and 8 data-driven ISO/IEC/IEEE 42010 views."),
    ("Objective 5 — Reproducible Cross-Repository Validation", "Benchmark precision, recall, F1, ARI/NMI, and ablation (Mode A vs. Mode B) against manually verified ground-truth datasets and a non-ROS negative control."),
], font_size=15, space_after=12)

# ==============================================================================
# SLIDE 9: METHODOLOGY — PIPELINE OVERVIEW
# ==============================================================================
s9 = prs.slides.add_slide(BLANK)
add_header(s9, "Methodology: 5-Stage ArchSynth Architecture", "Methodology (1/6)", 9)
stages = [
    ("Stage 1\nIngest & Gate", "Git identity,\nROS 2 check,\nprovenance", NAVY),
    ("Stage 2\nNode & Build", "Python AST, C++,\nCMake, pkg.xml,\nsetup.py", DARK_BLUE),
    ("Stage 3\nLaunch Tree", "Lexical scope,\nGroupAction,\ncontainers", RGBColor(3, 105, 161)),
    ("Phase 3\nInterfaces", "Topics, services,\nactions, TF,\ncomm graph", TEAL),
    ("Phase 4 / Stg 4\nSynthesis", "Subsystems, LC,\nPlugins, BT,\n8 ISO Views", RGBColor(21, 128, 61)),
    ("Stage 5\nValidation/Docs", "EvidenceValidator,\nREADME.md,\nFlask UI", SLATE),
]
x = 0.55
for idx, (st_title, st_body, col) in enumerate(stages):
    box = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(1.8), Inches(1.92), Inches(2.5))
    box.fill.solid()
    box.fill.fore_color.rgb = col
    box.line.fill.background()
    tb = s9.shapes.add_textbox(Inches(x + 0.08), Inches(1.95), Inches(1.76), Inches(2.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = st_title
    p1.font.size = Pt(14)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.alignment = PP_ALIGN.CENTER
    p1.space_after = Pt(10)
    p2 = tf.add_paragraph()
    p2.text = st_body
    p2.font.size = Pt(12)
    p2.font.color.rgb = RGBColor(226, 232, 240)
    p2.alignment = PP_ALIGN.CENTER
    if idx < len(stages) - 1:
        arr = s9.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 1.96), Inches(2.9), Inches(0.14), Inches(0.28))
        arr.fill.solid()
        arr.fill.fore_color.rgb = CYAN
        arr.line.fill.background()
    x += 2.08

add_card(s9, 0.55, 4.7, 12.2, 2.0, "Strict Provenance & Mode Separation", [
    ("Artifact Isolation", "Every intermediate JSON (nodes.json, launches.json, interfaces.json, architecture.json) carries commit SHA & repository provenance sidecars."),
    ("Two Execution Modes", "Mode A (skip_llm=True, 100% deterministic) vs. Mode B (skip_llm=False, live Gemini/Ollama constrained by Pydantic v2 schemas)."),
], accent=NAVY)

# ==============================================================================
# SLIDE 10: METHODOLOGY — STAGES 1 & 2
# ==============================================================================
s10 = prs.slides.add_slide(BLANK)
add_header(s10, "Methodology: Ingestion & Multi-Language Node Discovery", "Methodology (2/6)", 10)
add_card(s10, 0.7, 1.45, 5.8, 5.2, "Stage 1: Ingestion & Provenance (src/ingestor.py)", [
    ("ROS 2 Validation Gate", "Requires ROS 2 markers (package.xml, rclcpp/rclpy); rejects Express.js (0 entities)."),
    ("Commit Pinning", "Verifies exact Git URL, branch, and commit SHA via repo_identity.py."),
    ("Cross-Repo Isolation", "Rejects stale or mismatched artifacts via .provenance.json."),
], accent=NAVY)
add_card(s10, 6.8, 1.45, 5.8, 5.2, "Stage 2: Node Discovery (node_analyzer & cpp_analyzer)", [
    ("Python AST", "Detects Node subclasses + functional rclpy.create_node / rclcpp.Node + setup.py console_scripts."),
    ("C++ Analyzer", "Parses rclcpp::Node, LifecycleNode, make_shared, and RCLCPP_COMPONENTS_REGISTER_NODE."),
    ("v2.2 Accuracy Fixes", "Excludes anonymous '_' helper nodes; CamelCase->snake_case fallback for empty C++ node names (e.g., controller_manager, base_footprint_publisher)."),
    ("Test Separation", "Tags test/mock nodes (is_test=True) separately from production nodes."),
], accent=DARK_BLUE)

# ==============================================================================
# SLIDE 11: METHODOLOGY — STAGE 3
# ==============================================================================
s11 = prs.slides.add_slide(BLANK)
add_header(s11, "Methodology: Launch Resolution & Package Dependencies", "Methodology (3/6)", 11)
add_card(s11, 0.7, 1.45, 5.8, 5.2, "Stage 3: LaunchAnalyzer (src/launch_analyzer.py)", [
    ("Lexical-Order Traversal", "Replaced unordered ast.walk with deterministic source-order scoped traversal."),
    ("Namespace Isolation", "Clones context per FunctionDef so GroupAction / PushRosNamespace never leaks."),
    ("Containers & Profiles", "Tracks ComposableNodeContainer + LoadComposableNodes across deployment profiles."),
    ("Honest Uncertainty", "Logs OpaqueFunction, ExecuteProcess, RegisterEventHandler in unresolved_expressions."),
], accent=DARK_BLUE)
add_card(s11, 6.8, 1.45, 5.8, 5.2, "Build & Package Dependencies (src/build_analyzer.py)", [
    ("Manifest Parsing", "Extracts declared build/exec/test dependencies from package.xml and setup.py."),
    ("Source Scanning", "Extracts #include and Python imports from source files with file:line citations."),
    ("4-Way Categorization", "resolved_internal_package | resolved_ros_package | manifest_declared_external | unresolved_external_library."),
    ("Consistency Flag", "Surfaces undeclared source dependencies as 'Potential inconsistency' findings."),
], accent=TEAL)

# ==============================================================================
# SLIDE 12: METHODOLOGY — PHASE 3 INTERFACES
# ==============================================================================
s12 = prs.slides.add_slide(BLANK)
add_header(s12, "Methodology: Typed Interface & Communication Recovery", "Methodology (4/6)", 12)
add_card(s12, 0.7, 1.45, 5.8, 5.2, "InterfaceExtractor (src/interface_extractor.py)", [
    ("Python AST", "Supports both positional & keyword args (e.g., msg_type=..., topic=... in JACO2 jsp_gui_controller.py)."),
    ("C++ Patterns", "Skips shared_from_this() / node / this / get_node_base_interface() first args cleanly."),
    ("TF2 Support", "Extracts tf2_ros & nav2::create_transform_broadcaster (/tf, /tf_static) and TransformListener."),
    ("Claim Separation", "Distinguishes source_declared vs. api_inferred (MoveItPy/MTC) vs. config_declared (YAML)."),
], accent=TEAL)
add_card(s12, 6.8, 1.45, 5.8, 5.2, "CommunicationBuilder (src/communication_builder.py)", [
    ("Producer-Consumer Matching", "Links publishers<->subscribers, service clients<->servers, action clients<->servers."),
    ("Source vs. Deployment", "Separates source_potential_edges from launch-filtered deployment_runtime_edges."),
    ("External Endpoints", "Explicitly tracks unmatched/external ROS 2 endpoints (e.g., move_group, ros2_control)."),
    ("Runtime Honesty", "runtime_observation_available=False unless live ROS 2 DDS introspection is run."),
], accent=NAVY)

# ==============================================================================
# SLIDE 13: METHODOLOGY — PHASE 4 SYNTHESIS & VALIDATION
# ==============================================================================
s13 = prs.slides.add_slide(BLANK)
add_header(s13, "Methodology: Subsystems, ISO 42010 Views & Reconciliation", "Methodology (5/6)", 13)
add_card(s13, 0.7, 1.45, 5.8, 5.2, "Subsystem & Specialized Analyzers", [
    ("Generic Role Clustering", "Separates RViz/UI panels (visualization_operator_ui), map tools, localization, planning, control, supervision, client APIs, and tests."),
    ("Bounded Metrics", "Cohesion = E_internal / (N*(N-1)) in [0,1] (N/A for N<2); reports coupling_internal & coupling_external."),
    ("Lifecycle, Plugins & BT", "Recovers ManagedNode states, pluginlib manifests, and BehaviorTree.CPP leaf-to-server bindings."),
], accent=DARK_BLUE)
add_card(s13, 6.8, 1.45, 5.8, 5.2, "Data-Driven Views & Inventory Reconciliation", [
    ("Zero Hardcoded Diagrams", "All 8 ISO/IEC/IEEE 42010 views in view_generator.py derive directly from ArchitectureModel."),
    ("Non-Overlapping Inventory", "Case-insensitive deduplication links C++ AST nodes with pluginlib XML entries (no double-counting)."),
    ("Internal vs. External", "Separates internal unmapped launch instances from true external ROS 2 nodes."),
], accent=TEAL)

# ==============================================================================
# SLIDE 14: METHODOLOGY — EVALUATION & GROUND TRUTH PROTOCOL
# ==============================================================================
s14 = prs.slides.add_slide(BLANK)
add_header(s14, "Methodology: Benchmark & Ground-Truth Protocol", "Methodology (6/6)", 14)
add_card(s14, 0.7, 1.45, 5.8, 5.2, "Verified Ground-Truth Datasets (eval/ground_truth/)", [
    ("Navigation2", "Official Nav2 docs + source headers: 13 core nodes, 22 extended, 15 topics, 6/8 services, 14 actions, 13-node subsystems."),
    ("Kinova JACO2 Devkit", "Full manual audit of 11 packages: 11 nodes, 9 qualified (8 basename) topics, 3 services, 3 API actions, 2 YAML actions."),
    ("SLAM Toolbox (v2.2)", "Manual C++ audit: 4 unique runtime names (10 classes), 14 topics, 14 services, 0 actions."),
    ("ROS 2 Control (v2.2)", "Manual audit of controller_manager.cpp: 1 prod node, 2 prod topics, 11 prod services."),
], accent=NAVY)
add_card(s14, 6.8, 1.45, 5.8, 5.2, "Metrics & Invariants (eval/run_v22_benchmark.py)", [
    ("Canonical Basename Matching", "Strip '/', split '::' and '/', lowercase; deduplicate into sets; production-node interfaces only."),
    ("Strict Invariants", "Automatically asserts TP + FN = GT and TP + FP = Predicted for every single row."),
    ("P / R / F1", "Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2PR/(P+R); 0/0 -> 1.0; missing GT -> N/A."),
    ("Traceability != Recall", "Evidence Coverage measures file:line proof (100%); Precision/Recall measure accuracy vs. GT."),
], accent=TEAL)

# ==============================================================================
# SLIDE 15: RESULTS — CROSS-REPOSITORY SUMMARY
# ==============================================================================
s15 = prs.slides.add_slide(BLANK)
add_header(s15, "Results: Cross-Repository Architecture Recovery (6 Targets)", "Results (1/3)", 15)
add_table(s15, 0.5, 1.45, 12.3, 4.3,
    ["Repository", "Commit (Short)", "Prod / Test Nodes", "Launches / Inst.", "Source Ifaces", "Subsystems", "Evidence Cov.", "Time (s)", "Status"],
    [
        ["Navigation2", "6dbf4549", "28 / 47", "41 / 120", "288", "11", "100.0%", "16.197", "GT Evaluated"],
        ["SLAM Toolbox", "eee0cd5e", "10 / 0", "7 / 7", "61", "3", "100.0%", "3.712", "GT Evaluated"],
        ["ROS 2 Control", "4052b56d", "1 / 5", "1 / 1", "14", "2", "100.0%", "5.855", "GT Evaluated"],
        ["Kinova JACO2", "993a6e3d", "11 / 0", "12 / 38", "24", "6", "100.0%", "2.030", "GT Evaluated"],
        ["BehaviorTree.CPP", "365b2e49", "2 / 0", "0 / 0", "0", "1", "100.0%", "7.108", "No GT (N/A)"],
        ["Express.js (Neg. Ctrl)", "a3714473", "0 / 0", "0 / 0", "0", "0", "N/A (0/0)", "1.415", "Rejected (True)"],
    ], font_size=11)
add_card(s15, 0.5, 5.95, 12.3, 0.95, "Key Observation", [
    "All 5 ROS/C++ targets achieve 100.0% Evidence Coverage (0.0% unsupported entities); Express.js is cleanly rejected with 0 false ROS 2 entities."
], accent=TEAL)

# ==============================================================================
# SLIDE 16: RESULTS — GROUND-TRUTH EXTRACTION ACCURACY
# ==============================================================================
s16 = prs.slides.add_slide(BLANK)
add_header(s16, "Results: Ground-Truth Precision, Recall & F1 (v2.2 Updated)", "Results (2/3)", 16)
add_table(s16, 0.5, 1.38, 12.3, 4.4,
    ["Repository", "Category", "GT", "Pred", "TP", "FP", "FN", "Precision", "Recall", "F1"],
    [
        ["Nav2", "nodes_core (all 44 pkgs)", "13", "28", "13", "15", "0", "0.4643", "1.0000", "0.6341"],
        ["Nav2", "nodes_core_pkg_scoped", "13", "17", "13", "4", "0", "0.7647", "1.0000", "0.8667"],
        ["Nav2", "nodes_extended", "22", "28", "21", "7", "1", "0.7500", "0.9545", "0.8400"],
        ["Nav2", "topics / services (prod)", "15 / 6", "40 / 26", "10 / 6", "30 / 20", "5 / 0", "0.2500 / 0.2308", "0.6667 / 1.0000", "0.3636 / 0.3750"],
        ["Nav2", "actions (prod)", "14", "17", "13", "4", "1", "0.7647", "0.9286", "0.8387"],
        ["SLAM Toolbox", "nodes / topics / services", "4 / 14 / 14", "4 / 14 / 14", "4 / 14 / 14", "0", "0", "1.0000", "1.0000", "1.0000"],
        ["ROS 2 Control", "nodes / topics / services", "1 / 2 / 11", "1 / 2 / 11", "1 / 2 / 11", "0", "0", "1.0000", "1.0000", "1.0000"],
        ["Kinova JACO2", "nodes / topics / svcs / api_act / yaml", "11 / 8 / 3 / 3 / 2", "11 / 8 / 3 / 3 / 2", "all matched", "0", "0", "1.0000", "1.0000", "1.0000"],
    ], font_size=11)
add_card(s16, 0.5, 5.92, 12.3, 1.0, "Why Nav2 Full-Repo Precision Looks Lower Than Core Recall (1.0000)", [
    "Nav2 GT covers only a 13-node / 15-topic / 6-service bringup subset, while ArchSynth extracts all 44 Nav2 packages (28 prod nodes, 40 prod topics). Package-scoped core F1 is 0.8667 and extended F1 is 0.8400; Subsystem NMI = 0.8186 (ARI = 0.2632, Jaccard = 0.700)."
], accent=DARK_BLUE)

# ==============================================================================
# SLIDE 17: RESULTS — ABLATION & LIVE MODE B COMPARISON
# ==============================================================================
s17 = prs.slides.add_slide(BLANK)
add_header(s17, "Results: Staged Ablation & Mode A vs. Live Gemini Mode B", "Results (3/3)", 17)
add_table(s17, 0.5, 1.38, 12.3, 4.3,
    ["Configuration", "Nav2 Node F1", "Nav2 Topic F1", "Nav2 Action F1", "JACO2 Node / Topic / Act F1", "Evidence Cov.", "Unsupported Rate", "Time (Nav2 / JACO2)"],
    [
        ["A: Static Regex-only", "0.0000", "0.1322", "0.0000", "0.1000 / 1.0000 / 0.0000", "0.0%", "N/A", "0.596s / 0.039s"],
        ["B: Multi-language AST (Ph 1)", "0.6341", "0.0000", "0.0000", "1.0000 / 0.0000 / 0.0000", "100.0%", "0.0%", "3.799s / 0.195s"],
        ["C: Static + Launch (Ph 1+2)", "0.3662", "0.0000", "0.0000", "0.5946 / 0.0000 / 0.0000", "100.0%", "0.0%", "6.585s / 0.698s"],
        ["D: + Comm Graph (Ph 1-3)", "0.6341", "0.3636", "0.8387", "1.0000 / 1.0000 / 1.0000", "100.0%", "0.0%", "8.269s / 0.806s"],
        ["E: Mode A (skip_llm=True)", "0.6341", "0.3636", "0.8387", "1.0000 / 1.0000 / 1.0000", "100.0%", "0.0%", "16.197s / 2.030s"],
        ["E-LLM: Mode B (Live Gemini)", "0.6341", "0.3636", "0.8387", "1.0000 / 1.0000 / 1.0000", "100.0%", "0.0%", "28.559s / 19.645s"],
    ], font_size=11)
add_card(s17, 0.5, 5.85, 12.3, 1.05, "Verification & Test Suite", [
    "Mode B (Live Gemini + Pydantic schema) enriches System Context documentation with 0.0% unsupported entities across Nav2, SLAM Toolbox, ROS 2 Control, and JACO2. Automated suite: 109 / 109 unittest tests passing (18.469s)."
], accent=TEAL)

# ==============================================================================
# SLIDE 18: PUBLICATIONS (IF ANY)
# ==============================================================================
s18 = prs.slides.add_slide(BLANK)
add_header(s18, "Publications & Research Outputs", "Publications", 18)
add_card(s18, 0.7, 1.5, 11.9, 2.3, "Publication Status", [
    ("Current Status", "No peer-reviewed journal or conference paper has been published yet."),
    ("Thesis Deliverable", "Complete M.Tech Dissertation & Reproducible Research Package (DIAT Pune) with pinned commits, ground-truth datasets, and 109 automated tests."),
], accent=NAVY)
add_card(s18, 0.7, 4.1, 11.9, 2.5, "Planned Manuscript Submission", [
    ("Working Title", "ArchSynth: Evidence-Grounded Architecture Recovery and ISO/IEC/IEEE 42010 Documentation for ROS 2 Systems"),
    ("Target Venues", "IEEE International Conference on Software Architecture (ICSA) / Journal of Systems and Software (JSS) / IEEE IROS"),
    ("Key Empirical Artifacts Ready", "Dual-mode (Mode A vs. Live Mode B) ablation data, 4 verified ROS 2 ground-truth benchmarks, and non-ROS negative control."),
], accent=TEAL)

# ==============================================================================
# SLIDE 19: CONCLUSION & FUTURE WORK
# ==============================================================================
s19 = prs.slides.add_slide(BLANK)
add_header(s19, "Conclusion & Future Work", "Conclusion & Future Work", 19)
add_card(s19, 0.7, 1.45, 5.8, 5.2, "Conclusions", [
    ("Accurate Static Recovery", "F1 = 1.000 on JACO2, SLAM Toolbox, and ROS 2 Control; 0.8667 pkg-scoped / 0.8400 extended on Nav2."),
    ("Zero Hallucination", "100% file:line evidence coverage & 0.0% unsupported entity rate in both Mode A and Live Gemini Mode B."),
    ("Strict Scientific Hygiene", "No fabricated GT scores (BehaviorTree.CPP = N/A), 100% Express.js rejection, 109/109 tests passing."),
    ("Production-Ready Deliverables", "Interactive Flask UI, GitHub-clean repo, Vercel config, and reproducible benchmark scripts."),
], accent=NAVY)
add_card(s19, 6.8, 1.45, 5.8, 5.2, "Future Work", [
    ("Live ROS 2 Runtime Validation", "Execute Nav2, SLAM Toolbox, and JACO2 in Ubuntu/Docker ROS 2 Jazzy to compare static edges vs. live DDS graphs via runtime_validator.py."),
    ("Expand Nav2 Ground Truth", "Curate full 44-package Nav2 topic/service ground truth to eliminate scope mismatch in Precision."),
    ("Cluster Partition Benchmarks", "Add independent subsystem cluster ground truth for SLAM Toolbox and ROS 2 Control."),
    ("Language & Tooling Extensions", "Add Clang AST bindings for complex C++ macro/template topic resolution and CI/CD drift alerts."),
], accent=TEAL)

# ==============================================================================
# SLIDE 20: REFERENCE
# ==============================================================================
s20 = prs.slides.add_slide(BLANK)
add_header(s20, "References", "Reference", 20)
add_bullets(s20, 0.7, 1.35, 11.9, 5.5, [
    "Macenski, S., Foote, T., Gerkey, B., Lalancette, C., & Woodall, W. (2022). Robot Operating System 2: Design, architecture, and uses in the wild. Science Robotics, 7(66), eabm6074.",
    "Quigley, M., Conley, K., Gerkey, B., et al. (2009). ROS: an open-source Robot Operating System. ICRA Workshop on Open Source Software, 3(3.2), 5.",
    "Macenski, S., Martin, F., White, R., & Gines Clavero, J. (2020). The Marathon 2: A Navigation System. IEEE Transactions on Robotics, 36(6), 1804-1819.",
    "Ducasse, S., & Pollet, D. (2009). Software architecture reconstruction: A process-oriented taxonomy. IEEE Transactions on Software Engineering, 35(4), 573-591.",
    "ISO/IEC/IEEE 42010:2011. Systems and software engineering — Architecture description.",
    "Brown, S. (2018). Visualising software architecture with the C4 model. Leanpub.",
    "Santos, A., Santos, C., & Silva, V. (2016). HAROS: A framework for static analysis of ROS code. IEEE/RSJ IROS, 3656-3661.",
    "Benchat, S., Malavolta, I., & Lago, P. (2026). Static recovery of communication graphs in ROS 2 systems. Journal of Systems and Software.",
    "Briechle, K., Wimmer, M., & Kresse, I. (2026). Extracting deployment architectures from robotics launch scripts. IEEE ICSA.",
    "De Luca, C., Zampetti, F., Di Sorbo, A., & Canfora, G. (2024). CIAO: Generating software architecture documentation using LLMs. IEEE/ACM ASE, 112-124.",
    "Newman, M. E. (2006). Modularity and community structure in networks. PNAS, 103(23), 8577-8582.",
], font_size=12, space_after=6)

# ==============================================================================
# SLIDE 21: THANK YOU
# ==============================================================================
s21 = prs.slides.add_slide(BLANK)
set_bg(s21, NAVY)
bar21 = s21.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.28), Inches(7.5))
bar21.fill.solid()
bar21.fill.fore_color.rgb = CYAN
bar21.line.fill.background()

tb_ty = s21.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(1.4))
p_ty = tb_ty.text_frame.paragraphs[0]
p_ty.text = "Thank You"
p_ty.font.size = Pt(52)
p_ty.font.bold = True
p_ty.font.color.rgb = CYAN
p_ty.alignment = PP_ALIGN.CENTER

tb_q = s21.shapes.add_textbox(Inches(1.0), Inches(3.7), Inches(11.3), Inches(1.5))
tfq = tb_q.text_frame
pq1 = tfq.paragraphs[0]
pq1.text = "Questions & Discussion"
pq1.font.size = Pt(24)
pq1.font.bold = True
pq1.font.color.rgb = WHITE
pq1.alignment = PP_ALIGN.CENTER
pq1.space_after = Pt(14)

pq2 = tfq.add_paragraph()
pq2.text = "Aman Singh  |  M.Tech (Automation & Robotics)  |  DIAT Pune\nRepository: github.com/amanxsingh/ArchSynth"
pq2.font.size = Pt(15)
pq2.font.color.rgb = RGBColor(203, 213, 225)
pq2.alignment = PP_ALIGN.CENTER

prs.save(str(PPTX_PATH))
print(f"Saved {len(prs.slides)} slides to {PPTX_PATH}")
