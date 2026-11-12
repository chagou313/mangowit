/* Interactive knowledge graph: search, filter, and explore a node's relations. */
(function () {
    "use strict";

    var root = document.querySelector(".kg");
    if (!root) return;

    var COLORS = {
        female: { node: "#d9548f", soft: "#f3c3d8" },
        male: { node: "#3f6fd1", soft: "#c3d2f1" },
        dim: "#e3e0ea",
        edge: "rgba(107, 99, 128, 0.35)",
        edgeActive: "#7e57c2",
        label: "#2b2540",
        labelDim: "#c4bfd0"
    };
    var GROUP_NAMES = { female: "女生", male: "男生" };

    var statusEl = document.getElementById("kg-status");
    var sideEl = document.getElementById("kg-side");
    var typeSelect = document.getElementById("kg-type");
    var searchForm = document.getElementById("kg-search");
    var searchInput = document.getElementById("kg-search-input");
    var datalist = document.getElementById("kg-labels");
    var chips = root.querySelectorAll(".kg-chips button");
    var defaultSide = sideEl.innerHTML;

    function setStatus(text) {
        statusEl.textContent = text;
        statusEl.hidden = !text;
    }

    if (typeof vis === "undefined") {
        setStatus("图谱组件加载失败，请检查网络后刷新页面。");
        return;
    }

    fetch(root.dataset.src)
        .then(function (response) {
            if (!response.ok) throw new Error(response.status);
            return response.json();
        })
        .then(build)
        .catch(function () {
            setStatus("图谱数据加载失败，请刷新页面重试。");
        });

    function build(data) {
        var byId = {};
        var outgoing = {};
        var incoming = {};
        data.nodes.forEach(function (n) {
            byId[n.id] = n;
            outgoing[n.id] = [];
            incoming[n.id] = [];
        });
        data.edges.forEach(function (e, i) {
            e.id = "e" + i;
            outgoing[e.from].push(e);
            incoming[e.to].push(e);
        });
        function degree(id) {
            return outgoing[id].length + incoming[id].length;
        }

        document.getElementById("kg-node-count").textContent = data.nodes.length;
        document.getElementById("kg-edge-count").textContent = data.edges.length;

        var types = {};
        data.nodes.forEach(function (n) { types[n.type] = (types[n.type] || 0) + 1; });
        Object.keys(types)
            .sort(function (a, b) { return types[b] - types[a] || a.localeCompare(b, "zh"); })
            .forEach(function (t) {
                var opt = document.createElement("option");
                opt.value = t;
                opt.textContent = t + "（" + types[t] + "）";
                typeSelect.appendChild(opt);
            });
        data.nodes.forEach(function (n) {
            var opt = document.createElement("option");
            opt.value = n.label;
            datalist.appendChild(opt);
        });

        var maxDegree = data.nodes.reduce(function (m, n) { return Math.max(m, degree(n.id)); }, 0);
        // Chain-like graphs have no hubs, so label every node and space them out instead.
        var flat = maxDegree <= 3;
        var HUB_DEGREE = flat ? 0 : 4;
        var LABEL_ZOOM = 0.85;
        var zoomedIn = false;
        var stateOf = {};

        function nodeStyle(n, state) {
            var c = COLORS[n.group];
            var dim = state === "dim";
            var showLabel = state === "focus" || state === "near" || (!dim && (zoomedIn || degree(n.id) >= HUB_DEGREE));
            return {
                id: n.id,
                label: showLabel ? n.label : "",
                title: n.label + "（" + n.type + "）",
                group: n.group,
                kgType: n.type,
                shape: "dot",
                size: 9 + Math.min(degree(n.id), 12) * 2.2,
                borderWidth: state === "focus" ? 4 : 2,
                color: {
                    background: dim ? COLORS.dim : c.node,
                    border: dim ? COLORS.dim : (state === "focus" ? "#2b2540" : "#ffffff"),
                    highlight: { background: c.node, border: "#2b2540" },
                    hover: { background: c.node, border: "#2b2540" }
                },
                font: {
                    size: state === "focus" ? 17 : 14,
                    color: dim ? COLORS.labelDim : COLORS.label,
                    strokeWidth: dim ? 0 : 4,
                    strokeColor: "#ffffff",
                    face: "'Microsoft YaHei', 'PingFang SC', sans-serif"
                }
            };
        }
        function edgeStyle(e, state) {
            var active = state === "active";
            return {
                id: e.id,
                from: e.from,
                to: e.to,
                title: e.label || undefined,
                arrows: { to: { enabled: true, scaleFactor: 0.5 } },
                width: active ? 2.2 : 1,
                color: { color: active ? COLORS.edgeActive : (state === "dim" ? "rgba(200,196,210,0.25)" : COLORS.edge) },
                smooth: { type: "continuous" }
            };
        }

        // Start girls' topics on the left and boys' on the right so the two groups settle apart.
        var nodes = new vis.DataSet(data.nodes.map(function (n, i) {
            var item = nodeStyle(n);
            item.x = (n.group === "female" ? -1 : 1) * (300 + (i % 7) * 25);
            item.y = ((i * 97) % 600) - 300;
            return item;
        }));
        var edges = new vis.DataSet(data.edges.map(function (e) { return edgeStyle(e); }));

        var filter = { group: "all", type: "" };
        function visible(n) {
            return (filter.group === "all" || n.group === filter.group) && (!filter.type || n.kgType === filter.type);
        }
        var nodeView = new vis.DataView(nodes, { filter: visible });
        var edgeView = new vis.DataView(edges, {
            filter: function (e) {
                var a = nodes.get(e.from), b = nodes.get(e.to);
                return visible(a) && visible(b);
            }
        });

        var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        var network = new vis.Network(
            document.getElementById("kg-network"),
            { nodes: nodeView, edges: edgeView },
            {
                physics: {
                    solver: "forceAtlas2Based",
                    forceAtlas2Based: flat
                        ? { gravitationalConstant: -70, centralGravity: 0.015, springLength: 120, springConstant: 0.06, avoidOverlap: 0.8 }
                        : { gravitationalConstant: -38, centralGravity: 0.03, springLength: 70, springConstant: 0.08, avoidOverlap: 0.5 },
                    stabilization: { iterations: 500, updateInterval: 50 },
                    minVelocity: 0.75
                },
                interaction: { hover: true, tooltipDelay: 150, navigationButtons: false, keyboard: false },
                layout: { improvedLayout: data.nodes.length < 120 }
            }
        );

        network.on("stabilizationProgress", function (p) {
            setStatus("正在排布知识点… " + Math.round((p.iterations / p.total) * 100) + "%");
        });
        network.once("stabilizationIterationsDone", function () {
            setStatus("");
            network.setOptions({ physics: false });
            network.fit({ animation: false });
        });

        function restyleNodes() {
            nodes.update(data.nodes.map(function (n) { return nodeStyle(n, stateOf[n.id]); }));
        }
        network.on("zoom", function () {
            var next = network.getScale() >= LABEL_ZOOM;
            if (next !== zoomedIn) {
                zoomedIn = next;
                restyleNodes();
            }
        });
        network.on("animationFinished", function () {
            var next = network.getScale() >= LABEL_ZOOM;
            if (next !== zoomedIn) {
                zoomedIn = next;
                restyleNodes();
            }
        });

        var selected = null;

        function relationList(list, key) {
            if (!list.length) return '<p class="kg-empty">暂无</p>';
            return '<ul class="kg-links">' + list.map(function (e) {
                var other = byId[e[key]];
                return '<li><button type="button" data-go="' + other.id + '">' +
                    '<span class="kg-rel">' + escapeHtml(e.label || "相关") + '</span>' +
                    '<span>' + escapeHtml(other.label) + '</span></button></li>';
            }).join("") + "</ul>";
        }

        function renderSide(id) {
            if (!id) {
                var picks, heading, note;
                if (flat) {
                    picks = data.nodes.filter(function (n) { return !incoming[n.id].length && outgoing[n.id].length; });
                    heading = "可以从这里开始";
                    note = function (n) { return GROUP_NAMES[n.group]; };
                } else {
                    picks = data.nodes.slice().sort(function (a, b) { return degree(b.id) - degree(a.id); });
                    heading = "关联最多的知识点";
                    note = function (n) { return degree(n.id) + " 条关系"; };
                }
                sideEl.innerHTML = defaultSide +
                    "<h3>" + heading + '</h3><ul class="kg-links">' + picks.slice(0, 6).map(function (n) {
                        return '<li><button type="button" data-go="' + n.id + '">' +
                            '<span class="kg-rel">' + note(n) + '</span>' +
                            '<span>' + escapeHtml(n.label) + '</span></button></li>';
                    }).join("") + "</ul>";
                return;
            }
            var n = byId[id];
            sideEl.innerHTML =
                "<h2>" + escapeHtml(n.label) + "</h2>" +
                '<div class="kg-tags"><span class="kg-tag ' + n.group + '">' + GROUP_NAMES[n.group] + "</span>" +
                '<span class="kg-tag">' + escapeHtml(n.type) + "</span></div>" +
                "<h3>由它引出（" + outgoing[id].length + "）</h3>" + relationList(outgoing[id], "to") +
                "<h3>指向它（" + incoming[id].length + "）</h3>" + relationList(incoming[id], "from") +
                '<h3>想深入了解？</h3><p class="kg-hint">去 <a href="' + escapeHtml(root.dataset.ai) + '" style="color: var(--kg-accent)">问小青芒</a> 输入“' +
                escapeHtml(n.label) + '”试试。</p>';
        }

        function select(id, focus) {
            selected = id;
            var neighbors = {};
            if (id) {
                neighbors[id] = true;
                outgoing[id].forEach(function (e) { neighbors[e.to] = true; });
                incoming[id].forEach(function (e) { neighbors[e.from] = true; });
            }
            stateOf = {};
            data.nodes.forEach(function (n) {
                stateOf[n.id] = !id ? undefined : n.id === id ? "focus" : neighbors[n.id] ? "near" : "dim";
            });
            restyleNodes();
            edges.update(data.edges.map(function (e) {
                var touches = id && (e.from === id || e.to === id);
                return edgeStyle(e, !id ? undefined : touches ? "active" : "dim");
            }));
            renderSide(id);
            if (id && focus) {
                if (!nodeView.get(id)) resetFilters();
                network.selectNodes([id]);
                network.focus(id, { scale: 1.1, animation: reduceMotion ? false : { duration: 500, easingFunction: "easeInOutQuad" } });
            }
        }

        function resetFilters() {
            filter.group = "all";
            filter.type = "";
            typeSelect.value = "";
            chips.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.group === "all")); });
            nodeView.refresh();
            edgeView.refresh();
        }

        network.on("click", function (params) {
            select(params.nodes.length ? params.nodes[0] : null, false);
        });

        sideEl.addEventListener("click", function (event) {
            var btn = event.target.closest("[data-go]");
            if (btn) select(btn.dataset.go, true);
        });

        searchForm.addEventListener("submit", function (event) {
            event.preventDefault();
            var q = searchInput.value.trim();
            if (!q) return;
            var match = data.nodes.find(function (n) { return n.label === q; }) ||
                data.nodes.find(function (n) { return n.label.indexOf(q) !== -1; });
            if (match) {
                select(match.id, true);
            } else {
                sideEl.innerHTML = "<h2>没有找到“" + escapeHtml(q) + "”</h2>" +
                    '<p class="kg-hint">换个更短的关键词试试，或者从下拉提示里选择一个知识点。</p>';
            }
        });

        chips.forEach(function (btn) {
            btn.addEventListener("click", function () {
                filter.group = btn.dataset.group;
                chips.forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
                applyFilter();
            });
        });
        typeSelect.addEventListener("change", function () {
            filter.type = typeSelect.value;
            applyFilter();
        });
        function applyFilter() {
            nodeView.refresh();
            edgeView.refresh();
            if (selected && !nodeView.get(selected)) select(null);
            network.fit({ animation: reduceMotion ? false : { duration: 400 } });
        }

        document.getElementById("kg-fit").addEventListener("click", function () {
            network.fit({ animation: reduceMotion ? false : { duration: 400 } });
        });

        renderSide(null);
    }

    function escapeHtml(text) {
        return String(text).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }
})();
