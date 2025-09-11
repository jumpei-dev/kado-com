// LINE誘導ポップアップの状態管理
let linePromptShown = false;
let lastPromptTime = 0;

// ポップアップのHTML要素を作成
const createLinePrompt = () => {
  const promptDiv = document.createElement('div');
  promptDiv.id = 'linePrompt';
  promptDiv.className = 'fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-50';
  promptDiv.innerHTML = `
    <div class="bg-white p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
      <div class="text-center">
        <h3 class="text-lg font-semibold text-gray-700 mb-2">店舗名の閲覧には特別なアクセス権限が必要です</h3>
        <p class="text-gray-600 mb-6">LINEで問い合わせると、より詳細な情報が閲覧できるようになります</p>
        <a href="https://lin.ee/your-line-account" target="_blank" 
           class="inline-flex items-center justify-center px-4 py-2 bg-[#06C755] text-white rounded-md hover:bg-[#05B74C] transition-colors">
          <svg class="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
            <path d="M24 10.3c0-5.4-5.4-9.8-12-9.8S0 4.9 0 10.3c0 4.8 4.3 8.9 10.1 9.6 0.4 0.1 0.9 0.3 1.1 0.5 0.2 0.2 0.1 0.5 0.1 0.7-0.1 0.5-0.5 2.3-0.5 2.6-0.1 0.6 0.3 0.7 0.7 0.4 0.5-0.3 2.6-1.5 3.5-2.2 2.8-1.9 5.5-4.6 5.9-8.2C23.9 12.3 24 11.4 24 10.3z"/>
          </svg>
          LINE公式アカウントで問い合わせる
        </a>
      </div>
      <button class="absolute top-4 right-4 text-gray-400 hover:text-gray-600" onclick="hideLinePrompt()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
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
const handleLinePrompt = () => {
  // 既にログインしている場合は表示しない
  if (document.cookie.includes('logged_in=true')) return;
  
  const currentTime = Date.now();
  const timeSinceLastPrompt = currentTime - lastPromptTime;
  
  // 初回表示（30秒後）
  if (!linePromptShown) {
    setTimeout(showLinePrompt, 30000);
  }
  // 2回目以降（30分ごと）
  else if (timeSinceLastPrompt >= 1800000) { // 30分 = 1800000ミリ秒
    showLinePrompt();
  }
};

// ページ読み込み時にポップアップ制御を開始
document.addEventListener('DOMContentLoaded', handleLinePrompt);