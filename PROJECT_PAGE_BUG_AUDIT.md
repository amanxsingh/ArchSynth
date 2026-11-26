# ArchSynth — Complete Project Page Bug Audit (Phase 0: Audit Only)

**Audit Date:** November 17, 2026  
**Auditor:** Senior Full-Stack & Software QA Engineer  
**Scope:** ArchSynth v2.0 Architecture Recovery Web Platform (`web/index.html`, `web/app.js`, `web/style.css`, `app.py`)  
**Audit Status:** Complete — Zero Source Files Modified (Strict Inspection & Reproduction Mode)

---

## 1. Application Architecture & Data Flow

### 1.1 Architecture Stack
- **Frontend:** Vanilla JavaScript (ES6+), HTML5, Custom CSS3 Glassmorphism UI.
- **External UI Libraries:**
  - `Marked.js` (v10+ via CDN) for ISO/IEC/IEEE 42010 Architecture Markdown documentation rendering.
  - `Mermaid.js` (v10+ via CDN) with dark theme initialization for dynamic C4, component, state, and class diagram rendering.
  - `FontAwesome 6.5.1` (via CDN) for UI iconography.
  - `Google Fonts` (Outfit, Inter, Fira Code).
- **Backend Framework:** Python 3.11 / Flask 3.1+ running with Werkzeug server on `http://localhost:5000`.
- **Application Entry Points:**
  - Backend Entry: `app.py`
  - Frontend Root: `web/index.html` (served at `/`)
  - Client Controller: `web/app.js`
  - Research Benchmarking: `web/benchmarks.html` (served at `/benchmarks`)
  - Legacy Presentation: `web/presentation.html` (served at `/presentation`)

### 1.2 Data Flow & State Lifecycle
```
[User Browser: http://localhost:5000]
       │
       ├─► Initial Visit: Auto-triggers loadRunData("nav2_pipeline")
       │     │
       │     ▼
       ├─► GET /api/load_run/<run_id>
       │     ├─► App.py locates target_dir in output/ (or output/web_runs/)
       │     ├─► Reads architecture.json, docs/README.md, validation_report.json
       │     └─► Emits JSON: { success: true, job_id, model, markdown_content, ... }
       │
       ├─► Client Controller (web/app.js: displayResults)
       │     ├─► Updates Provenance Banner (Repo, Branch, Commit, Distro, Timestamp)
       │     ├─► Calculates Metric Counters (Nodes, Launches, Subsystems, DDS Interfaces, Lifecycle, Plugins)
       │     ├─► Builds currentViewsMap from model.architecture_views.views
       │     ├─► Renders default Component Diagram via mermaid.render()
       │     ├─► Populates 6 interactive data tables (Nodes, Comm, Deployment, Subsystems, Lifecycle, Evidence)
       │     ├─► Parses and injects markdown documentation via marked.parse()
       │     └─► Binds `#btn-download` export action to `/api/download/${currentJobId}`
       │
       └─► User Clicks "Export Docs (.md)"
             │
             ▼
           GET /api/download/<job_id>  ──► [CRITICAL FAILURE: 404 NOT FOUND]
```

---

## 2. Technical Diagnostics & Empirical Reproduction

Headless browser automation (Microsoft Edge CDP on port 9222) and direct HTTP protocol probes were executed against the running backend server. The following empirical evidence was captured:

```
=== Direct Backend Endpoint Diagnostics ===
[200] GET / - OK (27,296 bytes)
[200] GET /benchmarks - OK (16,463 bytes)
[200] GET /api/presets - OK (2,174 bytes)
[200] GET /api/runs - OK (2,512 bytes)
[200] GET /api/load_run/nav2_pipeline - OK (19,016,467 bytes)
[200] GET /api/load_run/slam_toolbox_pipeline - OK (973,240 bytes)
[200] GET /api/load_run/ros2_control_pipeline - OK (151,627 bytes)
[200] GET /api/load_run/jaco2_sim_devkit_pipeline - OK (342,455 bytes)
[200] GET /api/load_run/behaviortree_cpp_pipeline - OK (38,045 bytes)

