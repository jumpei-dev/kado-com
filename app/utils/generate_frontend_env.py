#!/usr/bin/env python3
"""
フロントエンド用環境変数生成スクリプト
config/config.yml から frontend/.env を自動生成
"""

import sys
import yaml
from pathlib import Path

def generate_frontend_env():
    """config.ymlからfrontend/.envを生成"""
    
    # プロジェクトルートを取得
    app_root = Path(__file__).parent.parent  # app/utils -> app
    project_root = app_root.parent  # app -> project root
    config_path = project_root / "config" / "config.yml"
    frontend_env_path = project_root / "frontend" / ".env"
    
    try:
        # config.ymlを読み込み
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # フロントエンド設定を取得
        frontend_config = config.get('frontend', {})
        
        # .envファイル内容を生成
        env_content = f"""# =============================================================================
# フロントエンド環境変数（config/config.yml から自動生成）
# このファイルは自動生成されます。直接編集しないでください。
# =============================================================================

# API Base URL
VITE_API_BASE_URL={frontend_config.get('api_base_url', 'http://localhost:8000')}

# Environment
VITE_NODE_ENV={frontend_config.get('node_env', 'development')}

# App Settings
VITE_APP_NAME={frontend_config.get('app_name', '稼働.com')}
VITE_APP_VERSION={frontend_config.get('app_version', '1.0.0')}

# 生成時刻: {Path(__file__).stem}により自動生成
"""
        
        # frontend/.envファイルに書き込み
        with open(frontend_env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ frontend/.env を生成しました")
        print(f"📄 設定ファイル: {config_path}")
        print(f"📄 出力ファイル: {frontend_env_path}")
        print(f"🌐 API URL: {frontend_config.get('api_base_url')}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ ファイルが見つかりません: {e}")
        return False
    except yaml.YAMLError as e:
        print(f"❌ YAML解析エラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = generate_frontend_env()
    sys.exit(0 if success else 1)
