// Application state
class AppState {
    constructor() {
        this.document = null;
        this.rules = [];
        this.selectedElement = null;
        this.observers = [];
    }

    subscribe(callback) {
        this.observers.push(callback);
    }

    notify(change) {
        this.observers.forEach(callback => callback(change));
    }

    setDocument(document) {
        this.document = document;
        this.notify({ type: 'document_changed', document });
    }

    addRule(rule) {
        this.rules.push(rule);
        this.notify({ type: 'rule_added', rule });
    }

    removeRule(ruleId) {
        this.rules = this.rules.filter(rule => rule.id !== ruleId);
        this.notify({ type: 'rule_removed', ruleId });
    }

    setSelectedElement(element) {
        this.selectedElement = element;
        this.notify({ type: 'element_selected', element });
    }
}

// API service
class APIService {
    constructor() {
        this.baseURL = 'http://localhost:8000';
    }

    async loadExample() {
        const response = await fetch(`${this.baseURL}/load-example`);
        if (!response.ok) throw new Error('Failed to load example');
        return response.json();
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseURL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return response.json();
    }

    async generateRule(element, intent) {
        const response = await fetch(`${this.baseURL}/generate-rule`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                element: element,
                intent: intent
            })
        });

        if (!response.ok) throw new Error('Failed to generate rule');
        return response.json();
    }

    async exportRules(rules) {
        const response = await fetch(`${this.baseURL}/export-rules`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rules: rules
            })
        });

        if (!response.ok) throw new Error('Failed to export rules');
        
        // Trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'formatting_rules.json';
        a.click();
        window.URL.revokeObjectURL(url);
    }
}

// UI Manager
class UIManager {
    constructor(state, apiService) {
        this.state = state;
        this.api = apiService;
        this.initializeElements();
        this.bindEvents();
        this.subscribeToState();
    }

    initializeElements() {
        this.originalDoc = document.getElementById('original-document');
        this.targetDoc = document.getElementById('target-document');
        this.rulesPanel = document.getElementById('rules-panel');
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');
        this.uploadBtn = document.getElementById('upload-btn');
        this.exportBtn = document.getElementById('export-btn');
        this.loadExampleBtn = document.getElementById('load-example-btn');
        this.uploadModal = document.getElementById('upload-modal');
        this.fileInput = document.getElementById('file-input');
        this.loading = document.getElementById('loading');
        this.statusText = document.getElementById('status-text');
    }

    bindEvents() {
        // Chat functionality
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // File upload
        this.uploadBtn.addEventListener('click', () => this.showUploadModal());
        this.loadExampleBtn.addEventListener('click', () => this.loadExample());
        
        // Modal controls
        document.getElementById('cancel-upload').addEventListener('click', () => this.hideUploadModal());
        document.getElementById('confirm-upload').addEventListener('click', () => this.uploadFile());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Export
        this.exportBtn.addEventListener('click', () => this.exportRules());

        // Drag and drop
        this.setupDragAndDrop();
    }

    subscribeToState() {
        this.state.subscribe((change) => {
            switch (change.type) {
                case 'document_changed':
                    this.renderDocument();
                    break;
                case 'rule_added':
                    this.renderRules();
                    this.applyRulesToTarget();
                    break;
                case 'rule_removed':
                    this.renderRules();
                    this.applyRulesToTarget();
                    break;
                case 'element_selected':
                    this.handleElementSelection(change.element);
                    break;
            }
        });
    }

    async loadExample() {
        try {
            this.showLoading();
            const document = await this.api.loadExample();
            this.state.setDocument(document);
            this.updateStatus('Example document loaded');
        } catch (error) {
            this.showError(`Failed to load example: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    showUploadModal() {
        this.uploadModal.classList.remove('hidden');
    }

    hideUploadModal() {
        this.uploadModal.classList.add('hidden');
        this.fileInput.value = '';
        document.getElementById('confirm-upload').disabled = true;
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            document.getElementById('confirm-upload').disabled = false;
        }
    }

    async uploadFile() {
        const file = this.fileInput.files[0];
        if (!file) return;

        try {
            this.showLoading();
            const response = await this.api.uploadFile(file);
            this.state.setDocument(response.document);
            this.hideUploadModal();
            this.updateStatus(`Document uploaded: ${file.name}`);
        } catch (error) {
            this.showError(`Upload failed: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    setupDragAndDrop() {
        const dropZone = document.querySelector('.border-dashed');
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.fileInput.files = files;
                this.handleFileSelect({ target: { files } });
            }
        });
    }

