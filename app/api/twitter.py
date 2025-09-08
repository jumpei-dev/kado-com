from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

# テンプレートの設定
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir.absolute()))

router = APIRouter(prefix="/api/twitter", tags=["twitter"])

@router.get("", response_class=HTMLResponse)
async def get_tweets(
    request: Request,
    count: int = 5
):
    """運営者のツイートを取得 - HTMLレスポンス"""
    
    # ダミーのツイートデータ
    kado_admin_tweets = [
        {
            "id": "1",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "【新機能追加】店舗詳細ページに「週間稼働率変化グラフ」を追加しました。一週間の稼働率の推移が一目でわかるようになりました。ぜひご活用ください🙌 #風俗稼働 #稼働com",
            "timestamp": "1時間前",
            "source": "Twitter Web App",
            "image": "https://pbs.twimg.com/media/GHFmnVaWIAA3uwh?format=jpg&name=medium",
            "replies": "5",
            "retweets": "28",
            "likes": "142"
        },
        {
            "id": "2",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "【お知らせ】ただいまサーバー負荷軽減のためのメンテナンスを行なっております。一部地域でアクセスしづらい状況が発生しておりますが、ご了承ください。11:00には復旧予定です。",
            "timestamp": "3時間前",
            "source": "Twitter for iPhone",
            "image": None,
            "replies": "3",
            "retweets": "18",
            "likes": "95"
        },
        {
            "id": "3",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "【ご好評いただいています】当サイトの「店舗フィルター機能」が多くのユーザー様にご利用いただいています。エリア、ジャンル、稼働率でピンポイント検索できるので、あなたの希望条件にぴったりの店舗が見つかります！ #風俗求人",
            "timestamp": "昨日",
            "source": "Twitter for Android",
            "image": "https://pbs.twimg.com/media/GGwZSGEXoAAFC3V?format=jpg&name=medium",
            "replies": "8", 
            "retweets": "42",
            "likes": "201"
        },
        {
            "id": "4",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "【データ更新】本日9:00に全店舗の稼働率データを更新しました。週末に向けて稼働率が上昇している店舗が多いようです。特に渋谷・新宿エリアは要チェック！ #風俗稼働率 #高収入",
            "timestamp": "2日前",
            "source": "Twitter Web App",
            "image": None,
            "replies": "4",
            "retweets": "22",
            "likes": "118"
        },
        {
            "id": "5",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "皆様からの貴重なフィードバックをもとに、サイトデザインを一部リニューアルしました！より見やすく、使いやすくなっています。特に店舗カードのデザインは好評です。引き続きご意見お待ちしています！ #サイトリニューアル",
            "timestamp": "3日前",
            "source": "Twitter Web App",
            "image": "https://pbs.twimg.com/media/GGrKLPoXIAAiCDZ?format=jpg&name=medium",
            "replies": "12",
            "retweets": "35",
            "likes": "159"
        }
    ]
    
    # 要求されたツイート数に制限
    tweets = kado_admin_tweets[:count]
    
    # HTMLテンプレートをレンダリングして返す
    return templates.TemplateResponse(
        "components/twitter_timeline.html", 
        {"request": request, "tweets": tweets}
    )

def get_time_ago(dt: datetime) -> str:
    """日時を「〇〇前」の形式に変換"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 30:
        months = diff.days // 30
        return f"{months}ヶ月前"
    elif diff.days > 0:
        return f"{diff.days}日前"
    elif diff.seconds // 3600 > 0:
        return f"{diff.seconds // 3600}時間前"
    elif diff.seconds // 60 > 0:
        return f"{diff.seconds // 60}分前"
    else:
        return "たった今"

def get_dummy_tweets(count: int = 3) -> List[Dict[str, Any]]:
    """Twitter APIが利用できない場合のダミーデータ"""
    now = datetime.now()
    dummy_tweets = [
        {
            "content": "【求人情報】札幌エリアで高単価の店舗が稼働率上昇中！出稼ぎ検討中の方はDMください！ #風俗求人 #高収入",
            "created_at": now - timedelta(hours=2),
            "timestamp": "2時間前"
        },
        {
            "content": "「稼働.com」の会員登録で非公開店舗の稼働率情報も見られるようになりました！登録は無料です。",
            "created_at": now - timedelta(days=1),
            "timestamp": "昨日"
        },
        {
            "content": "【稼働率速報】今週は関東エリアのNSソープが軒並み高稼働。大型連休の影響か。詳細は稼働.comで！",
            "created_at": now - timedelta(days=3),
            "timestamp": "3日前"
        },
        {
            "content": "出稼ぎ情報：今月の稼げる地域ランキング 1位:北海道 2位:東京 3位:大阪 詳しくは稼働.comをチェック！",
            "created_at": now - timedelta(days=5),
            "timestamp": "5日前"
        }
    ]
    return dummy_tweets[:count]

@router.get("/timeline")
async def twitter_timeline(request: Request, count: int = 3):
    """Twitterのタイムラインを取得して表示"""
    tweets = get_dummy_tweets(count=count)
    
    return templates.TemplateResponse(
        "components/twitter_timeline.html",
        {"request": request, "tweets": tweets}
    )
