// Tooltip initialization
function initializeTooltips() {
    const tooltips = document.querySelectorAll('.tooltip-trigger');
    
    tooltips.forEach(tooltip => {
        ['click', 'keydown'].forEach(eventType => {
            tooltip.addEventListener(eventType, handleTooltipEvent);
        });
    });

    // Global event listeners
    document.addEventListener('click', closeAllTooltips);
    document.addEventListener('focusin', handleOutsideClick);
    document.addEventListener('keydown', handleEscapeKey);
}

function handleTooltipEvent(e) {
    // For keyboard, only process Enter or Space
    if (e.type === 'keydown' && !(e.key === 'Enter' || e.key === ' ')) {
        return;
    }
    
    e.preventDefault();
    e.stopPropagation();
    
    // Close all other tooltips
    const tooltips = document.querySelectorAll('.tooltip-trigger');
    tooltips.forEach(t => {
        if (t !== this) {
            t.classList.remove('active');
            t.setAttribute('aria-expanded', 'false');
        }
    });
    
    // Toggle current tooltip
    const isActive = this.classList.toggle('active');
    this.setAttribute('aria-expanded', isActive);
}

function handleOutsideClick(e) {
    if (!e.target.closest('.tooltip-trigger')) {
        closeAllTooltips();
    }
}

function handleEscapeKey(e) {
    if (e.key === 'Escape') {
        closeAllTooltips();
    }
}

function closeAllTooltips() {
    const tooltips = document.querySelectorAll('.tooltip-trigger');
    tooltips.forEach(tooltip => {
        tooltip.classList.remove('active');
        tooltip.setAttribute('aria-expanded', 'false');
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeTooltips);