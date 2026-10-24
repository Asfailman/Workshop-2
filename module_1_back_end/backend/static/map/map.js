/**
 * FTMK Campus Live Indoor Navigator - Map Directory & Waze Engine
 * Supports:
 * - Dynamic SVG floorplan rendering (Blocks A to E)
 * - Floor level filtering (L1, L2, L3, L4, All)
 * - Waze-style glowing animated path with flowing dots
 * - Real-time Walker simulation and turn-by-turn guidance
 * - Pan, zoom, and interactive search autocomplete
 */

// Global State
const state = {
  mapData: null,
  currentFloor: 1,
  activeRoute: null,
  startId: "MAIN_ENTRANCE",
  destId: "",
  zoom: 1,
  panX: 0,
  panY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  walkerTimer: null,
  walkerStep: 0,
};

// DOM References
const el = {
  svg: document.getElementById("campusSvg"),
  svgContainer: document.getElementById("svgContainer"),
  zonesLayer: document.getElementById("zonesLayer"),
  bridgesLayer: document.getElementById("bridgesLayer"),
  corridorsLayer: document.getElementById("corridorsLayer"),
  nodesLayer: document.getElementById("nodesLayer"),
  navPathLayer: document.getElementById("navPathLayer"),
  pathGlow: document.getElementById("pathGlow"),
  pathTrack: document.getElementById("pathTrack"),
  pathDots: document.getElementById("pathDots"),
  startPin: document.getElementById("startPin"),
  destPin: document.getElementById("destPin"),
  walkerPin: document.getElementById("walkerPin"),
  startSelect: document.getElementById("startSelect"),
  destSelect: document.getElementById("destSelect"),
  quickSearchInput: document.getElementById("quickSearchInput"),
  quickSearchResults: document.getElementById("quickSearchResults"),
  btnCalculateRoute: document.getElementById("btnCalculateRoute"),
  btnSwapRoute: document.getElementById("btnSwapRoute"),
  btnClearRoute: document.getElementById("btnClearRoute"),
  btnSimulateWalk: document.getElementById("btnSimulateWalk"),
  liveGuidanceCard: document.getElementById("liveGuidanceCard"),
  hudIcon: document.getElementById("hudIcon"),
  hudInstruction: document.getElementById("hudInstruction"),
  hudDistance: document.getElementById("hudDistance"),
  hudTime: document.getElementById("hudTime"),
  hudStepsCount: document.getElementById("hudStepsCount"),
  floorBreadcrumbs: document.getElementById("floorBreadcrumbs"),
  turnStepsList: document.getElementById("turnStepsList"),
  directoryList: document.getElementById("directoryList"),
  nodeTooltip: document.getElementById("nodeTooltip"),
  ttIcon: document.getElementById("ttIcon"),
  ttTitle: document.getElementById("ttTitle"),
  ttLocation: document.getElementById("ttLocation"),
  ttDesc: document.getElementById("ttDesc"),
  ttSetStart: document.getElementById("ttSetStart"),
  ttSetDest: document.getElementById("ttSetDest"),
  btnZoomIn: document.getElementById("btnZoomIn"),
  btnZoomOut: document.getElementById("btnZoomOut"),
  btnResetZoom: document.getElementById("btnResetZoom"),
  btnResetView: document.getElementById("btnResetView"),
};

// =============================================================================
// 1. DATA INITIALIZATION & BOOTSTRAP
// =============================================================================

async function init() {
  try {
    const res = await fetch("/api/v1/map/data");
    const data = await res.json();
    if (data.status !== "success") throw new Error("Could not load map data");

    state.mapData = data;

    // Populate dropdowns and directory
    populateSelects();
    renderDirectory("all");

    // Render SVG Map layers
    renderZones();
    renderBridges();
    renderCorridors();
    renderNodes();

    // Setup Event Listeners
    setupEventListeners();
    setupPanZoom();

    // Check URL parameters (e.g. ?start=...&dest=...)
    const params = new URLSearchParams(window.location.search);
    const urlStart = params.get("start");
    const urlDest = params.get("dest");

    if (urlStart && state.mapData.nodes.some(n => n.id === urlStart)) {
      state.startId = urlStart;
      el.startSelect.value = urlStart;
    }
    if (urlDest && state.mapData.nodes.some(n => n.id === urlDest)) {
      state.destId = urlDest;
      el.destSelect.value = urlDest;
      calculateRoute(state.startId, state.destId);
    }

  } catch (err) {
    console.error("Initialization failed:", err);
  }
}

