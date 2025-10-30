/**
 * Utility functions for Markdownizer extension
 */

/**
 * Send payload to agent
 */
async function sendToAgent(agentUrl, payload) {
    const response = await fetch(`${agentUrl}/ingest`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        throw new Error(`Agent returned ${response.status}: ${response.statusText}`);
    }

    return await response.json();
}

/**
 * Download Markdown file
 */
function downloadMarkdown(markdown, title) {
    const filename = sanitizeFilename(title) + '.md';
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);

    // Trigger download via invisible link
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    setTimeout(() => URL.revokeObjectURL(url), 60000);
}

/**
 * Download fallback HTML when agent is offline
 */
function downloadFallbackHTML() {
    const filename = sanitizeFilename(document.title) + '_backup.html';
    const html = document.documentElement.outerHTML;
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    setTimeout(() => URL.revokeObjectURL(url), 60000);
}

/**
 * Check if URL is same origin
 */
function isSameOrigin(url) {
    try {
        const urlObj = new URL(url, window.location.href);
        return urlObj.origin === window.location.origin;
    } catch {
        return false;
    }
}

/**
 * Sanitize filename for download
 */
function sanitizeFilename(name) {
    return name
        .replace(/[^a-z0-9]/gi, '_')
        .replace(/_+/g, '_')
        .substring(0, 100);
}

/**
 * Sleep utility
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
