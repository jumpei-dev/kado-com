"""
Status Collection jobs package
"""

try:
    from .collector import collect_all_working_status, collect_status_for_business
    __all__ = ['collect_all_working_status', 'collect_status_for_business']
except ImportError as e:
    print(f"Status collection インポートエラー: {e}")
    __all__ = []