// =============================================================================
// 2. SVG MAP RENDERING ENGINE
// =============================================================================

function renderZones() {
  el.zonesLayer.innerHTML = "";
  const blocks = state.mapData.blocks;

  for (const [key, bld] of Object.entries(blocks)) {
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("class", "block-zone-group");

    // Background block rectangle
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", bld.x);
    rect.setAttribute("y", bld.y);
    rect.setAttribute("width", bld.width);
    rect.setAttribute("height", bld.height);
    rect.setAttribute("stroke", bld.color);
    rect.setAttribute("class", "block-zone-rect");
    group.appendChild(rect);

    // Title label
    const title = document.createElementNS("http://www.w3.org/2000/svg", "text");
    title.setAttribute("x", bld.x + 16);
    title.setAttribute("y", bld.y + 26);
    title.setAttribute("fill", bld.color);
    title.setAttribute("class", "block-title-text");
    title.textContent = bld.name;
    group.appendChild(title);

    // Subtitle Badge
    const badge = document.createElementNS("http://www.w3.org/2000/svg", "text");
    badge.setAttribute("x", bld.x + 16);
    badge.setAttribute("y", bld.y + 42);
    badge.setAttribute("class", "block-badge-text");
    badge.textContent = bld.badge;
    group.appendChild(badge);

    el.zonesLayer.appendChild(group);
  }
}

function renderBridges() {
  el.bridgesLayer.innerHTML = "";
  // Level 2 Bridge between Block A and Block B
  const bridgeA_B = document.createElementNS("http://www.w3.org/2000/svg", "line");
  bridgeA_B.setAttribute("x1", "500");
  bridgeA_B.setAttribute("y1", "650");
  bridgeA_B.setAttribute("x2", "370");
  bridgeA_B.setAttribute("y2", "570");
  bridgeA_B.setAttribute("class", "bridge-path");
  el.bridgesLayer.appendChild(bridgeA_B);

  const bridgeLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
  bridgeLabel.setAttribute("x", "430");
  bridgeLabel.setAttribute("y", "600");
  bridgeLabel.setAttribute("class", "bridge-label");
  bridgeLabel.textContent = "🌉 Level 2 Bridge (A ⇄ B)";
  el.bridgesLayer.appendChild(bridgeLabel);
}

function renderCorridors() {
  el.corridorsLayer.innerHTML = "";
  const edges = state.mapData.edges;
  const nodeMap = getNodeMap();

  edges.forEach(edge => {
    const src = nodeMap[edge.source];
    const tgt = nodeMap[edge.target];
    if (!src || !tgt) return;

    // Check floor visibility
    const isVisible = (state.currentFloor === "all") || (src.floor === state.currentFloor && tgt.floor === state.currentFloor);
    if (!isVisible) return;

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", src.x);
    line.setAttribute("y1", src.y);
    line.setAttribute("x2", tgt.x);
    line.setAttribute("y2", tgt.y);
    line.setAttribute("class", `corridor-edge ${isVisible ? "floor-active" : ""}`);
    el.corridorsLayer.appendChild(line);
  });
}

