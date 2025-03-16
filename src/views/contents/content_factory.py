"""
コンテンツファクトリモジュール
各種コンテンツの生成を担当
"""

import flet as ft

from src.views.contents.home_content import HomeContent
from src.views.contents.preview_content import PreviewContent
from src.views.contents.settings_content import SettingsContent
from src.views.contents.task_content import TaskContent


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
        elif destination_key == "task":
            return TaskContent()
        else:
            # デフォルトのコンテンツ
            return ft.Text(f"不明なデスティネーション: {destination_key}", size=20)


def create_content(destination_key, contents_viewmodel):
    """
    指定された宛先キーに基づいてコンテンツを作成する

    Args:
        destination_key: 宛先キー
        contents_viewmodel: コンテンツのViewModel

    Returns:
        作成されたコンテンツ
    """
    if destination_key == "home":
        return HomeContent(contents_viewmodel)
    elif destination_key == "preview":
        return PreviewContent(contents_viewmodel)
    elif destination_key == "settings":
        return SettingsContent(contents_viewmodel)
    elif destination_key == "task":
        return TaskContent(contents_viewmodel)
    else:
        return ft.Text("不明なコンテンツ")
