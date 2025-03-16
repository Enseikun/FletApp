"""
メインビューモデル
アプリケーション全体の状態を管理
"""

from typing import Callable, List, Optional


class MainViewModel:
    """
    メインビューモデル
    アプリケーション全体の状態を管理するクラス
    """

    def __init__(self):
        """初期化"""
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

    def add_destination_changed_callback(self, callback: Callable[[str], None]) -> None:
        """
        デスティネーション変更時のコールバックを追加

        Args:
            callback: コールバック関数
        """
        if callback not in self._destination_changed_callbacks:
            self._destination_changed_callbacks.append(callback)

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

    def _notify_destination_changed(self) -> None:
        """デスティネーション変更を通知"""
        for callback in self._destination_changed_callbacks:
            callback(self._current_destination)

    def _update_sidebar_destination(self, destination_key: str) -> None:
        """サイドバーのデスティネーションを更新"""
        if self._sidebar_viewmodel:
            # デスティネーションキーをサイドバーのキーに変換
            sidebar_key = self._map_destination_to_sidebar_key(destination_key)
            print(f"MainViewModel: サイドバー更新 - {destination_key} -> {sidebar_key}")
            if sidebar_key:
                self._sidebar_viewmodel.update_selected_destination(sidebar_key)
        else:
            print("MainViewModel: サイドバーViewModel未設定")

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

    def set_current_task_id(self, task_id):
        """現在のタスクIDを設定"""
        self.current_task_id = task_id

    def get_current_task_id(self):
        """現在のタスクIDを取得"""
        return self.current_task_id
