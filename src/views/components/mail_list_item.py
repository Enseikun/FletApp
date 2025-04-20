"""
メールリストの各アイテムを表示するコンポーネント
"""

from typing import Callable, Dict, Optional

import flet as ft

from src.views.styles.style import AppTheme


class MailListItem(ft.Container):
    """
    メールリストの各アイテムを表示するコンポーネント
    メールのメタデータとプレビューを表示
    """

    def __init__(self, mail_data: Dict, on_click: Optional[Callable] = None, **kwargs):
        """
        MailListItemの初期化

        Args:
            mail_data: メールデータの辞書
            on_click: クリック時のコールバック
            **kwargs: その他のキーワード引数
        """
        self.mail_data = mail_data
        self.mail_id = mail_data["id"]

        # メールの状態を取得
        is_unread = mail_data.get("unread", 0)
        has_attachments = bool(mail_data.get("attachments", []))
        is_flagged = mail_data.get("flagged", False)

        # コンテンツの作成
        content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(
                                name=ft.icons.CIRCLE,
                                size=8,
                                color=(
                                    ft.colors.BLUE
                                    if is_unread
                                    else ft.colors.TRANSPARENT
                                ),
                            ),
                            width=15,
                        ),
                        ft.Text(
                            mail_data["date"],
                            size=12,
                            color=ft.colors.GREY,
                            width=100,
                        ),
                        ft.Text(
                            mail_data["sender"]
                            .split("<")[0]
                            .strip(),  # 名前部分のみ表示
                            size=12,
                            color=ft.colors.GREY,
                            expand=True,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                        # フラグアイコンを表示（フラグが立っている場合）
                        (
                            ft.Icon(
                                name=ft.icons.FLAG,
                                size=14,
                                color=ft.colors.RED,
                            )
                            if is_flagged
                            else ft.Container(width=0)
                        ),
                        # 添付ファイルアイコン（添付ファイルがある場合）
                        (
                            ft.Icon(
                                name=ft.icons.ATTACH_FILE,
                                size=14,
                                color=ft.colors.GREY,
                            )
                            if has_attachments
                            else ft.Container(width=0)
                        ),
                    ],
                ),
                ft.Text(
                    mail_data["subject"] or "(件名なし)",
                    weight="bold" if is_unread else "normal",
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    mail_data.get("preview", ""),
                    size=12,
                    color=ft.colors.GREY,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=2,
        )

        # Containerの初期化
        super().__init__(
            content=content,
            padding=ft.padding.all(8),
            border_radius=5,
            on_click=on_click,
            data=mail_data["id"],  # データプロパティに識別子を保存
            ink=True,  # インクエフェクト
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.BLACK12),
            margin=ft.margin.only(bottom=5),
            tooltip=f"{mail_data['subject']} - {mail_data['sender']}",  # ツールチップを追加
            shadow=(
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=2,
                    color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                    offset=ft.Offset(0, 1),
                )
                if is_unread
                else None
            ),  # 未読メールに影をつける
            **kwargs,
        )

    def mark_as_read(self):
        """メールを既読としてマーク"""
        # 未読マークを非表示にする
        row = self.content.controls[0]
        if isinstance(row, ft.Row) and len(row.controls) > 0:
            circle_container = row.controls[0]
            if hasattr(circle_container, "content") and isinstance(
                circle_container.content, ft.Icon
            ):
                circle_container.content.color = ft.colors.TRANSPARENT

        # 太字を通常に戻す（2番目の行に subject がある想定）
        if len(self.content.controls) > 1 and isinstance(
            self.content.controls[1], ft.Text
        ):
            self.content.controls[1].weight = "normal"

        # シャドウを削除
        self.shadow = None
        self.update()

    def set_selected(self, selected: bool):
        """選択状態を設定"""
        self.bgcolor = ft.colors.BLUE_50 if selected else ft.colors.WHITE
        self.update()

    def update_flag_status(self, is_flagged: bool):
        """フラグ状態を更新"""
        # 内部のデータも更新
        self.mail_data["flagged"] = is_flagged

        # UIを更新
        row = self.content.controls[0]
        if isinstance(row, ft.Row) and len(row.controls) > 3:
            # フラグアイコンの位置（インデックス3）を直接使用
            if is_flagged:
                # フラグがオンの場合はアイコンを表示
                row.controls[3] = ft.Icon(
                    name=ft.icons.FLAG,
                    size=14,
                    color=ft.colors.RED,
                )
            else:
                # フラグがオフの場合は幅0のコンテナ
                row.controls[3] = ft.Container(width=0)

        # Containerのツールチップを更新
        self.tooltip = f"{self.mail_data['subject']} - {self.mail_data['sender']}"
        if is_flagged:
            self.tooltip += " [フラグ付き]"

        self.update()
