import flet as ft

from src.views.components.text_with_subtitle import TextWithSubtitle
from src.views.styles.style import AppTheme


class HomeContent(ft.Container):
    """
    ホーム画面のコンテンツ
    TextWithSubtitleコンポーネントを使用したリストを表示
    """

    def __init__(self, contents_viewmodel):
        """初期化"""

        super().__init__()
        self.contents_viewmodel = contents_viewmodel

        # TextWithSubtitleコンポーネントのクリックハンドラ
        def on_item_click(e):
            # TextWithSubtitleのインスタンスを取得
            component = e.control
            # コンポーネントのtext属性を安全に取得
            text = getattr(component, "text", "不明なアイテム")
            print(f"ホームアイテムがクリックされました: {text}")

        # ダミーのホームメニュー項目
        items = [
            TextWithSubtitle(
                text="最近の活動",
                subtitle="過去7日間の活動履歴を表示します",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="お気に入り",
                subtitle="お気に入りに登録したコンテンツ",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="通知",
                subtitle="未読の通知が3件あります",
                on_click_callback=on_item_click,
                activate=True,
            ),
            TextWithSubtitle(
                text="統計情報",
                subtitle="利用状況の統計を表示します",
                on_click_callback=on_item_click,
            ),
            TextWithSubtitle(
                text="ヘルプとサポート",
                subtitle="困ったときはこちら",
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
                ft.Text("ホーム", size=AppTheme.TITLE_SIZE, weight="bold"),
                ft.Divider(),
                ft.Text("メニュー", size=18, weight="bold"),
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
