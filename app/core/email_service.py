"""
SendGridを使用したメール送信サービス
"""

import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from typing import Optional
from fastapi import BackgroundTasks
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """SendGridを使用したメール送信サービス"""
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "noreply@kadocom.com")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "稼働.com")
        self.is_development = os.getenv("ENVIRONMENT", "development") == "development"
    
    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """メールを送信する"""
        # 開発環境では実際には送信せず、コンソールに出力
        if self.is_development:
            logger.info(f"\n=== 開発モード: メール送信 ===")
            logger.info(f"宛先: {to_email}")
            logger.info(f"件名: {subject}")
            logger.info(f"内容: {html_content}")
            logger.info("===========================\n")
            return True
        
        # 本番環境では実際に送信
        message = Mail(
            from_email=Email(self.from_email, self.from_name),
            to_emails=To(to_email),
            subject=subject,
            html_content=HtmlContent(html_content)
        )
        
        try:
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            status_code = response.status_code
            
            if status_code >= 200 and status_code < 300:
                logger.info(f"メール送信成功: {to_email}, ステータス: {status_code}")
                return True
            else:
                logger.error(f"メール送信エラー: ステータス {status_code}")
                return False
                
        except Exception as e:
            logger.error(f"メール送信例外: {str(e)}")
            return False
    
    async def send_verification_email(self, to_email: str, user_name: str, verification_url: str) -> bool:
        """メール確認用のメールを送信"""
        subject = "【稼働.com】メールアドレスの確認"
        html_content = f"""
        <html>
        <body style="font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 20px; border: 1px solid #e9ecef;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #343a40; margin-bottom: 5px;">メールアドレスの確認</h2>
                    <p style="color: #6c757d; font-size: 14px; margin-top: 0;">稼働.com</p>
                </div>
                
                <p>こんにちは、<strong>{user_name}</strong> さん</p>
                
                <p>稼働.comへのご登録ありがとうございます。以下のボタンをクリックして、メールアドレスの確認を完了してください。</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #4a5568; color: white; padding: 12px 24px; text-decoration: none; 
                              border-radius: 5px; font-weight: bold; display: inline-block;">
                        メールアドレスを確認する
                    </a>
                </div>
                
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
