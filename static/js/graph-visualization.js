// Knowledge Graph Visualization using D3.js and Cytoscape.js

class KnowledgeGraphVisualizer {
    constructor(containerId) {
        this.containerId = containerId;
        this.cy = null;
        this.fullscreenCy = null;
        this.currentEmployee = null;
        this.graphData = null;
        this.isInitialized = false;
        this.isFullscreen = false;
    }

    async initialize() {
        if (this.isInitialized) return;

        // Initialize Cytoscape
        this.cy = cytoscape({
            container: document.getElementById(this.containerId),

            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': '#667eea',
                        'label': 'data(label)',
                        'color': '#ffffff',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px',
                        'font-weight': 'bold',
                        'width': 'mapData(score, 0, 100, 20, 60)',
                        'height': 'mapData(score, 0, 100, 20, 60)',
                        'border-width': 2,
                        'border-color': '#ffffff',
                        'text-outline-color': '#667eea',
                        'text-outline-width': 2
                    }
                },
                {
                    selector: 'node[type="employee"]',
                    style: {
                        'background-color': '#28a745',
                        'shape': 'round-rectangle'
                    }
                },
                {
                    selector: 'node[type="skill"]',
                    style: {
                        'background-color': '#17a2b8',
                        'shape': 'ellipse'
                    }
                },
                {
                    selector: 'node[type="education"]',
                    style: {
                        'background-color': '#ffc107',
                        'shape': 'diamond'
                    }
                },
                {
                    selector: 'node[type="experience"]',
                    style: {
                        'background-color': '#dc3545',
                        'shape': 'triangle'
                    }
                },
                {
                    selector: 'node.highlighted',
                    style: {
                        'border-width': 4,
                        'border-color': '#ff4757',
                        'background-color': '#ff6b7a'
                    }
                },
                {
                    selector: 'node.selected',
                    style: {
                        'border-width': 6,
                        'border-color': '#2f3542',
                        'background-color': '#ff9ff3'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 'mapData(similarity, 0, 1, 1, 8)',
                        'line-color': '#ddd',
                        'target-arrow-color': '#ddd',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'opacity': 'mapData(similarity, 0, 1, 0.3, 1)'
                    }
                },
                {
                    selector: 'edge.highlighted',
                    style: {
                        'line-color': '#ff4757',
                        'target-arrow-color': '#ff4757',
                        'width': 4,
                        'opacity': 1
                    }
                }
            ],

            layout: {
                name: 'cose',
                idealEdgeLength: 100,
                nodeOverlap: 20,
                refresh: 20,
                fit: true,
                padding: 30,
                randomize: false,
                componentSpacing: 100,
                nodeRepulsion: 400000,
                edgeElasticity: 100,
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000,
                initialTemp: 200,
                coolingFactor: 0.95,
                minTemp: 1.0
            },

