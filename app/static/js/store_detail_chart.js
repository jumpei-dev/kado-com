// グローバル変数でチャートインスタンスを保持
let workingRateChart = null;
let currentPeriod = '7days';
let chartData = null;
let currentStoreId = null;

// 稼働推移の折れ線グラフを初期化する関数
function initWorkingRateChart(storeId, initialData = null) {
    console.log('稼働推移チャート初期化開始:', storeId);
    
    // storeIdを保存
    currentStoreId = storeId;
    
    const ctx = document.getElementById('workingRateChart');
    if (!ctx) {
        console.error('workingRateChart canvas element not found');
        return;
    }
    
    // 既存のチャートがあれば破棄
    if (workingRateChart) {
        workingRateChart.destroy();
    }
    
    if (initialData) {
        console.log('初期データあり:', initialData);
        // 初期データがある場合はそれを使用
        chartData = {
            daily: initialData.labels.map((label, index) => ({
                date: label, // 初期データのラベルをそのまま使用
                rate: initialData.data[index] || null
            })),
            weekly: [] // 週次データは後で実装
        };
        
        renderChart();
    } else {
        console.log('APIからデータ取得');
        // APIからデータを取得
        loadWorkingTrendData(storeId, currentPeriod);
    }
    
    // 期間切り替えボタンのイベントリスナーを設定
    setupPeriodButtons();
}

// APIから稼働推移データを取得する関数
async function loadWorkingTrendData(storeId, period = '7days') {
    try {
        showLoadingState();
        
        const response = await fetch(`/api/stores/${storeId}/working-trend?period=${period}`);
        const data = await response.json();
        
        if (data.success !== false && data.data && data.data.length > 0) {
            // APIレスポンスを内部データ形式に変換
            if (period === '2months') {
                // 2ヶ月データの場合は週次データとして保存
                chartData = {
                    daily: [],
                    weekly: data.labels.map((label, index) => ({
                        startDate: label.split('-')[0],
                        endDate: label.split('-')[1],
                        rate: data.data[index] === 0 ? null : data.data[index]
                    }))
                };
            } else {
                // 7日間データの場合は日次データとして保存
                chartData = {
                    daily: data.labels.map((label, index) => ({
                        date: label, // APIから取得したラベルをそのまま使用
                        rate: data.data[index] === 0 ? null : data.data[index]
                    })),
                    weekly: []
                };
            }
            
            renderChart();
            hideLoadingState();
        } else {
            // データが空の場合
            if (data.data && data.data.length === 0) {
                showErrorState('データがありません');
            } else {
                showErrorState(data.error || data.message || 'データの取得に失敗しました');
            }
        }
    } catch (error) {
        console.error('稼働推移データ取得エラー:', error);
        showErrorState('ネットワークエラーが発生しました');
    }
}

// チャートを描画する関数
function renderChart() {
    const ctx = document.getElementById('workingRateChart');
    if (!ctx) {
        console.error('チャート要素が見つかりません');
        return;
    }

    // 既存のチャートを破棄
    if (workingRateChart) {
        workingRateChart.destroy();
    }

    // 現在の期間に応じたデータを取得
    const periodData = getPeriodData(currentPeriod);
    
    if (!periodData || !periodData.labels || !periodData.data) {
        console.error('チャートデータが不正です:', periodData);
        return;
    }

    const chartCtx = ctx.getContext('2d');
    
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

// 現在の日付から指定されたインデックスの日付を取得（前日まで）
function getCurrentDateForIndex(index) {
    const today = new Date();
    const targetDate = new Date(today);
    // 前日までのデータにするため、今日から1日引いてから計算
    targetDate.setDate(today.getDate() - 1 - (6 - index));
    return targetDate.toISOString().split('T')[0];
}

// 期間に応じたデータを取得する関数
function getPeriodData(period) {
    if (!chartData) {
        console.warn('チャートデータが存在しません');
        return { labels: [], data: [] };
    }
    
    switch (period) {
        case '7days':
            // 日次データを使用
            if (chartData.daily && chartData.daily.length > 0) {
                return {
                    labels: chartData.daily.map(item => formatDate(item.date)),
                    data: chartData.daily.map(item => item.rate)
                };
            }
            break;
            
        case '2months':
            // 週次データを使用
            if (chartData.weekly && chartData.weekly.length > 0) {
                return {
                    labels: chartData.weekly.map(item => formatWeekRange(item.startDate, item.endDate)),
                    data: chartData.weekly.map(item => item.rate)
                };
            } else {
                // 週次データがない場合は日次データから生成
                console.warn('週次データが存在しないため、日次データから生成します');
                if (chartData.daily && chartData.daily.length > 0) {
                    return {
                        labels: chartData.daily.map(item => formatDate(item.date)),
                        data: chartData.daily.map(item => item.rate)
                    };
                }
                return { labels: [], data: [] };
            }
            break;
            
        default:
            console.warn('未対応の期間:', period);
            return { labels: [], data: [] };
    }
    
    // フォールバック
    console.warn('データが見つかりません:', period);
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
    
    // 新しい期間のデータを取得
    if (currentStoreId) {
        await loadWorkingTrendData(currentStoreId, period);
    }
}