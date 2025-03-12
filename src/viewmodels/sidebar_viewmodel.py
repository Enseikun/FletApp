"""
SideBarViewModelクラス
サイドバーのロジックを管理するビューモデル
"""


class SideBarViewModel:
    """
    SideBarのビューモデル
    サイドバーの選択状態とイベントを管理する
    """

    def __init__(self, main_viewmodel):
        """
        初期化

        Args:
            main_viewmodel (MainViewModel): メインビューモデルの参照
        """
        self._main_viewmodel = main_viewmodel

    def select_destination(self, destination_key):
        """
        デスティネーションを選択し、メインビューモデルに通知

        Args:
            destination_key (str): 選択されたデスティネーションキー
        """
        self._main_viewmodel.set_destination(destination_key)

    @property
    def current_destination(self):
        """現在選択されているデスティネーション"""
        return self._main_viewmodel.current_destination
