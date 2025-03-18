"""
プレビューコンテンツ
メールプレビュー画面のコンテンツを提供するクラス
"""

import os
from typing import Any, Dict, List, Optional

import flet as ft

from src.core.database import DatabaseManager
from src.core.logger import get_logger
from src.viewmodels.preview_content_viewmodel import PreviewContentViewModel
from src.views.components.text_with_subtitle import TextWithSubtitle
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

        # UI要素
        self.folder_list = ft.ListView(
            expand=1,
            spacing=2,
            padding=10,
        )

        # メールリスト
        self.mail_list = ft.ListView(
            expand=1,
            spacing=2,
            padding=10,
        )

        # メール内容表示
        self.mail_content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        # UIを構築
        self._build()
        self.logger.info("PreviewContent: 初期化完了")

    def _build(self):
        """UIを構築"""
        # タスク情報を取得
        task_name = "不明なタスク"  # デフォルト値
        self.logger.debug("PreviewContent: UI構築開始")

        # 左側のペイン（フォルダリスト＋メールリスト）
        left_pane = ft.Column(
            [
                ft.Container(
                    content=ft.Text("フォルダ", weight="bold"),
                    padding=10,
                ),
                ft.Container(
                    content=self.folder_list,
                    expand=1,
                    border=ft.border.all(1, ft.colors.BLACK12),
                    border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
                    padding=5,
                ),
                ft.Container(
                    content=ft.Text("メール", weight="bold"),
                    padding=10,
                ),
                ft.Container(
                    content=self.mail_list,
                    expand=3,
                    border=ft.border.all(1, ft.colors.BLACK12),
                    border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
                    padding=5,
                ),
            ],
            spacing=0,
            expand=1,
        )

        # 右側のペイン（メール内容表示）
        right_pane = ft.Container(
            content=self.mail_content,
            expand=2,
            border=ft.border.all(1, ft.colors.BLACK12),
            border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
            padding=10,
        )

        # 検索バー
        self.search_field = ft.TextField(
            label="検索",
            prefix_icon=ft.icons.SEARCH,
            on_submit=self.on_search,
            expand=True,
        )

        # 戻るボタン
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            tooltip="ホーム画面に戻る",
            on_click=self.on_back_click,
        )

        # ヘッダー
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(f"アーカイブ: {task_name}", size=20, weight="bold"),
                    self.search_field,
                    back_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(bottom=10),
        )

        # メインコンテンツ
        self.content = ft.Column(
            [
                header,
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
        self.logger.debug("PreviewContent: UI構築完了")

    def did_mount(self):
        """コンポーネントがマウントされた時の処理"""
        self.logger.info("PreviewContent: マウント処理開始")

        # contents_viewmodelの状態を詳細にログ出力
        if hasattr(self.contents_viewmodel, "current_task_id"):
            self.logger.debug(
                "PreviewContent: contents_viewmodel.current_task_id直接アクセス",
                value=self.contents_viewmodel.current_task_id,
            )

        # タスクIDを取得
        self.task_id = self._get_task_id()
        self.logger.debug("PreviewContent: タスクID取得", task_id=self.task_id)

        # データを読み込む
        self.load_data()
        self.logger.info("PreviewContent: マウント処理完了")

    def load_data(self):
        """データを読み込む"""
        self.logger.info("PreviewContent: データ読み込み開始")
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
                    # ヘッダーのテキストを更新
                    if (
                        isinstance(self.content.controls[0].content, ft.Row)
                        and self.content.controls[0].content.controls
                    ):
                        self.content.controls[0].content.controls[
                            0
                        ].value = f"アーカイブ: {task_name}"

                # フォルダ一覧を読み込む
                self.load_folders()

                # 最初のフォルダのメールを読み込む
                folders = self.viewmodel.get_folders()
                if folders:
                    self.logger.debug(
                        "PreviewContent: 最初のフォルダを読み込み",
                        folder_id=folders[0]["entry_id"],
                    )
                    self.load_folder_mails(folders[0]["entry_id"])
                self.logger.info("PreviewContent: データ読み込み完了")
            except Exception as e:
                self.logger.error("PreviewContent: データ読み込みエラー", error=str(e))
                self.show_error_message(f"データ読み込みエラー: {str(e)}")
        else:
            self.logger.error("PreviewContent: 有効なタスクIDがありません")
            self.show_error_message("有効なタスクIDがありません")

        self.update()

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

    def load_folders(self):
        """フォルダ一覧を読み込む"""
        self.logger.debug("PreviewContent: フォルダ一覧読み込み開始")
        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # フォルダリストをクリア
        self.folder_list.controls.clear()

        # フォルダ一覧を取得
        folders = self.viewmodel.get_folders()
        self.logger.debug("PreviewContent: フォルダ取得完了", folder_count=len(folders))

        # フォルダ一覧を表示
        for folder in folders:
            folder_item = TextWithSubtitle(
                text=folder["name"],
                subtitle=f"ID: {folder['entry_id']}",
                on_click=lambda e, folder_id=folder["entry_id"]: self.load_folder_mails(
                    folder_id
                ),
                enable_hover=True,
                enable_press=True,
            )
            self.folder_list.controls.append(folder_item)

        self.update()
        self.logger.debug("PreviewContent: フォルダ一覧読み込み完了")

    def load_folder_mails(self, folder_id):
        """指定フォルダのメール一覧を読み込む"""
        self.logger.info(
            "PreviewContent: フォルダメール読み込み開始", folder_id=folder_id
        )
        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # メールリストをクリア
        self.mail_list.controls.clear()

        # メール一覧を取得
        mails = self.viewmodel.load_folder_mails(folder_id)
        self.logger.debug("PreviewContent: メール取得完了", mail_count=len(mails))

        # メール一覧を表示
        for mail in mails:
            mail_item = TextWithSubtitle(
                text=mail["subject"] or "(件名なし)",
                subtitle=f"From: {mail['sender']}",
                on_click=lambda e, mail_id=mail["id"]: self.show_mail_content(mail_id),
                enable_hover=True,
                enable_press=True,
                # 未読の場合は太字で表示
                text_weight="bold" if mail.get("unread", 0) else "normal",
            )
            self.mail_list.controls.append(mail_item)

        # メール内容表示をクリア
        self.mail_content.controls.clear()
        self.mail_content.controls.append(
            ft.Text("メールを選択してください", color=ft.colors.GREY)
        )

        self.update()
        self.logger.info(
            "PreviewContent: フォルダメール読み込み完了", folder_id=folder_id
        )

    def on_search(self, e):
        """検索実行時の処理"""
        search_term = self.search_field.value
        self.logger.info("PreviewContent: 検索実行", search_term=search_term)
        if not search_term:
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
        for mail in mails:
            mail_item = TextWithSubtitle(
                text=mail["subject"] or "(件名なし)",
                subtitle=f"From: {mail['sender']}",
                on_click=lambda e, mail_id=mail["id"]: self.show_mail_content(mail_id),
                enable_hover=True,
                enable_press=True,
                # 未読の場合は太字で表示
                text_weight="bold" if mail.get("unread", 0) else "normal",
            )
            self.mail_list.controls.append(mail_item)

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

        # メール内容表示をクリア
        self.mail_content.controls.clear()

        # メール内容を表示
        self.mail_content.controls.extend(
            [
                ft.Text(f"件名: {mail['subject']}", size=16, weight="bold"),
                ft.Text(f"差出人: {mail['sender']}"),
                ft.Text(f"日時: {mail['date']}"),
                ft.Divider(),
                ft.Text(mail["content"]),
            ]
        )

        self.update()
        self.logger.info("PreviewContent: メール内容表示完了", mail_id=mail_id)

    def on_back_click(self, e):
        """戻るボタンクリック時の処理"""
        self.logger.info("PreviewContent: 戻るボタンクリック")
        if (
            hasattr(self.contents_viewmodel, "main_viewmodel")
            and self.contents_viewmodel.main_viewmodel
        ):
            self.contents_viewmodel.main_viewmodel.set_destination("home")
            self.logger.debug("PreviewContent: ホーム画面に遷移")

    def show_error_message(self, message):
        """エラーメッセージを表示"""
        self.logger.error("PreviewContent: エラーメッセージ表示", message=message)
        # メール内容表示をクリア
        self.mail_content.controls.clear()
        self.mail_content.controls.append(ft.Text(message, color=ft.colors.RED))

    def on_dispose(self):
        """リソース解放時の処理"""
        self.logger.info("PreviewContent: リソース解放")
        if self.viewmodel:
            self.viewmodel.close()
