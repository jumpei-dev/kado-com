// data-guide用の棒グラフ初期化
let workingExampleChart = null;

// 稼働例の棒グラフを初期化
function initWorkingExampleChart() {
    const ctx = document.getElementById('workingExampleChart');
    if (!ctx) {
        console.error('workingExampleChart canvas element not found');
        return;
    }

    // 既存のチャートがあれば破棄
    if (workingExampleChart) {
        workingExampleChart.destroy();
    }

    // 時間軸での断続的な接客データ（15:00-23:00の30分刻み）
    const timeLabels = [
        '15:00', '15:30', '16:00', '16:30', '17:00', '17:30',
        '18:00', '18:30', '19:00', '19:30', '20:00', '20:30',
        '21:00', '21:30', '22:00', '22:30'
    ];
    
    // 接客状況データ（断続的な接客パターン）
    const workingData = [0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0];
    const waitingData = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1];

    workingExampleChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['稼働時間'],
            datasets: timeLabels.map((time, index) => ({
                label: workingData[index] ? '接客中' : '待機中',
                data: [workingData[index] ? 0.5 : 0.5],
                backgroundColor: workingData[index] ? '#3B82F6' : '#9CA3AF',
                borderWidth: 0,
                stack: 'time',
                categoryPercentage: 1.0,
                barPercentage: 1.0
            }))
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 20,
                    bottom: 20
                }
            },
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        filter: function(legendItem, chartData) {
                            // 重複する凡例を除去
                            const labels = chartData.datasets.map(d => d.label);
                            return labels.indexOf(legendItem.text) === legendItem.datasetIndex;
                        },
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    enabled: false
                }
            },
            scales: {
                x: {
                    stacked: true,
                    beginAtZero: true,
                    max: timeLabels.length * 0.5,
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        stepSize: 1,
                        callback: function(value) {
                            const timeIndex = Math.floor(value * 2);
                            return timeIndex < timeLabels.length ? timeLabels[timeIndex] : '';
                        },
                        color: '#6B7280',
                        font: {
                            size: 10
                        }
                    },
                    title: {
                        display: true,
                        text: '時刻',
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    stacked: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#6B7280',
                        font: {
                            size: 12
                        }
                    },
                    title: {
                        display: false
                    },
                    categoryPercentage: 0.3,
                    barPercentage: 0.8
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeInOutQuart'
            }
        }
    });

    // 稼働率の計算と表示
    displayWorkingRateResult();
}

// 稼働率結果を表示
function displayWorkingRateResult() {
    const resultElement = document.getElementById('workingRateResult');
    if (resultElement) {
        const workingHours = 5; // 接客時間
        const waitingHours = 3; // 待機時間
        const totalHours = workingHours + waitingHours; // 総時間
        const workingRate = ((workingHours / totalHours) * 100).toFixed(1);
        
        resultElement.innerHTML = `
            <div class="bg-blue-50 p-4 rounded-lg text-center">
                <div class="text-2xl font-bold text-blue-800 mb-2">
                    稼働率: ${workingRate}%
                </div>
                <div class="text-sm text-blue-600">
                    接客${workingHours}時間 ÷ 総時間${totalHours}時間 × 100%
                </div>
            </div>
        `;
    }
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    // Chart.jsが読み込まれるまで少し待つ
    setTimeout(() => {
        initWorkingExampleChart();
    }, 100);
});