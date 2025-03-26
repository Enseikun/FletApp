"""
テキストとサブテキストを2行で表示するコンポーネント
"""

import flet as ft


class TextWithSubtitle(ft.Container):
    """
    メインテキストとサブテキストを2行で表示するコンポーネント
    クリック可能で、コールバック機能を持ちます
    """

    def __init__(
        self,
        text: str,
        subtitle: str,
        on_click=None,
        text_weight="normal",
        **kwargs,
    ):
        """
        TextWithSubtitleの初期化

        Args:
            text: メインテキスト
            subtitle: サブテキスト
            on_click: クリック時のコールバック関数
            text_weight: テキストの太さ
            **kwargs: その他のキーワード引数
        """
        super().__init__(
            content=ft.Column(
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