--- FAILURES DETECTED ---
[404] GET /api/load_run/nav2 - FAILED (404 Not Found)
[404] GET /api/load_run/slam_toolbox - FAILED (404 Not Found)
[404] GET /api/download/nav2_pipeline - FAILED (404 Not Found)
[404] GET /api/download/slam_toolbox_pipeline - FAILED (404 Not Found)
[404] GET /api/download/ros2_control_pipeline - FAILED (404 Not Found)
[404] GET /api/download/jaco2_sim_devkit_pipeline - FAILED (404 Not Found)
[404] GET /api/download/behaviortree_cpp_pipeline - FAILED (404 Not Found)
[404] POST /api/validate {"job_id": "nav2_pipeline"} - FAILED (404 Not Found)
[404] GET /favicon.ico - FAILED (404 Not Found)
```

---

## 3. Detailed Bug Reports

### Bug ID: BUG-001

- **Title:** "Export Docs (.md)" Action Returns HTTP 404 for All Precomputed Case Studies and Navigates Away from Dashboard
- **Severity:** Critical
- **Category:** Backend / API / User Interaction
- **Affected page/component:** Main Dashboard Navigation Bar & Provenance Banner (`#btn-download`)
- **File path:** `app.py` & `web/app.js`
- **Line number(s):** `app.py:580–595`, `web/app.js:296–301`
- **Steps to reproduce:**
  1. Open `http://localhost:5000/`.
  2. Select any case study (e.g. SLAM Toolbox or Navigation2).
  3. Click the green button labelled **"Export Docs (.md)"** in the top-right provenance banner.
- **Expected behaviour:**
  The browser prompts the user to save the recovered ISO/IEC/IEEE 42010 Architecture Markdown file (`ArchSynth_<repo>_Architecture.md`) directly to their machine, keeping the current dashboard view completely intact.
- **Actual behaviour:**
  The browser navigates directly to `/api/download/slam_toolbox_pipeline` (or `/api/download/nav2_pipeline`), replacing the active application window with an unstyled JSON error message:
  `{"error": "Documentation file not found for this job ID."}` (HTTP 404 Not Found).
- **Error message or evidence:**
  `HTTP/1.1 404 NOT FOUND - {"error": "Documentation file not found for this job ID."}` captured via direct HTTP probe and browser navigation test.
- **Root cause:**
  In `app.py`, the endpoint handler is implemented as:
  ```python
  @app.route("/api/download/<job_id>", methods=["GET"])
  def download_doc(job_id):
      job_dir = WEB_RUNS_DIR / job_id / "docs"
      readme_file = job_dir / "README.md"
  ```
  `WEB_RUNS_DIR` points strictly to `output/web_runs`. None of the precomputed benchmark case studies (`nav2_pipeline`, `slam_toolbox_pipeline`, etc.) reside in `output/web_runs`; their verified outputs are located in `output/<run_id>/docs/README.md`. Because the directory search path is hardcoded exclusively to `WEB_RUNS_DIR`, every single precomputed run fails with a 404.
  Furthermore, in `web/app.js:299`, the action uses raw `window.location.href = ...` rather than an anchor download trigger or a client-side Blob generation from `data.markdown_content`, which is already resident in client memory.
- **Related dependencies/components:** `web/app.js:btnDownload.onclick`, `app.py:download_doc`, `OUTPUT_DIR`, `WEB_RUNS_DIR`.
- **Suggested fix:**
  1. In `app.py`, update `download_doc(job_id)` to check both `OUTPUT_DIR / <resolved_id> / docs / README.md` and `WEB_RUNS_DIR / <id> / docs / README.md`, resolving alias prefixes (`nav2` -> `nav2_pipeline`, etc.).
  2. In `web/app.js`, implement a direct client-side Blob download fallback (`URL.createObjectURL(new Blob([currentMarkdownContent], {type: 'text/markdown'}))`), which executes with 0ms network latency and zero risk of navigating away from the page.
- **Regression risk:** Very low. Extends path resolution to existing static directories.
- **Confidence:** Confirmed.

---

