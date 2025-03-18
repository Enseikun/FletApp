# Outlook関連のモデルの基底クラス

from datetime import datetime

from src.core.logger import get_logger
from src.models.outlook.outlook_service import OutlookService


class OutlookBaseModel:
    """Outlookモデルの基底クラス"""

    def __init__(self):
        self._service = OutlookService()
        self.logger = get_logger()

    def _create_date_filter(self, start_date: datetime, end_date: datetime) -> str:
        """日付フィルタを作成する"""
        start_date_str = start_date.strftime("%Y%m%d %H:%M:%S")
        end_date_str = end_date.strftime("%Y%m%d %H:%M:%S")
        return f"[ReceivedTime] >= '{start_date_str}' AND [ReceivedTime] <= '{end_date_str}'"
