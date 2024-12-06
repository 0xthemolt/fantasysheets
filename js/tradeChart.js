// Declare variables at the top of the file to track instances
let tradeChart = null;
let currentPlugin = null;
let annotationPlugin = null;

function createLineChart(containerId, data, options = {}) {
    // Ensure proper cleanup of previous instances
    if (tradeChart) {
        console.log('Destroying existing trade chart');
        tradeChart.destroy();
        if (currentPlugin) {
            Chart.unregister(currentPlugin);
        }
        if (annotationPlugin) {
            Chart.unregister(annotationPlugin);
        }
        tradeChart = null;
        currentPlugin = null;
        annotationPlugin = null;
    }

    const canvas = document.getElementById(containerId);
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Define colors for different rarities
    const rarityColors = {
        'common': { border: 'rgb(72, 238, 75)', background: 'rgba(72, 238, 75, 0.1)' },
        'rare': { border: 'rgb(2, 224, 244)', background: 'rgba(2, 224, 244, 0.1)' },
        'epic': { border: 'rgb(205, 47, 215)', background: 'rgba(205, 47, 215, 0.1)' },
        'legendary': { border: 'rgb(127, 118, 245)', background: 'rgba(127, 118, 245, 0.1)' },
        'all': { border: 'rgb(102, 102, 102)', background: 'rgba(102, 102, 102, 0.1)' }
    };

    // Get unique labels and determine initial visibility
    const uniqueLabels = [...new Set(data.datasets.map(ds => ds.label.toLowerCase()))];
    const getInitialVisibility = (label) => {
        if (uniqueLabels.length === 1) return true;
        
        const priority = ['common', 'rare', 'epic', 'legendary'];
        const defaultLabel = priority.find(p => uniqueLabels.includes(p)) || uniqueLabels[0];
        return label.toLowerCase() === defaultLabel;
    };

    // Use the datasets directly from the input data
    const datasets = data.datasets.map(dataset => ({
        label: dataset.label,
        data: dataset.data,
        borderColor: rarityColors[dataset.label.toLowerCase()]?.border || 'rgb(0, 0, 0)',
        backgroundColor: rarityColors[dataset.label.toLowerCase()]?.background || 'rgba(0, 0, 0, 0.1)',
        tension: 0.4,
        fill: true,
        cubicInterpolationMode: 'monotone',
        hidden: !getInitialVisibility(dataset.label),
        borderWidth: 2.5,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBorderWidth: 2,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: rarityColors[dataset.label.toLowerCase()]?.border || 'rgb(0, 0, 0)',
    }));

    // Before creating the chart config, add the annotation plugin
    annotationPlugin = {
        id: 'customAnnotation',
        afterDraw: (chart) => {
            const annotations = [
                { date: new Date('2024-11-27T00:00:00'), label: 'MT27' },
                { date: new Date('2024-12-01T00:00:00'), label: 'MT28' }
            ];

            const ctx = chart.ctx;
            const xAxis = chart.scales.x;
            const yAxis = chart.scales.y;

            // Debug logging - only once
            if (!chart._annotationsDrawn) {
                console.log('Chart dimensions:', {
                    top: yAxis.top,
                    bottom: yAxis.bottom,
                    left: xAxis.left,
                    right: xAxis.right
                });

                annotations.forEach(({date, label}) => {
                    const xPos = xAxis.getPixelForValue(date);
                    console.log(`Annotation position for ${label}:`, {
                        date: date,
                        xPos: xPos,
                        visible: xPos >= xAxis.left && xPos <= xAxis.right
                    });
                });
                
                chart._annotationsDrawn = true;
            }

            annotations.forEach(({date, label}) => {
                const xPos = xAxis.getPixelForValue(date);
                
                // Only draw if the position is within the chart bounds
                if (xPos >= xAxis.left && xPos <= xAxis.right) {
                    // Draw vertical line
                    ctx.save();
                    ctx.beginPath();
                    ctx.setLineDash([5, 5]);
                    ctx.strokeStyle = 'rgba(150, 150, 150, 0.75)';
                    ctx.lineWidth = 1;
                    ctx.moveTo(xPos, yAxis.top);
                    ctx.lineTo(xPos, yAxis.bottom);
                    ctx.stroke();
                    
                    // Draw label
                    ctx.textAlign = 'center';
                    ctx.fillStyle = 'rgba(150, 150, 150, 0.9)';
                    ctx.font = '12px Arial';
                    ctx.fillText(label, xPos, yAxis.top + 20);
                    ctx.restore();
                }
            });
        }
    };

    // Register the plugin
    Chart.register(annotationPlugin);

    const chartConfig = {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 15
                    }
                },
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
                            if (value >= 1) {
                                return value.toFixed(2);
                            } else {
                                return value.toFixed(3);
                            }
                        }
                    }
                }
            }
        }
    };

    console.log('Data being plotted:', {
        datasets: data.datasets.map(ds => ({
            label: ds.label,
            dataPoints: ds.data
        }))
    });

    console.log('Creating new trade chart with config:', chartConfig);
    
    // Store the new chart instance
    tradeChart = new Chart(canvas, chartConfig);
    return tradeChart;
}
