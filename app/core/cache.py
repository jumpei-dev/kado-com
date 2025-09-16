from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import threading

class SimpleCache:
    """シンプルなメモリキャッシュ実装"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if datetime.now() < entry['expires_at']:
                    return entry['value']
                else:
                    # 期限切れのエントリを削除
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, timeout: int = 300) -> None:
        """キャッシュに値を設定（デフォルト5分）"""
        with self._lock:
            expires_at = datetime.now() + timedelta(seconds=timeout)
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
    
    def delete(self, key: str) -> bool:
        """キャッシュから値を削除"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """全てのキャッシュをクリア"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """期限切れのエントリを削除し、削除した件数を返す"""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items()
                if now >= entry['expires_at']
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    def size(self) -> int:
        """キャッシュのサイズを取得"""
        with self._lock:
            return len(self._cache)

# グローバルキャッシュインスタンス
cache = SimpleCache()

def get_cache_key(prefix: str, **kwargs) -> str:
    """キャッシュキーを生成"""
    key_parts = [prefix]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)