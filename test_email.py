from app.core.email_service import EmailService
import asyncio

async def test_send_email():
    print("メール送信テスト開始")
    email_service = EmailService()
    
    try:
        # APIキー情報の確認
        print(f"API KEY: {email_service.api_key[:5]}...{email_service.api_key[-5:] if email_service.api_key else 'なし'}")
        print(f"FROM: {email_service.from_email}")
        print(f"MODE: {'開発' if email_service.is_development else '本番'}")
        
        # テストメール送信
        result = await email_service.send_email(
            'test@example.com', 
            'テストメール', 
            '<html><body>これはテストメールです</body></html>'
        )
        
        print(f"送信結果: {'成功' if result else '失敗'}")
    except Exception as e:
        print(f"エラー発生: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_send_email())