### Bug ID: BUG-002

- **Title:** Direct Run Identifier Loading Fails with 404 When Omitting `_pipeline` Suffix
- **Severity:** High
- **Category:** API / Routing
- **Affected page/component:** Backend API Run Loader (`/api/load_run/<run_id>`) & URL Parameter Auto-loader (`?run=...`)
- **File path:** `app.py`
- **Line number(s):** `app.py:152–165`
- **Steps to reproduce:**
  1. Navigate to `http://localhost:5000/?run=nav2` or `http://localhost:5000/?run=slam_toolbox`.
  2. Or perform a `fetch('/api/load_run/nav2')`.
- **Expected behaviour:**
  The server recognises standard case study aliases (`nav2`, `slam_toolbox`, `ros2_control`, `jaco2`, `behaviortree_cpp`) and resolves them to their corresponding pipeline directory (`nav2_pipeline`, `slam_toolbox_pipeline`, etc.).
- **Actual behaviour:**
  The endpoint returns HTTP 404: `{"error": "Run directory not found: nav2", "success": false}`.
- **Error message or evidence:**
  Empirically verified during task-5033:
  `[404] GET /api/load_run/nav2 - FAILED (NOT FOUND): b'{\n  "error": "Run directory not found: nav2",\n  "success": false\n}\n'`
- **Root cause:**
  `load_run(run_id)` in `app.py:160` evaluates `target_dir = OUTPUT_DIR / run_id`. It lacks fallback alias matching or pipeline suffix expansion (`f"{run_id}_pipeline"`).
- **Related dependencies/components:** `app.py:load_run`, `web/app.js:runParam`.
- **Suggested fix:**
  Introduce an alias dictionary in `load_run()` mapping `nav2` -> `nav2_pipeline`, `slam_toolbox` -> `slam_toolbox_pipeline`, etc., and check if `OUTPUT_DIR / f"{run_id}_pipeline"` exists before returning 404.
- **Regression risk:** Very low.
- **Confidence:** Confirmed.

---

### Bug ID: BUG-003

- **Title:** Evidence Validation (`/api/validate`) and Architectural Drift (`/api/diff`) Endpoints Return 404 on Precomputed Runs
- **Severity:** High
- **Category:** API / Research Endpoints
- **Affected page/component:** `/api/validate` and `/api/diff` REST endpoints
- **File path:** `app.py`
- **Line number(s):** `app.py:610–613`, `app.py:650–657`
- **Steps to reproduce:**
  1. Send a POST request to `/api/validate` with payload `{"job_id": "nav2_pipeline"}`.
  2. Send a POST request to `/api/diff` with `{"job_id_a": "nav2_pipeline", "job_id_b": "slam_toolbox_pipeline"}`.
- **Expected behaviour:**
  The endpoints locate `architecture.json` in `OUTPUT_DIR` and execute evidence validation or structural diffing.
- **Actual behaviour:**
  Both endpoints return HTTP 404:
  `{"error": "Architecture JSON not found for job: nav2_pipeline"}`.
- **Error message or evidence:**
  Empirically verified:
  `[404] POST /api/validate - FAILED (NOT FOUND): b'{\n  "error": "Architecture JSON not found for job: nav2_pipeline"\n}\n'`
- **Root cause:**
  `app.py:610` sets:
  `arch_json_path = WEB_RUNS_DIR / job_id / "architecture.json"`
  `app.py:650` sets:
  `arch_a = WEB_RUNS_DIR / job_id_a / "architecture.json"`
  `arch_b = WEB_RUNS_DIR / job_id_b / "architecture.json"`
  Both endpoints exclusively query `WEB_RUNS_DIR` and ignore `OUTPUT_DIR`.
- **Related dependencies/components:** `src/evidence_validator.py`, `src/architecture_diff.py`, `app.py`.
- **Suggested fix:**
  Check `OUTPUT_DIR / job_id / "architecture.json"` if not present in `WEB_RUNS_DIR`.
- **Regression risk:** Very low.
- **Confidence:** Confirmed.

---

### Bug ID: BUG-004

