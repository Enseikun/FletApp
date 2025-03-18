"""
メインビューモデル
アプリケーション全体の状態を管理
"""

from typing import Callable, List, Optional

from src.core.logger import get_logger


class MainViewModel:
    """
    メインビューモデル
    アプリケーション全体の状態を管理するクラス
    """

    def __init__(self):
        """初期化"""
        self.logger = get_logger()
        self.logger.info("MainViewModel初期化")
        # 現在のデスティネーション
        self._current_destination = "home"
        # デスティネーション変更時のコールバック
        self._destination_changed_callbacks = []
        # サイドバーのビューモデル参照（循環参照を避けるため後から設定）
        self._sidebar_viewmodel = None
        self.current_task_id = "20250315172449"  # デフォルト値

    def set_sidebar_viewmodel(self, sidebar_viewmodel):
        """サイドバーのビューモデルを設定"""
        self._sidebar_viewmodel = sidebar_viewmodel
        self.logger.debug("サイドバーViewModelを設定")

    def get_current_destination(self) -> str:
        """現在のデスティネーションを取得"""
        return self._current_destination

    def set_destination(self, destination_key: str) -> None:
        """
        デスティネーションを設定

        Args:
            destination_key: デスティネーションキー
        """
        if self._current_destination != destination_key:
            self.logger.info(
                f"デスティネーション変更: {self._current_destination} -> {destination_key}"
            )
            self._current_destination = destination_key
            self._notify_destination_changed()

            # サイドバーのデスティネーションも更新
            self._update_sidebar_destination(destination_key)

    def set_initial_destination(self, destination_key: str) -> None:
        """
        初期デスティネーションを設定（通知なし）

        Args:
            destination_key: デスティネーションキー
        """
        self._current_destination = destination_key
        self.logger.debug(f"初期デスティネーション設定: {destination_key}")

    def add_destination_changed_callback(self, callback: Callable[[str], None]) -> None:
        """
        デスティネーション変更時のコールバックを追加

        Args:
            callback: コールバック関数
        """
        if callback not in self._destination_changed_callbacks:
            self._destination_changed_callbacks.append(callback)
            self.logger.debug("デスティネーション変更コールバック追加")

    def remove_destination_changed_callback(
        self, callback: Callable[[str], None]
    ) -> None:
        """
        デスティネーション変更時のコールバックを削除

        Args:
            callback: コールバック関数
        """
        if callback in self._destination_changed_callbacks:
            self._destination_changed_callbacks.remove(callback)
            self.logger.debug("デスティネーション変更コールバック削除")

    def _notify_destination_changed(self) -> None:
        """デスティネーション変更を通知"""
        self.logger.debug(f"デスティネーション変更通知: {self._current_destination}")
        for callback in self._destination_changed_callbacks:
            callback(self._current_destination)

    def _update_sidebar_destination(self, destination_key: str) -> None:
        """サイドバーのデスティネーションを更新"""
        if self._sidebar_viewmodel:
            # デスティネーションキーをサイドバーのキーに変換
            sidebar_key = self._map_destination_to_sidebar_key(destination_key)
            self.logger.debug(f"サイドバー更新: {destination_key} -> {sidebar_key}")
            if sidebar_key:
                self._sidebar_viewmodel.update_selected_destination(sidebar_key)
        else:
            self.logger.warning("サイドバーViewModel未設定")

    def _map_destination_to_sidebar_key(self, destination_key: str) -> Optional[str]:
        """デスティネーションキーをサイドバーのキーに変換"""
        # マッピングテーブル
        mapping = {
            "home": "home",
            "preview": "preview",
            "settings": "settings",
            "task": None,  # タスク画面はサイドバーに対応するアイテムがない
        }
        return mapping.get(destination_key)

    def set_current_task_id(self, task_id: str) -> None:
        """
        現在選択されているタスクIDを設定する

        Args:
            task_id: 設定するタスクID
        """
        self._current_task_id = task_id
        self.logger.info(f"現在のタスクIDを設定: {task_id}")

    def get_current_task_id(self) -> str:
        """
        現在選択されているタスクIDを取得する

        Returns:
            str: 現在のタスクID
        """
        return getattr(self, "_current_task_id", None)
