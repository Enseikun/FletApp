"""
Outlook関連のモデルの基底クラス

責務:
- Outlook関連モデルの共通機能の提供
- ロギング機能の提供
- OutlookServiceのインスタンス管理
- 日付フィルタの生成

主なメソッド:
- _create_date_filter: 日付範囲に基づくフィルタ条件の生成

連携:
- OutlookService: Outlook APIとの通信機能の提供
- 子クラス: OutlookItemModel, OutlookTaskModel, OutlookAccountModel
"""

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
