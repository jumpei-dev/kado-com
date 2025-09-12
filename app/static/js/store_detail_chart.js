// グローバル変数でチャートインスタンスを保持
let workingRateChart = null;
let currentPeriod = '7days';
let chartData = null;

// 稼働推移の折れ線グラフを初期化する関数
function initWorkingRateChart(data) {
    chartData = data;
    const ctx = document.getElementById('workingRateChart').getContext('2d');
    
    // 既存のチャートがあれば破棄
    if (workingRateChart) {
        workingRateChart.destroy();
    }
    
    const periodData = getPeriodData(currentPeriod);
    
    workingRateChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: periodData.labels,
            datasets: [{
                label: '稼働率 (%)',
                data: periodData.data,
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#3B82F6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#3B82F6',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        },
                        color: '#6B7280'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#6B7280'
                    }
                }
            },
            elements: {
                point: {
                    hoverBackgroundColor: '#1D4ED8'
                }
            }
        }
    });
    
    // 期間選択ボタンのイベントリスナーを設定
    setupPeriodButtons();
}

// 期間に応じたデータを取得する関数
function getPeriodData(period) {
    if (!chartData) return { labels: [], data: [] };
    
    if (period === '7days') {
        // 7日間のデータ（日付表示）
        return {
            labels: chartData.daily ? chartData.daily.map(item => formatDate(item.date)) : [],
            data: chartData.daily ? chartData.daily.map(item => item.rate) : []
        };
    } else if (period === '2months') {
        // 2ヶ月のデータ（週単位）
        return {
            labels: chartData.weekly ? chartData.weekly.map(item => formatWeekRange(item.week_start, item.week_end)) : [],
            data: chartData.weekly ? chartData.weekly.map(item => item.rate) : []
        };
    }
    
    return { labels: [], data: [] };
}

// 日付をフォーマットする関数（MM/DD形式）
function formatDate(dateString) {
    const date = new Date(dateString);
    return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
}

// 週の範囲をフォーマットする関数
function formatWeekRange(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    return `${formatDate(startDate)}-${formatDate(endDate)}`;
}

// 期間選択ボタンのイベントリスナーを設定
function setupPeriodButtons() {
    const button7days = document.getElementById('period-7days');
    const button2months = document.getElementById('period-2months');
    
    if (button7days && button2months) {
        button7days.addEventListener('click', () => switchPeriod('7days'));
        button2months.addEventListener('click', () => switchPeriod('2months'));
    }
}

// 期間を切り替える関数
function switchPeriod(period) {
    currentPeriod = period;
    
    // ボタンのスタイルを更新
    const button7days = document.getElementById('period-7days');
    const button2months = document.getElementById('period-2months');
    
    if (period === '7days') {
        button7days.className = 'px-3 py-1 text-sm font-medium rounded-md bg-white text-gray-900 shadow-sm transition-colors';
        button2months.className = 'px-3 py-1 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 transition-colors';
    } else {
        button7days.className = 'px-3 py-1 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 transition-colors';
        button2months.className = 'px-3 py-1 text-sm font-medium rounded-md bg-white text-gray-900 shadow-sm transition-colors';
    }
    
    // チャートを更新
    if (workingRateChart && chartData) {
        const periodData = getPeriodData(period);
        workingRateChart.data.labels = periodData.labels;
        workingRateChart.data.datasets[0].data = periodData.data;
        workingRateChart.update();
    }
}