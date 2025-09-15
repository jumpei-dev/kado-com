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
        })
        .catch(error => {
            console.error('❌ 統合API呼び出しエラー:', error);
            showErrorState('ネットワークエラーが発生しました');
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
    
    // APIから返されたデータをそのまま使用
    const labels = apiData.labels || [];
    const data = apiData.data || [];
    
    console.log('📊 グラフデータ:', { labels, data });
    
    // データが空の場合の処理
    if (labels.length === 0 || data.length === 0) {
        console.warn('⚠️ グラフデータが空です');
        showErrorState('表示するデータがありません');
        return;
    }
    
    // Chart.jsの設定
    const config = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '稼働率 (%)',
                data: data,
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
            console.log('📊 フィルター変更検出、チャートデータを確認中...');
            
            // 埋め込まれたチャートデータを確認
            const chartDataScript = event.target.querySelector('script[data-chart-data]');
            if (chartDataScript) {
                try {
                    const chartData = JSON.parse(chartDataScript.textContent);
                    console.log('📊 埋め込みチャートデータ発見:', chartData);
                    
                    if (chartData.success) {
                        renderOverallChart(chartData);
                    } else {
                        console.error('❌ 埋め込みチャートデータエラー:', chartData.error);
                        showErrorState(chartData.error || 'データの取得に失敗しました');
                    }
                } catch (e) {
                    console.error('❌ チャートデータ解析エラー:', e);
                    // フォールバック: 通常の初期化
                    setTimeout(() => {
                        initOverallChart();
                    }, 100);
                }
            } else {
                console.log('📊 埋め込みチャートデータなし、通常初期化');
                setTimeout(() => {
                    initOverallChart();
                }, 100);
            }
        } else {
            // 通常のページング等の場合は従来通り
            setTimeout(() => {
                initOverallChart();
            }, 100);
        }
    }
});