function renderNodes() {
  el.nodesLayer.innerHTML = "";
  const nodes = state.mapData.nodes;

  nodes.forEach(node => {
    // Check floor filter
    const isVisible = (state.currentFloor === "all") || (node.floor === state.currentFloor);
    if (!isVisible) return;

    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("class", "node-group");
    group.setAttribute("data-id", node.id);
    group.setAttribute("transform", `translate(${node.x}, ${node.y})`);

    const isHighlight = node.id === state.startId || node.id === state.destId;
    if (isHighlight) group.classList.add("active-target");

    const radius = node.is_facility ? 14 : 7;

    // Halo circle
    const halo = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    halo.setAttribute("r", radius);
    halo.setAttribute("class", "node-halo");
    group.appendChild(halo);

    // Core circle
    const core = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    core.setAttribute("r", radius - 3);
    core.setAttribute("class", "node-core");
    group.appendChild(core);

    // Icon or Dot
    if (node.is_facility) {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("y", "4");
      text.setAttribute("font-size", radius > 10 ? "11" : "8");
      text.textContent = node.icon || "📍";
      group.appendChild(text);

      // Label below
      const lbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
      lbl.setAttribute("y", radius + 11);
      lbl.setAttribute("class", "node-label-svg");
      lbl.textContent = truncateText(node.label || node.name, 18);
      group.appendChild(lbl);
    }

    // Click handler for tooltip
    group.addEventListener("click", (e) => {
      e.stopPropagation();
      showTooltip(node, e);
    });

    el.nodesLayer.appendChild(group);
  });
}

// =============================================================================
// 3. WAZE-STYLE GLOWING & FLOWING DOT ROUTE ENGINE
// =============================================================================

async function calculateRoute(startId, destId) {
  if (!startId || !destId || startId === destId) {
    alert("Please select different Start and Destination locations.");
    return;
  }

  try {
    const url = `/api/v1/map/route?start_id=${encodeURIComponent(startId)}&destination_id=${encodeURIComponent(destId)}`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.status !== "success") {
      alert("Route Error: " + (data.detail || "Could not calculate route."));
      return;
    }

    state.activeRoute = data;

    // Build SVG Path Definition
    const pathD = buildSvgPathString(data.points);
    el.pathGlow.setAttribute("d", pathD);
    el.pathTrack.setAttribute("d", pathD);
    el.pathDots.setAttribute("d", pathD);

    // Position Start & Destination Beacons
    const startPt = data.points[0];
    const destPt = data.points[data.points.length - 1];

    el.startPin.setAttribute("transform", `translate(${startPt.x}, ${startPt.y})`);
    el.startPin.classList.remove("hidden");

    el.destPin.setAttribute("transform", `translate(${destPt.x}, ${destPt.y})`);
    el.destPin.classList.remove("hidden");

    // Display Waze Live Guidance Card
    displayLiveGuidance(data);

    // If destination is on another floor, automatically adapt or highlight floor switcher
    if (startPt.floor !== state.currentFloor && state.currentFloor !== "all") {
      switchFloor(startPt.floor);
    }

    // Re-render nodes to update highlights
    renderNodes();

    // Auto-fit viewport to show entire route
    fitRouteInView(data.points);

  } catch (err) {
    console.error("Routing error:", err);
  }
}

function buildSvgPathString(points) {
  if (!points || points.length === 0) return "";
  let d = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    d += ` L ${points[i].x} ${points[i].y}`;
  }
  return d;
}

function displayLiveGuidance(route) {
  el.liveGuidanceCard.classList.remove("hidden");

  // Primary direction HUD
  const firstInstruction = route.instructions[0] || `Head towards ${route.destination_name}`;
  el.hudInstruction.textContent = firstInstruction;
  el.hudDistance.textContent = `${route.total_distance} m`;
  el.hudTime.textContent = route.estimated_time_formatted;
  el.hudStepsCount.textContent = `${route.instructions.length} Steps`;

  // Determine directional icon
  el.hudIcon.textContent = getDirectionIcon(firstInstruction);

  // Floor Transition Breadcrumbs
  el.floorBreadcrumbs.innerHTML = "";
  if (route.floor_transitions && route.floor_transitions.length > 1) {
    route.floor_transitions.forEach((trans, idx) => {
      if (idx > 0) {
        const arrow = document.createElement("span");
        arrow.className = "crumb-arrow";
        arrow.textContent = "🪜➔";
        el.floorBreadcrumbs.appendChild(arrow);
      }
      const crumb = document.createElement("button");
      crumb.className = `floor-crumb ${trans.floor === state.currentFloor ? "active" : ""}`;
      crumb.textContent = `Level ${trans.floor}`;
      crumb.title = `Switch to Level ${trans.floor} view`;
      crumb.addEventListener("click", () => switchFloor(trans.floor));
      el.floorBreadcrumbs.appendChild(crumb);
    });
  } else {
    const single = document.createElement("span");
    single.className = "floor-crumb active";
    single.textContent = `All on Level ${route.points[0].floor}`;
    el.floorBreadcrumbs.appendChild(single);
  }

  // Turn-by-Turn Instruction List
  el.turnStepsList.innerHTML = "";
  route.instructions.forEach((inst, idx) => {
    const li = document.createElement("li");
    li.className = `turn-step-item ${idx === 0 ? "active" : ""}`;
    li.textContent = `${idx + 1}. ${inst}`;
    el.turnStepsList.appendChild(li);
  });
}

