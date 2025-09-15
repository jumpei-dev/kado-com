// LINE誘導ポップアップの状態管理
let linePromptShown = false;
let lineConfig = null;
const LINE_PROMPT_SHOWN_KEY = 'linePromptShown';
const LINE_PROMPT_SESSION_KEY = 'linePromptSession';

// セッション管理：ブラウザセッション毎にフラグをリセット
const initializePromptSession = () => {
  const currentSession = sessionStorage.getItem(LINE_PROMPT_SESSION_KEY);
  const sessionId = Date.now().toString();
  
  if (!currentSession) {
    // 新しいセッション開始時にLocalStorageフラグをリセット
    console.log('新しいセッション開始：ポップアップフラグをリセットします');
    localStorage.removeItem(LINE_PROMPT_SHOWN_KEY);
    sessionStorage.setItem(LINE_PROMPT_SESSION_KEY, sessionId);
  }
};

// ページ読み込み時にセッション初期化
initializePromptSession();

// LocalStorageから表示済みフラグを確認
const hasShownPrompt = () => {
  const hasShown = localStorage.getItem(LINE_PROMPT_SHOWN_KEY) === 'true';
  console.log('ポップアップ表示済みフラグ:', hasShown);
  console.log('LocalStorage全体:', localStorage);
  return hasShown;
};

// LocalStorageに表示済みフラグを保存
const markPromptAsShown = () => {
  localStorage.setItem(LINE_PROMPT_SHOWN_KEY, 'true');
  console.log('ポップアップ表示済みフラグを設定しました');
};

// デバッグ用：表示済みフラグをクリア
const clearPromptFlag = () => {
  localStorage.removeItem(LINE_PROMPT_SHOWN_KEY);
  sessionStorage.removeItem(LINE_PROMPT_SESSION_KEY);
  console.log('ポップアップ表示済みフラグとセッション情報をクリアしました');
};

// 強制的にフラグをリセットする関数
const resetPromptFlag = () => {
  localStorage.setItem(LINE_PROMPT_SHOWN_KEY, 'false');
  sessionStorage.removeItem(LINE_PROMPT_SESSION_KEY);
  console.log('ポップアップフラグを強制的にfalseにリセットしました');
};

// デバッグ用：グローバル関数として公開
window.clearLinePromptFlag = clearPromptFlag;
window.resetLinePromptFlag = resetPromptFlag;
window.showLinePromptNow = () => {
  console.log('強制的にポップアップを表示します');
  showLinePrompt();
};

// LINE設定を取得する関数
const fetchLineConfig = async () => {
  console.log('LINE設定の取得を開始します');
  try {
    const response = await fetch('/api/config/line');
    console.log('API応答ステータス:', response.status);
    
    if (response.ok) {
      lineConfig = await response.json();
      console.log('LINE設定をAPIから取得しました:', lineConfig);
    } else {
      console.warn('API応答が正常ではありません。フォールバック設定を使用します');
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
    console.log('フォールバック設定を使用します:', lineConfig);
  }
};

// ポップアップのHTML要素を作成
const createLinePrompt = () => {
  const promptDiv = document.createElement('div');
  promptDiv.id = 'linePrompt';
  promptDiv.className = 'fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-50';
  const lineUrl = lineConfig ? lineConfig.url : "https://line.me/ti/p/fDpRYZH7C2";
  promptDiv.innerHTML = `
    <div class="bg-white p-8 pr-12 rounded-2xl shadow-xl max-w-md w-full mx-4 relative">
      <button class="absolute top-4 right-4 text-gray-400 hover:text-gray-600" onclick="hideLinePrompt()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
      <div class="text-center space-y-4">
        <h3 class="text-lg font-bold text-gray-900" style="font-size: 1rem !important; line-height: 1.4; word-break: keep-all; overflow-wrap: break-word;">店舗名を閲覧するためには<br>ログインが必要です</h3>
        <p class="text-sm text-gray-700">アカウントの発行については下のボタンから<br>LINEにてお問い合わせください</p>
        <div class="mt-6">
          <a href="${lineUrl}" target="_blank" 
             class="inline-block w-full px-6 py-3 bg-green-500 text-white text-base font-medium rounded-lg hover:bg-green-600 transition-colors text-center">
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
  console.log('ポップアップ表示関数が呼び出されました');
  
  if (document.getElementById('linePrompt')) {
    console.log('ポップアップは既に表示されています');
    return;
  }
  
  console.log('ポップアップを作成して表示します');
  const prompt = createLinePrompt();
  document.body.appendChild(prompt);
  linePromptShown = true;
  markPromptAsShown(); // LocalStorageに記録
  console.log('ポップアップが正常に表示されました');
};

// ポップアップを非表示にする関数
const hideLinePrompt = () => {
  const prompt = document.getElementById('linePrompt');
  if (prompt) {
    prompt.remove();
  }
};

// クッキーから認証状態を確認する関数
const isUserLoggedIn = () => {
  const cookies = document.cookie;
  console.log('現在のクッキー:', cookies);
  
  // access_tokenまたはtokenクッキーの存在を確認
  const hasAccessToken = cookies.includes('access_token=');
  const hasToken = cookies.includes('token=');
  const isLoggedIn = hasAccessToken || hasToken;
  
  console.log('ログイン状態:', isLoggedIn, '(access_token:', hasAccessToken, ', token:', hasToken, ')');
  return isLoggedIn;
};

// ポップアップの表示を制御する関数
const handleLinePrompt = async () => {
  console.log('=== LINE ポップアップ制御開始 ===');
  console.log('現在のURL:', window.location.href);
  console.log('現在の時刻:', new Date().toLocaleString());
  
  // 既にログインしている場合は表示しない
  const loginStatus = isUserLoggedIn();
  console.log('ログイン状態チェック結果:', loginStatus);
  if (loginStatus) {
    console.log('ユーザーがログイン済みのため、ポップアップを表示しません');
    return;
  }
  
  // 既に表示済みの場合は表示しない
  const hasShown = hasShownPrompt();
  console.log('表示済みフラグチェック結果:', hasShown);
  if (hasShown) {
    console.log('ポップアップは既に表示済みです');
    console.log('デバッグ用：window.clearLinePromptFlag() でフラグをクリア、window.resetLinePromptFlag() で強制リセットできます');
    return;
  }
  
  // LINE設定を取得
  if (!lineConfig) {
    console.log('LINE設定を取得中...');
    await fetchLineConfig();
    console.log('LINE設定取得完了:', lineConfig);
  }
  
  // 1分後に1回だけ表示
  const delayMs = 60 * 1000; // 1分 = 60秒
  console.log(`${delayMs/1000}秒後にポップアップを表示します`);
  console.log('デバッグ用：window.showLinePromptNow() で即座に表示できます');
  setTimeout(() => {
    console.log('=== タイマー実行：ポップアップを表示します ===');
    showLinePrompt();
  }, delayMs);
  
  console.log('=== handleLinePrompt 処理完了 ===');
};

// ページ読み込み時にポップアップ制御を開始
document.addEventListener('DOMContentLoaded', handleLinePrompt);