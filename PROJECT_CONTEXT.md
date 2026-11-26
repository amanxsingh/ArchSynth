# ArchSynth — Project Context & Build Guide

> **Keep this file at the root of your repository.** It's written so you can paste
> relevant sections into GitHub Copilot Chat as context, and so you (or anyone else)
> can understand the whole project without re-reading months of notes.

---

## 1. What is this project, in one paragraph

ArchSynth is a tool that automatically reads a ROS2 robot's source code and launch
files, and reconstructs (a) a diagram of its true software architecture — which
nodes exist, what topics/services connect them, how launch files compose them
hierarchically — and (b) human-readable, standards-based developer documentation
describing that architecture. It uses LLM agents (via API calls, orchestrated by
your own Python code) to do the reading and synthesis. The point is that ROS2
codebases almost never have accurate, up-to-date architecture documentation, and
this tool generates it automatically, on demand, from the code itself.

This is an M.Tech dissertation project (Automation & Robotics, DIAT) that is
fundamentally a **software engineering research tool** — no physical robot, no
simulator required to build or evaluate it.

---

## 2. Why this project — the research gap (condensed)

Two separate lines of published research (2026) exist, and nobody has combined them:

1. **ROS2-aware architecture *recovery*** (Benchat et al., arXiv:2602.18644;
   Briechle et al., arXiv:2605.20055) — LLM agents that read ROS2 source + launch
   files and reconstruct a hierarchical architecture *diagram* (nodes, topics,
   launch composition, namespaces). They stop at the diagram/model — no polished,
   standards-based documentation output, and accuracy still drops on complex
   launch-file composition.
2. **General-purpose architecture *documentation* generation** (CIAO — De Luca et
   al., arXiv:2604.08293, accepted ICSA 2026) — LLM pipeline that turns *any*
   GitHub repo into structured documentation (ISO/IEC/IEEE 42010, SEI Views &
   Beyond, C4 model), evaluated with 22 real developers. It has **no concept of
   ROS2** — no launch files, no nodes/topics, no namespace remapping.

**The gap ArchSynth fills:** combine ROS2-aware hierarchical recovery (line 1)
with structured, standards-based, developer-evaluated documentation generation
(line 2) — something neither line of work does. That is the dissertation's
citable, defensible novel contribution.

Full literature list, evaluation methodology references, and the formal proposal
are in `docs/dissertation_proposal.docx` and `docs/lit_review_log.xlsx` (build
these as you go — see Section 6).

---

## 3. Scope for THIS project (the achievable, part-time version)

Deliberately **not** in scope (would need way more time/hardware):
- ❌ No Gazebo/RViz simulation
- ❌ No Nav2 / MoveIt2 / physical robot
- ❌ No Kubernetes/Docker orchestration
- ❌ No live runtime tracing (`ros2_tracing`/`rosbag2`) — that's a stretch goal /
  future-work item, not part of the core deliverable
- ❌ No reinforcement learning, no computer vision

**In scope — the actual pipeline you're building:**
1. Clone a target open-source ROS2 repository at a fixed commit.
2. **NodeAnalyzer**: parse Python/C++ source → LLM call → structured JSON list of
   ROS2 nodes (name, class, publishers, subscribers, services, actions).
3. **LaunchFileAnalyzer**: parse launch files (Python launch / XML) → LLM call →
   JSON dependency graph (which launch files include which, what nodes they
   instantiate, under what namespace/remapping).
4. **SystemArchitectureConstructor**: combine steps 2+3 with an LLM call,
   constrained by a schema ("blueprint"), into a validated hierarchical
   architecture model (PlantUML or Mermaid).
5. **Documentation Generator**: convert the validated model into a structured,
   versioned Markdown doc (README-style, informed by CIAO's ISO 42010 / C4 model
   template) — **this is your key novel piece beyond existing papers.**
6. **Evaluation harness**: compare recovered architecture + generated docs against
   a hand-drawn ground truth (precision/recall/F1), and get 3-5 people (your
   guide, classmates, colleagues) to rate the documentation's usefulness.

