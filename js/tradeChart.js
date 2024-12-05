function createLineChart(containerId, data, options = {}) {
    // Get the canvas element
    const canvas = document.getElementById(containerId);
    
    // Destroy existing chart if it exists
    const existingChart = Chart.getChart(canvas);
    if (existingChart) {
        existingChart.destroy();
    }
    
    // Default configuration
    const defaultOptions = {
        chartTitle: 'Line Chart',
        xAxisLabel: 'X Axis',
        yAxisLabel: 'Y Axis',
        lineColor: '#4CAF50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)'
    };

    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };

    // Create the chart
    new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: chartOptions.chartTitle,
                data: data.values,
                borderColor: chartOptions.lineColor,
                backgroundColor: chartOptions.backgroundColor,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: chartOptions.chartTitle
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: chartOptions.xAxisLabel
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: chartOptions.yAxisLabel
                    }
                }
            }
        }
    });
}

// Example usage:
// const sampleData = {
//     labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
//     values: [10, 25, 15, 30, 20]
// };
//
// const customOptions = {
//     chartTitle: 'Monthly Sales',
//     xAxisLabel: 'Month',
//     yAxisLabel: 'Sales ($)',
//     lineColor: '#2196F3',
//     backgroundColor: 'rgba(33, 150, 243, 0.1)'
// };
//
// createLineChart('myChartCanvas', sampleData, customOptions);
