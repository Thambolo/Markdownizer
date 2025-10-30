/**
 * Payload builder
 * Collects metadata and builds payload for agent
 */

/**
 * Build payload for agent with multiple extraction results
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
 * Build enhanced payload with multiple extraction methods
 */
function buildEnhancedPayload(extractions) {
    // Pick the best extraction as primary
    const primary = extractions[0];

    // Collect iframe information
    const iframes = Array.from(document.querySelectorAll('iframe')).map(iframe => ({
        src: iframe.src,
        sameOrigin: isSameOrigin(iframe.src)
    }));

    // Collect stats from primary extraction
    const content = primary.content || '';
    const text = primary.textContent || '';

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = content;

    const stats = {
        char_count: text.length,
        headings: tempDiv.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
        lists: tempDiv.querySelectorAll('ul, ol').length
    };

    return {
        url: window.location.href,
        title: primary.title || document.title,
        html_readability: content,
        text_readability: text,
        meta: {
            captured_at: new Date().toISOString(),
            stats: stats,
            iframe_info: iframes,
            extraction_methods: extractions.map(e => e.method) // Track which methods succeeded
        }
    };
}
