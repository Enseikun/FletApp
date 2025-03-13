"""
コンテンツファクトリモジュール
各種コンテンツの生成を担当
"""

import flet as ft

from src.views.contents.home_content import HomeContent
from src.views.contents.preview_content import PreviewContent
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
        elif destination_key == "preview":
            return PreviewContent()
        elif destination_key == "settings":
            return SettingsContent()
        else:
            # デフォルトのコンテンツ
            return ft.Text(f"不明なデスティネーション: {destination_key}", size=20)


def create_content(destination_key: str, contents_viewmodel) -> ft.Container:
    """
    指定された destination_key に基づいてコンテンツを作成します

    Args:
        destination_key: 目的地を示すキー
        contents_viewmodel: コンテンツのビューモデル

    Returns:
        ft.Container: 作成されたコンテンツ
    """
    if destination_key == "home":
        return HomeContent(contents_viewmodel)
    elif destination_key == "preview":
        return PreviewContent(contents_viewmodel)
    elif destination_key == "settings":
        return SettingsContent(contents_viewmodel)
    else:
        return HomeContent(contents_viewmodel)
