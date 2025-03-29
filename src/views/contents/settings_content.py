"""
設定コンテンツ
設定画面のコンテンツを提供するクラス
"""

import os

import flet as ft

from src.views.components.text_with_subtitle import TextWithSubtitle
from src.views.styles.style import AppTheme


class SettingsContent(ft.Container):
    """
    設定画面のコンテンツ
    TextWithSubtitleコンポーネントを使用したリストを表示
    """

    def __init__(self, contents_viewmodel):
        """初期化"""
        super().__init__()
        self.contents_viewmodel = contents_viewmodel

        # 親クラスの初期化
        self.content = self._init_contents()
        self.padding = AppTheme.PAGE_PADDING
        self.bgcolor = AppTheme.PAGE_BGCOLOR
        self.border_radius = AppTheme.CONTAINER_BORDER_RADIUS
        self.expand = True

    def _init_contents(self):
        """コンテンツの初期化"""

        def get_config_text(file_name):
            """設定テキストを取得"""
            config_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                ),
                "config",
                f"{file_name}.txt",
            )
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    return file.read()
            except Exception as e:
                print(f"Error reading {file_name}.txt: {e}")
                return ""

        def save_keywords(e):
            """keywordsテキストを保存"""
            config_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                ),
                "config",
                "keywords.txt",
            )
            try:
                with open(config_path, "w", encoding="utf-8") as file:
                    file.write(e.control.value)
            except Exception as e:
                print(f"Error saving keywords.txt: {e}")

        def save_prompt(e):
            """promptテキストを保存"""
            config_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                ),
                "config",
                "prompt.txt",
            )
            try:
                with open(config_path, "w", encoding="utf-8") as file:
                    file.write(e.control.value)
            except Exception as e:
                print(f"Error saving prompt.txt: {e}")

        left_text_field = ft.TextField(
            label="keywords",
            label_style=ft.TextStyle(size=18),
            value=get_config_text("keywords"),
            multiline=True,
            on_change=save_keywords,
            expand=1,
        )
        right_text_field = ft.TextField(
            label="prompt",
            label_style=ft.TextStyle(size=18),
            value=get_config_text("prompt"),
            multiline=True,
            on_change=save_prompt,
            expand=2,
        )
        content = ft.Row(
            [left_text_field, right_text_field],
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        return content
