"""
テキストとサブテキストを2行で表示し、右端に削除アイコンを持つコンポーネント
"""

import flet as ft


class TextWithSubtitleWithDeleteIcon(ft.Container):
    """
    メインテキストとサブテキストを2行で表示し、右端に削除アイコンを持つコンポーネント
    クリック可能で、コールバック機能を持ちます
    """

    def __init__(
        self,
        text: str,
        subtitle: str,
        on_delete=None,
        on_click=None,
        text_weight="normal",
        **kwargs,
    ):
        """
        TextWithSubtitleWithDeleteIconの初期化

        Args:
            text: メインテキスト
            subtitle: サブテキスト
            on_delete: 削除アイコンクリック時のコールバック関数
            on_click: コンポーネントクリック時のコールバック関数
            text_weight: テキストの太さ
            **kwargs: その他のキーワード引数
        """
        # 削除アイコンの作成
        self.delete_icon = ft.IconButton(
            icon=ft.icons.DELETE,
            icon_color=ft.colors.ERROR,
            on_click=on_delete,
            tooltip="削除",
            hover_color=ft.colors.with_opacity(0.1, ft.colors.ERROR),
            highlight_color=ft.colors.with_opacity(0.2, ft.colors.ERROR),
            splash_color=ft.colors.with_opacity(0.3, ft.colors.ERROR),
        )

        super().__init__(
            content=ft.Row(
                controls=[
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(
                                text,
                                size=16,
                                weight="bold",
                            ),
                            ft.Text(
                                subtitle,
                                size=14,
                                opacity=0.8,
                            ),
                        ],
                    ),
                    self.delete_icon,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=8,
            border_radius=4,
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
            # ホバー時のスタイル
            self.bgcolor = ft.colors.SURFACE_VARIANT
            self.border = ft.border.all(1, ft.colors.PRIMARY)
            self.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=4,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK),
            )
        else:
            # 通常時のスタイル
            self.bgcolor = ft.colors.SURFACE
            self.border = ft.border.all(1, ft.colors.OUTLINE)
            self.shadow = None
        self.update()

    def _on_delete_icon_hover(self, e):
        """削除アイコンのホバー時の処理"""
        if e.data == "true":
            # ホバー時のスタイル
            self.delete_icon.icon_color = ft.colors.ERROR_700
            self.delete_icon.bgcolor = ft.colors.with_opacity(0.1, ft.colors.ERROR)
        else:
            # 通常時のスタイル
            self.delete_icon.icon_color = ft.colors.ERROR
            self.delete_icon.bgcolor = None
        self.delete_icon.update()
