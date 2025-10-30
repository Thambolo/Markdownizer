/**
 * Content extraction strategies
 * Multiple extraction methods for maximum reliability
 */

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
 * Extract content using Schema.org JSON-LD structured data
 * High reliability (~85-90% when present)
 */
function extractWithSchemaOrg() {
    // Look for JSON-LD structured data
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');

    for (const script of scripts) {
        try {
            const data = JSON.parse(script.textContent);

            // Handle single object or array
            const items = Array.isArray(data) ? data : [data];

            for (const item of items) {
                // Check for Article types
                if (item['@type'] === 'Article' ||
                    item['@type'] === 'NewsArticle' ||
                    item['@type'] === 'BlogPosting') {

                    const title = item.headline || item.name;
                    const body = item.articleBody;

                    if (body && body.length > 500) {
                        return {
                            title: title,
                            content: `<article><h1>${title}</h1><p>${body}</p></article>`,
                            textContent: body,
                            byline: item.author?.name || null,
                            excerpt: item.description || null
                        };
                    }
                }
            }
        } catch (e) {
            // Invalid JSON, skip
            continue;
        }
    }

    // Also check for itemprop microdata
    const articleBody = document.querySelector('[itemprop="articleBody"]');
    if (articleBody && articleBody.innerText.length > 500) {
        const title = document.querySelector('[itemprop="headline"]')?.innerText || document.title;
        return {
            title: title,
            content: articleBody.innerHTML,
            textContent: articleBody.innerText,
            byline: document.querySelector('[itemprop="author"]')?.innerText || null,
            excerpt: null
        };
    }

    return null;
}

/**
 * Extract content using semantic HTML5 tags
 * High reliability (~75-80% on modern sites)
 */
function extractWithSemanticHTML() {
    // Try standard landmarks in priority order
    const candidates = [
        document.querySelector('main article'),
        document.querySelector('main'),
        document.querySelector('[role="main"] article'),
        document.querySelector('[role="main"]'),
        document.querySelector('article'),
        document.querySelector('[role="article"]')
    ];

    for (const elem of candidates) {
        if (elem && elem.innerText.length > 500) {
            // Extract title from h1 if available
            const h1 = elem.querySelector('h1');
            const title = h1 ? h1.innerText : document.title;

            return {
                title: title,
                content: elem.innerHTML,
                textContent: elem.innerText,
                byline: null,
                excerpt: null
            };
        }
    }

    return null;
}
