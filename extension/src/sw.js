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
        // Inject Readability library
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['vendor/readability.js']
        });

        // Inject content script
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
        });

        // Send message to content script to start capture
        chrome.tabs.sendMessage(
            tab.id,
            { action: 'startCapture', agentUrl },
            (response) => {
                if (chrome.runtime.lastError) {
                    showNotification('Error', chrome.runtime.lastError.message, 'error');
                }
            }
        );

    } catch (error) {
        console.error('Injection failed:', error);

        // Check if CSP is blocking
        if (error.message.includes('Content Security Policy')) {
            showNotification(
                'CSP Blocked',
                'This page blocks extension scripts. Try opening in a new tab.',
                'warning'
            );
        } else {
            showNotification('Error', error.message, 'error');
        }
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
