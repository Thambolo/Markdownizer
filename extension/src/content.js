/**
 * Content Script for Markdownizer Extension
 * Captures page content using Readability and sends to agent
 */

(function () {
    'use strict';

    // Listen for capture command from service worker
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === 'startCapture') {
            captureAndConvert(message.agentUrl);
            sendResponse({ status: 'started' });
        }
    });

    /**
     * Main capture and conversion function
     */
    async function captureAndConvert(agentUrl) {
        try {
            console.log('[Markdownizer] Starting capture...');

            // Step 1: Auto-expand content
            await autoExpandContent();

            // Step 2: Extract with Readability
            const extracted = extractWithReadability();
            if (!extracted) {
                throw new Error('Readability extraction failed');
            }

            // Step 3: Collect metadata
            const payload = buildPayload(extracted);

            // Step 4: Send to agent
            const result = await sendToAgent(agentUrl, payload);

            // Step 5: Handle result
            if (result.ok) {
                // Download the Markdown
                downloadMarkdown(result.markdown, result.title);

                // Notify success
                chrome.runtime.sendMessage({
                    action: 'conversionComplete',
                    chosen: result.chosen
                });
            } else {
                // Handle error response
                throw new Error(result.message || 'Conversion failed');
            }

        } catch (error) {
            console.error('[Markdownizer] Error:', error);

            // Check if agent is offline
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                chrome.runtime.sendMessage({ action: 'agentOffline' });

                // Fallback: download raw HTML
                downloadFallbackHTML();
            } else {
                chrome.runtime.sendMessage({
                    action: 'conversionFailed',
                    error: error.message
                });
            }
        }
    }

    /**
     * Auto-expand page content (bounded)
     */
    async function autoExpandContent() {
        const maxSteps = 3;
        const scrollDelay = 500;

        // Expand <details> elements
        document.querySelectorAll('details:not([open])').forEach(details => {
            details.setAttribute('open', '');
        });

        // Click "show more" / "read more" buttons
        const expandButtons = Array.from(document.querySelectorAll('button, a')).filter(el => {
            const text = el.textContent.toLowerCase();
            return text.includes('show more') ||
                text.includes('read more') ||
                text.includes('expand') ||
                text.includes('see more');
        });

        expandButtons.slice(0, 3).forEach(button => {
            try {
                button.click();
            } catch (e) {
                // Ignore click errors
            }
        });

        // Scroll to bottom (for infinite scroll)
        let previousHeight = 0;
        for (let i = 0; i < maxSteps; i++) {
            const currentHeight = document.documentElement.scrollHeight;

            if (currentHeight === previousHeight) {
                break; // No more content loaded
            }

            window.scrollTo(0, currentHeight);
            await sleep(scrollDelay);
            previousHeight = currentHeight;
        }

        // Scroll back to top
        window.scrollTo(0, 0);
    }

    /**
     * Extract content using Readability.js
     */
    function extractWithReadability() {
        // Clone the document
        const documentClone = document.cloneNode(true);

        // Create Readability instance
        const reader = new Readability(documentClone, {
            debug: false,
            charThreshold: 500
        });

        // Parse the page
        const article = reader.parse();

        return article;
    }

    /**
     * Build payload for agent
     */
    function buildPayload(article) {
        // Collect iframe information
        const iframes = Array.from(document.querySelectorAll('iframe')).map(iframe => ({
            src: iframe.src,
            sameOrigin: isSameOrigin(iframe.src)
        }));

        // Collect stats
        const content = article.content || '';
        const text = article.textContent || '';

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = content;

        const stats = {
            char_count: text.length,
            headings: tempDiv.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
            lists: tempDiv.querySelectorAll('ul, ol').length
        };

        return {
            url: window.location.href,
            title: article.title || document.title,
            html_readability: content,
            text_readability: text,
            meta: {
                captured_at: new Date().toISOString(),
                stats: stats,
                iframe_info: iframes
            }
        };
    }

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

        chrome.runtime.sendMessage({
            action: 'download',
            url: url,
            filename: filename
        });

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
     * Utility: Check if URL is same origin
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
     * Utility: Sanitize filename
     */
    function sanitizeFilename(name) {
        return name
            .replace(/[^a-z0-9]/gi, '_')
            .replace(/_+/g, '_')
            .substring(0, 100);
    }

    /**
     * Utility: Sleep function
     */
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

})();
