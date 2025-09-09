import os
from datetime import timedelta

# JWT設定
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "kado-com-very-secret-key-for-development")  # 本番環境では環境変数から
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_DAYS = 7

# メール設定
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-password")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@kadocom.com")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8080")
