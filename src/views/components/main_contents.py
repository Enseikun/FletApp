"""
メインコンテンツコンポーネント
アプリケーションのメインコンテンツ領域を管理
"""

import flet as ft

from src.views.components.text_with_subtitle import TextWithSubtitle
from src.views.contents.content_factory import create_content
from src.views.styles.style import AppTheme


class MainContents(ft.Container):
    """
    アプリケーションのメインコンテンツ
    サイドバーの選択に応じて表示内容を切り替える
    """

    def __init__(self, main_viewmodel=None):
        """
        初期化

        Args:
            main_viewmodel (MainViewModel, optional): メインビューモデル
        """
        self.main_viewmodel = main_viewmodel
        self.current_content = None

        # 親クラスの初期化
        super().__init__(
            content=ft.Text("コンテンツを読み込み中..."), expand=True, padding=10
        )

        # ビューモデルが提供されている場合、コールバックを登録
        if self.main_viewmodel:
            self.main_viewmodel.add_destination_changed_callback(self.update_content)

    def update_content(self, destination_key):
        """
        表示するコンテンツを更新

        Args:
            destination_key (str): 表示するコンテンツのキー
        """
        # コンテンツファクトリからコンテンツを取得
        new_content = create_content(destination_key)

        # コンテンツを更新
        self.content = new_content
        self.current_content = new_content
        self.update()

    def create_content_for_destination(self, destination_key):
        """
        指定されたDestination用のコンテンツを作成する

        Args:
            destination_key: Destinationのキー

        Returns:
            作成されたコンテンツ
        """
        # 各Destinationに応じたコンテンツを作成
        if destination_key == "home":
            return ft.Column(
                [
                    ft.Text("ホーム画面", size=24, weight=ft.FontWeight.BOLD),
                    ft.TextField(label="検索", width=300),
                    ft.ElevatedButton("検索"),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
            )

        elif destination_key == "settings":
            return ft.Column(
                [
                    ft.Text("設定画面", size=24, weight=ft.FontWeight.BOLD),
                    ft.Switch(label="ダークモード"),
                    ft.Dropdown(
                        label="言語",
                        options=[
                            ft.dropdown.Option("日本語"),
                            ft.dropdown.Option("English"),
                        ],
                        width=200,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
            )

        elif destination_key == "profile":
            return ft.Column(
                [
                    ft.Text("プロフィール画面", size=24, weight=ft.FontWeight.BOLD),
                    ft.TextField(label="ユーザー名", width=300),
                    ft.TextField(label="メールアドレス", width=300),
                    ft.ElevatedButton("保存"),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
            )

        elif destination_key == "menu":
            return self.build_text_with_subtitle_section()

        # デフォルトのコンテンツ
        return ft.Text(f"不明なDestination: {destination_key}", size=20)

    def build_text_with_subtitle_section(self):
        """ダミーテキストを使ったTextWithSubtitleコンポーネントのセクションを構築"""

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

        # メインコンテナ
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("メニュー", size=AppTheme.TITLE_SIZE, weight="bold"),
                    ft.Divider(),
                    items_column,
                ],
                spacing=AppTheme.SPACING_MD,
            ),
            padding=AppTheme.PAGE_PADDING,
            bgcolor=AppTheme.PAGE_BGCOLOR,
            border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
            width=400,
        )
