/**
 * HTMX デバッグ用の検証スクリプト
 * ページ読み込み時にHTMXの設定を確認
 */

document.addEventListener('DOMContentLoaded', function() {
  console.log('=== HTMX 設定確認 ===');
  console.log('HTMXライブラリ利用可能:', typeof htmx !== 'undefined');
  
  if (typeof htmx !== 'undefined') {
    console.log('HTMX バージョン:', htmx.version ? htmx.version : '不明');
    console.log('HTMX 設定:', htmx.config ? '設定済み' : '未設定');
    
    // HTMX イベントリスナーの設定
    document.body.addEventListener('htmx:configRequest', function(event) {
      console.log('HTMX リクエスト設定:', event.detail);
    });
    
    document.body.addEventListener('htmx:beforeRequest', function(event) {
      console.log('HTMX リクエスト送信前:', event.detail.elt.id);
    });
    
    document.body.addEventListener('htmx:afterRequest', function(event) {
      console.log('HTMX リクエスト完了:', event.detail.elt.id, event.detail.successful ? '成功' : '失敗');
    });
    
    document.body.addEventListener('htmx:responseError', function(event) {
      console.error('HTMX レスポンスエラー:', event.detail);
    });
  }
  
  // ログインフォームの存在確認
  const loginForm = document.getElementById('login-form');
  console.log('ログインフォーム存在:', !!loginForm);
  
  if (loginForm) {
    console.log('ログインフォーム属性:');
    console.log('- action:', loginForm.getAttribute('action') || 'なし');
    console.log('- method:', loginForm.getAttribute('method') || 'なし');
    console.log('- hx-post:', loginForm.getAttribute('hx-post') || 'なし');
    console.log('- hx-target:', loginForm.getAttribute('hx-target') || 'なし');
    console.log('- hx-trigger:', loginForm.getAttribute('hx-trigger') || 'なし (デフォルト)');
    
    // 送信ボタンの確認
    const submitButton = loginForm.querySelector('button[type="submit"]');
    console.log('送信ボタン存在:', !!submitButton);
    
    // レスポンス表示領域の確認
    const responseArea = document.getElementById('login-response');
    console.log('レスポンスエリア存在:', !!responseArea);
  }
});

// 認証モーダルのデバッグ
document.addEventListener('htmx:afterSwap', function(event) {
  const targetId = event.detail.target.id;
  console.log('HTMX コンテンツスワップ:', targetId);
  
  if (targetId === 'login-response') {
    console.log('ログインレスポンス更新:', event.detail.target.innerHTML.substring(0, 50) + '...');
  }
});

// エラーハンドリング強化
window.addEventListener('error', function(event) {
  console.error('グローバルエラー:', event.message, 'at', event.filename, ':', event.lineno);
});
