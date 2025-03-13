"""
プレビューコンテンツ
プレビュー画面のコンテンツを提供するクラス
"""

import flet as ft

from src.views.components.text_with_subtitle import TextWithSubtitle
from src.views.styles.style import AppTheme


class PreviewContent(ft.Container):
    """
    プレビュー画面のコンテンツ
    TextWithSubtitleコンポーネントを使用したリストを表示
    """

    def __init__(self, contents_viewmodel):
        """初期化"""
        # 親クラスを先に初期化
        super().__init__()
        self.contents_viewmodel = contents_viewmodel

        # TextWithSubtitleコンポーネントのクリックハンドラ
        def on_item_click(e):
            # TextWithSubtitleのインスタンスを取得
            component = e.control
            # コンポーネントのtext属性を安全に取得
            text = getattr(component, "text", "不明なアイテム")
            print(f"プレビューアイテムがクリックされました: {text}")

        # ダミーのプレビューメニュー項目
        items = [
            TextWithSubtitle(
                text="ドキュメント",
                subtitle="プロジェクトのドキュメントを表示します",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="画像ギャラリー",
                subtitle="保存された画像を閲覧します",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="データ分析",
                subtitle="収集したデータの分析結果",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="レポート",
                subtitle="月次レポートを生成します",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="エクスポート",
                subtitle="データをエクスポートします",
                on_click_callback=on_item_click,
                enabled=False,
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
                ft.Text("プレビュー", size=AppTheme.TITLE_SIZE, weight="bold"),
                ft.Divider(),
                ft.Text("利用可能なプレビュー", size=18, weight="bold"),
                items_column,
            ],
            spacing=AppTheme.SPACING_MD,
            scroll=ft.ScrollMode.AUTO,
        )

        # プロパティを後から設定
        self.content = content
        self.padding = AppTheme.PAGE_PADDING
        self.bgcolor = AppTheme.PAGE_BGCOLOR
        self.border_radius = AppTheme.CONTAINER_BORDER_RADIUS
        self.expand = True
