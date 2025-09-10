/**
 * Authentication helper functions
 * Global event handlers for auth-related functionality
 */

document.addEventListener('DOMContentLoaded', function() {
  // リスポンス要素の表示を改善するグローバルイベントリスナー
  document.addEventListener('htmx:afterSwap', function(event) {
    // ログインレスポンス要素を検索
    const responseElement = document.getElementById('login-response');
    if (responseElement && responseElement.children.length > 0) {
      console.log('認証レスポンスを検出しました - 表示を確認します');
      
      // レスポンス要素が見えるようにスクロール
      responseElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      
      // レスポンス要素が見えるようにスタイルを調整
      responseElement.style.display = 'block';
      responseElement.style.opacity = '1';
    }
  });

  // 認証成功イベントのグローバルリスナー
  document.addEventListener('auth:login', function(event) {
    console.log('認証成功イベントを受信しました:', event.detail);
    
    // ユーザーメニューの更新やその他の認証後のアクションをここに追加できます
    
    // 例: ユーザー名を表示する要素を更新
    const userNameElements = document.querySelectorAll('.user-name-display');
    if (userNameElements.length > 0 && event.detail.userName) {
      userNameElements.forEach(element => {
        element.textContent = event.detail.userName;
      });
    }
    
    // 認証状態に応じてUIを更新
    const authRequiredElements = document.querySelectorAll('.auth-required');
    const noAuthElements = document.querySelectorAll('.no-auth-required');
    
    if (authRequiredElements.length > 0) {
      authRequiredElements.forEach(element => {
        element.classList.remove('hidden');
      });
    }
    
    if (noAuthElements.length > 0) {
      noAuthElements.forEach(element => {
        element.classList.add('hidden');
      });
    }
  });

  // モーダルを閉じるカスタムイベントのリスナー
  document.addEventListener('modal-close', function(event) {
    if (event.detail && event.detail.id) {
      const modalId = event.detail.id;
      const modalElement = document.getElementById(modalId);
      
      if (modalElement) {
        console.log(`モーダルを閉じます: ${modalId}`);
        
        // Alpine.jsの$dispatchを使用してモーダルを閉じる
        const alpineComponent = modalElement.closest('[x-data]');
        if (alpineComponent) {
          // Alpine.jsのx-dataコンポーネント内の変数を設定
          alpineComponent.__x.$data.open = false;
        } else {
          // フォールバック: クラスを直接操作
          modalElement.classList.add('hidden');
        }
      }
    }
  });
});
