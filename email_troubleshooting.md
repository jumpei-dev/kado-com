# ユーザーガイド: メール送信設定のトラブルシューティング

## 概要
SendGrid APIを使用したメール送信機能のトラブルシューティングガイドです。

## 問題点
現在、SendGrid APIキーで認証エラー（403 Forbidden）が発生しています。

## 解決方法

### 1. SendGridアカウントを確認

1. SendGridの管理コンソールにログインしてください
2. APIキーの状態を確認してください:
   - APIキーが有効であることを確認
   - APIキーに「Mail Send」権限があることを確認

### 2. メール送信ドメインの検証

1. SendGridの管理コンソールで「Sender Authentication」を確認
2. 送信元ドメイン（workingrate.com）が認証済みであることを確認
3. 認証されていない場合はドメイン認証プロセスを完了させる

### 3. 代替案: SMTP経由のメール送信

SendGrid APIが使用できない場合は、SMTPを使用することも検討できます。
設定例:

```python
# SMTPクライアントの設定例
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_smtp(to_email, subject, html_content):
    # SMTPサーバー設定
    smtp_server = "smtp.sendgrid.net"
    smtp_port = 587
    smtp_username = "apikey"
    smtp_password = "YOUR_SENDGRID_API_KEY"  # APIキーをそのまま使用
    
    # メッセージ設定
    message = MIMEMultipart()
    message["From"] = "info@workingrate.com"
    message["To"] = to_email
    message["Subject"] = subject
    
    # HTML本文の設定
    message.attach(MIMEText(html_content, "html"))
    
    # SMTP接続と送信
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(message["From"], to_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP送信エラー: {e}")
        return False
```

### 4. 一時的な対処法

本番環境でメール送信が必要な場合、以下の対処法があります:

- 新しいSendGrid APIキーを作成して設定
- 別のメールサービス（AWS SES、Mailgun、Mailjetなど）を検討
- 緊急用として環境変数で別のAPIキーを指定

## 本番環境向け推奨事項

1. SendGridアカウントを再確認し、APIキーとドメイン認証を完了させる
2. テスト環境で動作確認してから本番環境に適用する
3. メール送信失敗時のフォールバックメカニズムを実装する