    renderDocument() {
        if (!this.state.document) return;

        this.originalDoc.innerHTML = '';
        this.targetDoc.innerHTML = '';

        this.state.document.elements.forEach(element => {
            // Original document
            const originalEl = this.createDocumentElement(element, 'original');
            this.originalDoc.appendChild(originalEl);

            // Target document
            const targetEl = this.createDocumentElement(element, 'target');
            this.targetDoc.appendChild(targetEl);
        });

        this.enableChat();
    }

    createDocumentElement(element, type) {
        const div = document.createElement('div');
        div.className = `document-element ${type}`;
        div.textContent = element.text;
        div.dataset.elementId = element.id;

        if (type === 'original') {
            div.addEventListener('click', () => this.selectElement(element));
        }

        return div;
    }

    selectElement(element) {
        // Remove previous selection
        document.querySelectorAll('.document-element.selected').forEach(el => {
            el.classList.remove('selected');
        });

        // Add selection to clicked element
        document.querySelector(`[data-element-id="${element.id}"]`).classList.add('selected');

        this.state.setSelectedElement(element);
    }

    handleElementSelection(element) {
        if (element) {
            this.chatInput.placeholder = `Selected: "${element.text.substring(0, 50)}..." - Describe how this should be formatted`;
            this.chatInput.disabled = false;
            this.sendBtn.disabled = false;
        } else {
            this.chatInput.placeholder = 'Select a paragraph first';
            this.chatInput.disabled = true;
            this.sendBtn.disabled = true;
        }
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || !this.state.selectedElement) return;

        // Add user message
        this.addChatMessage('user', message);
        this.chatInput.value = '';

