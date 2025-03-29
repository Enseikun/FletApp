"""
タスクリストの各アイテムを表示するコンポーネント
"""

from datetime import datetime

import flet as ft


class TaskListItem(ft.Container):
    """
    タスクの詳細情報を表示するコンポーネント
    ステータス、メール数、日時などの情報を表示し、クリックで詳細を展開/折りたたみ可能
    """

    def __init__(
        self,
        task_id: str,
        folder_name: str,
        status: str,
        mail_count: int,
        start_date: datetime,
        on_delete=None,
        on_click=None,
        **kwargs,
    ):
        """
        TaskListItemの初期化

        Args:
            task_id: タスクID
            folder_name: フォルダ名
            status: タスクのステータス
            mail_count: メール数
            start_date: 開始日時
            on_delete: 削除ボタンクリック時のコールバック
            on_click: コンポーネントクリック時のコールバック
            **kwargs: その他のキーワード引数
        """
        # ステータスに応じた色を設定
        status_colors = {
            "created": ft.colors.BLUE,
            "processing": ft.colors.ORANGE,
            "completed": ft.colors.GREEN,
            "error": ft.colors.RED,
        }
        status_color = status_colors.get(status, ft.colors.GREY)

        # ステータスバッジ
        self.status_badge = ft.Container(
            content=ft.Text(
                status.upper(),
                size=12,
                color=ft.colors.WHITE,
                weight=ft.FontWeight.BOLD,
            ),
            bgcolor=status_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
        )

        # メイン情報
        self.main_info = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            f"タスクID: {task_id}",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        self.status_badge,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(
                    folder_name,
                    size=14,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            f"メール数: {mail_count}",
                            size=12,
                            color=ft.colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            f"開始: {start_date.strftime('%Y-%m-%d %H:%M')}",
                            size=12,
                            color=ft.colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=4,
        )

        # 削除ボタン
        self.delete_button = ft.IconButton(
            icon=ft.icons.DELETE,
            icon_color=ft.colors.ERROR,
            on_click=on_delete,
            tooltip="削除",
        )

        # 詳細表示/非表示ボタン
        self.expand_button = ft.IconButton(
            icon=ft.icons.EXPAND_MORE,
            icon_color=ft.colors.ON_SURFACE_VARIANT,
            on_click=self._toggle_details,
            tooltip="詳細表示",
        )

        # 詳細情報（初期状態は非表示）
        self.details = ft.Column(
            controls=[
                ft.Divider(),
                ft.Text("詳細情報", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("フォルダパス: 詳細情報は展開時に表示", size=12),
                ft.Text("終了日時: 詳細情報は展開時に表示", size=12),
                ft.Text("設定情報: 詳細情報は展開時に表示", size=12),
            ],
            visible=False,
            spacing=4,
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.main_info,
                            self.expand_button,
                            self.delete_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.details,
                ],
                spacing=8,
            ),
            padding=12,
            border_radius=8,
            border=ft.border.all(1, ft.colors.OUTLINE),
            bgcolor=ft.colors.SURFACE,
            on_click=on_click,
            on_hover=self._on_hover,
            expand=True,
            **kwargs,
        )

    def _on_hover(self, e):
        """ホバー時の処理"""
        if e.data == "true":
            self.bgcolor = ft.colors.SURFACE_VARIANT
            self.border = ft.border.all(1, ft.colors.PRIMARY)
            self.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=4,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK),
            )
        else:
            self.bgcolor = ft.colors.SURFACE
            self.border = ft.border.all(1, ft.colors.OUTLINE)
            self.shadow = None
        self.update()

    def _toggle_details(self, e):
        """詳細情報の表示/非表示を切り替え"""
        self.details.visible = not self.details.visible
        self.expand_button.icon = (
            ft.icons.EXPAND_LESS if self.details.visible else ft.icons.EXPAND_MORE
        )
        self.update()

    def set_details(
        self,
        folder_path: str,
        end_date: datetime,
        ai_review: bool,
        file_download: bool,
        exclude_extensions: str,
        error_message: str = None,
    ):
        """詳細情報を設定"""
        details_text = [
            f"フォルダパス: {folder_path}",
            f"終了日時: {end_date.strftime('%Y-%m-%d %H:%M')}",
            f"AIレビュー: {'有効' if ai_review else '無効'}",
            f"ファイルダウンロード: {'有効' if file_download else '無効'}",
            f"除外拡張子: {exclude_extensions or 'なし'}",
        ]

        if error_message:
            details_text.append(f"エラー: {error_message}")

        self.details.controls = [
            ft.Divider(),
            ft.Text("詳細情報", size=14, weight=ft.FontWeight.BOLD),
        ] + [ft.Text(text, size=12) for text in details_text]
        self.update()