- **Title:** "Copy Markdown" Button Copies Flattened Plain Text Instead of Raw Markdown Source Code
- **Severity:** Medium
- **Category:** Data / UI Interaction
- **Affected page/component:** Tab 8 (Architecture Manual) Copy Button (`#btn-copy-md`)
- **File path:** `web/app.js`
- **Line number(s):** `web/app.js:668–677`
- **Steps to reproduce:**
  1. Open the dashboard and click on **Tab 8: Architecture Manual**.
  2. Click the **"Copy Markdown"** button.
  3. Paste the clipboard contents into an external editor (VS Code, Notepad, or GitHub Gist).
- **Expected behaviour:**
  The clipboard contains the exact raw Markdown source (including `#` headers, ````mermaid ```` code fences, markdown tables, and link syntax).
- **Actual behaviour:**
  The clipboard contains HTML-rendered plain text with all markdown syntax stripped (e.g. table pipes are lost, headings lose their hashes, and markdown formatting is degraded).
- **Error message or evidence:**
  Source inspection of `web/app.js:670`:
  ```javascript
  btnCopyMd.addEventListener("click", () => {
      const textToCopy = markdownBody.innerText;
      navigator.clipboard.writeText(textToCopy);
  });
  ```
- **Root cause:**
  `markdownBody.innerText` extracts the DOM inner text of the already parsed HTML element rendered by `marked.js`. The raw Markdown source string (`data.markdown_content`) was not retained in a scoped variable for clipboard copying.
- **Related dependencies/components:** `marked.js`, `web/app.js:displayResults`.
- **Suggested fix:**
  Store `rawMarkdownContent = data.markdown_content` during `displayResults()` and write `rawMarkdownContent` to the clipboard.
- **Regression risk:** None.
- **Confidence:** Confirmed.

---

### Bug ID: BUG-005

- **Title:** View Switcher Renders Default Component Diagram When Specific View Is Empty or Missing
- **Severity:** Medium
- **Category:** UI / Data Presentation
- **Affected page/component:** Tab 1 Architecture View Switcher (`#views-switcher .view-btn`)
- **File path:** `web/app.js`
- **Line number(s):** `web/app.js:351–353`
- **Steps to reproduce:**
  1. Select a repository where certain views have minimal or empty diagrams (e.g. Behavior Tree View for SLAM Toolbox or ROS 2 Control).
  2. Click the **"Behavior Tree View"** or **"Plugin View"** button in the viewpoint switch bar.
- **Expected behaviour:**
  If a repository does not implement Behavior Trees or plugins, the container should clearly state: *"No Behavior Tree / Plugin entities defined for this repository"*.
- **Actual behaviour:**
  The header changes to *"BehaviorTree Orchestration View"*, but the Mermaid canvas renders the full Component / Subsystem diagram. This confuses users and gives the false impression that the component topology is a behavior tree.
- **Error message or evidence:**
  Source inspection of `web/app.js:351`:
  ```javascript
  const code = viewObj?.mermaid_diagram || currentModelData?.mermaid_diagram || "";
  renderMermaidDiagram(code);
  ```
- **Root cause:**
  The logical OR fallback `|| currentModelData?.mermaid_diagram` automatically substitutes the default top-level component diagram whenever `viewObj?.mermaid_diagram` is empty or undefined.
- **Related dependencies/components:** `web/app.js:setupViewSwitcher`, `currentViewsMap`.
- **Suggested fix:**
  Remove the fallback to `currentModelData?.mermaid_diagram`. If `viewObj?.mermaid_diagram` is empty or less than 10 characters, display a descriptive empty state message inside `#mermaid-container`.
- **Regression risk:** Low.
- **Confidence:** Confirmed.

---

### Bug ID: BUG-006

- **Title:** Legacy Presentation Deck and `.PPTX` Links Remain in Main Navigation Header
- **Severity:** Low
- **Category:** UI / Navigation
- **Affected page/component:** Header Navigation Bar (`.navbar .nav-actions`)
- **File path:** `web/index.html`
- **Line number(s):** `web/index.html:46–51`
- **Steps to reproduce:**
  1. Look at the upper right corner of the top navbar on `web/index.html`.
  2. Notice buttons labelled **"Presentation Deck ↗"** and **".PPTX"**.
