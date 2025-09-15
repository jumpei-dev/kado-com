// 一覧画面用の全体稼働推移グラフ
let overallChart = null;
let currentPeriod = '7days';
let currentFilters = {
    area: 'all',
    genre: 'all'
};
let isInitializing = false;

// グラフ初期化
function initOverallChart() {
    if (isInitializing) {
        console.log('⏳ 全体稼働推移グラフ初期化中のため、スキップ');
        return;
    }
    
    isInitializing = true;
    console.log('📊 全体稼働推移グラフを初期化中...');
    
    // 初期フィルター値を取得
    updateFiltersFromUI();
    
    // グラフを読み込み
    loadOverallChart();
}

// UIからフィルター値を更新
function updateFiltersFromUI() {
    // フィルターフォームから現在の値を取得
    const areaSelect = document.querySelector('select[name="area"]');
    const genreSelect = document.querySelector('select[name="genre"]');
    
    if (areaSelect) {
        currentFilters.area = areaSelect.value || 'all';
    }
    if (genreSelect) {
        currentFilters.genre = genreSelect.value || 'all';
    }
    
    console.log('🔍 現在のフィルター:', currentFilters);
}

// 期間切り替え
function switchPeriod(period) {
    console.log(`📅 期間切り替え: ${period}`);
    currentPeriod = period;
    
    // ボタンのスタイルを更新
    document.querySelectorAll('[id^="overall-period-"]').forEach(btn => {
        btn.className = 'px-3 py-1 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 transition-colors';
    });
    
    const activeBtn = document.getElementById(`overall-period-${period}`);
    if (activeBtn) {
        activeBtn.className = 'px-3 py-1 text-sm font-medium rounded-md bg-white text-gray-900 shadow-sm transition-colors';
    }
    
    // グラフを再読み込み
    loadOverallChart();
}

