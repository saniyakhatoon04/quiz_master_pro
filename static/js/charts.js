// QuizMaster Pro - Analytics Chart Engine

document.addEventListener('DOMContentLoaded', async () => {
    const container = document.getElementById('analyticsContainer');
    if (!container) return;

    try {
        const res = await fetch('/api/analytics');
        const json = await res.json();
        if (json.success && json.data) {
            renderScoreTrendChart(json.data.history_trend || []);
            renderCategoryMasteryChart(json.data.weak_categories || []);
        }
    } catch (err) {
        console.error('Error loading analytics chart data:', err);
    }
});

function renderScoreTrendChart(historyTrend) {
    const ctx = document.getElementById('scoreTrendChart');
    if (!ctx) return;

    const labels = historyTrend.map((item, idx) => `Quiz #${idx + 1}`);
    const scores = historyTrend.map(item => item.percentage);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.length > 0 ? labels : ['No Data'],
            datasets: [{
                label: 'Score Percentage (%)',
                data: scores.length > 0 ? scores : [0],
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#818cf8',
                pointBorderColor: '#ffffff',
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderWidth: 1,
                    titleColor: '#ffffff',
                    bodyColor: '#cbd5e1',
                    callbacks: {
                        label: (context) => `Score: ${context.parsed.y}%`
                    }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: {
                        color: '#94a3b8',
                        callback: (value) => `${value}%`
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function renderCategoryMasteryChart(weakCategories) {
    const ctx = document.getElementById('categoryMasteryChart');
    if (!ctx) return;

    const labels = weakCategories.map(c => c.category_name);
    const data = weakCategories.map(c => c.accuracy);
    const backgroundColors = weakCategories.map(c => {
        if (c.status === 'Weak') return 'rgba(244, 63, 94, 0.7)'; // Rose
        if (c.status === 'Average') return 'rgba(245, 158, 11, 0.7)'; // Amber
        return 'rgba(16, 185, 129, 0.7)'; // Emerald
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length > 0 ? labels : ['None'],
            datasets: [{
                label: 'Accuracy (%)',
                data: data.length > 0 ? data : [0],
                backgroundColor: backgroundColors.length > 0 ? backgroundColors : ['#6366f1'],
                borderRadius: 8,
                barThickness: 24
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderWidth: 1,
                    titleColor: '#ffffff',
                    bodyColor: '#cbd5e1',
                    callbacks: {
                        label: (context) => `Accuracy: ${context.parsed.y}%`
                    }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: {
                        color: '#94a3b8',
                        callback: (value) => `${value}%`
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 30,
                        minRotation: 0,
                        font: { size: 10 }
                    }
                }
            }
        }
    });
}
