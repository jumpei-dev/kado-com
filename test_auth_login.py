import requests
import json

def test_login():
    """ログイン処理のテスト"""
    print("認証システムのテスト開始")
    
    # ユーザー名とパスワードでログインテスト
    login_data = {
        "username": "admin",  # 管理者ユーザー名
        "password": "admin123"  # 管理者パスワード
    }
    
    try:
        # Content-Type: application/x-www-form-urlencoded として送信
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(
            "http://127.0.0.1:8080/api/auth/login", 
            data=login_data,
            headers=headers
        )
        
        print(f"ステータスコード: {response.status_code}")
        if response.status_code == 200:
            print("HTTP 200 OK 応答を受信しました")
            print("Cookieが設定されているか確認:", "token" in response.cookies)
            
            # レスポンス内容をチェック
            print("レスポンス内容:")
            content = response.text
            print(content[:200] + "..." if len(content) > 200 else content)
            
            # 成功またはエラーメッセージを確認
            if "success" in content and not "error" in content:
                print("✅ ログイン成功！")
            elif "error" in content:
                print("❌ ログイン失敗: フォームでエラーが返されました")
            else:
                print("⚠️ レスポンス内容が不明確です")
        else:
            print("ログイン失敗")
            print(response.text)
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    test_login()