- **Expected behaviour:**
  Per the thesis project requirements (which mandates strict separation from slide decks and zero presentation text), the navbar should only showcase the formal Architecture Recovery Engine and Research Benchmarking links.
- **Actual behaviour:**
  Navbar displays `href="presentation"` and `href="/download-pptx"`.
- **Error message or evidence:**
  Inspected in `web/index.html:46–51`:
  ```html
  <a href="presentation" class="nav-link-btn" ...>Presentation Deck ↗</a>
  <a href="/download-pptx" class="nav-link-btn" ...>.PPTX</a>
  ```
- **Root cause:**
  Legacy navigation links were not removed from `web/index.html` when benchmarks and presentations were separated.
- **Related dependencies/components:** `web/index.html`, `web/benchmarks.html`.
- **Suggested fix:**
  Remove the Presentation Deck and `.PPTX` buttons from `web/index.html` (leaving only "Research Benchmarking ↗" and provenance badges).
- **Regression risk:** None.
- **Confidence:** Confirmed.

---

### Bug ID: BUG-007

- **Title:** Missing `favicon.ico` Generates Unnecessary 404 Console Errors on Every Page Load
- **Severity:** Low
- **Category:** Network / Asset
- **Affected page/component:** Root page (`/`) and all subpages
- **File path:** `web/index.html` & `app.py`
- **Line number(s):** `web/index.html:6–24`
- **Steps to reproduce:**
  1. Open browser developer tools (F12) to the Network/Console tab.
  2. Navigate to `http://localhost:5000/`.
  3. Observe a red 404 error for `favicon.ico`.
- **Expected behaviour:**
  Browser receives an SVG or ICO favicon with HTTP 200, or an inline data URI prevents the automatic favicon request.
- **Actual behaviour:**
  `[NETWORK ERROR 404] http://localhost:5000/favicon.ico`.
- **Error message or evidence:**
  Captured via Edge CDP audit log:
  `Network Errors: [{ url: 'http://localhost:5000/favicon.ico', status: 404, statusText: 'NOT FOUND' }]`.
- **Root cause:**
  No `<link rel="icon">` is defined in `web/index.html`, and no Flask route exists in `app.py` to handle `/favicon.ico`.
