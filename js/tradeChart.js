// Declare variables at the top of the file to track instances
let tradeChart = null;
let currentPlugin = null;
let annotationPlugin = null;

function createLineChart(containerId, data, options = {}) {
    console.log('createLineChart called with:', { containerId, data, options });

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

    console.log('After cleanup, creating new chart');
    
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
    const datasets = data.datasets.map(dataset => {
        console.log('Creating dataset for:', dataset.label, 'with color:', rarityColors[dataset.label.toLowerCase()]);
        return {
            label: dataset.label,
            data: dataset.data,
            borderColor: rarityColors[dataset.label.toLowerCase()]?.border || 'rgb(0, 0, 0)',
            backgroundColor: rarityColors[dataset.label.toLowerCase()]?.background || 'rgba(0, 0, 0, 0.1)',
            tension: 0.4,
            fill: true,
            cubicInterpolationMode: 'monotone',
            hidden: !getInitialVisibility(dataset.label),
            borderWidth: 2.5,
            pointRadius: 3,
            pointBackgroundColor: rarityColors[dataset.label.toLowerCase()]?.border || 'rgb(0, 0, 0)',
            pointBorderColor: rarityColors[dataset.label.toLowerCase()]?.border || 'rgb(0, 0, 0)',
            pointBorderWidth: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: rarityColors[dataset.label.toLowerCase()]?.border || 'rgb(0, 0, 0)',
            pointHoverBorderWidth: 0,
        };
    });

    // Create and register the annotation plugin first
    annotationPlugin = {
        id: 'customAnnotation',
        afterDraw: (chart) => {
            console.log('Plugin afterDraw called');
            const ctx = chart.ctx;
            const xAxis = chart.scales.x;
            const yAxis = chart.scales.y;
            
            // Initialize array to track label positions
            const labels = [];
            
            // Get the current dataset and its last value
            const currentDataset = chart.data.datasets[0];
            if (currentDataset && currentDataset.data.length > 0) {
                const lastPoint = currentDataset.data[currentDataset.data.length - 1];
                const lastValue = lastPoint.y;
                labels.push({
                    value: lastValue,
                    label: `Last: ${lastValue.toFixed(3)}`,
                    color: currentDataset.borderColor,
                    yPos: yAxis.getPixelForValue(lastValue)
                });
            }
            
            // Add bid and floor labels
            const horizontalLines = [
                { 
                    value: options.bidPrice || 0.005, 
                    label: 'Bid', 
                    color: 'rgba(255, 99, 132, 0.75)' 
                },
                { 
                    value: options.floorPrice || 0.008, 
                    label: 'Floor', 
                    color: 'rgba(255, 165, 0, 0.75)' 
                }
            ];

            horizontalLines.forEach(({value, label, color}) => {
                labels.push({
                    value: value,
                    label: `${label}: ${value.toFixed(3)}`,
                    color: color,
                    yPos: yAxis.getPixelForValue(value)
                });
            });

            // Sort labels by y position (top to bottom)
            labels.sort((a, b) => a.yPos - b.yPos);

            // Adjust positions to prevent overlap
            const minSpacing = 25; // Minimum pixels between labels
            for (let i = 1; i < labels.length; i++) {
                const prevLabel = labels[i - 1];
                const currentLabel = labels[i];
                
                if (currentLabel.yPos - prevLabel.yPos < minSpacing) {
                    currentLabel.yPos = prevLabel.yPos + minSpacing;
                }
            }

            // Draw the lines and labels
            labels.forEach(({value, label, color, yPos}) => {
                const originalYPos = yAxis.getPixelForValue(value);
                
                // Draw horizontal line at the original value position
                ctx.save();
                ctx.beginPath();
                ctx.setLineDash([5, 5]);
                ctx.strokeStyle = color;
                ctx.lineWidth = 1;
                ctx.moveTo(xAxis.left, originalYPos);
                ctx.lineTo(xAxis.right, originalYPos);
                ctx.stroke();
                
                // Draw label with adjusted position
                ctx.textAlign = 'left';
                ctx.font = 'bold 12px Arial';
                const padding = 4;
                const textWidth = ctx.measureText(label).width;
                
                // Draw background rectangle
                ctx.fillStyle = 'rgba(255, 255, 255, 0)';
                ctx.fillRect(
                    xAxis.right + 5, 
                    yPos - 10, 
                    textWidth + (padding * 2), 
                    20
                );
                
                // Draw text
                ctx.fillStyle = color;
                ctx.fillText(label, xAxis.right + 5 + padding, yPos + 4);

                // If label position is different from value position, draw a connecting line
                if (Math.abs(yPos - originalYPos) > 1) {
                    ctx.beginPath();
                    ctx.setLineDash([2, 2]);
                    ctx.strokeStyle = color;
                    ctx.moveTo(xAxis.right, originalYPos);
                    ctx.lineTo(xAxis.right + 5, yPos);
                    ctx.stroke();
                }
                
                ctx.restore();
            });
        }
    };

    // Register the plugin explicitly
    console.log('Registering annotation plugin'); // Debug log
    Chart.register(annotationPlugin);

    // Determine the maximum value for the y-axis
    const maxDataValue = Math.max(...data.datasets.flatMap(ds => ds.data.map(point => point.y)));
    const maxYAxisValue = Math.max(maxDataValue, options.floorPrice || 0);

    const chartConfig = {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    right: 100  // Add padding for labels
                }
            },
            plugins: {
                legend: {
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle'
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
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM d'
                        }
                    },
                    title: {
                        display: true,
                        text: options.xAxisLabel || ''
                    },
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 10
                    }
                },
                y: {
                    beginAtZero: true,
                    max: maxYAxisValue, // Set the max y-axis value
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
