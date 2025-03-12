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

    def __init__(self):
        """初期化"""

        super().__init__()

        # TextWithSubtitleコンポーネントのクリックハンドラ
        def on_item_click(e):
            print(f"設定アイテムがクリックされました: {e.control.text}")

        # ダミーの設定メニュー項目
        items = [
            TextWithSubtitle(
                text="アカウント設定",
                subtitle="ユーザー情報とプロフィールの管理",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="表示設定",
                subtitle="テーマやレイアウトのカスタマイズ",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="通知設定",
                subtitle="通知の受信方法と頻度の設定",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="プライバシー",
                subtitle="プライバシーとセキュリティの設定",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="ヘルプ",
                subtitle="サポート情報とよくある質問",
                on_click_callback=on_item_click,
            ),
        ]

        # アイテムを縦に並べるカラム
        items_column = ft.Column(
            spacing=AppTheme.SPACING_MD,
            controls=items,
        )

        # メインコンテンツ
        content = ft.Column(
            controls=[
                ft.Text("設定", size=AppTheme.TITLE_SIZE, weight="bold"),
                ft.Divider(),
                ft.Text("設定オプション", size=18, weight="bold"),
                items_column,
            ],
            spacing=AppTheme.SPACING_MD,
            scroll=ft.ScrollMode.AUTO,
        )

        # 親クラスの初期化
        self.content = content
        self.padding = AppTheme.PAGE_PADDING
        self.bgcolor = AppTheme.PAGE_BGCOLOR
        self.border_radius = AppTheme.CONTAINER_BORDER_RADIUS
        self.expand = True
