from typing import Optional

from src.core.logger import get_logger
from src.views.styles.style import ComponentState


class MainContentsViewModel:
    """
    メインコンテンツのビューモデル
    コンテンツ間の連携を管理
    """

    def __init__(self, main_viewmodel=None):
        """
        初期化

        Args:
            main_viewmodel: メインビューモデル
        """
        self.logger = get_logger()
        self.logger.info("MainContentsViewModel初期化")
        self.main_viewmodel = main_viewmodel
        self.current_task_id = None
        self._observers = []
        self._is_loading = False

    def set_current_task_id(self, task_id):
        """現在のタスクIDを設定"""
        self.current_task_id = task_id
        self.logger.info(f"現在のタスクIDを設定: {task_id}")
        self._notify_observers()

    def get_current_task_id(self):
        """現在のタスクIDを取得"""
        return self.current_task_id

    def set_loading(self, is_loading: bool):
        """
        ローディング状態を設定

        Args:
            is_loading: ローディング中かどうか
        """
        self._is_loading = is_loading
        self.logger.debug(f"ローディング状態を設定: {is_loading}")
        self._notify_observers()

    def is_loading(self) -> bool:
        """
        ローディング状態を取得

        Returns:
            bool: ローディング中かどうか
        """
        return self._is_loading

    def add_observer(self, observer):
        """
        オブザーバーを追加

        Args:
            observer: 通知を受け取るオブザーバー
        """
        if observer not in self._observers:
            self._observers.append(observer)
            self.logger.debug(f"オブザーバー追加: {observer.__class__.__name__}")

    def remove_observer(self, observer):
        """
        オブザーバーを削除

        Args:
            observer: 削除するオブザーバー
        """
        if observer in self._observers:
            self._observers.remove(observer)
            self.logger.debug(f"オブザーバー削除: {observer.__class__.__name__}")

    def _notify_observers(self):
        """オブザーバーに変更を通知"""
        self.logger.debug(f"オブザーバー通知: {len(self._observers)}件")
        for observer in self._observers:
            if hasattr(observer, "on_view_model_changed"):
                observer.on_view_model_changed()

    def _notify_observers_component(self, state: ComponentState, component_id: str):
        self.logger.debug(f"コンポーネント状態変更通知: {component_id}, 状態: {state}")
        for observer in self._observers:
            observer.on_component_state_changed(state, component_id)
