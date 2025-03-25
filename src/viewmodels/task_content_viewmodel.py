"""
タスク設定画面のViewModel
入力データの保持とModelへのデータ受け渡しを担当
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.models.outlook.outlook_account_model import OutlookAccountModel
from src.models.task_content_model import TaskContentModel


class TaskContentViewModel:
    """タスク設定画面のViewModel"""

    def __init__(self):
        """初期化"""
        # Modelの初期化
        self._outlook_account_model = OutlookAccountModel()
        self._task_content_model = TaskContentModel()

        # 入力データの初期化
        self._init_input_data()

    def _init_input_data(self):
        """入力データの初期化"""
        # 現在の日時を取得
        now = datetime.now()
        self._start_date = now
        self._end_date = now + timedelta(minutes=30)

        # フォルダ選択の状態
        self._from_folder_id: str = ""
        self._to_folder_id: str = ""

        # オプション設定
        self._ai_review: bool = True
        self._file_download: bool = True
        self._exclude_extensions: str = ""

        # フォルダのキャッシュ
        self._folders: List[Dict[str, Any]] = []

    # 入力データのプロパティ
    @property
    def start_date(self) -> datetime:
        """開始日時を取得"""
        return self._start_date

    @start_date.setter
    def start_date(self, value: datetime):
        """開始日時を設定"""
        self._start_date = value
        # 終了日時が開始日時より前の場合、終了日時を調整
        if self._end_date < self._start_date:
            self._end_date = self._start_date + timedelta(minutes=30)

    @property
    def end_date(self) -> datetime:
        """終了日時を取得"""
        return self._end_date

    @end_date.setter
    def end_date(self, value: datetime):
        """終了日時を設定"""
        if value < self._start_date:
            raise ValueError("終了日時は開始日時より後に設定してください")
        self._end_date = value

    @property
    def from_folder_id(self) -> str:
        """送信元フォルダIDを取得"""
        return self._from_folder_id

    @from_folder_id.setter
    def from_folder_id(self, value: str):
        """送信元フォルダIDを設定"""
        self._from_folder_id = value

    @property
    def to_folder_id(self) -> str:
        """送信先フォルダIDを取得"""
        return self._to_folder_id

    @to_folder_id.setter
    def to_folder_id(self, value: str):
        """送信先フォルダIDを設定"""
        if value == self._from_folder_id:
            raise ValueError("移動元と移動先のフォルダが同じです")
        self._to_folder_id = value

    @property
    def ai_review(self) -> bool:
        """AIレビュー設定を取得"""
        return self._ai_review

    @ai_review.setter
    def ai_review(self, value: bool):
        """AIレビュー設定を設定"""
        self._ai_review = value

    @property
    def file_download(self) -> bool:
        """ファイルダウンロード設定を取得"""
        return self._file_download

    @file_download.setter
    def file_download(self, value: bool):
        """ファイルダウンロード設定を設定"""
        self._file_download = value

    @property
    def exclude_extensions(self) -> str:
        """除外拡張子を取得"""
        return self._exclude_extensions

    @exclude_extensions.setter
    def exclude_extensions(self, value: str):
        """除外拡張子を設定"""
        self._exclude_extensions = value

    # OutlookAccountModelとのデータ受け渡し
    async def connect_outlook(self) -> bool:
        """Outlookに接続してフォルダ一覧を取得"""
        try:
            # アカウント情報を保存
            success = self._outlook_account_model.save_account_folders()
            if not success:
                return False

            # フォルダ一覧を更新
            self._folders = self._outlook_account_model.get_folder_paths()
            return True

        except Exception as e:
            print(f"Outlook接続エラー: {str(e)}")
            return False

    def get_folder_paths(self) -> List[str]:
        """フォルダパスの一覧を取得"""
        if not self._folders:
            self._folders = self._outlook_account_model.get_folder_paths()
        return self._folders

    # TaskContentModelとのデータ受け渡し
    def create_task(self) -> bool:
        """タスクを作成"""
        # 入力値の検証
        self._validate_task_data()

        # タスク情報の作成
        task_info = self._create_task_info()

        # タスクを作成
        return self._task_content_model.create_task(task_info)

    def _validate_task_data(self):
        """タスクデータの検証"""
        if not self._from_folder_id:
            raise ValueError("移動元フォルダを選択してください")

        if not self._to_folder_id:
            raise ValueError("移動先フォルダを選択してください")

        if self._from_folder_id == self._to_folder_id:
            raise ValueError("移動元と移動先のフォルダが同じです")

        if self._end_date <= self._start_date:
            raise ValueError("終了日時は開始日時より後に設定してください")

    def _create_task_info(self) -> Dict[str, Any]:
        """タスク情報の作成"""
        # フォルダ情報を取得
        from_folder_info = self._outlook_account_model.get_folder_info(
            self._from_folder_id
        )
        to_folder_info = self._outlook_account_model.get_folder_info(self._to_folder_id)

        if not from_folder_info:
            raise ValueError("移動元フォルダの情報が取得できません")

        # 現在の日時を取得
        now = datetime.now()

        return {
            "id": now.strftime("%Y%m%d%H%M%S"),
            "account_id": from_folder_info["account_id"],
            "folder_id": self._from_folder_id,
            "from_folder_id": self._from_folder_id,
            "from_folder_name": from_folder_info["name"],
            "from_folder_path": from_folder_info["path"],
            "to_folder_id": self._to_folder_id,
            "to_folder_name": to_folder_info["name"] if to_folder_info else None,
            "to_folder_path": to_folder_info["path"] if to_folder_info else None,
            "start_date": self._start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": self._end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "mail_count": 0,
            "ai_review": 1 if self._ai_review else 0,
            "file_download": 1 if self._file_download else 0,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "created",
            "error_message": None,
        }

    def reset_form(self):
        """フォームをリセット"""
        self._init_input_data()
