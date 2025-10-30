/**
 * Content expansion utilities
 * Auto-expands hidden content before extraction
 */

/**
 * Auto-expand page content (bounded)
 * - Expands <details> elements
 * - Clicks "show more" buttons
 * - Scrolls for infinite scroll content
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