---

## 4. Tech stack (exact tools — don't deviate, this is deliberately minimal)

| Layer | Tool |
|---|---|
| Language | Python 3.10+ |
| LLM access | Google Gemini API (free tier) **+** local Ollama (Qwen2.5-Coder / Llama-3) for cost control |
| Source parsing | Python `ast` module (source code), `xml.etree.ElementTree` + regex (launch files) |
| Diagramming | **Mermaid** (renders natively in GitHub Markdown) |
| Documentation output | Markdown, optionally rendered to a static site with MkDocs |
| Evaluation | Plain Python (`sklearn.metrics` or hand-rolled precision/recall/F1) |
| Version control | Git + GitHub (also hosts your benchmark release) |
| Case-study repo | **Navigation2 (nav2)** — https://github.com/ros-planning/navigation2 |

---

## 5. Suggested repository structure

```
archsynth/
├── PROJECT_CONTEXT.md          <- this file
├── README.md                   <- public-facing project description
├── docs/
│   ├── dissertation_proposal.docx
│   ├── lit_review_log.xlsx     <- your reading log (see prior guidance)
│   └── ground_truth/           <- hand-drawn reference architectures per repo
├── case_studies/
│   └── nav2/                   <- cloned target repo (as a submodule or .gitignored clone)
├── src/
│   ├── ingestor.py             <- Stage 1: clone/checkout target repo
│   ├── node_analyzer.py        <- Stage 2
│   ├── launch_analyzer.py      <- Stage 3
│   ├── architecture_constructor.py  <- Stage 4
│   ├── doc_generator.py        <- Stage 5
│   ├── llm_client.py           <- thin wrapper around your LLM API calls
│   └── schema.py               <- the "blueprint" JSON schema constraining LLM output
├── eval/
│   ├── metrics.py              <- precision/recall/F1 computation
│   └── run_eval.py             <- runs pipeline + scores against ground truth
├── tests/
│   └── ...                     <- unit tests for each stage (parsers especially)
├── requirements.txt
└── .env.example                <- API key placeholders (never commit real keys)
```

---

## 6. Build plan — what to actually do, in order

### Phase 0 (this week): Setup
- Create the repo with the structure above.
- Get API access sorted (Gemini API key + local Ollama with Qwen2.5-Coder).
- Pick your first case-study repo: **Navigation2 (nav2)** — clone at a pinned commit.
- Hand-draw (on paper or in draw.io) the ground-truth architecture of that repo's
  simplest package (e.g., `nav2_bt_navigator`) — this becomes your first scoring reference.

### Phase 1: Stage 2 — NodeAnalyzer
- Write `ingestor.py` to clone a repo at a pinned commit.
- Write `node_analyzer.py`: for each Python file, extract class definitions,
  imports, and any `rclpy.node.Node` subclasses using `ast`.
- Feed the extracted structural info (not raw file text, to save tokens) to the
  LLM with a prompt asking for structured JSON output (node name, publishers,
  subscribers, services).
- **Test on one file at a time before running on a whole package.**

### Phase 2: Stage 3 — LaunchFileAnalyzer
- Parse `.launch.py` and `.launch.xml` files.
- Extract: which nodes are instantiated, under what namespace, with what
  remappings, and which other launch files are `Include`d.
- Same JSON-output pattern as Stage 2.

### Phase 3: Stage 4 — SystemArchitectureConstructor
- Combine Stage 2 + Stage 3 JSON outputs.
- Define your "blueprint" schema first (Python `dataclass` or `pydantic` model) —
  this constrains what the LLM is allowed to output, reducing hallucination
  (this is the key trick from the Benchat/Briechle papers — copy this idea).
- LLM call synthesizes the final hierarchical model; output as Mermaid diagram
  syntax.

### Phase 4: Stage 5 — Documentation Generator
- Take the validated architecture model and generate a structured Markdown doc:
  overview, component list, communication diagram (embedded Mermaid), each
  node's responsibilities.
