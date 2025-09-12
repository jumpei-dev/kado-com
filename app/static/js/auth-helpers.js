/**
 * Authentication helper functions
 * Global event handlers for auth-related functionality
 */

// 権限管理用のグローバル変数
window.userPermissions = {
  logged_in: false,
  can_see_contents: false,
  username: null,
  is_admin: false
};

// 権限を確認する関数
async function checkUserPermissions() {
  try {
    const response = await fetch('/api/auth/me');
    if (response.ok) {
      const permissions = await response.json();
      window.userPermissions = permissions;
      
      // 権限変更イベントを発火
      document.dispatchEvent(new CustomEvent('permissions:updated', { 
        detail: permissions 
      }));
      
      return permissions;
    }
  } catch (error) {
    console.error('権限チェックエラー:', error);
  }
  
  // エラー時はデフォルト値を返す
  window.userPermissions = {
    logged_in: false,
    can_see_contents: false,
    username: null,
    is_admin: false
  };
  
  return window.userPermissions;
}

// ページ読み込み時に権限をチェック
document.addEventListener('DOMContentLoaded', async function() {
  await checkUserPermissions();
  
  // 権限に応じてUIを更新
  updateUIBasedOnPermissions(window.userPermissions);
  
  // 権限変更時のUIアップデート
  document.addEventListener('permissions:updated', function(event) {
    updateUIBasedOnPermissions(event.detail);
  });
  
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
      
      // 認証成功の場合は権限を再チェック
      const successElement = responseElement.querySelector('.text-green-700');
      if (successElement) {
        setTimeout(async () => {
          await checkUserPermissions();
        }, 1000);
      }
    }
  });

  // 認証成功イベントのグローバルリスナー
  document.addEventListener('auth:login', async function(event) {
    console.log('認証成功イベントを受信しました:', event.detail);
    
    // 権限を再チェック
    await checkUserPermissions();
    
    // ユーザーメニューの更新やその他の認証後のアクションをここに追加できます
    
    // 例: ユーザー名を表示する要素を更新
    const userNameElements = document.querySelectorAll('.user-name-display');
    if (userNameElements.length > 0 && event.detail.userName) {
      userNameElements.forEach(element => {
        element.textContent = event.detail.userName;
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

// 権限に応じてUIを更新する関数
function updateUIBasedOnPermissions(permissions) {
  console.log('UIを更新中:', permissions);
  
  // 認証が必要な要素の表示制御
  const authRequiredElements = document.querySelectorAll('.auth-required');
  const noAuthElements = document.querySelectorAll('.no-auth-required');
  
  if (permissions.logged_in) {
    authRequiredElements.forEach(element => {
      element.classList.remove('hidden');
    });
    noAuthElements.forEach(element => {
      element.classList.add('hidden');
    });
  } else {
    authRequiredElements.forEach(element => {
      element.classList.add('hidden');
    });
    noAuthElements.forEach(element => {
      element.classList.remove('hidden');
    });
  }
  
  // コンテンツ閲覧権限に応じた表示制御
  const contentRestrictedElements = document.querySelectorAll('.content-restricted');
  const noContentPermissionElements = document.querySelectorAll('.no-content-permission');
  
  if (permissions.can_see_contents) {
    contentRestrictedElements.forEach(element => {
      element.classList.remove('hidden');
    });
    noContentPermissionElements.forEach(element => {
      element.classList.add('hidden');
    });
  } else {
    contentRestrictedElements.forEach(element => {
      element.classList.add('hidden');
    });
    noContentPermissionElements.forEach(element => {
      element.classList.remove('hidden');
    });
  }
  
  // ユーザー名表示の更新
  const userNameElements = document.querySelectorAll('.user-name-display');
  userNameElements.forEach(element => {
    element.textContent = permissions.username || '';
  });
}
