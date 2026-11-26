/* ==========================================================================
   ArchSynth v2.0 — Architecture Recovery Dashboard Logic
   Focus: Architecture Recovery Only (No Benchmarks on Main Page)
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // Initialize Mermaid.js with Dark Theme
    if (typeof mermaid !== "undefined") {
        mermaid.initialize({
            startOnLoad: false,
            theme: 'dark',
            securityLevel: 'loose',
            flowchart: { curve: 'basis' }
        });
    }

    // DOM Elements
    const form = document.getElementById("analyze-form");
    const repoInput = document.getElementById("repo-input");
    const runSelector = document.getElementById("run-selector");
    const btnSubmit = document.getElementById("btn-submit");
    const errorBanner = document.getElementById("error-banner");
    const errorMessage = document.getElementById("error-message");
    const loadingCard = document.getElementById("loading-card");
    const progressBar = document.getElementById("progress-bar");
    const resultsDashboard = document.getElementById("results-dashboard");
    const btnDownload = document.getElementById("btn-download");
    const btnDownloadTabMd = document.getElementById("btn-download-tab-md");
    const btnCopyMd = document.getElementById("btn-copy-md");
    const markdownBody = document.getElementById("markdown-body");
    const mermaidContainer = document.getElementById("mermaid-container");
    const viewTitle = document.getElementById("view-title");
    const viewBadge = document.getElementById("view-badge");

    // Provenance Elements
    const provRepoName = document.getElementById("prov-repo-name");
    const provBranch = document.getElementById("prov-branch");
    const provCommit = document.getElementById("prov-commit");
    const provDistro = document.getElementById("prov-distro");
    const provTimestamp = document.getElementById("prov-timestamp");

    // Statistics Elements
    const statNodes = document.getElementById("stat-nodes");
    const statLaunches = document.getElementById("stat-launches");
    const statSubsystems = document.getElementById("stat-subsystems");
    const statTopics = document.getElementById("stat-topics");
    const statLifecycle = document.getElementById("stat-lifecycle");
    const statPlugins = document.getElementById("stat-plugins");

    // Table Bodies
    const nodesTableBody = document.getElementById("nodes-table-body");
    const commTableBody = document.getElementById("comm-table-body");
    const deploymentTableBody = document.getElementById("deployment-table-body");
    const subsystemsContainer = document.getElementById("subsystems-container");
    const lifecycleTableBody = document.getElementById("lifecycle-table-body");
    const pluginsTableBody = document.getElementById("plugins-table-body");
    const evidenceTableBody = document.getElementById("evidence-table-body");

    // Search Inputs
    const nodeSearch = document.getElementById("node-search");
    const commSearch = document.getElementById("comm-search");
    const evidenceSearch = document.getElementById("evidence-search");

    let currentJobId = null;
    let progressTimer = null;
    let currentModelData = null;
    let currentViewsMap = {};
    let currentRawMarkdown = "";
    let mermaidRenderSeq = 0;

    // Tab Switching Logic
    const tabButtons = document.querySelectorAll(".arch-tab-btn");
    const tabPanes = document.querySelectorAll(".arch-tab-pane");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            tabButtons.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const targetPane = document.getElementById(targetTab);
            if (targetPane) targetPane.classList.add("active");
        });
    });

    // Preset Pill Click Handlers
    document.querySelectorAll(".preset-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            const url = pill.getAttribute("data-url");
            repoInput.value = url;
            // Highlight active pill
            document.querySelectorAll(".preset-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");

            // Map preset to pipeline ID if available for instant loading
            const mapping = {
                "case_studies/nav2": "nav2_corrected_pipeline",
                "case_studies/slam_toolbox": "slam_toolbox_pipeline",
                "case_studies/ros2_control": "ros2_control_pipeline",
                "case_studies/jaco2_sim_devkit": "jaco2_sim_devkit_pipeline",
                "case_studies/behaviortree_cpp": "behaviortree_cpp_pipeline"
            };
            if (mapping[url]) {
                if (runSelector) runSelector.value = mapping[url];
                loadRunData(mapping[url]);
            } else {
                triggerAnalysis(url);
            }
        });
    });

    // Welcome Section Gallery Load Buttons
    document.querySelectorAll(".welcome-load-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const runId = btn.getAttribute("data-run");
            if (runId) {
                if (runSelector) runSelector.value = runId;
                loadRunData(runId);
            }
        });
    });

    // Run Selector Dropdown Handler
    if (runSelector) {
        runSelector.addEventListener("change", () => {
            const selected = runSelector.value;
            if (selected) {
                loadRunData(selected);
            }
        });
    }

    // Navigation and Back to Home Handlers
    const btnBackHome = document.getElementById("btn-back-home");
    if (btnBackHome) {
        btnBackHome.addEventListener("click", showHomePage);
    }
    const navBtnHome = document.getElementById("nav-btn-home");
    if (navBtnHome) {
        navBtnHome.addEventListener("click", showHomePage);
    }
    const navBrand = document.querySelector(".nav-brand");
    if (navBrand) {
        navBrand.style.cursor = "pointer";
        navBrand.addEventListener("click", showHomePage);
    }

    // Main Form Submit Handler
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const repoUrl = repoInput.value.trim();
        if (!repoUrl) return;

        // Auto-route known presets to precomputed runs for instantaneous response
        const mapping = {
            "case_studies/nav2": "nav2_corrected_pipeline",
            "case_studies/slam_toolbox": "slam_toolbox_pipeline",
            "case_studies/ros2_control": "ros2_control_pipeline",
            "case_studies/jaco2_sim_devkit": "jaco2_sim_devkit_pipeline",
            "case_studies/behaviortree_cpp": "behaviortree_cpp_pipeline",
            "nav2": "nav2_corrected_pipeline",
            "slam_toolbox": "slam_toolbox_pipeline",
            "ros2_control": "ros2_control_pipeline",
            "jaco2_sim_devkit": "jaco2_sim_devkit_pipeline",
            "jaco2": "jaco2_sim_devkit_pipeline",
            "behaviortree_cpp": "behaviortree_cpp_pipeline"
        };
        const normalized = repoUrl.replace(/\\/g, "/").toLowerCase();
        for (const [k, v] of Object.entries(mapping)) {
            if (normalized === k || normalized.endsWith("/" + k)) {
                if (runSelector) runSelector.value = v;
                loadRunData(v);
                return;
            }
        }
        triggerAnalysis(repoUrl);
    });

    // Trigger Full Analysis via API
    async function triggerAnalysis(repoUrl) {
        hideElement(errorBanner);
        hideElement(resultsDashboard);
        const welcomeSection = document.getElementById("welcome-section");
        if (welcomeSection) hideElement(welcomeSection);
        showElement(loadingCard);
        setButtonLoading(btnSubmit, true);
        startProgressAnimation();

        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ repo_url: repoUrl })
            });

            const data = await response.json();
            stopProgressAnimation();

            if (!response.ok || !data.success) {
                const title = data.is_ros2 === false ? "Validation Failed: Non-ROS2 Repository" : "Analysis Failed";
                showError(data.error || "Failed to analyze repository.", title);
                hideElement(loadingCard);
                setButtonLoading(btnSubmit, false);
                return;
            }

            currentJobId = data.job_id;
            displayResults(data, repoUrl);
            hideElement(loadingCard);
            setButtonLoading(btnSubmit, false);
        } catch (err) {
            stopProgressAnimation();
            hideElement(loadingCard);
            setButtonLoading(btnSubmit, false);
            showError("Network or server connection error. Please ensure ArchSynth server is running.");
        }
    }

    // Direct Precomputed Run Loader
    async function loadRunData(runId) {
        hideElement(errorBanner);
        hideElement(resultsDashboard);
        const welcomeSection = document.getElementById("welcome-section");
        if (welcomeSection) hideElement(welcomeSection);
        showElement(loadingCard);
        setButtonLoading(btnSubmit, true);
        startProgressAnimation();

        try {
            const response = await fetch(`/api/load_run/${runId}`);
            const data = await response.json();
            stopProgressAnimation();

            if (!response.ok || !data.success) {
                showError(data.error || `Failed to load run: ${runId}`);
                hideElement(loadingCard);
                setButtonLoading(btnSubmit, false);
                return;
            }

            currentJobId = runId;
            displayResults(data, data.model?.repo_name || runId);
            hideElement(loadingCard);
            setButtonLoading(btnSubmit, false);
        } catch (err) {
            stopProgressAnimation();
            hideElement(loadingCard);
            setButtonLoading(btnSubmit, false);
            showError(`Error loading precomputed run: ${err.message}`);
        }
    }

    // Display Comprehensive Architecture Recovery Results
    function displayResults(data, inputRepo) {
        const model = data.model || {};
        currentModelData = model;

        // 1. Provenance Banner
        provRepoName.textContent = model.repo_name || inputRepo.split("/").pop() || "ROS2 Repository";
        provBranch.textContent = model.branch || "main";
        const commitHash = model.commit_hash || "N/A";
        provCommit.textContent = commitHash.length > 8 ? commitHash.substring(0, 8) : commitHash;

        let targetDistro = "ROS 2 Jazzy";
        if (model.repo_name?.toLowerCase().includes("nav2")) targetDistro = "ROS 2 Humble / Jazzy";
        else if (model.repo_name?.toLowerCase().includes("jaco2")) targetDistro = "ROS 2 Humble";
        else if (model.repo_name?.toLowerCase().includes("control")) targetDistro = "ROS 2 Rolling / Jazzy";
        else if (model.repo_name?.toLowerCase().includes("behaviortree")) targetDistro = "Agnostic / ROS 2";
        provDistro.textContent = targetDistro;

        provTimestamp.textContent = model.analysis_timestamp ? new Date(model.analysis_timestamp).toLocaleString() : new Date().toLocaleString();

        // 2. Metrics Counters
        const nodes = model.nodes || [];
        const launchFiles = model.launch_files || [];
        const launchProfiles = model.deployment_profiles || [];
        const subsystems = model.subsystems || [];
        const interfaces = model.interfaces || [];
        const runtimeInterfaces = model.runtime_interfaces || [];
        const plugins = model.plugin_architecture?.plugins || [];
        const btTrees = model.behavior_tree_model?.total_trees || 0;

        let lifecycleCount = 0;
        nodes.forEach(n => { if (n.is_lifecycle) lifecycleCount++; });

        statNodes.textContent = nodes.length;
        statLaunches.textContent = launchProfiles.length > 0 ? launchProfiles.length : launchFiles.length;
        statSubsystems.textContent = subsystems.length;
        statTopics.textContent = interfaces.length > 0 ? interfaces.length : (model.stats?.total_topics || 0);
        statLifecycle.textContent = lifecycleCount;
        statPlugins.textContent = plugins.length + btTrees;

        // 3. Build Architecture Views Map
        currentViewsMap = {};
        if (model.architecture_views && model.architecture_views.views) {
            const rawViews = model.architecture_views.views;
            if (Array.isArray(rawViews)) {
                rawViews.forEach(v => {
                    const key = v.view_type || v.view_id || v.name;
                    if (key) currentViewsMap[key] = v;
                });
            } else if (typeof rawViews === "object") {
                Object.entries(rawViews).forEach(([k, v]) => {
                    currentViewsMap[k] = v;
                    if (v.view_type) currentViewsMap[v.view_type] = v;
                    if (v.view_id) currentViewsMap[v.view_id] = v;
                });
            }
        }

        // Store raw markdown content for exact source export and copying
        currentRawMarkdown = data.markdown_content || "";

        // Render Initial Component View Diagram
        const defaultView = currentViewsMap["subsystem_component"] || currentViewsMap["component"] || Object.values(currentViewsMap)[0];
        const defaultDiagram = defaultView?.mermaid_diagram || "";
        renderMermaidDiagram(defaultDiagram, "Component View (Level 3)", !!defaultView);
        setupViewSwitcher();

        // 4. Populate Tables
        populateNodesTable(nodes);
        populateCommunicationTable(model);
        populateDeploymentTable(model);
        populateSubsystems(subsystems);
        populateLifecycleAndPlugins(model);
        populateEvidenceTable(model);

        // 5. Render ISO 42010 Markdown Documentation
        if (typeof marked !== "undefined" && currentRawMarkdown) {
            markdownBody.innerHTML = marked.parse(currentRawMarkdown);
        } else {
            markdownBody.textContent = currentRawMarkdown || "No documentation generated.";
        }

        // 6. Configure Download Button
        if (btnDownload) {
            btnDownload.onclick = () => triggerMarkdownDownload();
        }
        if (btnDownloadTabMd) {
            btnDownloadTabMd.onclick = () => triggerMarkdownDownload();
        }

        // Show Dashboard
        const welcomeSection = document.getElementById("welcome-section");
        if (welcomeSection) hideElement(welcomeSection);
        showElement(resultsDashboard);
        if (currentJobId) {
            const newUrl = `${window.location.pathname}?run=${encodeURIComponent(currentJobId)}`;
            window.history.replaceState({ run: currentJobId }, document.title, newUrl);
        }
    }

    // Helper: Determine meaningful export filename based on active run
    function getExportFilename(jobId, model) {
        const nameMap = {
            "nav2": "Navigation2",
            "nav2_pipeline": "Navigation2",
            "navigation2": "Navigation2",
            "nav2_corrected": "Navigation2",
            "nav2_corrected_pipeline": "Navigation2",
            "slam_toolbox": "SLAM_Toolbox",
            "slam_toolbox_pipeline": "SLAM_Toolbox",
            "ros2_control": "ROS2_Control",
            "ros2_control_pipeline": "ROS2_Control",
            "jaco2": "Kinova_Jaco2",
            "jaco2_sim_devkit": "Kinova_Jaco2",
            "jaco2_sim_devkit_pipeline": "Kinova_Jaco2",
            "behaviortree_cpp": "BehaviorTree_CPP",
            "behaviortree_cpp_pipeline": "BehaviorTree_CPP"
        };
        const key = (jobId || model?.repo_name || "").toLowerCase();
        let cleanName = nameMap[key];
        if (!cleanName) {
            if (model?.repo_name) {
                cleanName = model.repo_name.replace(/[^a-zA-Z0-9_-]/g, "_");
            } else {
                cleanName = (jobId || "ROS2").replace(/[^a-zA-Z0-9_-]/g, "_");
            }
        }
        return `ArchSynth_${cleanName}_Architecture.md`;
    }

    // Trigger Markdown Documentation Download with Zero-Navigation Protection
    function triggerMarkdownDownload() {
        const exportFilename = getExportFilename(currentJobId, currentModelData);

        // Priority 1: Instant client-side Blob download using resident markdown source
        if (currentRawMarkdown && currentRawMarkdown.trim().length > 0) {
            try {
                const blob = new Blob([currentRawMarkdown], { type: "text/markdown;charset=utf-8" });
                const blobUrl = URL.createObjectURL(blob);
                const tempLink = document.createElement("a");
                tempLink.href = blobUrl;
                tempLink.download = exportFilename;
                tempLink.style.display = "none";
                document.body.appendChild(tempLink);
                tempLink.click();
                document.body.removeChild(tempLink);
                setTimeout(() => URL.revokeObjectURL(blobUrl), 1500);
                return;
            } catch (err) {
                console.warn("Client-side Blob download failed, attempting server fetch fallback:", err);
            }
        }

        // Priority 2: Asynchronous server fetch fallback (does not leave active dashboard)
        if (currentJobId) {
            const downloadUrl = `/api/download/${encodeURIComponent(currentJobId)}`;
            fetch(downloadUrl)
                .then(async resp => {
                    if (!resp.ok) {
                        const errJson = await resp.json().catch(() => ({}));
                        alert(errJson.error || `Documentation file not found for run '${currentJobId}'.`);
                        return;
                    }
                    const blob = await resp.blob();
                    const blobUrl = URL.createObjectURL(blob);
                    const tempLink = document.createElement("a");
                    tempLink.href = blobUrl;
                    tempLink.download = exportFilename;
                    tempLink.style.display = "none";
                    document.body.appendChild(tempLink);
                    tempLink.click();
                    document.body.removeChild(tempLink);
                    setTimeout(() => URL.revokeObjectURL(blobUrl), 1500);
                })
                .catch(err => {
                    console.error("Network download failed:", err);
                    alert("Network error: Failed to download documentation. Ensure ArchSynth server is running.");
                });
        } else {
            alert("No documentation is currently loaded to export.");
        }
    }

    // View Switcher Handlers (Strict view isolation — no fallback to component diagram)
    function setupViewSwitcher() {
        const viewKeysMap = {
            "component": ["subsystem_component", "component"],
            "context": ["system_context", "context"],
            "functional": ["package_dependency", "functional"],
            "deployment": ["runtime_deployment", "deployment"],
            "lifecycle": ["lifecycle_architecture", "lifecycle"],
            "communication": ["communication_topology", "communication"],
            "plugin": ["plugin_architecture", "plugin"],
            "behavior_tree": ["behavior_tree_orchestration", "behavior_tree"]
        };

        const viewButtons = document.querySelectorAll("#views-switcher .view-btn");
        viewButtons.forEach(btn => {
            btn.onclick = () => {
                viewButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                const viewKey = btn.getAttribute("data-view");

                let viewObj = currentViewsMap[viewKey];
                if (!viewObj && viewKeysMap[viewKey]) {
                    for (const alt of viewKeysMap[viewKey]) {
                        if (currentViewsMap[alt]) {
                            viewObj = currentViewsMap[alt];
                            break;
                        }
                    }
                }

                const viewLabels = {
                    "component": "Component View (Level 3)",
                    "context": "System Context View (Level 1)",
                    "functional": "Functional Decomposition View",
                    "deployment": "Deployment & Container View (Level 4)",
                    "lifecycle": "Lifecycle State Machine View",
                    "communication": "Topic & Service Graph View",
                    "plugin": "Pluginlib Architecture View",
                    "behavior_tree": "BehaviorTree Orchestration View"
                };

                const viewLabel = viewLabels[viewKey] || viewKey;
                viewTitle.innerHTML = `<i class="fa-solid fa-diagram-project"></i> ${viewObj?.name || viewLabel}`;
                viewBadge.textContent = viewLabel;

                // Strict View Isolation: Do NOT fallback to default component diagram!
                const diagramCode = viewObj?.mermaid_diagram ? viewObj.mermaid_diagram.trim() : "";
                renderMermaidDiagram(diagramCode, viewLabel, !!viewObj);
            };
        });
    }

    // Render Mermaid Diagram with Sequence Cancellation and DOM Hygiene
    async function renderMermaidDiagram(mermaidCode, viewLabel = "Architecture View", viewExists = true) {
        const thisSequence = ++mermaidRenderSeq;

        if (!viewExists) {
            mermaidContainer.innerHTML = `
                <div class="empty-view-state">
                    <i class="fa-solid fa-diagram-project"></i>
                    <h4>${escapeHtml(viewLabel)} Not Available</h4>
                    <p>This architectural viewpoint was not synthesized or is not applicable for ${escapeHtml(currentModelData?.repo_name || "this repository")}.</p>
                </div>`;
            return;
        }

        if (!mermaidCode || mermaidCode.length <= 10) {
            mermaidContainer.innerHTML = `
                <div class="empty-view-state">
                    <i class="fa-solid fa-circle-info"></i>
                    <h4>No ${escapeHtml(viewLabel)} Entities Declared</h4>
                    <p>No components, states, or relationships were declared for this viewpoint in ${escapeHtml(currentModelData?.repo_name || "this repository")}.</p>
                </div>`;
            return;
        }

        try {
            mermaidContainer.innerHTML = `<div class="text-dim" style="padding: 2.5rem;"><i class="fa-solid fa-spinner fa-spin"></i> Rendering diagram...</div>`;
            const diagramId = `mermaid-render-${thisSequence}-${Date.now()}`;
            const { svg } = await mermaid.render(diagramId, mermaidCode);

            // Cancel update if a newer render was triggered in the meantime
            if (thisSequence !== mermaidRenderSeq) {
                return;
            }

            mermaidContainer.innerHTML = svg;

            // Clean up temporary DOM render element attached to body by Mermaid
            const tempEl = document.getElementById(`d${diagramId}`);
            if (tempEl && tempEl.parentNode) {
                tempEl.parentNode.removeChild(tempEl);
            }
        } catch (err) {
            if (thisSequence !== mermaidRenderSeq) return;
            console.warn("Mermaid rendering warning:", err);
            mermaidContainer.innerHTML = `
                <div class="empty-view-state error-view-state">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <h4>Diagram Syntax / Visual Rendering Notice</h4>
                    <p>The diagram specification could not be rendered as SVG. Raw diagram source:</p>
                    <pre><code>${escapeHtml(mermaidCode)}</code></pre>
                </div>`;
        }
    }

    // 1. Populate Nodes Table
    function populateNodesTable(nodes) {
        if (!nodes || nodes.length === 0) {
            nodesTableBody.innerHTML = `<tr><td colspan="7" class="text-dim">No nodes discovered.</td></tr>`;
            return;
        }

        let html = "";
        nodes.forEach(n => {
            const isTest = n.is_test;
            const typeBadge = isTest
                ? `<span class="status-pill status-pill-rose">Test Node</span>`
                : `<span class="status-pill status-pill-green">Production Node</span>`;

            const lcBadge = n.is_lifecycle
                ? `<span class="status-pill status-pill-purple"><i class="fa-solid fa-check"></i> Managed</span>`
                : `<span class="status-pill status-pill-blue">Unmanaged</span>`;

            const filePath = n.file_path || (n.evidence && n.evidence[0]?.source_file) || "--";

            html += `<tr>
                <td style="font-weight: 600; color: #fff;">${escapeHtml(n.name || n.class_name || "unnamed")}</td>
                <td><code>${escapeHtml(n.package_name || "--")}</code></td>
                <td>${escapeHtml(n.executable_name || n.name || "--")}</td>
                <td><code>${escapeHtml(n.class_name || "--")}</code></td>
                <td>${typeBadge}</td>
                <td>${lcBadge}</td>
                <td style="font-size: 0.75rem; color: var(--text-dim);">${escapeHtml(filePath)}</td>
            </tr>`;
        });
        nodesTableBody.innerHTML = html;

        // Search Filter
        if (nodeSearch) {
            nodeSearch.oninput = () => {
                const q = nodeSearch.value.toLowerCase();
                const rows = nodesTableBody.querySelectorAll("tr");
                rows.forEach(r => {
                    r.style.display = r.textContent.toLowerCase().includes(q) ? "" : "none";
                });
            };
        }
    }

    // 2. Populate Communication Table
    function populateCommunicationTable(model) {
        const interfaces = model.interfaces || [];
        const topicConns = model.topic_connections || [];
        const srvConns = model.service_connections || [];
        const actConns = model.action_connections || [];

        let rowsHtml = "";

        if (interfaces.length > 0) {
            interfaces.forEach(item => {
                let badgeClass = "status-pill-blue";
                let typeName = item.interface_type || "Topic";
                if (typeName.toLowerCase().includes("publisher")) { badgeClass = "status-pill-green"; typeName = "Publisher"; }
                else if (typeName.toLowerCase().includes("subscriber")) { badgeClass = "status-pill-cyan"; typeName = "Subscriber"; }
                else if (typeName.toLowerCase().includes("service")) { badgeClass = "status-pill-purple"; typeName = "Service Server"; }
                else if (typeName.toLowerCase().includes("action")) { badgeClass = "status-pill-amber"; typeName = "Action Server"; }
                else if (typeName.toLowerCase().includes("tf")) { badgeClass = "status-pill-rose"; typeName = "TF Broadcaster"; }

                const qos = item.qos_profile ? `${item.qos_profile.reliability || 'RELIABLE'} / ${item.qos_profile.durability || 'VOLATILE'}` : "RELIABLE / VOLATILE";
                const boundary = item.boundary_role || (item.name?.startsWith("/tf") ? "INTERNAL_MATCHED" : "EXTERNAL_FACING");

                rowsHtml += `<tr>
                    <td><span class="status-pill ${badgeClass}">${typeName}</span></td>
                    <td style="font-weight: 600; font-family: var(--font-code); color: var(--accent-cyan);">${escapeHtml(item.name || item.topic || "--")}</td>
                    <td><code>${escapeHtml(item.node_id || item.publisher || "--")}</code></td>
                    <td><code>${escapeHtml(item.subscriber || "--")}</code></td>
                    <td style="font-size: 0.78rem;">${escapeHtml(qos)}</td>
                    <td><span class="status-pill ${boundary === 'INTERNAL_MATCHED' ? 'status-pill-purple' : 'status-pill-green'}">${boundary}</span></td>
                </tr>`;
            });
        } else if (topicConns.length > 0 || srvConns.length > 0) {
            topicConns.forEach(tc => {
                const subs = (tc.subscribers || []).join(", ") || "--";
                rowsHtml += `<tr>
                    <td><span class="status-pill status-pill-green">Topic Pub/Sub</span></td>
                    <td style="font-weight: 600; font-family: var(--font-code); color: var(--accent-cyan);">${escapeHtml(tc.topic || "--")}</td>
                    <td><code>${escapeHtml(tc.publisher || "--")}</code></td>
                    <td><code>${escapeHtml(subs)}</code></td>
                    <td style="font-size: 0.78rem;">RELIABLE / VOLATILE</td>
                    <td><span class="status-pill status-pill-green">INTERNAL_MATCHED</span></td>
                </tr>`;
            });
            srvConns.forEach(sc => {
                const clients = (sc.clients || []).join(", ") || "--";
                rowsHtml += `<tr>
                    <td><span class="status-pill status-pill-purple">Service</span></td>
                    <td style="font-weight: 600; font-family: var(--font-code); color: var(--accent-cyan);">${escapeHtml(sc.service || "--")}</td>
                    <td><code>${escapeHtml(sc.server || "--")}</code></td>
                    <td><code>${escapeHtml(clients)}</code></td>
                    <td style="font-size: 0.78rem;">RELIABLE / VOLATILE</td>
                    <td><span class="status-pill status-pill-purple">SERVICE_SERVER</span></td>
                </tr>`;
            });
        } else {
            rowsHtml = `<tr><td colspan="6" class="text-dim">No communication interfaces extracted.</td></tr>`;
        }

        commTableBody.innerHTML = rowsHtml;

        // Search Filter
        if (commSearch) {
            commSearch.oninput = () => {
                const q = commSearch.value.toLowerCase();
                const rows = commTableBody.querySelectorAll("tr");
                rows.forEach(r => {
                    r.style.display = r.textContent.toLowerCase().includes(q) ? "" : "none";
                });
            };
        }
    }

    // 3. Populate Deployment Table
    function populateDeploymentTable(model) {
        const profiles = model.deployment_profiles || [];
        const launches = model.launch_files || [];

        if (profiles.length === 0 && launches.length === 0) {
            deploymentTableBody.innerHTML = `<tr><td colspan="5" class="text-dim">No launch deployment profiles recovered.</td></tr>`;
            return;
        }

        let html = "";
        if (profiles.length > 0) {
            profiles.forEach(p => {
                const activeNodes = (p.active_nodes || []).map(n => `<code>${escapeHtml(n)}</code>`).join(" ") || "--";
                html += `<tr>
                    <td style="font-weight: 600; color: #fff;">${escapeHtml(p.profile_name || p.name || "--")}</td>
                    <td><span class="status-pill status-pill-blue">${escapeHtml(p.profile_type || "STANDALONE")}</span></td>
                    <td><code>${escapeHtml(p.container_name || "--")}</code></td>
                    <td style="font-size: 0.78rem; color: var(--text-dim);">${escapeHtml(p.launch_file || "--")}</td>
                    <td>${activeNodes}</td>
                </tr>`;
            });
        } else {
            launches.forEach(lf => {
                const nodesCount = (lf.declared_nodes || []).length;
                html += `<tr>
                    <td style="font-weight: 600; color: #fff;">${escapeHtml(lf.filename || "--")}</td>
                    <td><span class="status-pill status-pill-blue">Launch File</span></td>
                    <td><code>standalone</code></td>
                    <td style="font-size: 0.78rem; color: var(--text-dim);">${escapeHtml(lf.filepath || "--")}</td>
                    <td>${nodesCount} declared nodes</td>
                </tr>`;
            });
        }
        deploymentTableBody.innerHTML = html;
    }

    // 4. Populate Subsystems Grid
    function populateSubsystems(subsystems) {
        if (!subsystems || subsystems.length === 0) {
            subsystemsContainer.innerHTML = `<p class="text-dim">No subsystems synthesized.</p>`;
            return;
        }

        let html = "";
        subsystems.forEach(s => {
            const memberNodes = (s.nodes || []).map(n => `<span class="subsystem-node-tag">${escapeHtml(n)}</span>`).join("");
            html += `<div class="subsystem-card">
                <h4><i class="fa-solid fa-cube"></i> ${escapeHtml(s.name)}</h4>
                <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.75rem;">${escapeHtml(s.description || "Synthesized functional subsystem cluster.")}</p>
                <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 0.5rem;">
                    <strong>Cohesion Rationale:</strong> ${escapeHtml(s.cohesion_rationale || "High intra-subsystem communication traffic and shared launch context.")}
                </div>
                <div style="margin-top: 0.5rem;">
                    <strong>Member Nodes (${(s.nodes || []).length}):</strong><br>
                    <div style="margin-top: 0.3rem;">${memberNodes || "<span class='text-dim'>None</span>"}</div>
                </div>
            </div>`;
        });
        subsystemsContainer.innerHTML = html;
    }

    // 5. Populate Lifecycle & Plugins Tables
    function populateLifecycleAndPlugins(model) {
        const nodes = model.nodes || [];
        const lcModel = model.lifecycle_graph;
        let lcHtml = "";

        const lcNodes = nodes.filter(n => n.is_lifecycle);
        if (lcNodes.length > 0) {
            lcNodes.forEach(n => {
                lcHtml += `<tr>
                    <td style="font-weight: 600; color: #fff;">${escapeHtml(n.name || n.class_name)}</td>
                    <td><code>${escapeHtml(n.package_name || "--")}</code></td>
                    <td><span class="status-pill status-pill-purple">Active / Managed</span></td>
                    <td style="font-size: 0.78rem;">on_configure, on_activate, on_deactivate, on_cleanup</td>
                    <td><code>lifecycle_manager</code></td>
                </tr>`;
            });
        } else {
            lcHtml = `<tr><td colspan="5" class="text-dim">No LifecycleNode instances found in this repository.</td></tr>`;
        }
        lifecycleTableBody.innerHTML = lcHtml;

        const plugins = model.plugin_architecture?.plugins || [];
        let plugHtml = "";
        if (plugins.length > 0) {
            plugins.forEach(p => {
                plugHtml += `<tr>
                    <td style="font-weight: 600; color: #fff;"><code>${escapeHtml(p.class_type || p.class_name || "--")}</code></td>
                    <td><code>${escapeHtml(p.base_class_type || "PluginInterface")}</code></td>
                    <td>${escapeHtml(p.package_name || "--")}</td>
                    <td style="font-size: 0.75rem; color: var(--text-dim);">${escapeHtml(p.declaration_file || "--")}</td>
                </tr>`;
            });
        } else {
            plugHtml = `<tr><td colspan="4" class="text-dim">No pluginlib declarations found.</td></tr>`;
        }
        pluginsTableBody.innerHTML = plugHtml;
    }

    // 6. Populate Evidence Traceability Table
    function populateEvidenceTable(model) {
        let items = [];

        // Collect from nodes
        (model.nodes || []).forEach(n => {
            if (n.evidence && n.evidence.length > 0) {
                n.evidence.forEach(ev => {
                    items.push({
                        entity: n.name || n.class_name,
                        type: ev.evidence_type || "node_definition",
                        file: ev.source_file || n.file_path,
                        lines: `${ev.line_start || 1}-${ev.line_end || ev.line_start || 1}`,
                        method: "AST / C++ Symbol Analysis",
                        status: "SOURCE_CONFIRMED"
                    });
                });
            } else if (n.file_path) {
                items.push({
                    entity: n.name || n.class_name,
                    type: "node_declaration",
                    file: n.file_path,
                    lines: `${n.line_number || 1}`,
                    method: "AST Class Visitor",
                    status: "SOURCE_CONFIRMED"
                });
            }
        });

        // Collect from interfaces
        (model.interfaces || []).forEach(iface => {
            if (iface.source_evidence) {
                const ev = iface.source_evidence;
                items.push({
                    entity: iface.name || iface.topic,
                    type: iface.interface_type || "interface_declaration",
                    file: ev.file || ev.source_file,
                    lines: `${ev.line || ev.line_start || 1}`,
                    method: "C++ LibClang / AST Extractor",
                    status: iface.boundary_role === "EXTERNAL_FACING" ? "DEPENDENCY_CONFIRMED" : "SOURCE_CONFIRMED"
                });
            }
        });

        if (items.length === 0) {
            evidenceTableBody.innerHTML = `<tr><td colspan="6" class="text-dim">No source evidence records captured.</td></tr>`;
            return;
        }

        let html = "";
        items.slice(0, 150).forEach(it => {
            const statusClass = it.status === "SOURCE_CONFIRMED" ? "status-pill-green" : "status-pill-amber";
            html += `<tr>
                <td style="font-weight: 600; color: #fff;">${escapeHtml(it.entity || "--")}</td>
                <td><span class="status-pill status-pill-blue">${escapeHtml(it.type)}</span></td>
                <td style="font-size: 0.78rem; font-family: var(--font-code); color: var(--text-dim);">${escapeHtml(it.file || "--")}</td>
                <td><code>L${escapeHtml(it.lines)}</code></td>
                <td style="font-size: 0.78rem;">${escapeHtml(it.method)}</td>
                <td><span class="status-pill ${statusClass}">${escapeHtml(it.status)}</span></td>
            </tr>`;
        });
        evidenceTableBody.innerHTML = html;

        // Search Filter
        if (evidenceSearch) {
            evidenceSearch.oninput = () => {
                const q = evidenceSearch.value.toLowerCase();
                const rows = evidenceTableBody.querySelectorAll("tr");
                rows.forEach(r => {
                    r.style.display = r.textContent.toLowerCase().includes(q) ? "" : "none";
                });
            };
        }
    }

    // Copy Exact Raw Markdown to Clipboard (Preserves headings, tables, mermaid blocks)
    if (btnCopyMd) {
        btnCopyMd.addEventListener("click", () => {
            if (!currentRawMarkdown || currentRawMarkdown.trim().length === 0) {
                alert("No Markdown documentation content is available to copy.");
                return;
            }

            const setSuccessUI = () => {
                const orig = btnCopyMd.innerHTML;
                btnCopyMd.innerHTML = '<i class="fa-solid fa-check"></i> Copied Markdown!';
                btnCopyMd.style.borderColor = "var(--accent-emerald)";
                btnCopyMd.style.color = "var(--accent-emerald)";
                setTimeout(() => {
                    btnCopyMd.innerHTML = orig;
                    btnCopyMd.style.borderColor = "";
                    btnCopyMd.style.color = "";
                }, 2200);
            };

            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(currentRawMarkdown)
                    .then(setSuccessUI)
                    .catch(err => {
                        console.warn("navigator.clipboard error, trying fallback copy:", err);
                        fallbackCopyText(currentRawMarkdown, setSuccessUI);
                    });
            } else {
                fallbackCopyText(currentRawMarkdown, setSuccessUI);
            }
        });
    }

    function fallbackCopyText(text, onSuccess) {
        try {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-9999px";
            textArea.style.top = "-9999px";
            textArea.style.opacity = "0";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            const successful = document.execCommand("copy");
            document.body.removeChild(textArea);
            if (successful && onSuccess) {
                onSuccess();
            } else if (!successful) {
                alert("Clipboard copy operation was not permitted. Please copy manually.");
            }
        } catch (e) {
            console.error("Fallback clipboard error:", e);
            alert("Clipboard access failed. Please select text manually.");
        }
    }

    // Pipeline Step Progress Animation
    function startProgressAnimation() {
        progressBar.style.width = "10%";
        const steps = [
            { id: "step-1", percent: 20 },
            { id: "step-2", percent: 40 },
            { id: "step-3", percent: 60 },
            { id: "step-4", percent: 80 },
            { id: "step-5", percent: 95 }
        ];

        let currentStep = 0;
        progressTimer = setInterval(() => {
            if (currentStep < steps.length) {
                const s = steps[currentStep];
                progressBar.style.width = `${s.percent}%`;
                document.querySelectorAll(".step-item").forEach(item => item.classList.remove("active"));
                const activeStepEl = document.getElementById(s.id);
                if (activeStepEl) activeStepEl.classList.add("active");
                currentStep++;
            }
        }, 800);
    }

    function stopProgressAnimation() {
        if (progressTimer) clearInterval(progressTimer);
        progressBar.style.width = "100%";
        document.querySelectorAll(".step-item").forEach(item => {
            item.classList.remove("active");
            item.classList.add("complete");
        });
    }

    // Error Alert Display
    function showError(msg, title = "Validation / Execution Error") {
        const titleEl = document.getElementById("error-title");
        if (titleEl) {
            titleEl.textContent = title;
        }
        errorMessage.textContent = msg;
        showElement(errorBanner);
    }

    // Utility Helpers
    function showElement(el) { if (el) el.classList.remove("hidden"); }
    function hideElement(el) { if (el) el.classList.add("hidden"); }

    function setButtonLoading(btn, isLoading) {
        if (!btn) return;
        const text = btn.querySelector(".btn-text");
        const spinner = btn.querySelector(".spinner-sm");
        if (isLoading) {
            btn.disabled = true;
            if (text) text.classList.add("hidden");
            if (spinner) spinner.classList.remove("hidden");
        } else {
            btn.disabled = false;
            if (text) text.classList.remove("hidden");
            if (spinner) spinner.classList.add("hidden");
        }
    }

    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Return to Clean Home Page State (Zero Preloaded Documentations)
    function showHomePage() {
        hideElement(errorBanner);
        hideElement(loadingCard);
        hideElement(resultsDashboard);
        const welcomeSection = document.getElementById("welcome-section");
        if (welcomeSection) showElement(welcomeSection);
        currentJobId = null;
        currentModelData = null;
        currentRawMarkdown = null;
        if (runSelector) runSelector.value = "";
        if (repoInput) repoInput.value = "";
        document.querySelectorAll(".preset-pill").forEach(p => p.classList.remove("active"));
        if (window.location.search) {
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    // Check query params to auto-load run if explicitly provided (e.g. ?run=nav2_corrected_pipeline)
    const urlParams = new URLSearchParams(window.location.search);
    const runParam = urlParams.get("run");
    if (runParam) {
        if (runSelector) runSelector.value = runParam;
        loadRunData(runParam);
    } else {
        // Show clean home page with zero preloaded documentations
        showHomePage();
    }
});