- Base the document's section structure on CIAO's template (ISO 42010 / C4-model
  inspired: Context → Containers/Components → Node-level detail).

### Phase 5: Evaluation
- Score Stage 2-4 output against your hand-drawn ground truth: precision, recall,
  F1 at node-level and subsystem-level (same metric definitions as Briechle et
  al. — makes your results directly comparable).
- Get 3-5 people to read the generated documentation and rate it (a short
  Likert-scale questionnaire: usefulness, accuracy, would-you-actually-use-this)
  — mirrors CIAO's 22-developer evaluation, just smaller-scale.
- Add a second, more complex case-study repo and repeat, to show generalization.

### Phase 6: Write-up
- Turn your reading log + results into the conference paper draft and dissertation
  chapters.

---

## 7. How to use GitHub Copilot effectively on this project

Paste the relevant section above into Copilot Chat before asking it to write code
— it writes much better code when it knows the *why*, not just the *what*. Some
starting prompts that work well for each phase:

**Setting up the blueprint schema:**
> "Using the ArchSynth context above, write a Python pydantic model representing
> a ROS2 node blueprint: node name, class name, source file, list of publishers
> (topic name + msg type), list of subscribers, list of services, list of
> actions. Keep it strict — no extra free-form fields."

**Stage 2 (NodeAnalyzer):**
> "Write a Python function using the `ast` module that walks a .py file and
> returns every class that subclasses `rclpy.node.Node` or `Node`, along with
> any calls to `self.create_publisher`, `self.create_subscription`,
> `self.create_service` found in its methods. Return as a list of dicts."

**LLM call wrapper:**
> "Write a thin wrapper function `call_llm(prompt: str, schema: BaseModel) ->
> BaseModel` that calls [Gemini/Ollama] API requesting structured JSON output
> matching a given pydantic schema, with retries on invalid JSON."

**Stage 3 (LaunchFileAnalyzer):**
> "Write a Python function that parses a ROS2 Python launch file (`.launch.py`)
> using the `ast` module and extracts calls to `Node(...)`, `IncludeLaunchDescription(...)`,
> and any `namespace=` or `remappings=` arguments passed to them."

**Evaluation metrics:**
> "Given two lists of node names (predicted vs ground truth), write a function
> computing precision, recall, and F1, handling near-miss name matching (e.g.
> case-insensitive, ignoring leading slashes)."

**General debugging habit:** when Copilot's suggestion looks structurally right
but ROS2-specific details look off (e.g. it invents a wrong `rclpy` API), that's
expected — Copilot's training data has plenty of ROS1 mixed in with ROS2. Always
cross-check generated ROS2 API calls against the current `rclpy` docs.

---

## 8. First-week checklist (do these in order)

- [x] Create the GitHub repo with the folder structure in Section 5
- [ ] Get LLM API access working — a 5-line "hello world" script that sends one
      prompt and prints the response
- [ ] Clone the Navigation2 repo into `case_studies/nav2/` at a pinned commit
- [ ] Hand-draw the ground-truth architecture of its simplest package (pen and
      paper or draw.io is fine — you'll formalize it later)
- [ ] Write and test `ingestor.py` (just clones + checks out a pinned commit)
- [ ] Write the very first version of `node_analyzer.py` on **one single file**
      from the repo, and get one clean JSON output out of it — this is your
      "hello world" for the actual research contribution

Once that last item works, you have a working proof of concept and the rest is
iteration and scaling up to more files, more repos, and the later pipeline
stages.

---

## 9. User Configuration Decisions (from setup)

- **Primary LLM**: Google Gemini API (free tier) - `gemini-1.5-flash` or `gemini-1.5-pro`
- **Open-weight LLM**: Local Ollama - Qwen2.5-Coder or Llama-3
- **Case Study Repo**: Navigation2 (nav2) - https://github.com/ros-planning/navigation2
- **Diagram Format**: Mermaid (renders natively in GitHub)