// グローバル変数でチャートインスタンスを保持
let workingRateChart = null;
let currentPeriod = '7days';
let chartData = null;
let currentStoreId = null;

// 稼働推移の折れ線グラフを初期化する関数
function initWorkingRateChart(storeId, initialData = null) {
    currentStoreId = storeId;
    chartData = initialData;
    
    const ctx = document.getElementById('workingRateChart');
    if (!ctx) {
        console.error('workingRateChart canvas element not found');
        return;
    }
    
    // 既存のチャートがあれば破棄
    if (workingRateChart) {
        workingRateChart.destroy();
    }
    
    // 初期データがない場合はAPIから取得
    if (!chartData) {
        loadWorkingTrendData(storeId);
        return;
    }
    
    renderChart();
    setupPeriodButtons();
}

// APIから稼働推移データを取得する関数
async function loadWorkingTrendData(storeId) {
    try {
        showLoadingState();
        
        const response = await fetch(`/api/stores/${storeId}/working-trend`);
        const data = await response.json();
        
        if (data.success !== false) {
            // APIレスポンスを内部データ形式に変換
            chartData = {
                daily: data.labels.map((label, index) => ({
                    date: getCurrentDateForIndex(index),
                    rate: data.data[index] || null
                })),
                weekly: [] // 週次データは後で実装
            };
            
            renderChart();
            hideLoadingState();
        } else {
            showErrorState(data.error || 'データの取得に失敗しました');
        }
    } catch (error) {
        console.error('稼働推移データ取得エラー:', error);
        showErrorState('ネットワークエラーが発生しました');
    }
}

// チャートを描画する関数
function renderChart() {
    const ctx = document.getElementById('workingRateChart').getContext('2d');
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
                pointHoverRadius: 8,
                spanGaps: false
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
}

// ローディング状態を表示
function showLoadingState() {
    const chartContainer = document.getElementById('workingRateChart').parentElement;
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'chart-loading';
    loadingDiv.className = 'absolute inset-0 flex items-center justify-center bg-white bg-opacity-75';
    loadingDiv.innerHTML = '<div class="text-gray-500">データを読み込み中...</div>';
    chartContainer.style.position = 'relative';
    chartContainer.appendChild(loadingDiv);
}

// エラー状態を表示
function showErrorState(message) {
    const chartContainer = document.getElementById('workingRateChart').parentElement;
    hideLoadingState();
    
    const errorDiv = document.createElement('div');
    errorDiv.id = 'chart-error';
    errorDiv.className = 'absolute inset-0 flex items-center justify-center bg-white';
    errorDiv.innerHTML = `<div class="text-red-500 text-center"><div class="mb-2">⚠️</div><div>${message}</div></div>`;
    chartContainer.style.position = 'relative';
    chartContainer.appendChild(errorDiv);
}

// データ情報を表示
function showDataInfo(dataCount, totalDays) {
    hideLoadingState();
    
    const infoElement = document.getElementById('chart-data-info');
    if (infoElement) {
        if (dataCount === 0) {
            infoElement.innerHTML = '<span class="text-gray-500">データがありません（過去7日間）</span>';
        } else if (dataCount < totalDays) {
            infoElement.innerHTML = `<span class="text-yellow-600">データ不足: ${dataCount}/${totalDays}日分のデータ</span>`;
        } else {
            infoElement.innerHTML = `<span class="text-green-600">完全なデータ: ${dataCount}/${totalDays}日分</span>`;
        }
    }
}

// ローディング状態を非表示
function hideLoadingState() {
    const loadingDiv = document.getElementById('chart-loading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
    const errorDiv = document.getElementById('chart-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// 現在の日付から指定されたインデックスの日付を取得
function getCurrentDateForIndex(index) {
    const today = new Date();
    const targetDate = new Date(today);
    targetDate.setDate(today.getDate() - (6 - index));
    return targetDate.toISOString().split('T')[0];
}

// 期間に応じたデータを取得する関数
function getPeriodData(period) {
    if (!chartData) {
        // データがない場合は空のデータを返す
        const emptyLabels = period === '7days' ? 
            ['月', '火', '水', '木', '金', '土', '日'] : 
            ['週1', '週2', '週3', '週4', '週5', '週6', '週7', '週8'];
        return {
            labels: emptyLabels,
            data: new Array(emptyLabels.length).fill(null)
        };
    }
    
    if (period === '7days') {
        // 7日間のデータ（日付表示）
        if (chartData.daily && chartData.daily.length > 0) {
            return {
                labels: chartData.daily.map(item => formatDate(item.date)),
                data: chartData.daily.map(item => item.rate || null)
            };
        } else {
            // データがない場合は曜日ラベルで空データを返す
            return {
                labels: ['月', '火', '水', '木', '金', '土', '日'],
                data: [null, null, null, null, null, null, null]
            };
        }
    } else if (period === '2months') {
        // 2ヶ月のデータ（週単位）
        if (chartData.weekly && chartData.weekly.length > 0) {
            return {
                labels: chartData.weekly.map(item => formatWeekRange(item.week_start, item.week_end)),
                data: chartData.weekly.map(item => item.rate || null)
            };
        } else {
            // データがない場合は週ラベルで空データを返す
            const weekLabels = ['週1', '週2', '週3', '週4', '週5', '週6', '週7', '週8'];
            return {
                labels: weekLabels,
                data: new Array(weekLabels.length).fill(null)
            };
        }
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
async function switchPeriod(period) {
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
    
    // 期間が変わった場合は新しいデータを取得
    if (currentStoreId) {
        await loadWorkingTrendData(currentStoreId);
    } else if (workingRateChart && chartData) {
        // データがある場合はチャートを更新
        const periodData = getPeriodData(period);
        workingRateChart.data.labels = periodData.labels;
        workingRateChart.data.datasets[0].data = periodData.data;
        workingRateChart.update();
    }
}