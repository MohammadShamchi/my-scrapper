// Site2MD Web UI JavaScript

class Site2MDApp {
    constructor() {
        this.websocket = null;
        this.currentCrawlId = null;
        this.isAdvancedOpen = false;
        
        this.initializeEventListeners();
        this.loadSavedSettings();
    }

    initializeEventListeners() {
        // Advanced options toggle
        document.getElementById('toggleAdvanced').addEventListener('click', () => {
            this.toggleAdvancedOptions();
        });

        // Form submission
        document.getElementById('crawlForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startCrawl();
        });

        // Preview button
        document.getElementById('previewBtn').addEventListener('click', () => {
            this.previewCrawl();
        });

        // Stop button
        document.getElementById('stopBtn').addEventListener('click', () => {
            this.stopCrawl();
        });

        // New crawl button
        document.getElementById('newCrawlBtn').addEventListener('click', () => {
            this.resetForm();
        });

        // Download button
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.downloadResults();
        });

        // Save settings on change
        document.querySelectorAll('input, textarea, select').forEach(element => {
            element.addEventListener('change', () => {
                this.saveSettings();
            });
        });

        // URL validation
        document.getElementById('url').addEventListener('blur', () => {
            this.validateUrl();
        });
    }

    toggleAdvancedOptions() {
        const options = document.getElementById('advancedOptions');
        const icon = document.getElementById('advancedIcon');
        
        this.isAdvancedOpen = !this.isAdvancedOpen;
        
        if (this.isAdvancedOpen) {
            options.classList.remove('collapse-hidden');
            options.classList.add('collapse-visible');
            icon.style.transform = 'rotate(180deg)';
        } else {
            options.classList.remove('collapse-visible');
            options.classList.add('collapse-hidden');
            icon.style.transform = 'rotate(0deg)';
        }
    }

    validateUrl() {
        const urlInput = document.getElementById('url');
        const url = urlInput.value.trim();
        
        if (!url) return;
        
        try {
            new URL(url);
            urlInput.classList.remove('border-red-300');
            urlInput.classList.add('border-green-300');
        } catch (e) {
            urlInput.classList.remove('border-green-300');
            urlInput.classList.add('border-red-300');
        }
    }

    getFormData() {
        const formData = new FormData();
        const form = document.getElementById('crawlForm');
        
        // Basic fields
        formData.append('url', document.getElementById('url').value);
        formData.append('output_dir', document.getElementById('output_dir').value);
        
        // Quick options
        formData.append('javascript_heavy', document.getElementById('javascript_heavy').checked);
        formData.append('deep_search', document.getElementById('deep_search').checked);
        formData.append('download_assets', document.getElementById('download_assets').checked);
        
        // Advanced options
        formData.append('max_pages', document.getElementById('max_pages').value);
        formData.append('max_depth', document.getElementById('max_depth').value);
        formData.append('concurrency', document.getElementById('concurrency').value);
        formData.append('delay', document.getElementById('delay').value);
        formData.append('respect_robots', document.getElementById('respect_robots').checked);
        formData.append('sitemap_first', document.getElementById('sitemap_first').checked);
        formData.append('add_toc', document.getElementById('add_toc').checked);
        formData.append('incremental', document.getElementById('incremental').checked);
        
        // Patterns (convert textarea to array)
        const includePatterns = document.getElementById('include_patterns').value
            .split('\n').map(s => s.trim()).filter(s => s);
        const excludePatterns = document.getElementById('exclude_patterns').value
            .split('\n').map(s => s.trim()).filter(s => s);
        
        formData.append('include_patterns', JSON.stringify(includePatterns));
        formData.append('exclude_patterns', JSON.stringify(excludePatterns));
        
        // Files
        const cookiesFile = document.getElementById('cookies_file').files[0];
        if (cookiesFile) {
            formData.append('cookies_file', cookiesFile);
        }
        
        const headersFile = document.getElementById('headers_file').files[0];
        if (headersFile) {
            formData.append('headers_file', headersFile);
        }
        
        return formData;
    }

    async previewCrawl() {
        const formData = this.getFormData();
        formData.append('dry_run', true);
        
        try {
            this.showLoading('Generating preview...');
            
            const response = await fetch('/api/crawl', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.showPreviewModal(result);
            
        } catch (error) {
            this.showError('Preview failed: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async startCrawl() {
        const formData = this.getFormData();
        
        try {
            this.showCrawlStarted();
            
            const response = await fetch('/api/crawl', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.currentCrawlId = result.crawl_id;
            
            // Connect to WebSocket for real-time updates
            this.connectWebSocket(result.crawl_id);
            
        } catch (error) {
            this.showError('Failed to start crawl: ' + error.message);
            this.resetCrawlUI();
        }
    }

    connectWebSocket(crawlId) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${crawlId}`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showError('Connection lost. Refresh page to check results.');
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket connection closed');
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'progress':
                this.updateProgress(data);
                break;
            case 'activity':
                this.updateActivity(data.message);
                break;
            case 'completed':
                this.showResults(data);
                break;
            case 'error':
                this.showError(data.message);
                this.resetCrawlUI();
                break;
        }
    }

    updateProgress(data) {
        // Update progress bar
        const progress = Math.round((data.completed / data.total) * 100);
        document.getElementById('progressBar').style.width = `${progress}%`;
        document.getElementById('progressText').textContent = `${progress}%`;
        
        // Update stats
        document.getElementById('pagesCount').textContent = data.pages_crawled || 0;
        document.getElementById('cachedCount').textContent = data.pages_cached || 0;
        document.getElementById('failedCount').textContent = data.pages_failed || 0;
        
        // Update size
        const sizeKB = Math.round((data.total_bytes || 0) / 1024);
        document.getElementById('sizeCount').textContent = `${sizeKB} KB`;
    }

    updateActivity(message) {
        document.getElementById('activityText').textContent = message;
    }

    showCrawlStarted() {
        // Hide form, show progress
        document.getElementById('crawlForm').style.display = 'none';
        document.getElementById('progressSection').classList.remove('hidden');
        
        // Update button state
        const startBtn = document.getElementById('startBtn');
        const startIcon = document.getElementById('startIcon');
        const startText = document.getElementById('startText');
        
        startIcon.className = 'fas fa-spinner spinning mr-2';
        startText.textContent = 'Crawling...';
        startBtn.disabled = true;
        
        this.updateActivity('Starting crawl...');
    }

    showResults(data) {
        // Hide progress, show results
        document.getElementById('progressSection').classList.add('hidden');
        document.getElementById('resultsSection').classList.remove('hidden');
        
        // Populate results
        const resultsContent = document.getElementById('resultsContent');
        resultsContent.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-green-50 p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-green-600">${data.pages_crawled}</div>
                    <div class="text-sm text-green-600">Pages Crawled</div>
                </div>
                <div class="bg-blue-50 p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-blue-600">${data.pages_cached}</div>
                    <div class="text-sm text-blue-600">Pages Cached</div>
                </div>
                <div class="bg-red-50 p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-red-600">${data.pages_failed}</div>
                    <div class="text-sm text-red-600">Pages Failed</div>
                </div>
                <div class="bg-purple-50 p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-purple-600">${Math.round((data.total_bytes || 0) / 1024)} KB</div>
                    <div class="text-sm text-purple-600">Total Size</div>
                </div>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg">
                <h4 class="font-semibold mb-2">Output Directory</h4>
                <p class="text-sm text-gray-600 font-mono">${data.output_directory}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg mt-4">
                <h4 class="font-semibold mb-2">Duration</h4>
                <p class="text-sm text-gray-600">${data.duration || 'N/A'}</p>
            </div>
        `;
        
        // Close WebSocket
        if (this.websocket) {
            this.websocket.close();
        }
    }

    async stopCrawl() {
        if (!this.currentCrawlId) return;
        
        try {
            await fetch(`/api/crawl/${this.currentCrawlId}/stop`, {
                method: 'POST'
            });
            
            this.showNotification('Crawl stopped');
            this.resetCrawlUI();
            
        } catch (error) {
            this.showError('Failed to stop crawl: ' + error.message);
        }
    }

    async downloadResults() {
        if (!this.currentCrawlId) return;
        
        try {
            const response = await fetch(`/api/crawl/${this.currentCrawlId}/download`);
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `site2md_export_${this.currentCrawlId}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            this.showError('Download failed: ' + error.message);
        }
    }

    resetForm() {
        // Show form, hide results
        document.getElementById('crawlForm').style.display = 'block';
        document.getElementById('progressSection').classList.add('hidden');
        document.getElementById('resultsSection').classList.add('hidden');
        
        this.resetCrawlUI();
        this.currentCrawlId = null;
    }

    resetCrawlUI() {
        const startBtn = document.getElementById('startBtn');
        const startIcon = document.getElementById('startIcon');
        const startText = document.getElementById('startText');
        
        startIcon.className = 'fas fa-play mr-2';
        startText.textContent = 'Start Crawling';
        startBtn.disabled = false;
        
        // Reset progress
        document.getElementById('progressBar').style.width = '0%';
        document.getElementById('progressText').textContent = '0%';
        document.getElementById('pagesCount').textContent = '0';
        document.getElementById('cachedCount').textContent = '0';
        document.getElementById('failedCount').textContent = '0';
        document.getElementById('sizeCount').textContent = '0 KB';
        document.getElementById('activityText').textContent = 'Ready to start...';
    }

    showPreviewModal(data) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-xl p-6 max-w-2xl max-h-96 overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold">Crawl Preview</h3>
                    <button class="text-gray-500 hover:text-gray-700" onclick="this.closest('.fixed').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="space-y-4">
                    <div>
                        <strong>Estimated Pages:</strong> ${data.estimated_pages || 'Unknown'}
                    </div>
                    <div>
                        <strong>Starting URL:</strong> ${data.start_url}
                    </div>
                    <div>
                        <strong>Output Directory:</strong> ${data.output_directory}
                    </div>
                    ${data.sample_urls ? `
                        <div>
                            <strong>Sample URLs (first 10):</strong>
                            <ul class="mt-2 text-sm text-gray-600 space-y-1">
                                ${data.sample_urls.slice(0, 10).map(url => `<li>• ${url}</li>`).join('')}
                            </ul>
                            ${data.sample_urls.length > 10 ? `<p class="text-sm text-gray-500 mt-2">... and ${data.sample_urls.length - 10} more</p>` : ''}
                        </div>
                    ` : ''}
                </div>
                <div class="mt-6 text-center">
                    <button class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700" 
                            onclick="this.closest('.fixed').remove()">
                        Close
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50';
        errorDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <span><i class="fas fa-exclamation-triangle mr-2"></i>${message}</span>
                <button class="ml-4 text-red-500 hover:text-red-700" onclick="this.closest('div').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    showNotification(message) {
        const notifDiv = document.createElement('div');
        notifDiv.className = 'fixed top-4 right-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded z-50';
        notifDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <span><i class="fas fa-check mr-2"></i>${message}</span>
                <button class="ml-4 text-green-500 hover:text-green-700" onclick="this.closest('div').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notifDiv);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notifDiv.parentNode) {
                notifDiv.parentNode.removeChild(notifDiv);
            }
        }, 3000);
    }

    showLoading(message) {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingOverlay';
        loadingDiv.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        loadingDiv.innerHTML = `
            <div class="bg-white rounded-lg p-6 flex items-center space-x-3">
                <i class="fas fa-spinner spinning text-blue-600"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(loadingDiv);
    }

    hideLoading() {
        const loadingDiv = document.getElementById('loadingOverlay');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    saveSettings() {
        const settings = {
            output_dir: document.getElementById('output_dir').value,
            javascript_heavy: document.getElementById('javascript_heavy').checked,
            deep_search: document.getElementById('deep_search').checked,
            download_assets: document.getElementById('download_assets').checked,
            max_pages: document.getElementById('max_pages').value,
            max_depth: document.getElementById('max_depth').value,
            concurrency: document.getElementById('concurrency').value,
            delay: document.getElementById('delay').value,
            respect_robots: document.getElementById('respect_robots').checked,
            sitemap_first: document.getElementById('sitemap_first').checked,
            add_toc: document.getElementById('add_toc').checked,
            incremental: document.getElementById('incremental').checked,
            include_patterns: document.getElementById('include_patterns').value,
            exclude_patterns: document.getElementById('exclude_patterns').value
        };
        
        localStorage.setItem('site2md_settings', JSON.stringify(settings));
    }

    loadSavedSettings() {
        const saved = localStorage.getItem('site2md_settings');
        if (!saved) return;
        
        try {
            const settings = JSON.parse(saved);
            
            // Apply saved settings
            Object.keys(settings).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = settings[key];
                    } else {
                        element.value = settings[key];
                    }
                }
            });
        } catch (e) {
            console.warn('Failed to load saved settings:', e);
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Site2MDApp();
});