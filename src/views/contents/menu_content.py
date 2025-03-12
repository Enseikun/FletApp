"""
メニューコンテンツ
メニュー画面のコンテンツを提供するクラス
"""

import flet as ft

from src.views.components.text_with_subtitle import TextWithSubtitle
from src.views.styles.style import AppTheme


class MenuContent(ft.Container):
    """
    メニュー画面のコンテンツ
    TextWithSubtitleコンポーネントを使用したメニューリストを表示
    """

    def __init__(self):
        """初期化"""

        # TextWithSubtitleコンポーネントのクリックハンドラ
        def on_item_click(e):
            print(f"アイテムがクリックされました: {e.control.text}")

        # ダミーデータを使ったTextWithSubtitleコンポーネント
        items = [
            TextWithSubtitle(
                text="プロジェクト管理",
                subtitle="タスクの追加、編集、削除ができます",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="スケジュール",
                subtitle="予定の確認と管理を行います",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="設定",
                subtitle="アプリケーションの設定を変更します",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="ヘルプ",
                subtitle="使い方とよくある質問",
                on_click_callback=on_item_click,
                enable_hover=False,
            ),
            TextWithSubtitle(
                text="ログアウト",
                subtitle="アカウントからログアウトします",
                on_click_callback=on_item_click,
                activate=True,
            ),
        ]

        # 無効化されたアイテムの例
        disabled_item = TextWithSubtitle(
            text="メンテナンス中",
            subtitle="この機能は現在利用できません",
            on_click_callback=on_item_click,
            enabled=False,
        )

        # アイテムを縦に並べるカラム
        items_column = ft.Column(
            spacing=AppTheme.SPACING_MD,
            controls=items + [disabled_item],
        )

        # メインコンテンツ
        content = ft.Column(
            controls=[
                ft.Text("メニュー", size=AppTheme.TITLE_SIZE, weight="bold"),
                ft.Divider(),
                items_column,
            ],
            spacing=AppTheme.SPACING_MD,
        )

        # 親クラスの初期化
        super().__init__(
            content=content,
            padding=AppTheme.PAGE_PADDING,
            bgcolor=AppTheme.PAGE_BGCOLOR,
            border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
            width=400,
        )