            wheelSensitivity: 0.2,
            minZoom: 0.1,
            maxZoom: 3
        });

        this.bindEvents();
        this.isInitialized = true;
    }

    bindEvents() {
        // Node click events
        this.cy.on('tap', 'node', (evt) => {
            const node = evt.target;
            this.selectNode(node);
        });

        // Node hover events
        this.cy.on('mouseover', 'node', (evt) => {
            const node = evt.target;
            this.highlightNode(node);
        });

        this.cy.on('mouseout', 'node', (evt) => {
            this.clearHighlights();
        });

        // Pan and zoom events
        this.cy.on('zoom pan', () => {
            this.updateGraphControls();
        });
    }

    async loadEmployeeGraph(employeeId, depth = 2) {
        try {
            this.currentEmployee = employeeId;

            // Show loading state
            this.showGraphLoading();

            // Fetch graph data
            const response = await fetch(`/api/graph/${employeeId}?depth=${depth}`);
            if (!response.ok) {
                throw new Error('Failed to load graph data');
            }

            this.graphData = await response.json();

            // Clear existing graph
            this.cy.elements().remove();

            // Add nodes and edges
            this.cy.add(this.graphData.elements);

            // Apply layout
            const layout = this.cy.layout({
                name: 'cose',
                idealEdgeLength: 80,
                nodeOverlap: 10,
                refresh: 20,
                fit: true,
                padding: 50,
                randomize: false,
                componentSpacing: 40,
                nodeRepulsion: 2048,
                edgeElasticity: 32,
                nestingFactor: 1.2,
                gravity: 1,
                numIter: 1000,
                initialTemp: 1000,
                coolingFactor: 0.99,
                minTemp: 1.0
            });

            layout.run();

            // Highlight the main employee
            setTimeout(() => {
                const mainNode = this.cy.getElementById(employeeId);
                if (mainNode.length > 0) {
                    mainNode.addClass('selected');
                    this.cy.center(mainNode);
                }
                this.hideGraphLoading();
            }, 1000);

            // Update graph stats
            this.updateGraphStats();

        } catch (error) {
            console.error('Error loading employee graph:', error);
            this.showGraphError(error.message);
        }
    }

    selectNode(node) {
        // Clear previous selections
        this.cy.nodes().removeClass('selected');

        // Select current node
        node.addClass('selected');

        // Show node details
        this.showNodeDetails(node);

        // Highlight connected nodes
        this.highlightConnections(node);
    }

    highlightNode(node) {
        // Clear previous highlights
        this.cy.elements().removeClass('highlighted');

        // Highlight node and its connections
        node.addClass('highlighted');
        node.connectedEdges().addClass('highlighted');
        node.neighbors().addClass('highlighted');
    }

    clearHighlights() {
        this.cy.elements().removeClass('highlighted');
    }

    highlightConnections(node) {
        // Highlight connected edges and nodes
        const connections = node.connectedEdges();
        const connectedNodes = node.neighbors();

        connections.addClass('highlighted');
        connectedNodes.addClass('highlighted');
    }

    showNodeDetails(node) {
        const data = node.data();
        const detailsPanel = document.getElementById('nodeDetails');

        if (!detailsPanel) return;

        let detailsHTML = `
            <div class="node-details-card">
                <div class="node-header">
                    <div class="node-type-badge ${data.type}">${data.type.toUpperCase()}</div>
                    <h6>${data.label}</h6>
                </div>
                <div class="node-content">
        `;

        if (data.type === 'employee') {
            detailsHTML += `
                <div class="detail-row">
                    <span class="detail-label">Employee ID:</span>
                    <span class="detail-value">${data.id}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Similarity Score:</span>
                    <span class="detail-value">${data.score || 100}%</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Connections:</span>
                    <span class="detail-value">${node.degree()}</span>
                </div>
                <button class="btn btn-sm btn-primary mt-2" onclick="graphViz.loadEmployeeGraph('${data.id}')">
                    Focus on this employee
                </button>
            `;
        } else if (data.type === 'skill') {
            detailsHTML += `
                <div class="detail-row">
                    <span class="detail-label">Skill:</span>
                    <span class="detail-value">${data.label}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Employees with this skill:</span>
                    <span class="detail-value">${node.degree()}</span>
                </div>
            `;
        }

        detailsHTML += `
                </div>
            </div>
        `;

        detailsPanel.innerHTML = detailsHTML;
    }

    updateGraphStats() {
        const stats = {
            nodes: this.cy.nodes().length,
            edges: this.cy.edges().length,
            employees: this.cy.nodes('[type="employee"]').length,
            skills: this.cy.nodes('[type="skill"]').length,
            education: this.cy.nodes('[type="education"]').length
        };

        const statsPanel = document.getElementById('graphStats');
        if (statsPanel) {
            statsPanel.innerHTML = `
                <div class="graph-stats">
                    <div class="stat-item">
                        <span class="stat-number">${stats.nodes}</span>
                        <span class="stat-label">Total Nodes</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.edges}</span>
                        <span class="stat-label">Connections</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.employees}</span>
                        <span class="stat-label">Employees</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.skills}</span>
                        <span class="stat-label">Skills</span>
                    </div>
                </div>
            `;
        }
    }

    updateGraphControls() {
        const zoom = this.cy.zoom();
        const pan = this.cy.pan();

        const controlsPanel = document.getElementById('graphControls');
        if (controlsPanel) {
            controlsPanel.querySelector('.zoom-level').textContent = `${Math.round(zoom * 100)}%`;
        }
    }

    showGraphLoading() {
        const container = document.getElementById(this.containerId);
        const loading = container.querySelector('.graph-loading');
        if (loading) {
            loading.style.display = 'flex';
        }
    }

    hideGraphLoading() {
        const container = document.getElementById(this.containerId);
        const loading = container.querySelector('.graph-loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    showGraphError(message) {
        const container = document.getElementById(this.containerId);
        container.innerHTML = `
            <div class="graph-error">
                <i class="fas fa-exclamation-triangle fa-2x text-danger mb-3"></i>
                <h6>Failed to Load Graph</h6>
                <p class="text-muted">${message}</p>
                <button class="btn btn-primary btn-sm" onclick="location.reload()">
                    Try Again
                </button>
            </div>
        `;
    }

    // Graph manipulation methods
    resetView() {
        this.cy.fit();
        this.cy.center();
    }

    zoomIn() {
        this.cy.zoom(this.cy.zoom() * 1.25);
    }

    zoomOut() {
        this.cy.zoom(this.cy.zoom() * 0.8);
    }

    toggleLayout(layoutName = 'cose') {
        const layout = this.cy.layout({ name: layoutName });
        layout.run();
    }

    exportGraph() {
        const png64 = this.cy.png({ scale: 2 });
        const link = document.createElement('a');
        link.download = `knowledge-graph-${this.currentEmployee}.png`;
        link.href = png64;
        link.click();
    }

    filterByType(type) {
        if (type === 'all') {
            this.cy.elements().style('display', 'element');
        } else {
            this.cy.elements().style('display', 'none');
            this.cy.nodes(`[type="${type}"]`).style('display', 'element');
            this.cy.edges().style('display', 'element');
        }
    }

    searchInGraph(query) {
        if (!query) {
            this.cy.elements().removeClass('highlighted');
            return;
        }

        this.cy.elements().removeClass('highlighted');

        const matchingNodes = this.cy.nodes().filter(node =>
            node.data('label').toLowerCase().includes(query.toLowerCase()) ||
            node.data('id').toLowerCase().includes(query.toLowerCase())
        );

        if (matchingNodes.length > 0) {
            matchingNodes.addClass('highlighted');
            this.cy.center(matchingNodes.first());
        }
    }

    // Fullscreen functionality
    toggleFullscreen() {
        const overlay = document.getElementById('fullscreenOverlay');
        const icon = document.getElementById('fullscreenIcon');

        if (!this.isFullscreen) {
            // Enter fullscreen
            this.isFullscreen = true;
            overlay.classList.add('active');
            icon.className = 'fas fa-compress';

            // Initialize fullscreen graph if not already done
            if (!this.fullscreenCy) {
                this.initializeFullscreenGraph();
            }

            // Copy current graph data to fullscreen
            if (this.graphData && this.currentEmployee) {
                this.loadFullscreenGraph(this.currentEmployee);
            }

            // Update employee ID in header
            document.getElementById('fullscreenEmployeeId').textContent = this.currentEmployee || '';

            // Prevent body scroll
            document.body.style.overflow = 'hidden';

        } else {
            // Exit fullscreen
            this.isFullscreen = false;
            overlay.classList.remove('active');
            icon.className = 'fas fa-expand';

            // Restore body scroll
            document.body.style.overflow = '';
        }
    }

    initializeFullscreenGraph() {
        this.fullscreenCy = cytoscape({
            container: document.getElementById('fullscreenKnowledgeGraph'),
            style: this.getGraphStyle(),
            layout: this.getGraphLayout(),
            wheelSensitivity: 0.2,
            minZoom: 0.1,
            maxZoom: 3
        });

        this.bindFullscreenEvents();
    }

    bindFullscreenEvents() {
        // Node interactions for fullscreen graph
        this.fullscreenCy.on('tap', 'node', (evt) => {
            const node = evt.target;
            this.selectFullscreenNode(node);
        });

        this.fullscreenCy.on('mouseover', 'node', (evt) => {
            const node = evt.target;
            this.highlightFullscreenNode(node);
        });

        this.fullscreenCy.on('mouseout', 'node', (evt) => {
            this.clearFullscreenHighlights();
        });

        // Update controls on zoom/pan
        this.fullscreenCy.on('zoom pan', () => {
            this.updateFullscreenControls();
        });
    }

    async loadFullscreenGraph(employeeId) {
        if (!this.fullscreenCy) return;

        try {
            // Show loading
            this.showFullscreenLoading();

            // Use existing graph data or fetch new
            let graphData = this.graphData;
            if (!graphData || this.currentEmployee !== employeeId) {
                const response = await fetch(`/api/graph/${employeeId}?depth=3`); // Larger depth for fullscreen
                if (!response.ok) throw new Error('Failed to load graph data');
                graphData = await response.json();
            }

            // Clear and populate fullscreen graph
            this.fullscreenCy.elements().remove();
            this.fullscreenCy.add(graphData.elements);

            // Apply layout
            const layout = this.fullscreenCy.layout({
                name: 'cose',
                idealEdgeLength: 120,
                nodeOverlap: 20,
                refresh: 20,
                fit: true,
                padding: 80,
                randomize: false,
                componentSpacing: 60,
                nodeRepulsion: 8192,
                edgeElasticity: 64,
                nestingFactor: 1.5,
                gravity: 2,
                numIter: 1500,
                initialTemp: 1500,
                coolingFactor: 0.98,
                minTemp: 1.0
            });

            layout.run();

            // Highlight main employee
            setTimeout(() => {
                const mainNode = this.fullscreenCy.getElementById(employeeId);
                if (mainNode.length > 0) {
                    mainNode.addClass('selected');
                    this.fullscreenCy.center(mainNode);
                }
                this.hideFullscreenLoading();
                this.updateFullscreenStats();
            }, 1500);

        } catch (error) {
            console.error('Error loading fullscreen graph:', error);
            this.hideFullscreenLoading();
        }
    }

    selectFullscreenNode(node) {
        // Clear previous selections
        this.fullscreenCy.nodes().removeClass('selected');
        node.addClass('selected');

        // Show node details in sidebar
        this.showFullscreenNodeDetails(node);
        this.highlightFullscreenConnections(node);
    }

    highlightFullscreenNode(node) {
        this.fullscreenCy.elements().removeClass('highlighted');
        node.addClass('highlighted');
        node.connectedEdges().addClass('highlighted');
        node.neighbors().addClass('highlighted');
    }

    clearFullscreenHighlights() {
        this.fullscreenCy.elements().removeClass('highlighted');
    }

    highlightFullscreenConnections(node) {
        const connections = node.connectedEdges();
        const connectedNodes = node.neighbors();
        connections.addClass('highlighted');
        connectedNodes.addClass('highlighted');
    }

    showFullscreenNodeDetails(node) {
        const data = node.data();
        const detailsPanel = document.getElementById('fullscreenNodeDetails');

        let detailsHTML = this.generateNodeDetailsHTML(data, node);
        detailsPanel.innerHTML = detailsHTML;
    }

    updateFullscreenStats() {
        const stats = {
            nodes: this.fullscreenCy.nodes().length,
            edges: this.fullscreenCy.edges().length,
            employees: this.fullscreenCy.nodes('[type="employee"]').length,
            skills: this.fullscreenCy.nodes('[type="skill"]').length,
            education: this.fullscreenCy.nodes('[type="education"]').length
        };

        const statsPanel = document.getElementById('fullscreenGraphStats');
        if (statsPanel) {
            statsPanel.innerHTML = `
                <div class="graph-stats">
                    <div class="stat-item">
                        <span class="stat-number">${stats.nodes}</span>
                        <span class="stat-label">Total Nodes</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.edges}</span>
                        <span class="stat-label">Connections</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.employees}</span>
                        <span class="stat-label">Employees</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.skills}</span>
                        <span class="stat-label">Skills</span>
                    </div>
                </div>
            `;
        }
    }

    updateFullscreenControls() {
        const zoom = this.fullscreenCy.zoom();
        const controlsPanel = document.getElementById('fullscreenGraphControls');
        if (controlsPanel) {
            controlsPanel.querySelector('.zoom-level').textContent = `${Math.round(zoom * 100)}%`;
        }
    }

    showFullscreenLoading() {
        const container = document.getElementById('fullscreenKnowledgeGraph');
        const loading = container.querySelector('.graph-loading');
        if (loading) {
            loading.style.display = 'flex';
        }
    }

    hideFullscreenLoading() {
        const container = document.getElementById('fullscreenKnowledgeGraph');
        const loading = container.querySelector('.graph-loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    generateNodeDetailsHTML(data, node) {
        let detailsHTML = `
            <div class="node-details-card">
                <div class="node-header">
                    <div class="node-type-badge ${data.type}">${data.type.toUpperCase()}</div>
                    <h6>${data.label}</h6>
                </div>
                <div class="node-content">
        `;

        if (data.type === 'employee') {
            detailsHTML += `
                <div class="detail-row">
                    <span class="detail-label">Employee ID:</span>
                    <span class="detail-value">${data.id}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Similarity Score:</span>
                    <span class="detail-value">${data.score || 100}%</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Connections:</span>
                    <span class="detail-value">${node.degree()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Education:</span>
                    <span class="detail-value">${data.education || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Experience:</span>
                    <span class="detail-value">${data.experience || 'Unknown'}</span>
                </div>
                ${data.skills ? `
                <div class="detail-row">
                    <span class="detail-label">Top Skills:</span>
                    <div class="detail-value">
                        ${data.skills.slice(0, 3).map(skill =>
                            `<span class="badge bg-primary me-1">${skill}</span>`
                        ).join('')}
                    </div>
                </div>
                ` : ''}
                <button class="btn btn-sm btn-primary mt-2" onclick="graphViz.focusOnEmployee('${data.id}')">
                    Focus on this employee
                </button>
            `;
        } else if (data.type === 'skill') {
            detailsHTML += `
                <div class="detail-row">
                    <span class="detail-label">Skill:</span>
                    <span class="detail-value">${data.label}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Employees with this skill:</span>
                    <span class="detail-value">${node.degree()}</span>
                </div>
            `;
        }

        detailsHTML += `
                </div>
            </div>
        `;

        return detailsHTML;
    }

    focusOnEmployee(employeeId) {
        const graph = this.isFullscreen ? this.fullscreenCy : this.cy;
        if (graph) {
            const node = graph.getElementById(employeeId);
            if (node.length > 0) {
                graph.center(node);
                graph.zoom(1.5);
                this.selectNode(node);
            }
        }
    }

    getGraphStyle() {
        return [
            {
                selector: 'node',
                style: {
                    'background-color': '#667eea',
                    'label': 'data(label)',
                    'color': '#ffffff',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '12px',
                    'font-weight': 'bold',
                    'width': 'mapData(score, 0, 100, 20, 60)',
                    'height': 'mapData(score, 0, 100, 20, 60)',
                    'border-width': 2,
                    'border-color': '#ffffff',
                    'text-outline-color': '#667eea',
                    'text-outline-width': 2
                }
            },
            {
                selector: 'node[type="employee"]',
                style: {
                    'background-color': '#28a745',
                    'shape': 'round-rectangle'
                }
            },
            {
                selector: 'node[type="skill"]',
                style: {
                    'background-color': '#17a2b8',
                    'shape': 'ellipse'
                }
            },
            {
                selector: 'node[type="education"]',
                style: {
                    'background-color': '#ffc107',
                    'shape': 'diamond'
                }
            },
            {
                selector: 'node[type="experience"]',
                style: {
                    'background-color': '#dc3545',
                    'shape': 'triangle'
                }
            },
            {
                selector: 'node.highlighted',
                style: {
                    'border-width': 4,
                    'border-color': '#ff4757',
                    'background-color': '#ff6b7a'
                }
            },
            {
                selector: 'node.selected',
                style: {
                    'border-width': 6,
                    'border-color': '#2f3542',
                    'background-color': '#ff9ff3'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 'mapData(similarity, 0, 1, 1, 8)',
                    'line-color': '#ddd',
                    'target-arrow-color': '#ddd',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'opacity': 'mapData(similarity, 0, 1, 0.3, 1)'
                }
            },
            {
                selector: 'edge.highlighted',
                style: {
                    'line-color': '#ff4757',
                    'target-arrow-color': '#ff4757',
                    'width': 4,
                    'opacity': 1
                }
            }
        ];
    }

    getGraphLayout() {
        return {
            name: 'cose',
            idealEdgeLength: 100,
            nodeOverlap: 20,
            refresh: 20,
            fit: true,
            padding: 30,
            randomize: false,
            componentSpacing: 100,
            nodeRepulsion: 400000,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
        };
    }
}

// Graph control functions
function initializeGraphVisualization() {
    window.graphViz = new KnowledgeGraphVisualizer('knowledgeGraph');
    window.graphViz.initialize();
}

function toggleFullscreen() {
    if (window.graphViz) {
        window.graphViz.toggleFullscreen();
    }
}

function resetGraphView() {
    if (window.graphViz) {
        window.graphViz.resetView();
    }
}

function zoomGraphIn() {
    if (window.graphViz) {
        window.graphViz.zoomIn();
    }
}

function zoomGraphOut() {
    if (window.graphViz) {
        window.graphViz.zoomOut();
    }
}

function exportGraph() {
    if (window.graphViz) {
        window.graphViz.exportGraph();
    }
}

function toggleGraphLayout() {
    if (window.graphViz) {
        const layouts = ['cose', 'circle', 'grid', 'random', 'concentric'];
        const currentLayout = window.graphViz.currentLayout || 'cose';
        const currentIndex = layouts.indexOf(currentLayout);
        const nextLayout = layouts[(currentIndex + 1) % layouts.length];

        window.graphViz.currentLayout = nextLayout;
        window.graphViz.toggleLayout(nextLayout);
    }
}

function filterGraph(type) {
    if (window.graphViz) {
        window.graphViz.filterByType(type);
    }
}

function searchGraph() {
    const searchInput = document.getElementById('graphSearch');
    if (window.graphViz && searchInput) {
        window.graphViz.searchInGraph(searchInput.value);
    }
}

function searchGraphFullscreen() {
    const searchInput = document.getElementById('fullscreenGraphSearch');
    if (window.graphViz && searchInput) {
        window.graphViz.searchInGraph(searchInput.value);
    }
}

function focusOnEmployee() {
    if (window.graphViz && window.graphViz.currentEmployee) {
        window.graphViz.focusOnEmployee(window.graphViz.currentEmployee);
    }
}

function expandGraph() {
    if (window.graphViz) {
        const graph = window.graphViz.isFullscreen ? window.graphViz.fullscreenCy : window.graphViz.cy;
        if (graph) {
            graph.fit();
            graph.zoom(graph.zoom() * 0.8);
        }
    }
}

function toggleFullscreen() {
    if (window.graphViz) {
        window.graphViz.toggleFullscreen();
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize graph visualization if container exists
    if (document.getElementById('knowledgeGraph')) {
        initializeGraphVisualization();
    }
});