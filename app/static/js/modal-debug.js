/**
 * モーダルデバッグユーティリティ
 * 認証モーダルの制御に問題がある場合のデバッグ支援
 */

// モーダルデバッグ関数
function debugModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) {
    console.error(`❌ ${modalId} が見つかりません`);
    return;
  }

  console.group(`🔍 モーダル「${modalId}」のデバッグ情報`);
  
  // 表示状態の確認
  console.log('表示状態:', {
    display: window.getComputedStyle(modal).display,
    visibility: window.getComputedStyle(modal).visibility,
    opacity: window.getComputedStyle(modal).opacity,
    zIndex: window.getComputedStyle(modal).zIndex
  });
  
  // Alpine.js状態の確認
  if (modal.__x) {
    console.log('Alpine.js 状態:', {
      show: modal.__x.$data.show,
      authState: modal.__x.$data.authState
    });
  } else {
    console.log('❌ Alpine.js データが見つかりません');
  }
  
  // 強制的に閉じる処理を提供
  console.log('🔄 モーダルを閉じる方法を実行します...');
  
  // 方法1: Alpine.js
  try {
    if (modal.__x) {
      console.log('1️⃣ Alpine.jsでモーダルを閉じる試行');
      modal.__x.$data.show = false;
    }
  } catch (e) {
    console.error('❌ Alpine.js方式失敗:', e);
  }
  
  // 方法2: スタイル直接変更
  try {
    console.log('2️⃣ スタイル直接変更でモーダルを閉じる試行');
    modal.style.display = 'none';
  } catch (e) {
    console.error('❌ スタイル変更方式失敗:', e);
  }
  
  // 方法3: イベント発行
  try {
    console.log('3️⃣ イベント発行でモーダルを閉じる試行');
    document.dispatchEvent(new CustomEvent('modal-close', {
      detail: { id: modalId }
    }));
  } catch (e) {
    console.error('❌ イベント発行方式失敗:', e);
  }
  
  console.log('✅ デバッグ処理完了');
  console.groupEnd();
}

// ページ読み込み時にデバッグボタンを追加
document.addEventListener('DOMContentLoaded', function() {
  // 開発環境でのみデバッグボタンを表示
  const isDevMode = window.location.hostname === 'localhost' || 
                    window.location.hostname === '127.0.0.1' ||
                    window.location.hostname.includes('dev');
  
  if (isDevMode) {
    setTimeout(addModalDebugButton, 1000);
  }
});
