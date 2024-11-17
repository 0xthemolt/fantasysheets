function updateTimeAgo() {
   
    // Get the timestamp text and parse it more carefully
    const timestampText = document.getElementById('timestamp').textContent;
    if (enableLogging) console.log('Timestamp Text:', timestampText); // Log the raw timestamp text
    // Split the timestamp into components
    const [date, time] = timestampText.split(' ');
    if (enableLogging) console.log('Date:', date, 'Time:', time); // Log the split date and time
    // Create a proper ISO timestamp
    const isoTimestamp = `${date}T${time}Z`; // Adding T between date/time and Z for UTC
    if (enableLogging) console.log('ISO Timestamp:', isoTimestamp); // Log the ISO formatted timestamp
    const timestampUTC = new Date(isoTimestamp);
    if (enableLogging) console.log('Timestamp UTC:', timestampUTC); // Log the UTC timestamp
    const now = new Date();
    if (enableLogging) console.log('Current Time:', now); // Log the current time
    
    // Check if the date is valid before proceeding
    if (isNaN(timestampUTC.getTime())) {
        if (enableLogging) console.error('Invalid timestamp:', timestampText);
        document.getElementById('timeAgo').textContent = '';
        return;
    }

    const diffMinutes = Math.floor((now - timestampUTC) / (1000 * 60));
    if (enableLogging) console.log('Difference in Minutes:', diffMinutes); // Log the difference in minutes
    
    let timeAgoText = '';
    if (diffMinutes < 60) {
        timeAgoText = `(${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago)`;
    } else {
        const hours = Math.floor(diffMinutes / 60);
        const minutes = diffMinutes % 60;
        timeAgoText = `(${hours} hour${hours !== 1 ? 's' : ''} ${minutes} minute${minutes !== 1 ? 's' : ''} ago)`;
    }
    
    if (enableLogging) console.log('Time Ago Text:', timeAgoText); // Log the final time ago text

    const timeAgoElement = document.getElementById('timeAgo');
    if (!timeAgoElement) {
        if (enableLogging) console.error('Element with ID "timeAgo" not found');
        return;
    } else {
        if (enableLogging) console.log('Element with ID "timeAgo" found');
    }

    timeAgoElement.textContent = ' ' + timeAgoText;
}

document.addEventListener('DOMContentLoaded', function() {
    if (enableLogging) console.log('DOM fully loaded and parsed'); // Add this line
    updateTimeAgo();
    setInterval(updateTimeAgo, 60000); // Update every minute
});