// Declare variables at the top of the file to track instances
let tradeChart = null;
let currentPlugin = null;

function createLineChart(containerId, data, options = {}) {
    // Ensure proper cleanup of previous instances
    if (tradeChart) {
        console.log('Destroying existing trade chart');
        tradeChart.destroy();
        if (currentPlugin) {
            Chart.unregister(currentPlugin);
        }
        tradeChart = null;
        currentPlugin = null;
    }

    const canvas = document.getElementById(containerId);
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Define colors for different rarities
    const rarityColors = {
        'common': { border: 'rgb(169, 169, 169)', background: 'rgba(169, 169, 169, 0.1)' },
        'uncommon': { border: 'rgb(0, 128, 0)', background: 'rgba(0, 128, 0, 0.1)' },
        'rare': { border: 'rgb(0, 0, 255)', background: 'rgba(0, 0, 255, 0.1)' },
        'epic': { border: 'rgb(128, 0, 128)', background: 'rgba(128, 0, 128, 0.1)' },
        'legendary': { border: 'rgb(255, 165, 0)', background: 'rgba(255, 165, 0, 0.1)' }
    };

    // Use the datasets directly from the input data
    const datasets = data.datasets.map(dataset => ({
        label: dataset.label,
        data: dataset.data,  // Data is already in {x, y} format
        borderColor: rarityColors[dataset.label.toLowerCase()]?.border || 'rgb(0, 0, 0)',
        backgroundColor: rarityColors[dataset.label.toLowerCase()]?.background || 'rgba(0, 0, 0, 0.1)',
        tension: 0.4,
        fill: true,
        cubicInterpolationMode: 'monotone'
    }));

    const chartConfig = {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,  // Added to ensure proper rendering
            plugins: {
                title: {
                    display: true,
                    text: options.chartTitle || 'Chart'
                }
            },
            scales: {
                x: {
                    type: 'time',
                    grid: {
                        display: false
                    },
                    time: {
                        unit: 'minute',
                        displayFormats: {
                            minute: 'MMM d'
                        }
                    },
                    title: {
                        display: true,
                        text: options.xAxisLabel || ''
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: options.yAxisLabel || ''
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

    console.log('Data being plotted:', {
        labels: data.labels,
        values: data.values
    });

    console.log('Creating new trade chart with config:', chartConfig);
    
    // Store the new chart instance
    tradeChart = new Chart(canvas, chartConfig);
    return tradeChart;
}
