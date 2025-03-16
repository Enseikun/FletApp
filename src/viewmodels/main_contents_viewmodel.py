from typing import Optional

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
        self.main_viewmodel = main_viewmodel
        self.current_task_id = None
        self._observers = []

    def set_current_task_id(self, task_id):
        """現在のタスクIDを設定"""
        self.current_task_id = task_id
        self._notify_observers()

    def get_current_task_id(self):
        """現在のタスクIDを取得"""
        return self.current_task_id

    def add_observer(self, observer):
        """
        オブザーバーを追加

        Args:
            observer: 通知を受け取るオブザーバー
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        """
        オブザーバーを削除

        Args:
            observer: 削除するオブザーバー
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self):
        """オブザーバーに変更を通知"""
        for observer in self._observers:
            if hasattr(observer, "on_view_model_changed"):
                observer.on_view_model_changed()

    def _notify_observers_component(self, state: ComponentState, component_id: str):
        for observer in self._observers:
            observer.on_component_state_changed(state, component_id)
