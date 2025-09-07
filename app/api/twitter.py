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
    """イーロンマスクのツイートを取得 - HTMLレスポンス"""
    
    # ダミーのツイートデータ
    elon_tweets = [
        {
            "id": "1",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "SpaceX Starship 飛行試験成功！全段回収も間もなく実現します。火星移住への大きな一歩です 🚀",
            "timestamp": "2時間前",
            "source": "Twitter for iPhone",
            "image": "https://pbs.twimg.com/media/GHFmnVaWIAA3uwh?format=jpg&name=medium",
            "replies": "5.2K",
            "retweets": "28.5K",
            "likes": "142.7K"
        },
        {
            "id": "2",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "Tesla AI Dayで新しいヒューマノイドロボット「Optimus Gen 2」を発表します。人間の仕事を代替し、危険な作業から人を解放します。",
            "timestamp": "5時間前",
            "source": "Twitter Web App",
            "image": None,
            "replies": "3.1K",
            "retweets": "18.2K",
            "likes": "95.3K"
        },
        {
            "id": "3",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "Neuralink人体実験が成功。被験者はわずかな思考だけでコンピュータを操作できるようになりました。医療革命の始まりです。",
            "timestamp": "昨日",
            "source": "Twitter for Android",
            "image": "https://pbs.twimg.com/media/GGwZSGEXoAAFC3V?format=jpg&name=medium",
            "replies": "8.7K", 
            "retweets": "42.1K",
            "likes": "201.8K"
        },
        {
            "id": "4",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "Xのビジョンは、世界中の金融をより効率的にすること。すべてのユーザーが簡単に送金や貯蓄ができるようにします。銀行口座不要の時代へ。",
            "timestamp": "2日前",
            "source": "Twitter Web App",
            "image": None,
            "replies": "4.5K",
            "retweets": "22.3K",
            "likes": "118.6K"
        },
        {
            "id": "5",
            "profile_image": "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
            "content": "宇宙インターネットStarlinkが緊急災害支援を強化。被災地でも高速インターネットを提供し、命を救います。通信は基本的人権です。",
            "timestamp": "3日前",
            "source": "Twitter for iPhone",
            "image": "https://pbs.twimg.com/media/GGMNXo0WMAAoMDx?format=jpg&name=medium",
            "replies": "2.9K",
            "retweets": "15.7K",
            "likes": "87.4K"
        }
    ]
    
    # 要求されたツイート数に制限
    tweets = elon_tweets[:count]
    
    # HTMLテンプレートをレンダリングして返す
    return templates.TemplateResponse(
        "components/twitter_timeline.html", 
        {"request": request, "tweets": tweets}
    )
    
    # キャッシュチェック
    now = datetime.now()
    if tweet_cache["last_updated"] and (now - tweet_cache["last_updated"]).total_seconds() < CACHE_EXPIRY:
        return tweet_cache["data"][:count]
    
    try:
        # Twitter API v2 ベアラートークン
        bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
        if not bearer_token:
            logger.warning("TWITTER_BEARER_TOKENが設定されていません。ダミーデータを返します。")
            return get_dummy_tweets(count)
        
        # Twitter API v2エンドポイント
        url = f"https://api.twitter.com/2/users/by/username/{username}"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        
        async with httpx.AsyncClient() as client:
            # まずユーザーIDを取得
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Twitter API エラー: {response.status_code}, {response.text}")
                return get_dummy_tweets(count)
            
            user_data = response.json()
            user_id = user_data["data"]["id"]
            
            # ユーザーIDを使ってツイートを取得
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets?max_results={count}&tweet.fields=created_at"
            tweets_response = await client.get(tweets_url, headers=headers)
            
            if tweets_response.status_code != 200:
                logger.error(f"Twitter API エラー: {tweets_response.status_code}, {tweets_response.text}")
                return get_dummy_tweets(count)
            
            tweets_data = tweets_response.json()
            
            # データ整形
            tweets = []
            for tweet in tweets_data["data"]:
                created_at = datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
                tweets.append({
                    "content": tweet["text"],
                    "created_at": created_at,
                    "timestamp": get_time_ago(created_at)
                })
            
            # キャッシュ更新
            tweet_cache["data"] = tweets
            tweet_cache["last_updated"] = now
            
            return tweets
    
    except Exception as e:
        logger.error(f"Twitter APIリクエストエラー: {e}")
        return get_dummy_tweets(count)

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
            "text": "出稼ぎ情報：今月の稼げる地域ランキング 1位:北海道 2位:東京 3位:大阪 詳しくは稼働.comをチェック！",
            "created_at": now - timedelta(days=5),
            "time_ago": "5日前"
        }
    ]
    return dummy_tweets[:count]

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

@router.get("/twitter/timeline")
async def twitter_timeline(request: Request, count: int = 3):
    """Twitterのタイムラインを取得して表示"""
    tweets = await get_twitter_timeline(count=count)
    
    return templates.TemplateResponse(
        "components/twitter_timeline.html",
        {"request": request, "tweets": tweets}
    )
