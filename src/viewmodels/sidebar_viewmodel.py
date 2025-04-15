"""
サイドバーのビューモデル
サイドナビゲーションの状態を管理
"""

from typing import Callable, List, Optional


class SideBarViewModel:
    """
    サイドバーのビューモデル
    サイドナビゲーションの状態を管理するクラス
    """

    def __init__(self, main_viewmodel=None):
        """
        初期化

        Args:
            main_viewmodel (MainViewModel, optional): メインビューモデル
        """
        self._main_viewmodel = main_viewmodel
        self._selected_destination = "home"
        self._observers = []

        # MainViewModelにこのインスタンスを設定
        if self._main_viewmodel:
            self._main_viewmodel.set_sidebar_viewmodel(self)

    def select_destination(self, destination_key: str) -> None:
        """
        デスティネーションを選択

        Args:
            destination_key: デスティネーションキー
        """
        self._selected_destination = destination_key
        if self._main_viewmodel:
            self._main_viewmodel.set_destination(destination_key)

    def get_selected_destination(self) -> str:
        """
        選択されているデスティネーションを取得

        Returns:
            選択されているデスティネーションキー
        """
        return self._selected_destination

    def update_selected_destination(self, destination_key: str) -> None:
        """
        選択されているデスティネーションを更新（内部状態のみ）

        Args:
            destination_key: デスティネーションキー
        """
        print(f"SideBarViewModel: デスティネーション更新 - {destination_key}")
        self._selected_destination = destination_key
        self._notify_observers()

    def add_observer(self, observer) -> None:
        """
        オブザーバーを追加

        Args:
            observer: 通知を受け取るオブザーバー
        """
        if observer not in self._observers:
            self._observers.append(observer)
            print(f"SideBarViewModel: オブザーバー追加 - {observer.__class__.__name__}")

    def remove_observer(self, observer) -> None:
        """
        オブザーバーを削除

        Args:
            observer: 登録済みのオブザーバー
        """
        if observer in self._observers:
            self._observers.remove(observer)
            print(f"SideBarViewModel: オブザーバー削除 - {observer.__class__.__name__}")

    def _notify_observers(self) -> None:
        """
        全てのオブザーバーに変更を通知
        """
        for observer in self._observers:
            if hasattr(observer, "update_selected_destination"):
                observer.update_selected_destination(self._selected_destination)
            elif hasattr(observer, "on_sidebar_viewmodel_changed"):
                observer.on_sidebar_viewmodel_changed()
