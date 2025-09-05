"""
Status Collection jobs package
"""

try:
    from .collector import collect_all_working_status, collect_status_for_business, collect_status_by_url
    __all__ = ['collect_all_working_status', 'collect_status_for_business', 'collect_status_by_url']
except ImportError as e:
    print(f"Status collection インポートエラー: {e}")
    try:
        # Fallback to absolute import
        from collector import collect_all_working_status, collect_status_for_business, collect_status_by_url
        __all__ = ['collect_all_working_status', 'collect_status_for_business', 'collect_status_by_url']
        print("✓ 絶対インポートでcollectorを読み込みました")
    except ImportError as e2:
        print(f"絶対インポートも失敗: {e2}")
        __all__ = []