// 全体稼働推移データを読み込み
function loadOverallChart() {
    console.log('📊 全体稼働推移データを読み込み中...');
    
    // フィルター値を更新
    updateFiltersFromUI();
    
    // ローディング状態を表示
    showLoadingState();
    
    // 統合されたAPIエンドポイントを構築
    const params = new URLSearchParams({
        chart_period: currentPeriod,
        area: currentFilters.area,
        genre: currentFilters.genre,
        include_chart_data: 'true',
        page: '1',
        page_size: '1'  // チャートデータのみ必要なので最小限
    });
    
    const url = `/api/stores?${params.toString()}`;
    console.log('🌐 統合API URL:', url);
    
    fetch(url, {
        headers: {
            'Accept': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📊 統合API全体レスポンス:', data);
            
            // chart_dataプロパティからチャートデータを取得
            if (data.chart_data) {
                console.log('📊 全体稼働推移データ受信:', data.chart_data);
                
                if (data.chart_data.success !== false) {
                    renderOverallChart(data.chart_data);
                } else {
                    console.error('❌ APIエラー:', data.chart_data.error);
                    showErrorState(data.chart_data.error || 'データの取得に失敗しました');
                }
            } else {
                console.error('❌ chart_dataが見つかりません');
                showErrorState('チャートデータの取得に失敗しました');
            }
            
            // 初期化フラグをリセット
            isInitializing = false;
        })
        .catch(error => {
            console.error('❌ 統合API呼び出しエラー:', error);
            showErrorState('ネットワークエラーが発生しました');
            
            // 初期化フラグをリセット
            isInitializing = false;
        });
}



// グラフを描画
function renderOverallChart(apiData) {
    console.log('🎨 全体稼働推移グラフを描画中...', apiData);
    
    const canvas = document.getElementById('overallChart');
    if (!canvas) {
        console.error('❌ キャンバス要素が見つかりません');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // 既存のグラフを破棄
    if (overallChart) {
        overallChart.destroy();
    }
    
    // 期間に応じて固定のx軸ラベルを生成
    let fixedLabels = [];
    let chartData = [];
    
    if (currentPeriod === '7days') {
        // 7日間の固定ラベルを生成
        const today = new Date();
        for (let i = 6; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(today.getDate() - i);
            const label = `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
            fixedLabels.push(label);
            
            // APIデータから対応する値を探す
            const dateStr = date.toISOString().split('T')[0];
            const apiIndex = (apiData.labels || []).findIndex(l => {
                // APIのラベルがMM/DD形式の場合とYYYY-MM-DD形式の場合に対応
                return l === label || l.startsWith(dateStr) || l === dateStr;
            });
            chartData.push(apiIndex >= 0 ? (apiData.data || [])[apiIndex] : null);
        }
    } else if (currentPeriod === '2months') {
        // 8週間の固定ラベルを生成
        const today = new Date();
        for (let i = 7; i >= 0; i--) {
            const startDate = new Date(today);
            startDate.setDate(today.getDate() - (i * 7) - (today.getDay() || 7) + 1); // 週の始まり（月曜日）
            const endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 6); // 週の終わり（日曜日）
            
            const formatDate = (date) => `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
            const label = `${formatDate(startDate)}-${formatDate(endDate)}`;
            fixedLabels.push(label);
            
            // APIデータから対応する値を探す（週の開始日で検索）
            const weekStartStr = startDate.toISOString().split('T')[0];
            const apiIndex = (apiData.labels || []).findIndex(l => {
                return l === label || l.startsWith(weekStartStr);
            });
            chartData.push(apiIndex >= 0 ? (apiData.data || [])[apiIndex] : null);
        }
    }
    
    console.log('📊 固定ラベル:', fixedLabels);
    console.log('📊 マッピングされたデータ:', chartData);
    
    // データが全て空の場合の処理
    if (chartData.every(d => d === null)) {
        console.warn('⚠️ グラフデータが空です');
        showErrorState('表示するデータがありません');
        return;
    }
    
    // Chart.jsの設定
    const config = {
        type: 'line',
        data: {
            labels: fixedLabels,
            datasets: [{
                label: '稼働率 (%)',
                data: chartData,
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
                title: {
                    display: false
                },
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
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    };
    
    // グラフを作成
    overallChart = new Chart(ctx, config);
    
    // データ情報を更新
    updateDataInfo(apiData);
    
    // ローディング状態を非表示
    hideLoadingState();
    
    // 初期化フラグをリセット
    isInitializing = false;
    
    console.log('✅ 全体稼働推移グラフの描画完了');
}

// データ情報を更新
function updateDataInfo(apiData) {
    const infoElement = document.getElementById('overall-chart-data-info');
    if (!infoElement) return;
    
    // データ情報表示を空にする
    infoElement.innerHTML = '';
}

// ローディング状態を表示
function showLoadingState() {
    const loading = document.getElementById('chart-loading');
    const error = document.getElementById('chart-error');
    
    if (loading) loading.classList.remove('hidden');
    if (error) error.classList.add('hidden');
}

// ローディング状態を非表示
function hideLoadingState() {
    const loading = document.getElementById('chart-loading');
    if (loading) loading.classList.add('hidden');
}

// エラー状態を表示
function showErrorState(message = 'データの読み込みに失敗しました') {
    const loading = document.getElementById('chart-loading');
    const error = document.getElementById('chart-error');
    
    if (loading) loading.classList.add('hidden');
    if (error) {
        error.classList.remove('hidden');
        const errorText = error.querySelector('p');
        if (errorText) {
            errorText.textContent = message;
        }
    }
    
    // 初期化フラグをリセット
    isInitializing = false;
}

// フィルター変更時にグラフを更新
function updateOverallChart() {
    console.log('🔄 フィルター変更によるグラフ更新');
    loadOverallChart();
}

// DOMContentLoaded時に初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 全体稼働推移グラフの初期化開始');
    
    // Chart.jsが読み込まれているかチェック
    if (typeof Chart === 'undefined') {
        console.error('❌ Chart.jsが読み込まれていません');
        showErrorState('グラフライブラリの読み込みに失敗しました');
        return;
    }
    
    // 少し遅延してから初期化（他の要素の読み込み完了を待つ）
    setTimeout(() => {
        initOverallChart();
        
        // 期間切り替えボタンのイベントリスナーを追加
        const period7daysBtn = document.getElementById('overall-period-7days');
        const period2monthsBtn = document.getElementById('overall-period-2months');
        
        if (period7daysBtn) {
            period7daysBtn.addEventListener('click', () => {
                switchPeriod('7days');
                loadOverallChart();
            });
        }
        
        if (period2monthsBtn) {
            period2monthsBtn.addEventListener('click', () => {
                switchPeriod('2months');
                loadOverallChart();
            });
        }
    }, 500);
});

// HTMXイベントリスナー（フィルター変更時）
document.addEventListener('htmx:afterSwap', function(event) {
    // 店舗一覧が更新された後にグラフを再初期化
    if (event.target.id === 'store-list') {
        console.log('🔄 店舗一覧更新後、全体稼働推移グラフを再初期化');
        
        // フィルター変更による更新かチェック
        const triggerElement = event.detail.elt;
        const isFilterChange = triggerElement && triggerElement.hasAttribute('data-filter-change');
        
        if (isFilterChange) {
            console.log('📊 フィルター変更検出、チャートを更新');
            // フィルター変更時は直接loadOverallChartを呼び出し
            setTimeout(() => {
                updateFiltersFromUI();
                loadOverallChart();
            }, 100);
        } else {
            // 通常のページング等の場合は初期化をスキップ
            console.log('📊 ページング更新のため、グラフ初期化をスキップ');
        }
    }
});