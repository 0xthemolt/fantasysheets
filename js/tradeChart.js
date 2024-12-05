function createLineChart(containerId, data, options = {}) {
    const canvas = document.getElementById(containerId);
    
    // Destroy existing chart if it exists
    const existingChart = Chart.getChart(canvas);
    if (existingChart) {
        console.log('Destroying existing chart');
        existingChart.destroy();
    }
    
    // Log the actual data structure
    console.log('Chart input data structure:', {
        labels: data.labels,
        values: data.values
    });

    // Create chart configuration object separately for debugging
    const chartConfig = {
        type: 'line',
        data: {
            labels: data.labels.map(timestamp => new Date(timestamp).toLocaleString()),
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
                    type: 'time',
                    time: {
                        unit: 'minute',
                        displayFormats: {
                            minute: 'MMM D'
                        }
                    },
                    title: {
                        display: true,
                        text: chartOptions.xAxisLabel
                    },
                    sorting: 'ascending'
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: chartOptions.yAxisLabel
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    };

    console.log('Full chart configuration:', chartConfig);
    
    // Create the chart with the verified configuration
    const newChart = new Chart(canvas, chartConfig);
    
    // Log the actual scales configuration from the created chart
    console.log('Applied scales configuration:', newChart.options.scales);
}
