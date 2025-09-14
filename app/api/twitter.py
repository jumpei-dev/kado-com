from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import tweepy
import logging
import asyncio
from functools import lru_cache

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

# 設定読み込み
from app.core.config import get_config

# テンプレートの設定
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir.absolute()))

# ログ設定
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/twitter", tags=["twitter"])

# X API クライアントのキャッシュ
_twitter_client = None
_last_tweets_cache = None
_cache_timestamp = None

def get_twitter_client():
    """X API クライアントを取得（シングルトン）"""
    global _twitter_client
    
    if _twitter_client is not None:
        return _twitter_client
    
    # X API機能は削除されました - ダミーデータのみ使用
    logger.info("X API client disabled, using dummy data only")
    return None

def get_real_tweets(username: str, count: int = 10) -> List[Dict[str, Any]]:
    """X APIから実際のツイートを取得"""
    global _last_tweets_cache, _cache_timestamp
    
    try:
        # X API機能は削除されました - 常にダミーデータを使用
        logger.info("Using dummy data for tweets")
        if True:  # 常にダミーデータを使用
            logger.info("Using dummy data as configured in fallback settings")
            return get_dummy_tweets(count)
        
        # キャッシュチェック（TTLを15分に延長してAPI呼び出し頻度を削減）
        if (cache_config.get('enabled', True) and 
            _last_tweets_cache is not None and 
            _cache_timestamp is not None):
            
            cache_ttl = cache_config.get('ttl_seconds', 900)  # デフォルト15分に延長
            if (datetime.now() - _cache_timestamp).total_seconds() < cache_ttl:
                logger.info(f"Returning cached tweets (age: {int((datetime.now() - _cache_timestamp).total_seconds())}s)")
                return _last_tweets_cache[:count]
        
        client = get_twitter_client()
        if client is None:
            return get_dummy_tweets(count)
        
        # ユーザー情報を取得
        user = client.get_user(username=username)
        if not user.data:
            logger.error(f"User {username} not found")
            return get_dummy_tweets(count)
        
        user_id = user.data.id
        
        # タイムライン設定
        timeline_config = x_config.get('timeline', {})
        max_results = min(timeline_config.get('max_results', 10), 100)  # API制限
        exclude_replies = timeline_config.get('exclude_replies', True)
        exclude_retweets = timeline_config.get('exclude_retweets', False)
        
        # 除外する項目を設定
        exclude_list = []
        if exclude_replies:
            exclude_list.append('replies')
        if exclude_retweets:
            exclude_list.append('retweets')
        
        # ツイートを取得
        tweets_response = client.get_users_tweets(
            id=user_id,
            max_results=max_results,
            exclude=exclude_list if exclude_list else None,
            tweet_fields=['created_at', 'public_metrics', 'context_annotations', 'attachments'],
            user_fields=['profile_image_url', 'name', 'username']
        )
        
        if not tweets_response.data:
            logger.warning("No tweets found")
            return get_dummy_tweets(count)
        
        # ツイートデータを整形
        formatted_tweets = []
        for tweet in tweets_response.data:
            formatted_tweet = {
                "id": str(tweet.id),
                "profile_image": user.data.profile_image_url or "https://abs.twimg.com/sticky/default_profile_images/default_profile_400x400.png",
                "content": tweet.text,
                "timestamp": get_time_ago(tweet.created_at),
                "source": "Twitter API v2",
                "image": None,  # 画像は別途処理が必要
                "replies": str(tweet.public_metrics.get('reply_count', 0)) if tweet.public_metrics else "0",
                "retweets": str(tweet.public_metrics.get('retweet_count', 0)) if tweet.public_metrics else "0",
                "likes": str(tweet.public_metrics.get('like_count', 0)) if tweet.public_metrics else "0"
            }
            formatted_tweets.append(formatted_tweet)
        
        # キャッシュを更新
        _last_tweets_cache = formatted_tweets
        _cache_timestamp = datetime.now()
        
        logger.info(f"Successfully fetched {len(formatted_tweets)} tweets from X API")
        return formatted_tweets[:count]
        
    except tweepy.TooManyRequests:
        logger.warning("X API rate limit exceeded")
        # rateリミット時は空の配列を返してエラーメッセージを表示させる
        return []
        
    except Exception as e:
        logger.error(f"Error fetching tweets from X API: {e}")
        # API接続エラー時は空の配列を返してエラーメッセージを表示させる
        return []

@router.get("", response_class=HTMLResponse)
async def get_tweets(
    request: Request,
    count: int = 5
):
    """Twitterタイムラインを取得してHTMLを返す"""
    try:
        config = get_config()
        twitter_config = config.get('frontend', {}).get('twitter', {})
        
        # 実際のツイートを取得
        tweets = get_real_tweets(twitter_config.get('username', 'kado_admin'), count)
        
        # rate limit時やAPI接続エラー時は空配列が返されるので、エラーメッセージを表示
        # ダミーデータは使用しない
        
        return templates.TemplateResponse(
            "components/twitter_timeline.html", 
            {
                "request": request, 
                "tweets": tweets, 
                "loading": False,
                "twitter_username": twitter_config.get('username', 'kado_admin'),
                "config": config
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_tweets endpoint: {e}")
        # 予期しないエラー時はエラーメッセージを表示
        return templates.TemplateResponse(
            "components/twitter_timeline.html", 
            {
                "request": request, 
                "tweets": [], 
                "loading": False,
                "twitter_username": config.get('frontend', {}).get('twitter', {}).get('username', 'kado_admin'),
                "config": config
            }
        )

def get_time_ago(dt: datetime) -> str:
    """日時を「〇〇前」の形式に変換"""
    if dt.tzinfo is None:
        # タイムゾーン情報がない場合はUTCとして扱う
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    
    now = datetime.now().astimezone()
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
    """X APIが利用できない場合のダミーデータ（現在は空の配列を返す）"""
    # ダミーツイートは削除し、空の配列を返してエラーメッセージを表示させる
    return []

@router.get("/timeline")
async def twitter_timeline(request: Request, count: int = 3):
    """Twitterのタイムラインを取得して表示（非同期処理）"""
    try:
        config = get_config()
        
        # 設定からユーザー名を取得
        frontend_config = config.get('frontend', {})
        twitter_config = frontend_config.get('twitter', {})
        username = twitter_config.get('username', 'elonmusk')  # デフォルト
        
        # 非同期でX APIからツイートを取得
        tweets = await asyncio.to_thread(get_real_tweets, username, count)
        
        return templates.TemplateResponse(
            "components/twitter_timeline.html",
            {
                "request": request, 
                "tweets": tweets, 
                "loading": False,
                "twitter_username": twitter_config.get('username', 'kado_admin'),
                "config": config
            }
        )
        
    except Exception as e:
        logger.error(f"Error in twitter_timeline endpoint: {e}")
        # X APIエラー時は空の配列を返してエラーメッセージを表示
        return templates.TemplateResponse(
            "components/twitter_timeline.html",
            {
                "request": request, 
                "tweets": [], 
                "loading": False,
                "twitter_username": config.get('frontend', {}).get('twitter', {}).get('username', 'kado_admin'),
                "config": config
            }
        )
