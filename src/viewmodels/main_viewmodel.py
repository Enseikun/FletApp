"""
MainViewModelクラス
アプリケーションのメイン画面のロジックを管理するビューモデル
"""


class MainViewModel:
    """
    MainViewのビューモデル
    サイドバーとメインコンテンツの連携を管理する
    """

    def __init__(self):
        self._current_destination = None
        self._destination_changed_callbacks = []

    @property
    def current_destination(self):
        """現在選択されているデスティネーション"""
        return self._current_destination

    def set_destination(self, destination_key):
        """
        デスティネーションを変更し、登録されたコールバックを呼び出す

        Args:
            destination_key (str): 変更先のデスティネーションキー
        """
        if self._current_destination != destination_key:
            self._current_destination = destination_key
            self._notify_destination_changed()

    def add_destination_changed_callback(self, callback):
        """
        デスティネーション変更時のコールバックを登録

        Args:
            callback (callable): デスティネーション変更時に呼び出される関数
        """
        if callback not in self._destination_changed_callbacks:
            self._destination_changed_callbacks.append(callback)

    def remove_destination_changed_callback(self, callback):
        """
        登録済みのコールバックを削除

        Args:
            callback (callable): 削除するコールバック関数
        """
        if callback in self._destination_changed_callbacks:
            self._destination_changed_callbacks.remove(callback)

    def _notify_destination_changed(self):
        """登録されたすべてのコールバックを呼び出す"""
        for callback in self._destination_changed_callbacks:
            callback(self._current_destination)

    def set_initial_destination(self, destination):
        """
        コールバックを呼ばずに初期デスティネーションを設定

        Args:
            destination (str): 設定するデスティネーション
        """
        self._current_destination = destination
