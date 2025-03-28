"""
プレビューコンテンツ
メールプレビュー画面のコンテンツを提供するクラス
"""

import asyncio
from typing import Any, Dict, List, Optional

import flet as ft

from src.core.logger import get_logger
from src.viewmodels.preview_content_viewmodel import PreviewContentViewModel
from src.views.styles.style import AppTheme


class PreviewContent(ft.Container):
    """
    メールプレビュー画面のコンテンツ
    左側にメールリスト、右側に選択したメールのプレビューを表示
    """

    def __init__(self, contents_viewmodel):
        """初期化"""
        super().__init__()
        self.contents_viewmodel = contents_viewmodel  # ViewModelへの参照を保持
        self.logger = get_logger()
        self.logger.info("PreviewContent: 初期化開始")

        # 初期化時にはタスクIDを取得しない
        # ViewModelの初期化も遅延させる
        self.viewmodel = None
        self.task_id = None

        # 会話ごとに集約するフラグ
        self.group_by_conversation = False

        # 会話表示の時系列ソート順（True: 新しい順、False: 古い順）
        self.conversation_sort_newest_first = True

        # メール一覧のソート順
        self.mail_sort_order = "date_desc"

        # 会話グループのコンテナを保存する辞書
        self.conversation_containers = {}

        # 検索フィールド
        self.search_field = ft.TextField(
            hint_text="メールを検索...",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_submit=self.on_search,
            border_radius=20,
            height=40,
        )

        # メールリスト
        self.mail_list = ft.ListView(
            expand=True,
            spacing=2,
            padding=5,
        )

        # メール内容表示
        self.mail_content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        # UIを構築
        self._build()
        self.logger.info("PreviewContent: 初期化完了")

        # サンプルデータフラグ
        self.use_sample_data = True

    def _build(self):
        """UIを構築"""
        self.logger.debug("PreviewContent: UI構築開始")

        # 左側のペイン（メールリスト）
        left_pane = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("メール一覧", weight="bold", size=16),
                                ft.IconButton(
                                    icon=ft.icons.REFRESH,
                                    tooltip="更新",
                                    on_click=lambda _: self.load_all_mails(),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=ft.padding.only(left=10, top=10, right=10, bottom=5),
                    ),
                    ft.Container(
                        content=self.search_field,
                        padding=ft.padding.only(left=10, right=10, bottom=5),
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("会話ごとに集約:", size=12),
                                ft.Switch(
                                    value=False,
                                    on_change=self.on_group_by_conversation_changed,
                                    scale=0.8,
                                ),
                                ft.IconButton(
                                    icon=ft.icons.HELP_OUTLINE,
                                    tooltip="同じ件名のメールをまとめて表示します",
                                    icon_size=16,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=ft.padding.only(left=10, right=10, bottom=5),
                    ),
                    ft.Container(
                        content=self.mail_list,
                        expand=True,
                        border=ft.border.all(1, ft.colors.BLACK12),
                        border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
                        padding=5,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=1,
        )

        # 右側のペイン（メール内容表示）
        right_pane = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text("メールプレビュー", weight="bold", size=16),
                        padding=ft.padding.only(left=10, top=10, right=10, bottom=10),
                    ),
                    ft.Container(
                        content=self.mail_content,
                        expand=True,
                        border=ft.border.all(1, ft.colors.BLACK12),
                        border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
                        padding=10,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=2,
        )

        # メインコンテンツ
        self.content = ft.Column(
            [
                ft.Row(
                    [left_pane, right_pane],
                    spacing=10,
                    expand=True,
                ),
            ],
            spacing=10,
            expand=True,
        )

        self.padding = 20
        self.expand = True
        self.bgcolor = ft.colors.WHITE
        self.logger.debug("PreviewContent: UI構築完了")

    def on_close_button_click(self, e):
        """終了ボタンがクリックされたときの処理"""
        self.logger.info("PreviewContent: 終了ボタンクリック")

        # コンテンツビューモデルに戻る処理を委譲
        if hasattr(self.contents_viewmodel, "show_home"):
            self.contents_viewmodel.show_home()
        elif hasattr(self.contents_viewmodel, "main_viewmodel") and hasattr(
            self.contents_viewmodel.main_viewmodel, "show_home"
        ):
            self.contents_viewmodel.main_viewmodel.show_home()
        else:
            self.logger.error("PreviewContent: ホーム画面に戻る処理が見つかりません")

    def did_mount(self):
        """コンポーネントがマウントされた時の処理"""
        self.logger.info("PreviewContent: マウント処理開始")

        # タスクIDを取得
        self.task_id = self._get_task_id()
        self.logger.debug("PreviewContent: タスクID取得", task_id=self.task_id)

        # ViewModelを初期化
        self.viewmodel = PreviewContentViewModel(self.task_id)

        # サンプルデータを使用するフラグをViewModelから取得
        self.use_sample_data = self.viewmodel.use_sample_data
        self.logger.debug(
            "PreviewContent: サンプルデータ使用フラグ設定",
            use_sample=self.use_sample_data,
        )

        # データを読み込む
        self.load_data()
        self.logger.info("PreviewContent: マウント処理完了")

    def load_data(self):
        """データを読み込む"""
        self.logger.info("PreviewContent: データ読み込み開始")

        # サンプルデータを使用する場合
        if self.use_sample_data:
            self.logger.debug("PreviewContent: サンプルデータを使用")
            self.load_sample_data()
            return

        if self.task_id:
            self.logger.debug("PreviewContent: タスクID有効", task_id=self.task_id)
            # ViewModelを初期化
            self.viewmodel = PreviewContentViewModel(self.task_id)

            try:
                # タスク情報を取得して表示を更新
                task_info = self.viewmodel.get_task_info()
                if task_info:
                    task_name = task_info.get("name", "不明なタスク")
                    self.logger.debug(
                        "PreviewContent: タスク情報取得", task_name=task_name
                    )

                # すべてのメールを読み込む
                self.load_all_mails()
                self.logger.info("PreviewContent: データ読み込み完了")
            except Exception as e:
                self.logger.error("PreviewContent: データ読み込みエラー", error=str(e))
                self.show_error_message(f"データ読み込みエラー: {str(e)}")
        else:
            self.logger.error("PreviewContent: 有効なタスクIDがありません")
            self.show_error_message("有効なタスクIDがありません")

        self.update()
        self.logger.info("PreviewContent: すべてのメール読み込み完了")

    def _get_task_id(self):
        """タスクIDを取得する内部メソッド"""
        task_id = None

        # 直接contents_viewmodelからtask_idを取得
        if hasattr(self.contents_viewmodel, "get_current_task_id"):
            task_id = self.contents_viewmodel.get_current_task_id()
            self.logger.debug(
                "PreviewContent: contents_viewmodelからタスクID取得", task_id=task_id
            )

        # main_viewmodelからも取得を試みる
        if (
            task_id is None
            and hasattr(self.contents_viewmodel, "main_viewmodel")
            and self.contents_viewmodel.main_viewmodel
        ):
            if hasattr(self.contents_viewmodel.main_viewmodel, "get_current_task_id"):
                task_id = self.contents_viewmodel.main_viewmodel.get_current_task_id()
                self.logger.debug(
                    "PreviewContent: main_viewmodelからタスクID取得", task_id=task_id
                )

        # デバッグ用に追加のログを出力
        if task_id is None:
            self.logger.error("PreviewContent: タスクIDの取得に失敗しました")
            # contents_viewmodelの状態を確認
            if hasattr(self.contents_viewmodel, "current_task_id"):
                self.logger.debug(
                    "PreviewContent: contents_viewmodel.current_task_id",
                    value=self.contents_viewmodel.current_task_id,
                )

        return task_id

    def load_all_mails(self):
        """すべてのメールを読み込む"""
        self.logger.info("PreviewContent: すべてのメール読み込み開始")
        if not self.viewmodel and not self.use_sample_data:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # メールリストをクリア
        self.mail_list.controls.clear()

        # サンプルデータを使用する場合
        if self.use_sample_data:
            # ViewModelからメールデータを取得（ソート順指定を削除）
            mails = self.viewmodel.get_all_mails()
            self.logger.debug(
                "PreviewContent: サンプルメール取得完了", mail_count=len(mails)
            )

            # デバッグログを追加
            self.logger.debug(
                "PreviewContent: 会話集約モード",
                group_by_conversation=self.group_by_conversation,
            )

            # 会話ごとに集約する場合
            if self.group_by_conversation:
                self._display_grouped_mails(mails)
            else:
                # 通常表示
                for mail in mails:
                    mail_item = self._create_mail_item(mail)
                    self.mail_list.controls.append(mail_item)
        else:
            # すべてのメールを取得（ソート順指定を削除）
            mails = self.viewmodel.get_all_mails()
            self.logger.debug("PreviewContent: メール取得完了", mail_count=len(mails))

            # メール一覧を表示
            if mails:
                # 会話ごとに集約する場合
                if self.group_by_conversation:
                    self._display_grouped_mails(mails)
                else:
                    # 通常表示
                    for mail in mails:
                        mail_item = self._create_mail_item(mail)
                        self.mail_list.controls.append(mail_item)
            else:
                # データがない場合の表示を改善
                self.mail_list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    name=ft.icons.EMAIL_OUTLINED,
                                    size=40,
                                    color=ft.colors.GREY,
                                ),
                                ft.Text(
                                    "メールはありません",
                                    color=ft.colors.GREY,
                                    text_align=ft.TextAlign.CENTER,
                                    weight="bold",
                                ),
                                ft.Text(
                                    "このタスクにはメールデータが登録されていません",
                                    color=ft.colors.GREY,
                                    size=12,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        alignment=ft.alignment.center,
                        expand=True,
                    )
                )

        # メール内容表示をクリア
        self._show_empty_mail_content()

        # 明示的に更新
        self.update()
        self.logger.info("PreviewContent: すべてのメール読み込み完了")

    def _create_mail_item(self, mail):
        """メールアイテムを作成"""
        is_unread = mail.get("unread", 0)
        has_attachments = bool(mail.get("attachments", []))
        is_flagged = mail.get("flagged", False)  # フラグ状態を取得

        return ft.Container(
            content=ft.Column(
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
                                mail["date"],
                                size=12,
                                color=ft.colors.GREY,
                                width=100,
                            ),
                            ft.Text(
                                mail["sender"]
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
                        mail["subject"] or "(件名なし)",
                        weight="bold" if is_unread else "normal",
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        mail.get("preview", ""),
                        size=12,
                        color=ft.colors.GREY,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=2,
            ),
            padding=ft.padding.all(8),
            border_radius=5,
            on_click=lambda e, mail_id=mail["id"]: self.show_mail_content(mail_id),
            ink=True,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.BLACK12),
            margin=ft.margin.only(bottom=5),
        )

    def _show_empty_mail_content(self):
        """空のメール内容表示"""
        self.mail_content.controls.clear()
        self.mail_content.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.EMAIL_OUTLINED,
                            size=40,
                            color=ft.colors.GREY,
                        ),
                        ft.Text(
                            "メールを選択してください",
                            color=ft.colors.GREY,
                            text_align=ft.TextAlign.CENTER,
                            weight="bold",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )

    def on_search(self, e):
        """検索実行時の処理"""
        search_term = self.search_field.value
        self.logger.info("PreviewContent: 検索実行", search_term=search_term)
        if not search_term:
            self.load_all_mails()
            return

        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # メールリストをクリア
        self.mail_list.controls.clear()

        # 検索を実行
        mails = self.viewmodel.search_mails(search_term)
        self.logger.debug("PreviewContent: 検索結果取得", result_count=len(mails))

        # 検索結果を表示
        if mails:
            for mail in mails:
                mail_item = self._create_mail_item(mail)
                self.mail_list.controls.append(mail_item)
        else:
            self.mail_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                name=ft.icons.SEARCH_OFF,
                                size=40,
                                color=ft.colors.GREY,
                            ),
                            ft.Text(
                                f"「{search_term}」に一致するメールはありません",
                                color=ft.colors.GREY,
                                text_align=ft.TextAlign.CENTER,
                                weight="bold",
                            ),
                            ft.TextButton(
                                text="すべてのメールを表示",
                                on_click=lambda _: self.load_all_mails(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                )
            )

        self.update()
        self.logger.info("PreviewContent: 検索完了", search_term=search_term)

    def show_mail_content(self, mail_id):
        """メール内容を表示"""
        self.logger.info("PreviewContent: メール内容表示", mail_id=mail_id)

        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # メール内容を取得
        mail = self.viewmodel.get_mail_content(mail_id)
        if not mail:
            self.logger.error("PreviewContent: メール内容取得失敗", mail_id=mail_id)
            return

        # メールを既読にする
        if mail.get("unread", 0):
            self.viewmodel.mark_as_read(mail_id)
            self.logger.debug("PreviewContent: メールを既読に設定", mail_id=mail_id)
            # メールリストを更新して既読状態を反映
            self.load_all_mails()

        # メール内容表示をクリア
        self.mail_content.controls.clear()

        # 送信者情報を解析
        sender_name = mail["sender"].split("<")[0].strip()
        sender_email = (
            mail["sender"].split("<")[1].replace(">", "")
            if "<" in mail["sender"]
            else mail["sender"]
        )

        # 受信者情報を解析
        recipient_name = mail.get("recipient", "").split("<")[0].strip()
        recipient_email = (
            mail.get("recipient", "").split("<")[1].replace(">", "")
            if "<" in mail.get("recipient", "")
            else mail.get("recipient", "")
        )

        # 添付ファイルがあれば表示用のリストを作成
        attachments_section = []
        if mail.get("attachments"):
            attachments = mail["attachments"]
            attachments_list = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    name=ft.icons.ATTACH_FILE,
                                    size=16,
                                    color=ft.colors.BLUE,
                                ),
                                ft.Text("添付ファイル", weight="bold"),
                            ],
                            spacing=5,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            self._get_file_icon(attachment["name"]),
                                            ft.Text(attachment["name"]),
                                            ft.Text(
                                                self._get_file_type(attachment["name"]),
                                                size=12,
                                                color=ft.colors.GREY,
                                            ),
                                        ],
                                        spacing=10,
                                    )
                                    for attachment in attachments
                                ],
                                spacing=5,
                            ),
                            padding=10,
                        ),
                    ],
                    spacing=5,
                ),
                padding=10,
                border=ft.border.all(1, ft.colors.BLACK12),
                border_radius=5,
                margin=ft.margin.only(top=10),
            )
            attachments_section = [attachments_list]

        # メール内容を表示
        self.mail_content.controls.extend(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        mail["subject"] or "(件名なし)",
                                        size=18,
                                        weight="bold",
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.FLAG_OUTLINED,
                                        tooltip="問題のあるメールとしてフラグを立てる",
                                        icon_color=ft.colors.GREY,
                                        on_click=lambda e, mail_id=mail[
                                            "id"
                                        ]: self._toggle_flag(e, mail_id),
                                        data={"flagged": False, "mail_id": mail["id"]},
                                    ),
                                ],
                            ),
                            ft.Divider(height=1, color=ft.colors.BLACK12),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        "送信者:",
                                                        weight="bold",
                                                        width=80,
                                                    ),
                                                    ft.Text(
                                                        f"{sender_name} <{sender_email}>"
                                                    ),
                                                ],
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        "宛先:", weight="bold", width=80
                                                    ),
                                                    ft.Text(
                                                        f"{recipient_name} <{recipient_email}>"
                                                    ),
                                                ],
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        "日時:", weight="bold", width=80
                                                    ),
                                                    ft.Text(mail["date"]),
                                                ],
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=10,
                    bgcolor=ft.colors.WHITE,
                    border_radius=5,
                    border=ft.border.all(1, ft.colors.BLACK12),
                ),
                *attachments_section,
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "本文:",
                                weight="bold",
                            ),
                            ft.Container(
                                content=ft.Text(mail["content"]),
                                padding=10,
                                bgcolor=ft.colors.WHITE,
                                border_radius=5,
                                border=ft.border.all(1, ft.colors.BLACK12),
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                    margin=ft.margin.only(top=10),
                    expand=True,
                ),
            ]
        )

        # メールリスト内の該当アイテムの背景色を変更して選択状態を示す
        for item in self.mail_list.controls:
            if hasattr(item, "on_click") and item.on_click.__closure__:
                for cell in item.on_click.__closure__:
                    if hasattr(cell, "cell_contents") and cell.cell_contents == mail_id:
                        item.bgcolor = ft.colors.BLUE_50
                    else:
                        item.bgcolor = ft.colors.WHITE

        self.update()
        self.logger.info("PreviewContent: メール内容表示完了", mail_id=mail_id)

    def download_attachment(self, file_id):
        """添付ファイルをダウンロード"""
        self.logger.info("PreviewContent: 添付ファイルダウンロード", file_id=file_id)

        if not self.viewmodel:
            return

        # ViewModelに処理を委譲
        success = self.viewmodel.download_attachment(file_id)

        if success:
            # ダウンロード成功時の通知
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("ファイルをダウンロードしました"),
                action="閉じる",
            )
            self.page.snack_bar.open = True
            self.page.update()
        else:
            # ダウンロード失敗時の通知
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("ファイルのダウンロードに失敗しました"),
                action="閉じる",
            )
            self.page.snack_bar.open = True
            self.page.update()

    def show_error_message(self, message):
        """エラーメッセージを表示"""
        self.logger.error("PreviewContent: エラーメッセージ表示", message=message)
        # メール内容表示をクリア
        self.mail_content.controls.clear()
        self.mail_content.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.ERROR_OUTLINE,
                            size=40,
                            color=ft.colors.RED,
                        ),
                        ft.Text(
                            "エラーが発生しました",
                            color=ft.colors.RED,
                            text_align=ft.TextAlign.CENTER,
                            weight="bold",
                        ),
                        ft.Text(
                            message,
                            color=ft.colors.RED_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )
        self.update()

    def show_no_data_message(self, message):
        """データがない場合のメッセージを表示"""
        self.logger.info("PreviewContent: データなしメッセージ表示", message=message)

        # メールリストをクリア
        self.mail_list.controls.clear()
        self.mail_list.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.WARNING_AMBER_ROUNDED,
                            size=40,
                            color=ft.colors.AMBER,
                        ),
                        ft.Text(
                            "メールデータがありません",
                            color=ft.colors.GREY,
                            text_align=ft.TextAlign.CENTER,
                            weight="bold",
                        ),
                        ft.Text(
                            message,
                            color=ft.colors.GREY,
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )

        # メール内容表示をクリア
        self._show_empty_mail_content()
        self.update()

    def on_dispose(self):
        """リソース解放時の処理"""
        self.logger.info("PreviewContent: リソース解放")
        if self.viewmodel:
            self.viewmodel.close()

    def load_sample_data(self):
        """サンプルデータを読み込む"""
        self.logger.info("PreviewContent: サンプルデータ読み込み開始")

        # ViewModelからサンプルデータを取得
        if self.viewmodel:
            sample_mails = self.viewmodel.get_all_mails()
            self.logger.debug(
                "PreviewContent: サンプルデータ取得完了", mail_count=len(sample_mails)
            )
        else:
            # ViewModelが初期化されていない場合は初期化
            self.viewmodel = PreviewContentViewModel()
            sample_mails = self.viewmodel.get_all_mails()
            self.logger.debug(
                "PreviewContent: ViewModelを初期化してサンプルデータ取得",
                mail_count=len(sample_mails),
            )

        # メールリストをクリア
        self.mail_list.controls.clear()

        # サンプルメールを表示
        for mail in sample_mails:
            mail_item = self._create_mail_item(mail)
            self.mail_list.controls.append(mail_item)

        # 初期状態では空のメール内容を表示
        self._show_empty_mail_content()

        self.update()
        self.logger.info("PreviewContent: サンプルデータ読み込み完了")

    def on_group_by_conversation_changed(self, e):
        """会話ごとに集約する設定が変更された時の処理"""
        self.logger.info("PreviewContent: 会話集約設定変更", value=e.control.value)

        # 状態を更新
        self.group_by_conversation = e.control.value

        # 会話表示の時系列ソート順（True: 新しい順、False: 古い順）
        self.conversation_sort_newest_first = e.control.value

        # 会話コンテナを初期化
        self.conversation_containers = {}
        self.logger.debug("PreviewContent: 会話コンテナ初期化")

        # メール一覧を再読み込み
        self.load_all_mails()

        # 明示的に更新
        self.update()

    def _display_grouped_mails(self, mails):
        """会話ごとにグループ化されたメールを表示（静的な階層表示）"""
        self.logger.debug("PreviewContent: 会話ごとにグループ化して表示")

        # メールリストをクリア
        self.mail_list.controls.clear()

        # 件名でグループ化
        conversation_groups = {}
        for mail in mails:
            # 件名を正規化（Re:や空白を除去）して会話IDとする
            subject = mail["subject"] or "(件名なし)"
            normalized_subject = subject.lower().replace("re:", "").strip()

            if normalized_subject not in conversation_groups:
                conversation_groups[normalized_subject] = []

            conversation_groups[normalized_subject].append(mail)

        # グループごとに表示
        # リスクレベルでソートする場合の条件分岐を削除

        # 会話グループのソート - 単純に新しい順のみにする
        sorted_subjects = sorted(
            conversation_groups.keys(),
            key=lambda s: max([mail["date"] for mail in conversation_groups[s]]),
            reverse=True,  # 新しい順
        )

        # 会話コンテナを初期化
        self.conversation_containers = {}

        # ソートされた順序でグループを表示
        for subject in sorted_subjects:
            group = conversation_groups[subject]

            # グループIDを生成
            group_id = f"group_{subject}"

            # 会話コンテナに保存
            self.conversation_containers[group_id] = group

            # 最新のメールを取得（日付でソート）
            latest_mail = sorted(group, key=lambda x: x["date"], reverse=True)[0]

            # 未読メールがあるかチェック
            has_unread = any(mail.get("unread", 0) for mail in group)

            # 添付ファイルがあるかチェック
            has_attachments = any(mail.get("attachments") for mail in group)

            # フラグが立っているかチェック
            is_flagged = any(mail.get("flagged", False) for mail in group)

            # リスク評価を取得
            risk_score = self._get_conversation_risk_score(group)

            # 会話グループアイテムを作成
            conversation_item = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(
                                        name=ft.icons.CIRCLE,
                                        size=8,
                                        color=(
                                            ft.colors.BLUE
                                            if has_unread
                                            else ft.colors.TRANSPARENT
                                        ),
                                    ),
                                    width=15,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        risk_score["label"],
                                        color=ft.colors.WHITE,
                                        text_align=ft.TextAlign.CENTER,
                                        size=12,
                                    ),
                                    bgcolor=risk_score["color"],
                                    border_radius=15,
                                    width=30,
                                    height=20,
                                    alignment=ft.alignment.center,
                                    tooltip=risk_score["tooltip"],
                                ),
                                ft.Text(
                                    f"{len(group)}件",
                                    size=12,
                                    color=ft.colors.GREY,
                                    width=40,
                                ),
                                ft.Text(
                                    latest_mail["date"],
                                    size=12,
                                    color=ft.colors.GREY,
                                ),
                                (
                                    ft.Icon(
                                        name=ft.icons.FLAG,
                                        size=14,
                                        color=ft.colors.RED,
                                    )
                                    if is_flagged
                                    else ft.Container(width=0)
                                ),
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
                            subject or "(件名なし)",
                            weight="bold" if has_unread else "normal",
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            f"参加者: {latest_mail['sender'].split('<')[0].strip()} 他",
                            size=12,
                            color=ft.colors.GREY,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=2,
                ),
                padding=ft.padding.all(8),
                border_radius=5,
                on_click=lambda e, gid=group_id: self._on_conversation_click(e, gid),
                data=group_id,
                ink=True,
                bgcolor=ft.colors.WHITE,
                border=ft.border.all(1, ft.colors.BLACK12),
                margin=ft.margin.only(bottom=5),
            )

            # メールリストに追加
            self.mail_list.controls.append(conversation_item)

    def _get_conversation_risk_score(self, mails):
        """会話のAIリスク評価を取得"""
        if self.viewmodel:
            return self.viewmodel.get_conversation_risk_score(mails)

        # ViewModelが初期化されていない場合のフォールバック処理
        # ... 既存のコード ...

    def _on_conversation_click(self, e, group_id):
        """会話グループがクリックされたときの処理"""
        self.logger.info(
            "PreviewContent: 会話グループクリック",
            group_id=group_id,
            control_type=type(e.control).__name__,
        )

        # グループIDに対応するメールリストを取得
        if group_id in self.conversation_containers:
            mails = self.conversation_containers[group_id]
            self.logger.debug(
                "PreviewContent: 会話メール取得成功", mail_count=len(mails)
            )
            self._show_conversation(mails)
        else:
            self.logger.error(
                "PreviewContent: 会話グループが見つかりません", group_id=group_id
            )

    def _get_file_icon(self, filename):
        """ファイル名から適切なアイコンを返す"""
        extension = filename.split(".")[-1].lower() if "." in filename else ""

        if extension in ["pdf"]:
            return ft.Icon(name=ft.icons.PICTURE_AS_PDF, size=24, color=ft.colors.RED)
        elif extension in ["doc", "docx"]:
            return ft.Icon(name=ft.icons.ARTICLE, size=24, color=ft.colors.BLUE)
        elif extension in ["xls", "xlsx"]:
            return ft.Icon(name=ft.icons.TABLE_CHART, size=24, color=ft.colors.GREEN)
        elif extension in ["ppt", "pptx"]:
            return ft.Icon(name=ft.icons.SLIDESHOW, size=24, color=ft.colors.ORANGE)
        elif extension in ["jpg", "jpeg", "png", "gif"]:
            return ft.Icon(name=ft.icons.IMAGE, size=24, color=ft.colors.PURPLE)
        elif extension in ["zip", "rar", "7z"]:
            return ft.Icon(name=ft.icons.FOLDER_ZIP, size=24, color=ft.colors.BROWN)
        else:
            return ft.Icon(
                name=ft.icons.INSERT_DRIVE_FILE, size=24, color=ft.colors.GREY
            )

    def _get_file_type(self, filename):
        """ファイル名から種類の説明を返す"""
        extension = filename.split(".")[-1].lower() if "." in filename else ""

        if extension in ["pdf"]:
            return "PDF文書"
        elif extension in ["doc", "docx"]:
            return "Word文書"
        elif extension in ["xls", "xlsx"]:
            return "Excel表計算"
        elif extension in ["ppt", "pptx"]:
            return "PowerPointプレゼンテーション"
        elif extension in ["jpg", "jpeg", "png", "gif"]:
            return "画像ファイル"
        elif extension in ["zip", "rar", "7z"]:
            return "圧縮ファイル"
        else:
            return f"{extension.upper()}ファイル" if extension else "ファイル"

    def _show_conversation(self, mails):
        """会話グループのメール内容を表示"""
        self.logger.info("PreviewContent: 会話内容表示開始", mail_count=len(mails))

        # メール内容表示をクリア
        self.mail_content.controls.clear()

        if not mails:
            self.logger.error("PreviewContent: 会話内容が空です")
            return

        # 時系列でソート（新しい順/古い順）
        sorted_mails = sorted(
            mails, key=lambda x: x["date"], reverse=self.conversation_sort_newest_first
        )

        # 最新のメールを取得（ソート前のリストから）
        latest_mail = mails[0]

        # 送信者情報を解析
        sender_name = latest_mail["sender"].split("<")[0].strip()
        sender_email = (
            latest_mail["sender"].split("<")[1].replace(">", "")
            if "<" in latest_mail["sender"]
            else latest_mail["sender"]
        )

        # 受信者情報を解析
        recipient_name = latest_mail.get("recipient", "").split("<")[0].strip()
        recipient_email = (
            latest_mail.get("recipient", "").split("<")[1].replace(">", "")
            if "<" in latest_mail.get("recipient", "")
            else latest_mail.get("recipient", "")
        )

        # 添付ファイルがあれば表示用のリストを作成
        attachments_section = []
        if latest_mail.get("attachments"):
            attachments = latest_mail["attachments"]
            attachments_list = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    name=ft.icons.ATTACH_FILE,
                                    size=16,
                                    color=ft.colors.BLUE,
                                ),
                                ft.Text("添付ファイル", weight="bold"),
                            ],
                            spacing=5,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            self._get_file_icon(attachment["name"]),
                                            ft.Text(attachment["name"]),
                                            ft.Text(
                                                self._get_file_type(attachment["name"]),
                                                size=12,
                                                color=ft.colors.GREY,
                                            ),
                                        ],
                                        spacing=10,
                                    )
                                    for attachment in attachments
                                ],
                                spacing=5,
                            ),
                            padding=10,
                        ),
                    ],
                    spacing=5,
                ),
                padding=10,
                border=ft.border.all(1, ft.colors.BLACK12),
                border_radius=5,
                margin=ft.margin.only(top=10),
            )
            attachments_section = [attachments_list]

        # AIリスク評価を取得
        risk_score = self._get_conversation_risk_score(mails)

        # AIレビューセクション（会話集約モード専用）
        ai_review_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                name=ft.icons.PSYCHOLOGY_ALT,
                                size=16,
                                color=ft.colors.BLUE,
                            ),
                            ft.Text("AIレビュー", weight="bold"),
                            ft.IconButton(
                                icon=ft.icons.REFRESH,
                                tooltip="AIに再評価させる",
                                icon_size=16,
                                on_click=self._on_ai_review_refresh,
                            ),
                        ],
                        spacing=5,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text("リスクスコア:", weight="bold"),
                                        ft.Container(
                                            content=ft.Text(
                                                risk_score["label"],
                                                color=ft.colors.WHITE,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            bgcolor=risk_score["color"],
                                            border_radius=5,
                                            padding=5,
                                            width=50,
                                            alignment=ft.alignment.center,
                                        ),
                                    ],
                                    spacing=10,
                                ),
                                ft.Text(
                                    risk_score["tooltip"],
                                    size=14,
                                ),
                                ft.Row(
                                    [
                                        ft.Text("キーポイント:", weight="bold"),
                                    ],
                                ),
                                ft.Column(
                                    [
                                        # リスク要因がある場合は表示
                                        *(
                                            [
                                                ft.Text(
                                                    f"• {factor}",
                                                    size=14,
                                                    color=(
                                                        ft.colors.RED
                                                        if risk_score["label"] == "高"
                                                        else None
                                                    ),
                                                    weight=(
                                                        "bold"
                                                        if risk_score["label"] == "高"
                                                        else None
                                                    ),
                                                )
                                                for factor in risk_score.get(
                                                    "factors", []
                                                )
                                            ]
                                            if risk_score.get("factors")
                                            else [
                                                ft.Text(
                                                    "• 特に注意すべき点はありません",
                                                    size=14,
                                                    color=ft.colors.GREY,
                                                )
                                            ]
                                        ),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=10,
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.border.all(1, ft.colors.BLACK12),
            border_radius=5,
            margin=ft.margin.only(top=10),
        )

        # 会話の概要セクション
        conversation_summary = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                latest_mail["subject"] or "(件名なし)",
                                size=18,
                                weight="bold",
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.icons.FLAG_OUTLINED,
                                tooltip="問題のある会話としてフラグを立てる",
                                icon_color=ft.colors.GREY,
                                on_click=lambda e, group_id=f"group_{latest_mail['subject']}": self._toggle_conversation_flag(
                                    e, group_id
                                ),
                                data={
                                    "flagged": False,
                                    "group_id": f"group_{latest_mail['subject']}",
                                },
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=ft.colors.BLACK12),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "会話数:",
                                                weight="bold",
                                                width=80,
                                            ),
                                            ft.Text(f"{len(mails)}件のメール"),
                                        ],
                                    ),
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "期間:",
                                                weight="bold",
                                                width=80,
                                            ),
                                            ft.Text(
                                                f"{mails[-1]['date']} - {mails[0]['date']}"
                                            ),
                                        ],
                                    ),
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "参加者:",
                                                weight="bold",
                                                width=80,
                                            ),
                                            ft.Text(f"{sender_name}、{recipient_name}"),
                                        ],
                                    ),
                                ],
                                spacing=5,
                            ),
                        ],
                    ),
                ],
                spacing=10,
            ),
            padding=10,
            bgcolor=ft.colors.WHITE,
            border_radius=5,
            border=ft.border.all(1, ft.colors.BLACK12),
        )

        # 時系列ソート順切り替えボタン
        sort_order_toggle = ft.Container(
            content=ft.Row(
                [
                    ft.Text("表示順:", size=14),
                    ft.TextButton(
                        text=(
                            "新しい順"
                            if self.conversation_sort_newest_first
                            else "古い順"
                        ),
                        icon=(
                            ft.icons.ARROW_DOWNWARD
                            if self.conversation_sort_newest_first
                            else ft.icons.ARROW_UPWARD
                        ),
                        on_click=self._toggle_conversation_sort_order,
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
            margin=ft.margin.only(top=10, bottom=5),
        )

        # 会話内のすべてのメールを表示
        conversation_label = ft.Container(
            content=ft.Text(
                "会話内容:",
                weight="bold",
            ),
            padding=10,
        )

        # サンプルボタン
        sample_button = ft.Container(
            content=ft.TextButton(
                text="サンプルボタン",
                icon=ft.icons.ADD_CIRCLE_OUTLINE,
                icon_color=ft.colors.BLUE,
                style=ft.ButtonStyle(
                    color=ft.colors.BLUE,
                    bgcolor=ft.colors.WHITE,
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    shape=ft.RoundedRectangleBorder(radius=20),
                    elevation=0,
                    overlay_color=ft.colors.BLUE_50,
                ),
                on_click=lambda e: self.logger.info(
                    "PreviewContent: サンプルボタンがクリックされました"
                ),
            ),
            padding=ft.padding.only(left=10, bottom=10),
            alignment=ft.alignment.center_left,
        )

        conversation_mails = ft.Container(
            content=ft.Column(
                [
                    self._create_mail_content_item(mail, index)
                    for index, mail in enumerate(sorted_mails)
                ],
                spacing=15,
            ),
            padding=10,
            bgcolor=ft.colors.WHITE,
            border_radius=5,
            border=ft.border.all(1, ft.colors.BLACK12),
            expand=True,
        )

        # メール内容を表示
        self.mail_content.controls.extend(
            [
                conversation_summary,
                ai_review_section,
                *attachments_section,
                sort_order_toggle,
                conversation_label,
                sample_button,
                conversation_mails,
            ]
        )

        self.update()
        self.logger.info("PreviewContent: 会話内容表示完了")

    def _create_mail_content_item(self, mail, index):
        """会話内の個別メールアイテムを作成"""
        # 送信者情報を解析
        sender_name = mail["sender"].split("<")[0].strip()
        sender_email = (
            mail["sender"].split("<")[1].replace(">", "")
            if "<" in mail["sender"]
            else mail["sender"]
        )

        # 添付ファイルアイコン
        attachments_icon = (
            ft.Row(
                [
                    ft.Icon(
                        name=ft.icons.ATTACH_FILE,
                        size=14,
                        color=ft.colors.GREY,
                    ),
                    ft.Text(
                        f"{len(mail['attachments'])}個の添付ファイル",
                        size=12,
                        color=ft.colors.GREY,
                    ),
                ],
                spacing=2,
            )
            if mail.get("attachments")
            else ft.Container(width=0)
        )

        # メール本文を処理
        content = mail["content"]
        content_lines = content.split("\n")

        # 最初は5行まで表示
        preview_line_count = 5
        is_truncated = len(content_lines) > preview_line_count

        # メール本文のプレビュー
        preview_text = ft.Text(
            "\n".join(content_lines[:preview_line_count])
            + ("..." if is_truncated else "")
        )

        # 全文
        full_text = ft.Text(content, visible=False)

        # 続きを見るボタン
        expand_button = ft.TextButton(
            text="続きを見る",
            icon=ft.icons.EXPAND_MORE,
            on_click=lambda e, t1=preview_text, t2=full_text, b=None: self._toggle_mail_content(
                e, t1, t2, b
            ),
            visible=is_truncated,
        )
        # ボタン自身への参照を設定
        expand_button.data = expand_button

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    f"#{index+1}",
                                    color=ft.colors.WHITE,
                                    text_align=ft.TextAlign.CENTER,
                                    size=12,
                                ),
                                bgcolor=(
                                    ft.colors.BLUE
                                    if mail.get("unread", 0)
                                    else ft.colors.GREY
                                ),
                                border_radius=15,
                                width=30,
                                height=20,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(
                                mail["date"],
                                size=12,
                                color=ft.colors.GREY,
                            ),
                            ft.Text(
                                f"送信者: {sender_name}",
                                size=12,
                                weight="bold",
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.icons.FLAG_OUTLINED,
                                tooltip="問題のあるメールとしてフラグを立てる",
                                icon_color=ft.colors.GREY,
                                icon_size=16,
                                on_click=lambda e, mail_id=mail[
                                    "id"
                                ]: self._toggle_flag(e, mail_id),
                                data={"flagged": False, "mail_id": mail["id"]},
                            ),
                            attachments_icon,
                        ],
                        spacing=5,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                preview_text,
                                full_text,
                                ft.Container(
                                    content=expand_button,
                                    alignment=ft.alignment.center,
                                ),
                            ],
                            spacing=5,
                        ),
                        padding=10,
                        bgcolor=ft.colors.WHITE,
                        border_radius=5,
                        border=ft.border.all(1, ft.colors.BLACK12),
                    ),
                ],
                spacing=5,
            ),
            padding=5,
            bgcolor=ft.colors.BLUE_50 if mail.get("unread", 0) else ft.colors.WHITE,
            border_radius=5,
            border=ft.border.all(1, ft.colors.BLACK12),
        )

    def _toggle_mail_content(self, e, preview_text, full_text, button):
        """メール内容の全文表示/折りたたみを切り替える"""
        self.logger.info("PreviewContent: メール内容表示切り替え")

        # ボタンを取得
        button = e.control

        # 現在の表示状態を確認
        is_expanded = full_text.visible

        if is_expanded:
            # 折りたたむ
            preview_text.visible = True
            full_text.visible = False
            button.text = "続きを見る"
            button.icon = ft.icons.EXPAND_MORE
        else:
            # 展開する
            preview_text.visible = False
            full_text.visible = True
            button.text = "折りたたむ"
            button.icon = ft.icons.EXPAND_LESS

        # 更新
        self.update()
        self.logger.info(
            "PreviewContent: メール内容表示切り替え完了", expanded=not is_expanded
        )

    def _toggle_conversation_sort_order(self, e):
        """会話表示の時系列ソート順を切り替える"""
        self.logger.info(
            "PreviewContent: 会話ソート順切り替え",
            current_order=(
                "新しい順" if self.conversation_sort_newest_first else "古い順"
            ),
        )

        # ソート順を反転
        self.conversation_sort_newest_first = not self.conversation_sort_newest_first

        # 現在表示中の会話グループを再表示
        for group_id, mails in self.conversation_containers.items():
            # 現在選択されているグループを特定
            for item in self.mail_list.controls:
                if (
                    hasattr(item, "data")
                    and item.data == group_id
                    and item.bgcolor == ft.colors.BLUE_50
                ):
                    self._show_conversation(mails)
                    break

        self.logger.info(
            "PreviewContent: 会話ソート順切り替え完了",
            new_order="新しい順" if self.conversation_sort_newest_first else "古い順",
        )

    def _on_ai_review_refresh(self, e):
        """AIレビューの再評価ボタンがクリックされたときの処理"""
        self.logger.info("PreviewContent: AIレビュー再評価リクエスト")

        # 再評価中の表示
        ai_review_section = e.control.parent.parent.parent
        original_content = ai_review_section.content

        # 読み込み中表示に切り替え
        ai_review_section.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            name=ft.icons.PSYCHOLOGY_ALT,
                            size=16,
                            color=ft.colors.BLUE,
                        ),
                        ft.Text("AIレビュー", weight="bold"),
                        ft.ProgressRing(width=16, height=16),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("AIによる再評価中...", italic=True),
                            ft.ProgressBar(width=300),
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                ),
            ],
            spacing=5,
        )
        self.update()

        # 実際のアプリケーションでは、ここでAI評価のAPIを呼び出す
        # サンプルデータでは、少し待ってから新しい評価結果を表示

        async def simulate_ai_review():
            # 処理時間をシミュレート
            await asyncio.sleep(2)

            # 新しい評価結果
            ai_review_section.content = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                name=ft.icons.PSYCHOLOGY_ALT,
                                size=16,
                                color=ft.colors.BLUE,
                            ),
                            ft.Text("AIレビュー (更新済み)", weight="bold"),
                            ft.IconButton(
                                icon=ft.icons.REFRESH,
                                tooltip="AIに再評価させる",
                                icon_size=16,
                                on_click=self._on_ai_review_refresh,
                            ),
                        ],
                        spacing=5,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text("リスクスコア:", weight="bold"),
                                        ft.Container(
                                            content=ft.Text(
                                                "中",
                                                color=ft.colors.WHITE,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            bgcolor=ft.colors.ORANGE,
                                            border_radius=5,
                                            padding=5,
                                            width=50,
                                            alignment=ft.alignment.center,
                                        ),
                                    ],
                                    spacing=10,
                                ),
                                ft.Text(
                                    "この会話には注意が必要な項目があります。期限や重要な決定事項について確認してください。",
                                    size=14,
                                ),
                                ft.Row(
                                    [
                                        ft.Text("キーポイント:", weight="bold"),
                                    ],
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            "• 重要な期限が近づいています",
                                            size=14,
                                        ),
                                        ft.Text(
                                            "• 複数の関係者への連絡が必要です",
                                            size=14,
                                        ),
                                        ft.Text(
                                            "• 添付ファイルに重要な情報が含まれています",
                                            size=14,
                                            weight="bold",
                                        ),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=10,
                    ),
                ],
                spacing=5,
            )
            self.update()

        # 非同期処理を開始
        asyncio.create_task(simulate_ai_review())

    def _toggle_flag(self, e, mail_id):
        """メールのフラグ状態を切り替える"""
        self.logger.info("PreviewContent: メールフラグ切り替え", mail_id=mail_id)

        # ボタンの状態を取得
        button = e.control
        is_flagged = button.data.get("flagged", False)

        # フラグ状態を切り替え
        is_flagged = not is_flagged
        button.data["flagged"] = is_flagged

        # アイコンと色を更新
        if is_flagged:
            button.icon = ft.icons.FLAG
            button.icon_color = ft.colors.RED
            button.tooltip = "フラグを解除する"
        else:
            button.icon = ft.icons.FLAG_OUTLINED
            button.icon_color = ft.colors.GREY
            button.tooltip = "問題のあるメールとしてフラグを立てる"

        # フラグ状態をViewModelに保存
        if self.viewmodel:
            self.viewmodel.set_mail_flag(mail_id, is_flagged)
            # メールリストを更新
            self.load_all_mails()

        self.update()
        self.logger.info(
            "PreviewContent: メールフラグ切り替え完了",
            mail_id=mail_id,
            flagged=is_flagged,
        )

    def _toggle_conversation_flag(self, e, group_id):
        """会話グループのフラグ状態を切り替える"""
        self.logger.info("PreviewContent: 会話フラグ切り替え", group_id=group_id)

        # ボタンの状態を取得
        button = e.control
        is_flagged = button.data.get("flagged", False)

        # フラグ状態を切り替え
        is_flagged = not is_flagged
        button.data["flagged"] = is_flagged

        # アイコンと色を更新
        if is_flagged:
            button.icon = ft.icons.FLAG
            button.icon_color = ft.colors.RED
            button.tooltip = "フラグを解除する"
        else:
            button.icon = ft.icons.FLAG_OUTLINED
            button.icon_color = ft.colors.GREY
            button.tooltip = "問題のある会話としてフラグを立てる"

        # サンプルデータを使用する場合
        if self.use_sample_data:
            # 会話グループ内のすべてのメールのフラグ状態を更新
            if group_id in self.conversation_containers:
                mails = self.conversation_containers[group_id]
                for mail in mails:
                    mail["flagged"] = is_flagged

                # サンプルメールデータを更新
                sample_mails = [
                    # ... existing sample mails ...
                ]

                # 該当する会話のすべてのメールのフラグ状態を更新
                for mail in sample_mails:
                    if mail["subject"].lower().replace(
                        "re:", ""
                    ).strip() == group_id.replace("group_", ""):
                        mail["flagged"] = is_flagged

                # メールリストを更新して新しいフラグ状態を反映
                self.mail_list.controls.clear()
                self._display_grouped_mails(sample_mails)
        else:
            # 実際のアプリケーションでは、ここでデータベースにフラグ状態を保存する処理を追加
            if self.viewmodel and group_id in self.conversation_containers:
                mails = self.conversation_containers[group_id]
                for mail in mails:
                    self.viewmodel.set_mail_flag(mail["id"], is_flagged)
                # メールリストを更新
                self.load_all_mails()

        self.update()
        self.logger.info(
            "PreviewContent: 会話フラグ切り替え完了",
            group_id=group_id,
            flagged=is_flagged,
        )
