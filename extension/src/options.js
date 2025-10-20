/**
 * Options page script for Markdownizer Extension
 */

// DOM elements
const agentUrlInput = document.getElementById('agent-url');
const autoDownloadCheckbox = document.getElementById('auto-download');
const saveButton = document.getElementById('save-settings');
const testButton = document.getElementById('test-connection');
const saveStatus = document.getElementById('save-status');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const statusDetails = document.getElementById('status-details');

// Load saved settings
async function loadSettings() {
    const settings = await chrome.storage.sync.get({
        agentUrl: 'http://127.0.0.1:5050',
        autoDownloadBackup: false
    });

    agentUrlInput.value = settings.agentUrl;
    autoDownloadCheckbox.checked = settings.autoDownloadBackup;

    // Test connection on load
    testConnection();
}

// Save settings
async function saveSettings() {
    const agentUrl = agentUrlInput.value.trim();

    if (!agentUrl) {
        showSaveStatus('Please enter an agent URL', 'error');
        return;
    }

    // Validate URL format
    try {
        new URL(agentUrl);
    } catch (e) {
        showSaveStatus('Invalid URL format', 'error');
        return;
    }

    // Save to storage
    await chrome.storage.sync.set({
        agentUrl: agentUrl,
        autoDownloadBackup: autoDownloadCheckbox.checked
    });

    showSaveStatus('Settings saved successfully!', 'success');

    // Test new connection
    setTimeout(testConnection, 500);
}

// Test agent connection
async function testConnection() {
    const agentUrl = agentUrlInput.value.trim();

    if (!agentUrl) {
        updateStatus('offline', 'No agent URL configured');
        return;
    }

    updateStatus('checking', 'Testing connection...');

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${agentUrl}/health`, {
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (response.ok) {
            const data = await response.json();
            updateStatus(
                'online',
                'Agent connected',
                `Version ${data.version} • ${data.status}`
            );
        } else {
            updateStatus('error', `HTTP ${response.status}: ${response.statusText}`);
        }

    } catch (error) {
        if (error.name === 'AbortError') {
            updateStatus('offline', 'Connection timeout', 'Agent not responding after 5 seconds');
        } else {
            updateStatus(
                'offline',
                'Agent not reachable',
                'Make sure the agent service is running'
            );
        }
    }
}

// Update connection status display
function updateStatus(state, message, details = '') {
    statusIndicator.className = `status-indicator ${state}`;
    statusText.textContent = message;
    statusDetails.textContent = details;
}

// Show save status message
function showSaveStatus(message, type) {
    saveStatus.textContent = message;
    saveStatus.className = `save-status ${type}`;
    saveStatus.style.display = 'block';

    setTimeout(() => {
        saveStatus.style.display = 'none';
    }, 3000);
}

// Event listeners
saveButton.addEventListener('click', saveSettings);
testButton.addEventListener('click', testConnection);

// Load settings on page load
loadSettings();

// Auto-test connection every 10 seconds
setInterval(testConnection, 10000);
