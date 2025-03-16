"""
設定コンテンツ
設定画面のコンテンツを提供するクラス
"""

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
            with open(f"config/{file_name}.txt", "r") as file:
                return file.read()

        def save_keywords(e):
            """keywordsテキストを保存"""
            with open("config/keywords.txt", "w") as file:
                file.write(e.control.value)

        def save_prompt(e):
            """promptテキストを保存"""
            with open("config/prompt.txt", "w") as file:
                file.write(e.control.value)

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
