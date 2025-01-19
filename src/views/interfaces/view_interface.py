from abc import ABC, abstractmethod

import flet as ft


class ViewInterface(ABC, ft.View):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.initialize()

    @abstractmethod
    def initialize(self):
        """ビューの初期化処理"""
        pass

    def update_with_shared_data(self, data: dict):
        """共有データでビューを更新するメソッド"""
        pass