function getDirectionIcon(text) {
  const lower = text.toLowerCase();
  if (lower.includes("stairs") || lower.includes("stair")) return "🪜";
  if (lower.includes("bridge")) return "🌉";
  if (lower.includes("right")) return "➡️";
  if (lower.includes("left")) return "⬅️";
  if (lower.includes("straight") || lower.includes("follow") || lower.includes("walkway")) return "⬆️";
  if (lower.includes("arrive") || lower.includes("door")) return "🎯";
  return "🚶";
}

// =============================================================================
// 4. WAZE WALKER SIMULATION (ANIMATED AVATAR)
// =============================================================================

function startWalkingSimulation() {
  if (!state.activeRoute || !state.activeRoute.points) return;
  const points = state.activeRoute.points;
  const instructions = state.activeRoute.instructions;

  if (state.walkerTimer) {
    clearInterval(state.walkerTimer);
  }

  state.walkerStep = 0;
  el.walkerPin.classList.remove("hidden");
  el.btnSimulateWalk.innerHTML = "<span>⏸</span> Simulating...";

  function advanceStep() {
    if (state.walkerStep >= points.length) {
      clearInterval(state.walkerTimer);
      state.walkerTimer = null;
      el.btnSimulateWalk.innerHTML = "<span>▶</span> Replay Walking (Waze)";
      el.hudInstruction.textContent = `🎉 You have arrived at ${state.activeRoute.destination_name}!`;
      el.hudIcon.textContent = "🏁";
      return;
    }

    const currentPt = points[state.walkerStep];
    el.walkerPin.setAttribute("transform", `translate(${currentPt.x}, ${currentPt.y})`);

    // Auto-switch floor if walker climbs stairs
    if (currentPt.floor !== state.currentFloor && state.currentFloor !== "all") {
      switchFloor(currentPt.floor);
    }

    // Update instruction highlight
    const stepItems = el.turnStepsList.querySelectorAll(".turn-step-item");
    stepItems.forEach((item, idx) => {
      item.classList.toggle("active", idx === state.walkerStep);
    });

    if (instructions[state.walkerStep]) {
      el.hudInstruction.textContent = instructions[state.walkerStep];
      el.hudIcon.textContent = getDirectionIcon(instructions[state.walkerStep]);
    }

    state.walkerStep++;
  }

  advanceStep();
  state.walkerTimer = setInterval(advanceStep, 1400);
}

function clearRoute() {
  if (state.walkerTimer) {
    clearInterval(state.walkerTimer);
    state.walkerTimer = null;
  }
  state.activeRoute = null;
  el.pathGlow.setAttribute("d", "");
  el.pathTrack.setAttribute("d", "");
  el.pathDots.setAttribute("d", "");
  el.startPin.classList.add("hidden");
  el.destPin.classList.add("hidden");
  el.walkerPin.classList.add("hidden");
  el.liveGuidanceCard.classList.add("hidden");
  el.btnSimulateWalk.innerHTML = "<span>▶</span> Simulate Walking (Waze)";
  renderNodes();
}

// =============================================================================
// 5. PAN, ZOOM & VIEW CONTROLS
// =============================================================================