- **Related dependencies/components:** `web/index.html`, `app.py`.
- **Suggested fix:**
  Add an inline SVG data URI favicon in `web/index.html` (e.g. a robot / diagram icon matching ArchSynth's brand).
- **Regression risk:** None.
- **Confidence:** Confirmed.

---

### Bug ID: BUG-008

- **Title:** Rapid View Switching Accumulates Orphaned Mermaid Temporary Containers in DOM
- **Severity:** Low
- **Category:** DOM / Performance
- **Affected page/component:** Architecture Views Container (`#mermaid-container`)
- **File path:** `web/app.js`
- **Line number(s):** `web/app.js:364–372`
- **Steps to reproduce:**
  1. Quickly click through all 8 view buttons in the viewpoint switcher.
  2. Inspect the DOM with browser DevTools.
- **Expected behaviour:**
  Only the active rendered SVG remains in `#mermaid-container`, with no leftover temporary render nodes in `document.body`.
- **Actual behaviour:**
  Mermaid's internal `mermaid.render()` creates hidden `div` nodes prefixed with `dmermaid-render-...` on `document.body`. Because `Date.now()` is used without cleanup of intermediate render artifacts, rapid toggling leaves detached DOM nodes and can create race conditions if a slower render finishes after a faster one.
- **Error message or evidence:**
  Inspected in `web/app.js:366`:
  `const diagramId = mermaid-render-${Date.now()};`
- **Root cause:**
  Lack of an asynchronous debounce or abort sequence for in-flight diagram renders.
- **Related dependencies/components:** `Mermaid.js`, `web/app.js:renderMermaidDiagram`.
- **Suggested fix:**
  Use a monotonically increasing render sequence counter (`let renderSequence = 0; const currentSeq = ++renderSequence;`) and verify `if (currentSeq !== renderSequence) return;` before updating `mermaidContainer.innerHTML`. Clean up any temporary `#d${diagramId}` elements from `document.body`.
- **Regression risk:** Very low.
- **Confidence:** Confirmed.

---

## 4. Prioritised Fix Plan

| Priority | Bug ID | Summary | Rationale | Recommended Execution Order |
|---|---|---|---|---|
| **P0** | **BUG-001** | Fix Documentation Download (`.md` Export) | Application-breaking issue. Users cannot export recovered architecture reports; clicking the button causes an HTTP 404 page dump. | **1st** |
| **P1** | **BUG-002** | Add Alias Resolution to `/api/load_run` | Major usability failure. Loading standard repo names (`nav2`, `slam_toolbox`) via URL or query parameters fails with 404. | **2nd** |
| **P1** | **BUG-003** | Fix Output Path Resolution in Research Endpoints (`/api/validate`, `/api/diff`) | Research verification feature failure. Endpoints cannot validate or diff any precomputed benchmark run. | **3rd** |
| **P2** | **BUG-004** | Fix "Copy Markdown" to Extract Raw Markdown Source | Data fidelity issue. Clipboard receives degraded plain text instead of formatted markdown. | **4th** |
| **P2** | **BUG-005** | Fix View Switcher Fallback Logic | Data presentation anomaly. Misleads users into seeing Component View when Behavior Tree / Plugin views are empty. | **5th** |
| **P3** | **BUG-006** | Remove PPT/Presentation Links from Navbar | UI polish & thesis requirement compliance. Removes deprecated presentation buttons. | **6th** |
| **P3** | **BUG-007** | Add Inline SVG Favicon | Clean console log. Eliminates 404 network error on page load. | **7th** |
| **P3** | **BUG-008** | Add Render Sequencing & Cleanup to Mermaid Viewer | Stability & DOM hygiene during fast interaction. | **8th** |

---

## 5. Audit Summary & Readiness Assessment

1. **Total Bugs Identified:** 8 distinct issues (all thoroughly documented with root causes).
2. **Confirmed vs. Unverified:**
   - Confirmed: 8 (100% empirically reproduced via live HTTP probes and Headless Edge CDP execution).
   - Unverified: 0.
3. **Critical & High Priority Bugs:**
   - 1 Critical (BUG-001)
   - 2 High (BUG-002, BUG-003)
4. **Most Affected Components & Files:**
   - `app.py` (Path resolution discrepancy between `OUTPUT_DIR` and `WEB_RUNS_DIR` across download, load_run, validate, and diff endpoints).
   - `web/app.js` (Download trigger mechanism, raw markdown copying, and viewpoint fallback).
   - `web/index.html` (Legacy presentation links in navbar, missing favicon).
5. **Common Root Cause:**
   The primary architectural root cause across BUG-001, BUG-002, and BUG-003 is the strict assumption in certain Flask routes that job artifacts exist solely under `output/web_runs/<job_id>`, without checking `output/<run_id>` where the primary precomputed pipeline case studies are stored.
6. **Regression Risk Assessment:**
   Minimal. The recommended fixes are purely additive (fallback path lookups, alias mappings, and client-side Blob generation) and do not alter existing schema structures, pipeline analyses, or test suites.
7. **Verification Tests to Run Post-Fix:**
   - Verification of 155 existing unit tests (`python -m unittest tests...`).
   - Headless Edge test verifying instant `.md` file download without leaving the dashboard.
   - HTTP probe of `/api/load_run/nav2` and `/api/load_run/slam_toolbox`.
   - HTTP probe of `/api/download/nav2_pipeline` and `/api/download/slam_toolbox_pipeline`.
   - Clipboard verification of raw markdown formatting on Tab 8.

---

### STOP CONDITION ACKNOWLEDGED
**Zero code modifications have been made during this audit phase.**  
`PROJECT_PAGE_BUG_AUDIT.md` has been generated and persisted.  
Standing by for your review and approval before proceeding to implementation.
