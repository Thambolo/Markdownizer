/**
 * Service Worker for Markdownizer Extension
 * Handles extension icon clicks and coordinates content script injection
 */

// Default agent URL
const DEFAULT_AGENT_URL = 'http://127.0.0.1:5050';

// Handle extension icon click
chrome.action.onClicked.addListener(async (tab) => {
    if (!tab.id) return;

    // Get agent URL from storage
    const { agentUrl = DEFAULT_AGENT_URL } = await chrome.storage.sync.get('agentUrl');

    try {
        // Try sending message first (scripts might already be loaded)
        chrome.tabs.sendMessage(
            tab.id,
            { action: 'startCapture', agentUrl },
            async (response) => {
                // If no response, content script isn't loaded yet - inject it
                if (chrome.runtime.lastError) {
                    console.log('Content script not loaded, injecting now...');

                    try {
                        // Inject all scripts in order
                        await chrome.scripting.executeScript({
                            target: { tabId: tab.id },
                            files: [
                                'vendor/readability.js',
                                'utils.js',
                                'expander.js',
                                'extractors.js',
                                'payload.js',
                                'content.js'
                            ]
                        });

                        // Now send the message
                        chrome.tabs.sendMessage(
                            tab.id,
                            { action: 'startCapture', agentUrl }
                        );
                    } catch (injectError) {
                        console.error('Injection failed:', injectError);

                        // Check if CSP is blocking
                        if (injectError.message.includes('Content Security Policy')) {
                            showNotification(
                                'CSP Blocked',
                                'This page blocks extension scripts. Try opening in a new tab.',
                                'warning'
                            );
                        } else {
                            showNotification('Error', injectError.message, 'error');
                        }
                    }
                }
            }
        );

    } catch (error) {
        console.error('Error:', error);
        showNotification('Error', error.message, 'error');
    }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'conversionComplete') {
        showNotification(
            'Success!',
            `Markdown ready (${message.chosen} source used)`,
            'success'
        );
    } else if (message.action === 'conversionFailed') {
        showNotification(
            'Conversion Failed',
            message.error || 'Unknown error',
            'error'
        );
    } else if (message.action === 'agentOffline') {
        showNotification(
            'Agent Offline',
            'Local agent service is not running. Start the agent server and try again.',
            'warning'
        );
    }
});

// Show browser notification
function showNotification(title, message, type = 'info') {
    const icons = {
        success: 'icons/icon48.png',
        error: 'icons/icon48.png',
        warning: 'icons/icon48.png',
        info: 'icons/icon48.png'
    };

    chrome.notifications.create({
        type: 'basic',
        iconUrl: icons[type],
        title: title,
        message: message,
        priority: 2
    });
}

// Install/update handler
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        // Set default settings
        chrome.storage.sync.set({
            agentUrl: DEFAULT_AGENT_URL,
            autoDownloadBackup: false
        });

        console.log('Markdownizer installed! Default agent URL:', DEFAULT_AGENT_URL);
    }
});
