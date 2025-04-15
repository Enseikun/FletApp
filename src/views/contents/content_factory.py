"""
コンテンツファクトリモジュール
各種コンテンツの生成を担当
"""

import flet as ft

from src.core.logger import get_logger
from src.views.contents.home_content import HomeContent
from src.views.contents.preview_content import PreviewContent
from src.views.contents.settings_content import SettingsContent
from src.views.contents.task_content import TaskContent

# 現在のコンテンツを管理するためのグローバル変数
_current_contents = []


class ContentFactory:
    """
    コンテンツを生成するファクトリークラス
    """

    @staticmethod
    def create_content(destination_key, contents_viewmodel=None):
        """
        指定されたデスティネーションキーに対応するコンテンツを作成する

        Args:
            destination_key (str): デスティネーションキー
            contents_viewmodel: コンテンツのViewModel

        Returns:
            ft.Control: 作成されたコンテンツ
        """
        logger = get_logger()
        logger.debug(f"ContentFactory: コンテンツ作成リクエスト - {destination_key}")

        content = None
        if destination_key == "home":
            logger.info(
                f"HomeContentを作成 (ViewModel: {'あり' if contents_viewmodel else 'なし'})"
            )
            content = HomeContent(contents_viewmodel)
        elif destination_key == "preview":
            logger.info(
                f"PreviewContentを作成 (ViewModel: {'あり' if contents_viewmodel else 'なし'})"
            )
            content = PreviewContent(contents_viewmodel)
        elif destination_key == "settings":
            logger.info(
                f"SettingsContentを作成 (ViewModel: {'あり' if contents_viewmodel else 'なし'})"
            )
            content = SettingsContent(contents_viewmodel)
        elif destination_key == "task":
            logger.info(
                f"TaskContentを作成 (ViewModel: {'あり' if contents_viewmodel else 'なし'})"
            )
            content = TaskContent(contents_viewmodel)
        else:
            # デフォルトのコンテンツ
            logger.warning(f"不明なデスティネーション: {destination_key}")
            content = ft.Text(f"不明なデスティネーション: {destination_key}", size=20)

        # コンテンツを生成したら、グローバル変数に追加
        global _current_contents
        _current_contents.append(content)

        # リストが大きくなりすぎないように古いものを削除
        if len(_current_contents) > 10:  # 最大10個まで保持
            _current_contents = _current_contents[-10:]

        return content


# 後方互換性のための関数
def create_content(destination_key, contents_viewmodel=None):
    """
    指定された宛先キーに基づいてコンテンツを作成する
    ContentFactoryクラスのラッパー関数

    Args:
        destination_key: 宛先キー
        contents_viewmodel: コンテンツのViewModel

    Returns:
        作成されたコンテンツ
    """
    return ContentFactory.create_content(destination_key, contents_viewmodel)


def get_current_contents():
    """
    現在管理されているコンテンツのリストを取得

    Returns:
        list: 現在管理されているコンテンツのリスト
    """
    global _current_contents
    return _current_contents
