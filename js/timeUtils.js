document.addEventListener('DOMContentLoaded', function() {
    // Initialize time ago and set update interval
    updateTimeAgo();
    setInterval(updateTimeAgo, 60000); // Update every minute
});

function updateTimeAgo() {
    const timeAgoElement = document.getElementById('timeAgo');
    if (!timeAgoElement) {
        console.log('TimeAgo element not found');
        return;
    }

    const timestamp = timeAgoElement.getAttribute('data-timestamp');
    if (!timestamp) {
        console.log('No timestamp found', timeAgoElement);
        return;
    }

    console.log('Processing timestamp:', timestamp);
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) {
        console.log('Invalid date from timestamp');
        return;
    }

    const timeAgoText = calculateTimeAgo(date);
    timeAgoElement.textContent = ` (${timeAgoText})`;
}


function calculateTimeAgo(date) {
    const now = new Date();
    const secondsAgo = Math.floor((now - date) / 1000);

    if (secondsAgo < 60) {
        return `${secondsAgo} seconds ago`;
    } else if (secondsAgo < 3600) {
        const minutesAgo = Math.floor(secondsAgo / 60);
        return `${minutesAgo} minutes ago`;
    } else if (secondsAgo < 86400) {
        const hoursAgo = Math.floor(secondsAgo / 3600);
        return `${hoursAgo} hours ago`;
    } else {
        const daysAgo = Math.floor(secondsAgo / 86400);
        return `${daysAgo} days ago`;
    }
}


// Add this to check if the script is loading
console.log('TimeUtils script loaded');
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing timeAgo');
    updateTimeAgo();
    setInterval(updateTimeAgo, 60000);
});