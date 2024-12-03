let heroChart; // Declare a variable to hold the chart instance
let currentPlugin = null; // Track the current plugin instance

function createHeroChart(containerId, jsonUrl, heroName) {
    // Ensure proper cleanup of the previous chart and plugin
    if (heroChart) {
        heroChart.destroy();
        if (currentPlugin) {
            Chart.unregister(currentPlugin);
        }
    }

    console.log('Creating chart for:', { containerId, jsonUrl, heroName });
    return fetch(jsonUrl)
        .then(response => response.json())
        .then(data => {
            console.log('Chart data received:', data);
            const scores = data.hero_scores[heroName];
            console.log('Processed scores:', scores);
            
            const timestamps = scores.map(d => new Date(d.start_datetime));
            console.log('Processed timestamps:', timestamps);
            
            const fanScores = scores.map(d => d.fan_score);
            const postIncreases = scores.map(d => d.post_increase);
            const views = scores.map(d => d.views);

            const ctx = document.getElementById(containerId).getContext('2d');
            const chartGradient = ctx.createLinearGradient(0, 0, 0, 400);
            chartGradient.addColorStop(0, 'rgba(75, 192, 192, 0.8)');
            chartGradient.addColorStop(0.5, 'rgba(75, 192, 192, 0.2)');
            chartGradient.addColorStop(1, 'rgba(75, 192, 192, 0)');

            const postCountPlugin = {
                id: 'postCount',
                afterDraw: (chart) => {
                    // Only draw if this is the current active chart
                    if (chart !== heroChart) return;
                    
                    const ctx = chart.ctx;
                    chart.data.labels.forEach((value, index) => {
                        const increase = postIncreases[index];
                        
                        if (increase > 0) {
                            const xPos = chart.scales.x.getPixelForValue(value);
                            const yPos = chart.scales.y.getPixelForValue(fanScores[index]);
                            
                            // Draw the white circle background
                            ctx.beginPath();
                            ctx.arc(xPos, yPos, 8, 0, Math.PI * 2);
                            ctx.fillStyle = 'white';
                            ctx.strokeStyle = 'rgb(75, 192, 192)'; // Match line color
                            ctx.lineWidth = 2;
                            ctx.fill();
                            ctx.stroke();
                            
                            // Draw the post increase number
                            ctx.fillStyle = 'black';
                            ctx.font = 'bold 8px Arial';
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(`+${increase}`, xPos, yPos);
                        }
                    });
                }
            };

            // Update current plugin reference and register
            currentPlugin = postCountPlugin;
            Chart.register(postCountPlugin);

            const priorMainScore = data.heroes[heroName].prior_main_score;
            const sevenDayScore = data.heroes[heroName].seven_day_score;

            heroChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timestamps,
                    datasets: [{
                        label: 'Views',
                        data: views,
                        type: 'bar',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderWidth: 0,
                        barThickness: 12,
                        yAxisID: 'y1'
                    },
                    {
                        label: 'Fan Score',
                        data: fanScores,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: chartGradient,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Prior Main Score',
                        data: Array(timestamps.length).fill(priorMainScore),
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        hoverBorderWidth: 0,
                        yAxisID: 'y'
                    },
                    {
                        label: '7-Day Score',
                        data: Array(timestamps.length).fill(sevenDayScore),
                        borderColor: 'rgba(255, 159, 64, 1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        hoverBorderWidth: 0,
                        yAxisID: 'y'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                displayFormats: {
                                    hour: 'HHmm'
                                }
                            },
                            display: true,
                            ticks: {
                                autoSkip: true,
                                maxRotation: 45,
                                minRotation: 45,
                                source: 'data'
                            },
                            distribution: 'linear',
                            bounds: 'data',
                            offset: false
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Fan Score',
                                font: {
                                    weight: 'bold'
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            },
                            min: 0,
                            max: 1000,
                            beginAtZero: true
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Views',
                                font: {
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                display: true,
                                callback: function(value) {
                                    if (value >= 1000000) {
                                        return (value / 1000000).toFixed(1) + 'M';
                                    } else if (value >= 1000) {
                                        return (value / 1000).toFixed(1) + 'K';
                                    }
                                    return value;
                                },
                                count: 6,
                                stepSize: 'auto'
                            },
                            grid: {
                                drawOnChartArea: false
                            },
                            max: function(context) {
                                const maxViews = Math.max(...views);
                                return maxViews * 4;
                            },
                            min: 0,
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    if (context.dataset.label === 'Fan Score') {
                                        return `Score: ${Math.round(context.raw)}`;
                                    }
                                    if (context.dataset.label === 'Views') {
                                        const value = context.raw;
                                        const dataIndex = context.dataIndex;
                                        const posts = scores[dataIndex].posts;
                                        let viewsLabel = '';
                                        if (value >= 1000000) {
                                            viewsLabel = `Views: ${(value / 1000000).toFixed(1)}M`;
                                        } else if (value >= 1000) {
                                            viewsLabel = `Views: ${(value / 1000).toFixed(1)}K`;
                                        } else {
                                            viewsLabel = `Views: ${value}`;
                                        }
                                        return [viewsLabel, `Posts: ${posts}`];
                                    }
                                    return null;
                                }
                            },
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: {
                                size: 13
                            },
                            bodyFont: {
                                size: 12
                            },
                            cornerRadius: 6
                        },
                        legend: {
                            position: 'bottom',
                            align: 'center',
                            padding: {
                                top: 10,
                                bottom: 0
                            },
                            labels: {
                                boxWidth: 12,
                                usePointStyle: true,
                                pointStyle: 'circle'
                            },
                            labels: {
                                generateLabels: function(chart) {
                                    const originalLabels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                                    
                                    // Add custom legend item for post indicators
                                    originalLabels.push({
                                        text: 'Posts Added',
                                        fillStyle: 'white',
                                        strokeStyle: 'rgb(75, 192, 192)',
                                        lineWidth: 2,
                                        hidden: false,
                                        index: originalLabels.length,
                                        pointStyle: 'circle'
                                    });
                                    
                                    return originalLabels;
                                }
                            }
                        }
                    }
                }
            });
        });
} 