function setupPanZoom() {
  const container = el.svgContainer;

  container.addEventListener("mousedown", (e) => {
    state.isDragging = true;
    state.dragStartX = e.clientX - state.panX;
    state.dragStartY = e.clientY - state.panY;
  });

  window.addEventListener("mousemove", (e) => {
    if (!state.isDragging) return;
    state.panX = e.clientX - state.dragStartX;
    state.panY = e.clientY - state.dragStartY;
    updateSvgTransform();
  });

  window.addEventListener("mouseup", () => {
    state.isDragging = false;
  });

  container.addEventListener("wheel", (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.88;
    state.zoom = Math.min(Math.max(0.6, state.zoom * zoomFactor), 4.0);
    updateSvgTransform();
  }, { passive: false });
}

function updateSvgTransform() {
  el.svg.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${state.zoom})`;
}

function resetZoom() {
  state.zoom = 1;
  state.panX = 0;
  state.panY = 0;
  updateSvgTransform();
}

function fitRouteInView(points) {
  if (!points || points.length === 0) return;
  const xs = points.map(p => p.x);
  const ys = points.map(p => p.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;

  // Center on route
  state.panX = (500 - centerX) * 0.5;
  state.panY = (400 - centerY) * 0.5;
  state.zoom = 1.15;
  updateSvgTransform();
}

// =============================================================================
// 6. TOOLTIP, SEARCH & CONTROLS EVENT HANDLERS
// =============================================================================

function showTooltip(node, event) {
  el.ttIcon.textContent = node.icon || "📍";
  el.ttTitle.textContent = node.label || node.name;
  el.ttLocation.textContent = `${node.building}, Level ${node.floor}`;
  el.ttDesc.textContent = node.description || "Campus destination in FTMK.";

  // Position relative to viewport
  const rect = el.svgContainer.getBoundingClientRect();
  const screenX = event.clientX - rect.left;
  const screenY = event.clientY - rect.top;

  el.nodeTooltip.style.left = `${screenX}px`;
  el.nodeTooltip.style.top = `${screenY}px`;
  el.nodeTooltip.classList.remove("hidden");

  // Actions
  el.ttSetStart.onclick = () => {
    state.startId = node.id;
    el.startSelect.value = node.id;
    el.nodeTooltip.classList.add("hidden");
    if (state.destId) calculateRoute(state.startId, state.destId);
  };

  el.ttSetDest.onclick = () => {
    state.destId = node.id;
    el.destSelect.value = node.id;
    el.nodeTooltip.classList.add("hidden");
    calculateRoute(state.startId, state.destId);
  };
}

function switchFloor(floor) {
  state.currentFloor = floor === "all" ? "all" : parseInt(floor);

  document.querySelectorAll(".floor-btn").forEach(btn => {
    const bf = btn.getAttribute("data-floor");
    btn.classList.toggle("active", bf === String(floor));
  });

  renderCorridors();
  renderNodes();
}

function setupEventListeners() {
  // Floor switcher buttons
  document.querySelectorAll(".floor-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      switchFloor(btn.getAttribute("data-floor"));
    });
  });

  // Calculate route button
  el.btnCalculateRoute.addEventListener("click", () => {
    calculateRoute(el.startSelect.value, el.destSelect.value);
  });

  // Swap button
  el.btnSwapRoute.addEventListener("click", () => {
    const s = el.startSelect.value;
    const d = el.destSelect.value;
    el.startSelect.value = d;
    el.destSelect.value = s;
    state.startId = d;
    state.destId = s;
    if (state.startId && state.destId) calculateRoute(state.startId, state.destId);
  });

  // Clear button
  el.btnClearRoute.addEventListener("click", clearRoute);

  // Simulate Walking button
  el.btnSimulateWalk.addEventListener("click", startWalkingSimulation);

  // Quick Chips
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const dest = chip.getAttribute("data-dest");
      el.destSelect.value = dest;
      state.destId = dest;
      calculateRoute(el.startSelect.value, dest);
    });
  });

  // Zoom toolbar
  el.btnZoomIn.addEventListener("click", () => {
    state.zoom = Math.min(state.zoom * 1.25, 4.0);
    updateSvgTransform();
  });
  el.btnZoomOut.addEventListener("click", () => {
    state.zoom = Math.max(state.zoom * 0.8, 0.6);
    updateSvgTransform();
  });
  el.btnResetZoom.addEventListener("click", resetZoom);
  el.btnResetView.addEventListener("click", resetZoom);

  // Hide tooltip on canvas click
  window.addEventListener("click", () => {
    el.nodeTooltip.classList.add("hidden");
    el.quickSearchResults.classList.add("hidden");
  });

  // Sidebar Tab Switcher
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const tabId = btn.getAttribute("data-tab");
      document.getElementById(tabId).classList.add("active");
    });
  });

  // Quick search input autocomplete
  el.quickSearchInput.addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      el.quickSearchResults.classList.add("hidden");
      return;
    }
    const matches = state.mapData.nodes.filter(n =>
      n.name.toLowerCase().includes(q) || (n.label && n.label.toLowerCase().includes(q))
    ).slice(0, 8);

    el.quickSearchResults.innerHTML = "";
    if (matches.length > 0) {
      matches.forEach(m => {
        const item = document.createElement("div");
        item.className = "search-dropdown-item";
        item.innerHTML = `
          <span style="font-size:18px">${m.icon}</span>
          <div class="search-item-info">
            <span class="search-item-title">${m.label || m.name}</span>
            <span class="search-item-meta">${m.building}, Level ${m.floor}</span>
          </div>
        `;
        item.addEventListener("click", () => {
          el.destSelect.value = m.id;
          state.destId = m.id;
          el.quickSearchInput.value = "";
          el.quickSearchResults.classList.add("hidden");
          calculateRoute(el.startSelect.value, m.id);
        });
        el.quickSearchResults.appendChild(item);
      });
      el.quickSearchResults.classList.remove("hidden");
    } else {
      el.quickSearchResults.classList.add("hidden");
    }
  });

  // Directory filter pills
  document.querySelectorAll(".cat-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      document.querySelectorAll(".cat-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      renderDirectory(pill.getAttribute("data-cat"));
    });
  });
}

function populateSelects() {
  const nodes = state.mapData.nodes.filter(n => n.is_facility);
  el.startSelect.innerHTML = "";
  el.destSelect.innerHTML = '<option value="">Select Destination...</option>';

  nodes.forEach(n => {
    const opt1 = document.createElement("option");
    opt1.value = n.id;
    opt1.textContent = `${n.icon} ${n.label || n.name} (${n.building}, L${n.floor})`;
    el.startSelect.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = n.id;
    opt2.textContent = `${n.icon} ${n.label || n.name} (${n.building}, L${n.floor})`;
    el.destSelect.appendChild(opt2);
  });

  el.startSelect.value = state.startId;
}

function renderDirectory(category) {
  el.directoryList.innerHTML = "";
  const nodes = state.mapData.nodes.filter(n => n.is_facility);
  const filtered = category === "all" ? nodes : nodes.filter(n => n.category === category);

  filtered.forEach(n => {
    const card = document.createElement("div");
    card.className = "dir-card";
    card.innerHTML = `
      <div class="dir-main">
        <span class="dir-icon">${n.icon}</span>
        <div>
          <div class="dir-name">${n.label || n.name}</div>
          <div class="dir-badge">${n.building} • Level ${n.floor}</div>
        </div>
      </div>
      <button class="icon-btn" style="padding: 4px 10px; font-size: 11px;">Navigate</button>
    `;
    card.addEventListener("click", () => {
      el.destSelect.value = n.id;
      state.destId = n.id;
      // Switch tab to Route
      document.querySelector('[data-tab="routeTab"]').click();
      calculateRoute(el.startSelect.value, n.id);
    });
    el.directoryList.appendChild(card);
  });
}

// Helpers
function getNodeMap() {
  const map = {};
  if (state.mapData) {
    state.mapData.nodes.forEach(n => { map[n.id] = n; });
  }
  return map;
}

function truncateText(str, max) {
  if (!str) return "";
  return str.length > max ? str.substring(0, max - 2) + ".." : str;
}

// Boot application on DOM ready
document.addEventListener("DOMContentLoaded", init);
