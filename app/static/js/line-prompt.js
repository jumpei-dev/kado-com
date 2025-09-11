// LINE誘導ポップアップの状態管理
let linePromptShown = false;
let lastPromptTime = 0;
let lineConfig = null;

// LINE設定を取得する関数
const fetchLineConfig = async () => {
  try {
    const response = await fetch('/api/config/line');
    if (response.ok) {
      lineConfig = await response.json();
    } else {
      // フォールバック設定
      lineConfig = {
        url: "https://line.me/ti/p/fDpRYZH7C2",
        initial_delay_seconds: 30,
        reoccurrence_interval_minutes: 30
      };
    }
  } catch (error) {
    console.warn('LINE設定の取得に失敗しました:', error);
    // フォールバック設定
    lineConfig = {
      url: "https://line.me/ti/p/fDpRYZH7C2",
      initial_delay_seconds: 30,
      reoccurrence_interval_minutes: 30
    };
  }
};

// ポップアップのHTML要素を作成
const createLinePrompt = () => {
  const promptDiv = document.createElement('div');
  promptDiv.id = 'linePrompt';
  promptDiv.className = 'fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-50';
  const lineUrl = lineConfig ? lineConfig.url : "https://line.me/ti/p/fDpRYZH7C2";
  promptDiv.innerHTML = `
    <div class="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full mx-4 relative">
      <button class="absolute top-4 right-4 text-gray-400 hover:text-gray-600" onclick="hideLinePrompt()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
      <div class="text-center space-y-4">
        <h3 class="text-xl font-bold text-gray-900">店舗名の閲覧には特別なアクセス権限が必要です</h3>
        <p class="text-gray-700">LINEで問い合わせると、より詳細な情報が閲覧できるようになります</p>
        <p class="text-gray-600">下のボタンからLINEの友だちに追加してください</p>
        <div class="mt-6">
          <a href="${lineUrl}" target="_blank" 
             class="inline-block w-full px-6 py-3 bg-green-500 text-white text-lg font-medium rounded-lg hover:bg-green-600 transition-colors text-center">
             LINE公式アカウントを友だち追加
          </a>
        </div>
      </div>
    </div>
  `;
  return promptDiv;
};

// ポップアップを表示する関数
const showLinePrompt = () => {
  if (document.getElementById('linePrompt')) return;
  
  const prompt = createLinePrompt();
  document.body.appendChild(prompt);
  linePromptShown = true;
  lastPromptTime = Date.now();
};

// ポップアップを非表示にする関数
const hideLinePrompt = () => {
  const prompt = document.getElementById('linePrompt');
  if (prompt) {
    prompt.remove();
  }
};

// ポップアップの表示を制御する関数
const handleLinePrompt = async () => {
  // 既にログインしている場合は表示しない
  if (document.cookie.includes('logged_in=true')) return;
  
  // LINE設定を取得
  if (!lineConfig) {
    await fetchLineConfig();
  }
  
  const currentTime = Date.now();
  const timeSinceLastPrompt = currentTime - lastPromptTime;
  
  // 設定から遅延時間と間隔を取得
  const initialDelayMs = (lineConfig?.initial_delay_seconds || 30) * 1000;
  const reoccurrenceIntervalMs = (lineConfig?.reoccurrence_interval_minutes || 30) * 60 * 1000;
  
  // 初回表示（設定された秒数後）
  if (!linePromptShown) {
    setTimeout(showLinePrompt, initialDelayMs);
  }
  // 2回目以降（設定された分数ごと）
  else if (timeSinceLastPrompt >= reoccurrenceIntervalMs) {
    showLinePrompt();
  }
};

// ページ読み込み時にポップアップ制御を開始
document.addEventListener('DOMContentLoaded', handleLinePrompt);