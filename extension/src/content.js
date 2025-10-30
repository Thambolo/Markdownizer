/**
 * Content Script for Markdownizer Extension
 * Main orchestrator - coordinates extraction and conversion
 * 
 * Dependencies (loaded in order via manifest.json):
 * - utils.js: Utility functions
 * - expander.js: Content expansion
 * - extractors.js: Extraction strategies
 * - payload.js: Payload builder
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

            // Step 2: Try multiple extraction strategies
            const extractions = [];

            // Try Schema.org first (highest reliability when present)
            const schemaResult = extractWithSchemaOrg();
            if (schemaResult && schemaResult.textContent.length > 500) {
                extractions.push({ ...schemaResult, method: 'schema', confidence: 0.95 });
            }

            // Try Semantic HTML (second best, wider coverage)
            const semanticResult = extractWithSemanticHTML();
            if (semanticResult && semanticResult.textContent.length > 500) {
                extractions.push({ ...semanticResult, method: 'semantic', confidence: 0.85 });
            }

            // Fallback to Readability
            const readabilityResult = extractWithReadability();
            if (readabilityResult) {
                extractions.push({ ...readabilityResult, method: 'readability', confidence: 0.70 });
            }

            if (extractions.length === 0) {
                throw new Error('All extraction methods failed');
            }

            // Use the first successful extraction (prioritized by reliability)
            const extracted = extractions[0];
            console.log(`[Markdownizer] Using extraction method: ${extracted.method}`);

            // Step 3: Build payload
            const payload = buildEnhancedPayload(extractions);

            // Step 4: Send to agent
            const result = await sendToAgent(agentUrl, payload);

            // Step 5: Handle result
            if (result.ok) {
                // Download the Markdown
                downloadMarkdown(result.markdown, result.title);

                // Notify success
                chrome.runtime.sendMessage({
                    action: 'conversionComplete',
                    chosen: result.chosen,
                    method: extracted.method
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

})();
