"""
SendGridを使用したメール送信サービス
開発環境とSMTP対応両方に対応
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from typing import Optional, Dict, Any
from fastapi import BackgroundTasks
from datetime import datetime
from pathlib import Path
import sys
import traceback

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

try:
    from app.core.config import config_manager
except ImportError:
    config_manager = None

logger = logging.getLogger(__name__)

class EmailService:
    """SendGridを使用したメール送信サービス（SMTP対応）"""
    
    def __init__(self):
        # 設定ファイルから読み込み
        if config_manager:
            email_config = config_manager.get_email_config()
            self.api_key = email_config.get('api_key')
            self.from_email = email_config.get('from_email', "noreply@kadocom.com")
            self.from_name = email_config.get('from_name', "稼働.com")
            self.provider = email_config.get('provider', 'sendgrid')
            self.is_development = config_manager.get('environment.mode', 'development') == 'development'
            
            # SMTP設定
            self.smtp_server = email_config.get('smtp_server', 'smtp.sendgrid.net')
            self.smtp_port = int(email_config.get('smtp_port', 587))
            self.smtp_username = email_config.get('smtp_username', 'apikey')
            self.smtp_password = email_config.get('smtp_password', self.api_key)
            
            print(f"EmailService初期化: 設定ファイルから読み込み (Provider: {self.provider})")
        else:
            # フォールバック：環境変数から読み込み
            self.api_key = os.getenv("SENDGRID_API_KEY")
            self.from_email = os.getenv("EMAIL_FROM", "noreply@kadocom.com")
            self.from_name = os.getenv("EMAIL_FROM_NAME", "稼働.com")
            self.provider = os.getenv("EMAIL_PROVIDER", "sendgrid")
            self.is_development = os.getenv("ENVIRONMENT", "development") == "development"
            
            # SMTP設定
            self.smtp_server = os.getenv("SMTP_SERVER", "smtp.sendgrid.net")
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
            self.smtp_username = os.getenv("SMTP_USERNAME", "apikey")
            self.smtp_password = os.getenv("SMTP_PASSWORD", self.api_key)
            
            print(f"EmailService初期化: 環境変数から読み込み (Provider: {self.provider})")
    
    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """メールを送信する"""
        # 開発環境でも送信テスト用（通常コメントアウト）
        force_send = False  # ここを True にすると開発環境でも実際に送信します
        
        # 開発環境では実際には送信せず、コンソールに出力
        if self.is_development and not force_send:
            print(f"\n\n")
            print(f"====================================================")
            print(f"=== 開発モード: メール送信 ===")
            print(f"====================================================")
            print(f"宛先: {to_email}")
            print(f"件名: {subject}")
            print(f"内容: {html_content[:300]}...")  # 長すぎるので一部だけ表示
            print(f"====================================================")
            print(f"(開発モードのため、実際のメール送信はスキップされました)")
            print(f"====================================================")
            print(f"\n\n")
            return True
        
        # 本番環境では実際に送信
        try:
            # プロバイダに応じた送信方法を使用
            if self.provider == 'smtp':
                return await self._send_via_smtp(to_email, subject, html_content)
            else:  # デフォルトはSendGrid API
                return await self._send_via_sendgrid(to_email, subject, html_content)
                
        except Exception as e:
            logger.error(f"メール送信例外: {str(e)}")
            print(f"メール送信エラー: {type(e).__name__}: {str(e)}")
            # スタックトレースも出力
            print(traceback.format_exc())
            return False
    
    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> bool:
        """SendGrid APIを使用してメールを送信"""
        # APIキーチェック
        if not self.api_key:
            logger.error("SendGrid API キーが設定されていません")
            print("ERROR: SendGrid API キーが設定されていません")
            return False
            
        message = Mail(
            from_email=Email(self.from_email, self.from_name),
            to_emails=To(to_email),
            subject=subject,
            html_content=HtmlContent(html_content)
        )
        
        sg = SendGridAPIClient(self.api_key)
        print(f"SendGrid API接続を開始します: API_KEY={self.api_key[:5]}...")
        response = sg.send(message)
        status_code = response.status_code
        
        if status_code >= 200 and status_code < 300:
            logger.info(f"メール送信成功: {to_email}, ステータス: {status_code}")
            print(f"メール送信成功: {to_email}, ステータス: {status_code}")
            return True
        else:
            logger.error(f"メール送信エラー: ステータス {status_code}")
            print(f"メール送信エラー: ステータス {status_code}")
            return False
    
    async def _send_via_smtp(self, to_email: str, subject: str, html_content: str) -> bool:
        """SMTPを使用してメールを送信"""
        try:
            # メッセージ作成
            message = MIMEMultipart()
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # HTML本文の設定
            message.attach(MIMEText(html_content, "html"))
            
            # SMTP接続と送信
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.from_email, to_email, message.as_string())
            server.quit()
            
            logger.info(f"SMTP メール送信成功: {to_email}")
            print(f"SMTP メール送信成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP メール送信エラー: {str(e)}")
            print(f"SMTP メール送信エラー: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            return False
    
    async def send_verification_email(self, to_email: str, user_name: str, verification_url: str) -> bool:
        """メール確認用のメールを送信"""
        subject = "【稼働.com】重要: メールアドレスの確認をお願いします"
        html_content = f"""
        <html>
        <body style="font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 20px; border: 1px solid #e9ecef;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #343a40; margin-bottom: 5px;">メールアドレスの確認</h2>
                    <p style="color: #6c757d; font-size: 14px; margin-top: 0;">稼働.com</p>
                </div>
                
                <p>こんにちは、<strong>{user_name}</strong> さん</p>
                
                <p>稼働.comへのご登録ありがとうございます。<strong>サービスを利用するには、メールアドレスの確認が必要です</strong>。</p>
                
                <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; color: #856404;"><strong>重要:</strong> メールアドレスを確認しないと、サービスの一部機能が制限されます。以下のボタンをクリックして確認を完了してください。</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #4a5568; color: white; padding: 12px 24px; text-decoration: none; 
                              border-radius: 5px; font-weight: bold; display: inline-block;">
                        メールアドレスを確認する
                    </a>
                </div>
                
                <p><strong>確認後は自動的にログインされ</strong>、すべての機能がご利用いただけるようになります。</p>
                
                <p>このリンクの有効期限は24時間です。期限が切れた場合は、再度登録手続きを行ってください。</p>
                
                <p>もし心当たりがない場合は、このメールを無視していただいて構いません。</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e9ecef; font-size: 12px; color: #6c757d;">
                    <p>このメールは自動送信されています。返信はできませんのでご了承ください。</p>
                    <p>&copy; 2025 稼働.com All Rights Reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_password_reset_email(self, to_email: str, user_name: str, reset_url: str) -> bool:
        """パスワードリセット用のメールを送信"""
        subject = "【稼働.com】パスワードのリセット"
        html_content = f"""
        <html>
        <body style="font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 20px; border: 1px solid #e9ecef;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #343a40; margin-bottom: 5px;">パスワードのリセット</h2>
                    <p style="color: #6c757d; font-size: 14px; margin-top: 0;">稼働.com</p>
                </div>
                
                <p>こんにちは、<strong>{user_name}</strong> さん</p>
                
                <p>パスワードリセットのリクエストを受け付けました。以下のボタンをクリックして、新しいパスワードを設定してください。</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #4a5568; color: white; padding: 12px 24px; text-decoration: none; 
                              border-radius: 5px; font-weight: bold; display: inline-block;">
                        パスワードをリセットする
                    </a>
                </div>
                
                <p>このリンクの有効期限は1時間です。期限が切れた場合は、再度リセット手続きを行ってください。</p>
                
                <p>もしパスワードリセットをリクエストしていない場合は、このメールを無視してください。アカウントのセキュリティは保たれています。</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e9ecef; font-size: 12px; color: #6c757d;">
                    <p>このメールは自動送信されています。返信はできませんのでご了承ください。</p>
                    <p>&copy; 2025 稼働.com All Rights Reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)


# バックグラウンドタスクヘルパー関数
def send_email_background(background_tasks: BackgroundTasks, to_email: str, subject: str, html_content: str):
    """バックグラウンドでメールを送信"""
    email_service = EmailService()
    background_tasks.add_task(email_service.send_email, to_email, subject, html_content)

def send_verification_email_background(background_tasks: BackgroundTasks, to_email: str, user_name: str, verification_url: str):
    """バックグラウンドでメール確認メールを送信"""
    email_service = EmailService()
    background_tasks.add_task(email_service.send_verification_email, to_email, user_name, verification_url)

def send_password_reset_email_background(background_tasks: BackgroundTasks, to_email: str, user_name: str, reset_url: str):
    """バックグラウンドでパスワードリセットメールを送信"""
    email_service = EmailService()
    background_tasks.add_task(email_service.send_password_reset_email, to_email, user_name, reset_url)
