"""
コンテンツファクトリー
各種コンテンツを生成するファクトリークラスと関数
"""

import flet as ft

from src.views.contents.home_content import HomeContent
from src.views.contents.menu_content import MenuContent
from src.views.contents.profile_content import ProfileContent
from src.views.contents.settings_content import SettingsContent


class ContentFactory:
    """
    コンテンツを生成するファクトリークラス
    """

    @staticmethod
    def create_content(destination_key):
        """
        指定されたデスティネーションキーに対応するコンテンツを作成する

        Args:
            destination_key (str): デスティネーションキー

        Returns:
            ft.Control: 作成されたコンテンツ
        """
        if destination_key == "home":
            return HomeContent()
        elif destination_key == "menu":
            return MenuContent()
        elif destination_key == "profile":
            return ProfileContent()
        elif destination_key == "settings":
            return SettingsContent()
        else:
            # デフォルトのコンテンツ
            return ft.Text(f"不明なデスティネーション: {destination_key}", size=20)


# クラスメソッドと同じ機能を持つ関数版（利便性のため）
def create_content(destination_key):
    """
    指定されたデスティネーションキーに対応するコンテンツを作成する

    Args:
        destination_key (str): デスティネーションキー

    Returns:
        ft.Control: 作成されたコンテンツ
    """
    return ContentFactory.create_content(destination_key)
