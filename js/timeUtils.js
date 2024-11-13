function updateTimeAgo() {
    // Get the timestamp text and parse it more carefully
    const timestampText = document.querySelector('.small-text span').textContent;
    // Split the timestamp into components
    const [date, time] = timestampText.split(' ');
    // Create a proper ISO timestamp
    const isoTimestamp = `${date}T${time}Z`; // Adding T between date/time and Z for UTC
    const timestampUTC = new Date(isoTimestamp);
    const now = new Date();
    
    // Check if the date is valid before proceeding
    if (isNaN(timestampUTC.getTime())) {
        console.error('Invalid timestamp:', timestampText);
        document.getElementById('timeAgo').textContent = '';
        return;
    }

    const diffMinutes = Math.floor((now - timestampUTC) / (1000 * 60));
    
    let timeAgoText = '';
    if (diffMinutes < 60) {
        timeAgoText = `(${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago)`;
    } else {
        const hours = Math.floor(diffMinutes / 60);
        const minutes = diffMinutes % 60;
        timeAgoText = `(${hours} hour${hours !== 1 ? 's' : ''} ${minutes} minute${minutes !== 1 ? 's' : ''} ago)`;
    }
    
    document.getElementById('timeAgo').textContent = ' ' + timeAgoText;
}

// Start updating time ago when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    updateTimeAgo();
    setInterval(updateTimeAgo, 60000); // Update every minute
});