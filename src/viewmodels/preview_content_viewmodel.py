"""
プレビューコンテンツのビューモデル
メールプレビュー画面のデータ処理を担当
"""

from typing import Any, Dict, List, Optional, Union

from src.core.logger import get_logger
from src.models.preview_content_model import PreviewContentModel


class PreviewContentViewModel:
    """プレビューコンテンツのビューモデル"""

    def __init__(self, task_id: Optional[str] = None):
        """
        初期化

        Args:
            task_id: タスクID
        """
        self.logger = get_logger()
        self.logger.info("PreviewContentViewModel: 初期化開始", task_id=task_id)
        self.task_id = task_id
        # モデルのインスタンス化
        self.model = PreviewContentModel(task_id)

        # 現在選択されているフォルダID
        self.current_folder_id = None

        # キャッシュされたメールリスト
        self.cached_mail_list = []
        self.logger.info("PreviewContentViewModel: 初期化完了")

    def get_task_info(self) -> Optional[Dict]:
        """タスク情報を取得"""
        self.logger.debug("PreviewContentViewModel: タスク情報取得開始")
        result = self.model.get_task_info()
        if result:
            self.logger.debug(
                "PreviewContentViewModel: タスク情報取得成功", task_info=result
            )
        else:
            self.logger.warning(
                "PreviewContentViewModel: タスク情報が見つかりません",
                task_id=self.task_id,
            )
        return result

    def get_folders(self) -> List[Dict]:
        """フォルダ一覧を取得"""
        self.logger.debug("PreviewContentViewModel: フォルダ一覧取得開始")
        folders = self.model.get_folders()
        self.logger.debug(
            "PreviewContentViewModel: フォルダ一覧取得完了", folder_count=len(folders)
        )
        return folders

    def load_folder_mails(self, folder_id: str) -> List[Dict]:
        """指定フォルダのメール一覧を取得"""
        self.logger.info(
            "PreviewContentViewModel: フォルダメール取得開始", folder_id=folder_id
        )
        self.current_folder_id = folder_id
        self.cached_mail_list = self.model.load_folder_mails(folder_id)
        self.logger.info(
            "PreviewContentViewModel: フォルダメール取得完了",
            folder_id=folder_id,
            mail_count=len(self.cached_mail_list),
        )
        return self.cached_mail_list

    def search_mails(self, search_term: str) -> List[Dict]:
        """メールを検索"""
        self.logger.info(
            "PreviewContentViewModel: メール検索開始", search_term=search_term
        )
        self.cached_mail_list = self.model.search_mails(search_term)
        self.logger.info(
            "PreviewContentViewModel: メール検索完了",
            search_term=search_term,
            result_count=len(self.cached_mail_list),
        )
        return self.cached_mail_list

    def get_mail_content(self, entry_id: str) -> Optional[Dict]:
        """メールの内容を取得"""
        self.logger.debug("PreviewContentViewModel: メール内容取得", entry_id=entry_id)
        result = self.model.get_mail_content(entry_id)
        if result:
            self.logger.debug(
                "PreviewContentViewModel: メール内容取得成功", entry_id=entry_id
            )
        else:
            self.logger.warning(
                "PreviewContentViewModel: メール内容が見つかりません", entry_id=entry_id
            )
        return result

    def mark_as_read(self, entry_id: str) -> bool:
        """メールを既読にする"""
        self.logger.debug("PreviewContentViewModel: メール既読設定", entry_id=entry_id)
        result = self.model.mark_as_read(entry_id)
        if result:
            self.logger.debug(
                "PreviewContentViewModel: メール既読設定成功", entry_id=entry_id
            )
        else:
            self.logger.error(
                "PreviewContentViewModel: メール既読設定失敗", entry_id=entry_id
            )
        return result

    def close(self):
        """リソースを解放"""
        self.logger.info("PreviewContentViewModel: リソース解放")
        self.model.close()
