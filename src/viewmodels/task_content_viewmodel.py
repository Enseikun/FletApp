"""
タスク設定画面のViewModel
入力データの保持とModelへのデータ受け渡しを担当
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.core.logger import get_logger
from src.models.outlook.outlook_account_model import OutlookAccountModel
from src.models.task_content_model import TaskContentModel
from src.views.components.progress_dialog import ProgressDialog


class TaskContentViewModel:
    """タスク設定画面のViewModel"""

    def __init__(self):
        """初期化"""
        self.logger = get_logger()
        self.logger.info("TaskContentViewModel: 初期化開始")

        # Modelの初期化
        self._outlook_account_model = OutlookAccountModel()
        self._task_content_model = TaskContentModel()

        # ProgressDialogのインスタンスを取得
        self._progress_dialog = ProgressDialog()

        # 入力データの初期化
        self._init_input_data()

        self.logger.info("TaskContentViewModel: 初期化完了")

    def _init_input_data(self):
        """入力データの初期化"""
        # 現在の日時を取得
        now = datetime.now()
        self._start_date = now
        self._end_date = now + timedelta(minutes=30)

        # フォルダ選択の状態
        self._from_folder_id: str = ""
        self._from_folder_path: str = ""
        self._to_folder_id: str = ""
        self._to_folder_path: str = ""

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
    def from_folder_path(self) -> str:
        """送信元フォルダパスを取得"""
        return self._from_folder_path

    @from_folder_path.setter
    def from_folder_path(self, value: str):
        """送信元フォルダパスを設定"""
        self._from_folder_path = value

    @property
    def to_folder_path(self) -> str:
        """送信先フォルダパスを取得"""
        return self._to_folder_path

    @to_folder_path.setter
    def to_folder_path(self, value: str):
        """送信先フォルダパスを設定"""
        self._to_folder_path = value

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
            # プログレスダイアログを表示（不確定モード）
            # ページコンテキストを使用した方法
            await self._progress_dialog.show_async(
                "Outlook接続中", "Outlookアカウントに接続しています...", 0, None
            )

            await asyncio.sleep(0.1)

            # アカウント情報を保存
            success = self._outlook_account_model.save_account_folders()
            if not success:
                await self._progress_dialog.close_async()
                return False

            # フォルダ一覧を更新
            self._folders = self._outlook_account_model.get_folder_paths()

            # ダイアログを閉じる
            await self._progress_dialog.close_async()
            return True

        except Exception as e:
            self.logger.error(f"Outlook接続エラー: {str(e)}")
            try:
                await self._progress_dialog.close_async()
            except:
                pass
            return False

    def get_folder_paths(self) -> List[str]:
        """フォルダパスの一覧を取得"""
        if not self._folders:
            self._folders = self._outlook_account_model.get_folder_paths()
        return self._folders

    def get_folder_info(self) -> List[Dict[str, Any]]:
        """フォルダ情報の一覧を取得"""
        return self._outlook_account_model.get_folder_info()

    # TaskContentModelとのデータ受け渡し
    def create_task(self) -> bool:
        """タスクを作成"""
        # 入力値の検証
        self._validate_task_data()

        # タスク情報の作成
        task_info = self._create_task_info()

        # タスクを作成
        success = self._task_content_model.create_task(task_info)
        if success:
            # タスクフォルダとデータベースを作成
            success = self._task_content_model.create_task_directory_and_database(
                task_info["id"]
            )
            if not success:
                self.logger.error("タスクフォルダとデータベースの作成に失敗しました")
                return False

            return True

    def _validate_task_data(self):
        """タスクデータの検証"""
        if not self._from_folder_path:
            raise ValueError("移動元フォルダを選択してください")

        if not self._to_folder_path:
            raise ValueError("移動先フォルダを選択してください")

        if self._from_folder_path == self._to_folder_path:
            raise ValueError("移動元と移動先のフォルダが同じです")

        if self._end_date <= self._start_date:
            raise ValueError("終了日時は開始日時より後に設定してください")

    def _create_task_info(self) -> Dict[str, Any]:
        """タスク情報の作成"""
        # フォルダ情報を取得
        folder_info = self._outlook_account_model.get_folder_info()
        from_folder = next(
            (f for f in folder_info if f["entry_id"] == self._from_folder_id), None
        )
        to_folder = next(
            (f for f in folder_info if f["entry_id"] == self._to_folder_id), None
        )

        if not from_folder or not to_folder:
            raise ValueError("フォルダ情報が見つかりません")

        # 現在時刻を取得
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "account_id": from_folder["store_id"],
            "folder_id": self._from_folder_id,
            "from_folder_id": self._from_folder_id,
            "from_folder_name": from_folder["name"],
            "from_folder_path": from_folder["path"],
            "to_folder_id": self._to_folder_id,
            "to_folder_name": to_folder["name"],
            "to_folder_path": to_folder["path"],
            "start_date": self._start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": self._end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "ai_review": 1 if self._ai_review else 0,
            "file_download": 1 if self._file_download else 0,
            "exclude_extensions": (
                self._exclude_extensions.split(",")
                if self._file_download and self._exclude_extensions
                else []
            ),
            "status": "created",
            "created_at": now,
            "updated_at": now,
        }

    def reset_form(self):
        """フォームをリセット"""
        self._init_input_data()