        try {
            // Generate rule
            const response = await this.api.generateRule(this.state.selectedElement, message);

            if (response.type === 'success' && response.rule) {
                this.state.addRule(response.rule);
                this.addChatMessage('system', `✅ ${response.message}`);
                this.showRulePreview(response.rule);
            } else if (response.type === 'clarification') {
                this.addChatMessage('system', `❓ ${response.message}`);
            } else {
                this.addChatMessage('system', `❌ ${response.message}`);
            }
        } catch (error) {
            this.addChatMessage('system', `❌ Error: ${error.message}`);
        }
    }

    addChatMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    showRulePreview(rule) {
        const previewDiv = document.createElement('div');
        previewDiv.className = 'message system-message';
        previewDiv.innerHTML = `
            <div class="message-content">
                <strong>Rule Created:</strong><br>
                ${rule.description}<br>
                <code class="text-xs">${rule.conditions.length} conditions → ${rule.action.classify_as}</code>
            </div>
        `;
        this.chatMessages.appendChild(previewDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    renderRules() {
        if (this.state.rules.length === 0) {
            this.rulesPanel.innerHTML = '<div class="text-center text-gray-500 mt-8"><p>No rules created yet</p></div>';
            return;
        }

        this.rulesPanel.innerHTML = '';
        this.state.rules.forEach(rule => {
            const ruleEl = this.createRuleElement(rule);
            this.rulesPanel.appendChild(ruleEl);
        });
    }

    createRuleElement(rule) {
        const div = document.createElement('div');
        div.className = 'rule-item';
        div.innerHTML = `
            <div class="rule-title">${rule.action.classify_as || 'Classification Rule'}</div>
            <div class="rule-description">${rule.description}</div>
            <div class="rule-conditions">
                ${rule.conditions.map(c => `${c.property} ${c.operator} ${c.value}`).join(' AND ')}
            </div>
            <div class="rule-actions">
                <button class="edit-btn" onclick="editRule('${rule.id}')">Edit</button>
                <button class="delete-btn" onclick="deleteRule('${rule.id}')">Delete</button>
            </div>
        `;
        return div;
    }

    applyRulesToTarget() {
        if (!this.state.document) return;

        this.state.document.elements.forEach(element => {
            const targetEl = this.targetDoc.querySelector(`[data-element-id="${element.id}"]`);
            if (!targetEl) return;

            // Reset classes
            targetEl.className = 'document-element target';

            // Apply rules
            const appliedRule = this.findMatchingRule(element);
            if (appliedRule) {
                if (appliedRule.action.classify_as === 'FILTER') {
                    targetEl.style.display = 'none';
                } else {
                    const className = this.getStyleClassName(appliedRule.action.classify_as);
                    targetEl.classList.add(className);
                }
            }
        });
    }

    findMatchingRule(element) {
        // Sort rules by priority (highest first)
        const sortedRules = [...this.state.rules].sort((a, b) => b.priority - a.priority);

        for (const rule of sortedRules) {
            if (this.evaluateRuleConditions(element, rule.conditions)) {
                return rule;
            }
        }

        return null;
    }

    evaluateRuleConditions(element, conditions) {
        return conditions.every(condition => {
            const value = this.getElementProperty(element, condition.property);
            return this.evaluateCondition(value, condition.operator, condition.value);
        });
    }

    getElementProperty(element, property) {
        if (property === 'text') {
            return element.text;
        }
        return element.properties[property];
    }

    evaluateCondition(actualValue, operator, expectedValue) {
        switch (operator) {
            case 'equals':
                return actualValue === expectedValue;
            case 'notEquals':
                return actualValue !== expectedValue;
            case 'contains':
                return String(actualValue).toLowerCase().includes(String(expectedValue).toLowerCase());
            case 'greaterThan':
                return Number(actualValue) > Number(expectedValue);
            case 'lessThan':
                return Number(actualValue) < Number(expectedValue);
            case 'startsWith':
                return String(actualValue).startsWith(String(expectedValue));
            case 'endsWith':
                return String(actualValue).endsWith(String(expectedValue));
            case 'matchesRegex':
                return new RegExp(expectedValue).test(String(actualValue));
            default:
                return false;
        }
    }

    getStyleClassName(classification) {
        const classMap = {
            'Heading 1': 'style-heading-1',
            'Heading 2': 'style-heading-2',
            'Heading 3': 'style-heading-3',
            'Heading 4': 'style-heading-4',
            'Heading 5': 'style-heading-5',
            'Body Text': 'style-body-text',
            'List Paragraph': 'style-list-paragraph'
        };
        return classMap[classification] || 'style-body-text';
    }

    async exportRules() {
        if (this.state.rules.length === 0) {
            this.showError('No rules to export');
            return;
        }

        try {
            await this.api.exportRules(this.state.rules);
            this.updateStatus('Rules exported successfully');
        } catch (error) {
            this.showError(`Export failed: ${error.message}`);
        }
    }

    enableChat() {
        this.chatInput.disabled = false;
        this.updateStatus('Document loaded - Click on paragraphs to create rules');
    }

    showLoading() {
        this.loading.classList.remove('hidden');
    }

    hideLoading() {
        this.loading.classList.add('hidden');
    }

    showError(message) {
        this.addChatMessage('system', `❌ ${message}`);
        this.updateStatus(`Error: ${message}`);
    }

    updateStatus(message) {
        this.statusText.textContent = message;
    }
}

// Global functions for rule management
function editRule(ruleId) {
    // TODO: Implement rule editing
    console.log('Edit rule:', ruleId);
}

function deleteRule(ruleId) {
    if (confirm('Are you sure you want to delete this rule?')) {
        app.state.removeRule(ruleId);
        app.ui.updateStatus('Rule deleted');
    }
}

// Initialize application
const app = {
    state: new AppState(),
    api: new APIService(),
    ui: null
};

document.addEventListener('DOMContentLoaded', () => {
    app.ui = new UIManager(app.state, app.api);
    console.log('🚀 Document Formatting Rule Trainer initialized');
});