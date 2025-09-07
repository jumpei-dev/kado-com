from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
import httpx
import re
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

# キャッシュ設定
CACHE_EXPIRY = 3600  # 1時間（秒）
tweet_cache = {
    "data": [],
    "last_updated": None
}

async def get_twitter_timeline(username: str = "kadou_com", count: int = 3) -> List[Dict[str, Any]]:
    """TwitterのタイムラインをAPIから取得（または、キャッシュから）"""
    global tweet_cache
    
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
