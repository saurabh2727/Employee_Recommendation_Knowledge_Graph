// Employee Recommendation System - Frontend JavaScript

class EmployeeRecommendationApp {
    constructor() {
        this.initializeApp();
        this.bindEvents();
    }

    initializeApp() {
        // Show welcome state on load
        this.showWelcomeState();

        // Initialize tooltips
        this.initializeTooltips();

        // Add typing effect to welcome text
        this.addTypingEffect();
    }

    bindEvents() {
        // Form submission
        document.getElementById('recommendationForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmission();
        });

        // Sample ID buttons
        document.querySelectorAll('.sample-id').forEach(button => {
            button.addEventListener('click', (e) => {
                const id = e.target.getAttribute('data-id');
                document.getElementById('candidateId').value = id;
                this.handleFormSubmission();
            });
        });

        // Input field enter key
        document.getElementById('candidateId').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.handleFormSubmission();
            }
        });

        // Auto-focus on input when clicking anywhere on the search card
        document.querySelector('.card').addEventListener('click', () => {
            document.getElementById('candidateId').focus();
        });

        // View mode toggle
        document.querySelectorAll('input[name="viewMode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.toggleViewMode(e.target.id);
            });
        });
    }

    async handleFormSubmission() {
        const candidateId = document.getElementById('candidateId').value.trim();

        if (!candidateId) {
            this.showError('Please enter an employee ID');
            return;
        }

        if (!this.isValidId(candidateId)) {
            this.showError('Please enter a valid employee ID (numbers only)');
            return;
        }

        try {
            this.showLoadingState();
            const results = await this.fetchRecommendations(candidateId);
            this.displayResults(results);
        } catch (error) {
            this.showError(error.message);
        }
    }

    isValidId(id) {
        return /^\d+$/.test(id) && id.length > 0;
    }

    async fetchRecommendations(candidateId) {
        const formData = new FormData();
        formData.append('candidate_id', candidateId);

        const response = await fetch('/results', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Request failed: ${errorText}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        return data;
    }

    async fetchEmployeeDetails(employeeId) {
        try {
            const response = await fetch(`/employee/${employeeId}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.log('Employee details not available');
        }
        return null;
    }

    showWelcomeState() {
        document.getElementById('welcomeState').style.display = 'block';
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('resultsState').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
    }

    showLoadingState() {
        document.getElementById('welcomeState').style.display = 'none';
        document.getElementById('loadingState').style.display = 'block';
        document.getElementById('resultsState').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('welcomeState').style.display = 'none';
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('resultsState').style.display = 'none';
        document.getElementById('errorState').style.display = 'block';

        // Auto-hide error after 5 seconds
        setTimeout(() => {
            this.showWelcomeState();
        }, 5000);
    }

    async displayResults(data) {
        document.getElementById('resultEmployeeId').textContent = data.candidate_id;
        this.currentEmployeeId = data.candidate_id;

        const recommendationsList = document.getElementById('recommendationsList');
        recommendationsList.innerHTML = '';

        if (!data.similar_candidates || data.similar_candidates.length === 0) {
            recommendationsList.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-info-circle fa-2x text-info mb-3"></i>
                    <h5>No Similar Employees Found</h5>
                    <p class="text-muted">No recommendations available for employee ${data.candidate_id}</p>
                </div>
            `;
        } else {
            // Display recommendations with animations
            data.similar_candidates.forEach((candidateId, index) => {
                setTimeout(() => {
                    this.addRecommendationItem(candidateId, index + 1, recommendationsList);
                }, index * 200);
            });
        }

        // Show employee details if available
        await this.displayEmployeeDetails(data.candidate_id);

        // Load graph visualization if in graph view
        if (document.getElementById('graphView').checked) {
            this.loadGraphVisualization(data.candidate_id);
        }

        // Show results state
        document.getElementById('welcomeState').style.display = 'none';
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('resultsState').style.display = 'block';
        document.getElementById('errorState').style.display = 'none';

        // Show appropriate view based on toggle
        this.updateViewDisplay();

        // Scroll to results
        document.getElementById('resultsState').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }

    addRecommendationItem(candidateId, rank, container) {
        const similarity = this.calculateSimilarity(rank);
        const borderColor = this.getSimilarityColor(similarity);

        const item = document.createElement('div');
        item.className = 'recommendation-item';
        item.style.borderLeftColor = borderColor;
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';

        item.innerHTML = `
            <div class="rank-badge">${rank}</div>
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <h6 class="mb-2">
                        <i class="fas fa-user me-2"></i>
                        Employee ID: <strong>${candidateId}</strong>
                    </h6>
                    <div class="d-flex align-items-center mb-2">
                        <span class="me-2">Similarity Score:</span>
                        <span class="badge" style="background: ${borderColor}; color: white;">
                            ${similarity}%
                        </span>
                    </div>
                    <div class="similarity-bar">
                        <div class="similarity-fill" style="width: 0%; background: linear-gradient(90deg, ${borderColor}, ${this.lightenColor(borderColor)});">
                        </div>
                    </div>
                </div>
                <div class="ms-3">
                    <button class="btn btn-outline-primary btn-sm" onclick="app.showCandidateDetails('${candidateId}')">
                        <i class="fas fa-info-circle me-1"></i>
                        Details
                    </button>
                </div>
            </div>
            <div class="mt-2">
                <small class="text-muted">
                    <i class="fas fa-lightbulb me-1"></i>
                    Based on semantic skill matching, education analysis, and experience level
                </small>
            </div>
        `;

        container.appendChild(item);

        // Animate in
        setTimeout(() => {
            item.style.transition = 'all 0.5s ease-out';
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';

            // Animate similarity bar
            setTimeout(() => {
                const fillBar = item.querySelector('.similarity-fill');
                fillBar.style.width = `${similarity}%`;
            }, 300);
        }, 100);
    }

    calculateSimilarity(rank) {
        // Simulate similarity scores based on rank
        const baseScore = 95;
        const decrease = (rank - 1) * 8;
        return Math.max(baseScore - decrease, 60);
    }

    getSimilarityColor(similarity) {
        if (similarity >= 90) return '#28a745';
        if (similarity >= 80) return '#17a2b8';
        if (similarity >= 70) return '#ffc107';
        return '#dc3545';
    }

    lightenColor(color) {
        // Simple color lightening
        const hex = color.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);

        return `rgb(${Math.min(255, r + 40)}, ${Math.min(255, g + 40)}, ${Math.min(255, b + 40)})`;
    }

    async displayEmployeeDetails(employeeId) {
        const detailsContainer = document.getElementById('employeeDetails');

        // Show loading state for details
        detailsContainer.innerHTML = `
            <div class="text-center">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading employee details...</span>
            </div>
        `;

        const details = await this.fetchEmployeeDetails(employeeId);

        if (details) {
            detailsContainer.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <div class="detail-item">
                            <strong><i class="fas fa-tools me-2"></i>Skills:</strong>
                            <div class="mt-1">
                                ${details.skills ? details.skills.slice(0, 5).map(skill =>
                                    `<span class="badge bg-primary me-1">${skill}</span>`
                                ).join('') : 'Not available'}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="detail-item">
                            <strong><i class="fas fa-graduation-cap me-2"></i>Education:</strong>
                            <div class="mt-1">${details.education || 'Not available'}</div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="detail-item">
                            <strong><i class="fas fa-briefcase me-2"></i>Experience Level:</strong>
                            <div class="mt-1">
                                <span class="badge bg-info">${details.experience || 'Not specified'}</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="detail-item">
                            <strong><i class="fas fa-university me-2"></i>University Tier:</strong>
                            <div class="mt-1">${details.university_tier || 'Not available'}</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            detailsContainer.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-info-circle me-2"></i>
                    Detailed profile information is not available for this employee.
                </div>
            `;
        }
    }

    showCandidateDetails(candidateId) {
        // Update the search field and trigger new search
        document.getElementById('candidateId').value = candidateId;
        this.handleFormSubmission();
    }

    toggleViewMode(viewId) {
        if (viewId === 'graphView') {
            // Show graph container
            document.getElementById('graphContainer').style.display = 'block';
            document.getElementById('resultsState').style.display = 'none';

            // Load graph if we have a current employee
            if (this.currentEmployeeId) {
                this.loadGraphVisualization(this.currentEmployeeId);
            }
        } else {
            // Show results container
            document.getElementById('graphContainer').style.display = 'none';
            document.getElementById('resultsState').style.display = 'block';
        }
    }

    updateViewDisplay() {
        const isGraphView = document.getElementById('graphView').checked;
        if (isGraphView) {
            document.getElementById('graphContainer').style.display = 'block';
            document.getElementById('resultsState').style.display = 'none';
        } else {
            document.getElementById('graphContainer').style.display = 'none';
            document.getElementById('resultsState').style.display = 'block';
        }
    }

    async loadGraphVisualization(employeeId) {
        if (!window.graphViz) {
            console.error('Graph visualization not initialized');
            return;
        }

        try {
            await window.graphViz.loadEmployeeGraph(employeeId);
        } catch (error) {
            console.error('Failed to load graph visualization:', error);
            this.showError('Failed to load knowledge graph visualization');
        }
    }

    clearResults() {
        document.getElementById('candidateId').value = '';
        this.currentEmployeeId = null;
        this.showWelcomeState();
        document.getElementById('candidateId').focus();

        // Clear graph if exists
        if (window.graphViz && window.graphViz.cy) {
            window.graphViz.cy.elements().remove();
        }
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips if needed
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    addTypingEffect() {
        // Add subtle typing effect to the welcome text
        const welcomeTitle = document.querySelector('#welcomeState h3');
        if (welcomeTitle) {
            const text = welcomeTitle.textContent;
            welcomeTitle.textContent = '';

            let i = 0;
            const typeWriter = () => {
                if (i < text.length) {
                    welcomeTitle.textContent += text.charAt(i);
                    i++;
                    setTimeout(typeWriter, 50);
                }
            };

            setTimeout(typeWriter, 500);
        }
    }

    // Utility methods
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';

        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new EmployeeRecommendationApp();
});

// Global functions for onclick events
function clearResults() {
    window.app.clearResults();
}

// Add some easter eggs and smooth interactions
document.addEventListener('keydown', (e) => {
    // Konami code or special shortcuts could go here
    if (e.key === 'Escape') {
        window.app.clearResults();
    }
});

// Add smooth scroll behavior
document.documentElement.style.scrollBehavior = 'smooth';

// Performance optimization - lazy load heavy animations
window.addEventListener('load', () => {
    // Add any heavy animations or effects after page load
    document.body.classList.add('loaded');
});

// Service worker registration for PWA capabilities (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}