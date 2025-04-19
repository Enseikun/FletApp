"""
プレビューコンテンツ
メールプレビュー画面のコンテンツを提供するクラス
"""

import asyncio
from typing import Any, Dict, List, Optional

import flet as ft

from src.core.logger import get_logger
from src.models.mail.styled_text import StyledText
from src.models.preview_content_model import PreviewContentModel
from src.viewmodels.preview_content_viewmodel import PreviewContentViewModel
from src.views.components.mail_content_viewer import MailContentViewer
from src.views.components.mail_list import MailList
from src.views.styles.color import Colors
from src.views.styles.style import AppTheme, ComponentState, Styles


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
        self.group_by_thread = False

        # 会話表示の時系列ソート順（True: 新しい順、False: 古い順）
        self.thread_sort_newest_first = True

        # メール一覧のソート順
        self.mail_sort_order = "date_desc"

        # 会話グループのコンテナを保存する辞書
        self.thread_containers = {}

        # メールリストコンポーネント
        self.mail_list_component = MailList(
            on_mail_selected=self.show_mail_content,
            on_refresh=self.load_all_mails,
        )

        # 検索イベントを設定
        self.mail_list_component.on_search = self.on_search

        # 会話グループ変更イベントを設定
        self.mail_list_component.on_group_changed = self.on_group_by_thread_changed

        # 会話選択イベントを設定
        self.mail_list_component.on_thread_selected = self._show_thread

        # メール内容表示コンポーネント
        self.mail_content_viewer = MailContentViewer(
            on_flag_click=self._toggle_flag,
            on_download_attachment=self.download_attachment,
        )

        # Fletコンテナの設定
        self.padding = 20
        self.expand = True
        self.bgcolor = Colors.BACKGROUND

        # StyledTextインスタンス
        self.styled_text = StyledText()

        # キーワードリスト
        self.keywords = self._load_keywords()

        # UIを構築
        self._build()
        self.logger.info("PreviewContent: 初期化完了")

        # サンプルデータフラグ
        self.use_sample_data = False

    def _build(self):
        """UIを構築"""
        self.logger.debug("PreviewContent: UI構築開始")

        # 左側のペイン（メールリスト）
        left_pane = Styles.container(
            content=self.mail_list_component,
            expand=1,
            padding=0,
        )

        # 右側のペイン（メール内容表示）
        right_pane = Styles.container(
            content=ft.Column(
                [
                    Styles.container(
                        content=Styles.title("メールプレビュー", size=16),
                        padding=10,
                        border=None,
                    ),
                    Styles.card(
                        content=self.mail_content_viewer,
                        expand=True,
                        padding=10,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=2,
            padding=0,
        )

        # メインコンテンツ
        self.content = ft.Stack(
            [
                ft.Column(
                    [
                        ft.Row(
                            [left_pane, right_pane],
                            spacing=10,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                    expand=True,
                ),
            ],
            expand=True,
        )

        self.floating_action_button = ft.FloatingActionButton(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.icons.CHECK_CIRCLE,
                        size=AppTheme.ICON_SIZE_SM,
                        color=Colors.TEXT_ON_ACTION,
                    ),
                    ft.Text(
                        "査閲終了", size=AppTheme.BODY_SIZE, color=Colors.TEXT_ON_ACTION
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            shape=ft.RoundedRectangleBorder(radius=AppTheme.BORDER_RADIUS),
            bgcolor=Colors.ACTION,
            height=36,
            width=112,
            on_click=None,
        )

        # コンテナのスタイルを設定
        self.bgcolor = Colors.BACKGROUND

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

        # FloatingActionButton
        self.page.floating_action_button = self.floating_action_button
        self.page.update()

        # データを読み込む
        self.load_data()

        self.logger.info("PreviewContent: マウント処理完了")

    def will_unmount(self):
        """コンポーネントがアンマウントされる前の処理"""
        self.logger.info("PreviewContent: アンマウント処理開始")

        try:
            # ViewModelリソース解放
            if hasattr(self, "viewmodel") and self.viewmodel:
                self.viewmodel.close()
                self.logger.debug("PreviewContent: ViewModelのリソースを解放")
                self.viewmodel = None

            # 会話コンテナのリセット
            if hasattr(self, "thread_containers") and self.thread_containers:
                self.thread_containers.clear()
                self.logger.debug("PreviewContent: 会話コンテナをクリア")

            # メールリストとメールコンテンツビューアーのリセット
            if hasattr(self, "mail_list_component"):
                self.mail_list_component.reset()
                self.logger.debug("PreviewContent: メールリストをリセット")

            if hasattr(self, "mail_content_viewer"):
                self.mail_content_viewer.reset()
                self.logger.debug(
                    "PreviewContent: メールコンテンツビューアーをリセット"
                )

            # タスクIDをクリア
            self.task_id = None

            # FloatingActionButtonをクリア
            self.page.floating_action_button = None
            self.page.update()

            self.logger.info("PreviewContent: アンマウント処理完了")
        except Exception as e:
            self.logger.error(f"PreviewContent: アンマウント処理中にエラー - {str(e)}")

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

                # すべてのメールを読み込む
                self.load_all_mails()
                self.logger.info("PreviewContent: データ読み込み完了")
            except Exception as e:
                error_msg = f"PreviewContent: データ読み込みエラー - {str(e)}"
                self.logger.error(error_msg)
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
            (task_id is None or task_id == "")
            and hasattr(self.contents_viewmodel, "main_viewmodel")
            and self.contents_viewmodel.main_viewmodel
        ):
            if hasattr(self.contents_viewmodel.main_viewmodel, "get_current_task_id"):
                task_id = self.contents_viewmodel.main_viewmodel.get_current_task_id()
                self.logger.debug(
                    "PreviewContent: main_viewmodelからタスクID取得", task_id=task_id
                )

        # タスクIDが取得できたかチェック
        if task_id:
            self.logger.info("PreviewContent: タスクID取得成功", task_id=task_id)
        else:
            self.logger.error("PreviewContent: タスクIDの取得に失敗しました")
            # contents_viewmodelの状態を確認
            if hasattr(self.contents_viewmodel, "current_task_id"):
                current_task_id = getattr(
                    self.contents_viewmodel, "current_task_id", None
                )
                self.logger.debug(
                    f"PreviewContent: contents_viewmodel.current_task_id = {current_task_id}"
                )
            # main_viewmodelの状態も確認
            if (
                hasattr(self.contents_viewmodel, "main_viewmodel")
                and self.contents_viewmodel.main_viewmodel
                and hasattr(
                    self.contents_viewmodel.main_viewmodel, "get_current_task_id"
                )
            ):
                main_task_id = (
                    self.contents_viewmodel.main_viewmodel.get_current_task_id()
                )
                self.logger.debug(
                    f"PreviewContent: main_viewmodel.get_current_task_id()の直接呼び出し結果 = {main_task_id}"
                )

        return task_id

    def load_all_mails(self):
        """すべてのメールを読み込む"""
        self.logger.info("PreviewContent: すべてのメール読み込み開始")
        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # すべてのメールを取得
        mails = self.viewmodel.get_all_mails()
        self.logger.debug("PreviewContent: メール取得完了", mail_count=len(mails))

        # メール一覧コンポーネントに表示
        self.mail_list_component.display_mails(mails)

        # メール内容表示をクリア
        self._show_empty_mail_content()

        # 明示的に更新
        self.update()
        self.logger.info("PreviewContent: すべてのメール読み込み完了")

    def on_search(self, search_term):
        """検索実行時の処理"""
        self.logger.info("PreviewContent: 検索実行", search_term=search_term)
        if not search_term:
            self.load_all_mails()
            return

        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # 検索を実行
        mails = self.viewmodel.search_mails(search_term)
        self.logger.debug("PreviewContent: 検索結果取得", result_count=len(mails))

        # 検索結果をコンポーネントに表示
        self.mail_list_component.display_search_results(mails, search_term)

        # メール内容表示をクリア
        self._show_empty_mail_content()

        self.update()
        self.logger.info("PreviewContent: 検索完了", search_term=search_term)

    def _show_empty_mail_content(self):
        """空のメール内容表示"""
        self.mail_content_viewer._show_empty_content()

    def show_mail_content(self, e=None, mail_id=None):
        """メール内容を表示"""
        # イベントオブジェクトから呼び出された場合
        if e and not mail_id:
            if hasattr(e, "control") and hasattr(e.control, "data"):
                mail_id = e.control.data
            elif hasattr(e, "data"):
                # e自体がmailIdの場合（MailListコンポーネントから直接渡された場合）
                mail_id = e.data
            else:
                # メールIDそのものが渡された場合
                mail_id = e

            self.logger.info(f"PreviewContent: メール内容表示 - mail_id: {mail_id}")
        else:
            self.logger.info(f"PreviewContent: メール内容表示 - mail_id: {mail_id}")

        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # メール内容を取得
        mail = self.viewmodel.get_mail_content(mail_id)
        if not mail:
            self.logger.error(
                f"PreviewContent: メール内容取得失敗 - mail_id: {mail_id}"
            )
            return

        # メールデータの整合性チェックと修正（必須フィールドのデフォルト値を設定）
        # 送信者情報
        if "sender" not in mail or not mail["sender"]:
            mail["sender"] = "不明 <unknown@example.com>"

        # 受信者情報
        if "recipient" not in mail or not mail["recipient"]:
            mail["recipient"] = "不明 <unknown@example.com>"

        # 件名
        if "subject" not in mail or mail["subject"] is None:
            mail["subject"] = "(件名なし)"

        # 本文
        if "content" not in mail or mail["content"] is None:
            mail["content"] = ""

        # 添付ファイル
        if "attachments" not in mail:
            mail["attachments"] = []

        # 未読フラグ
        if "unread" not in mail:
            mail["unread"] = 0

        # フラグ状態
        if "flagged" not in mail:
            mail["flagged"] = False

        # 日付
        if "date" not in mail or not mail["date"]:
            mail["date"] = "不明な日時"

        # メールを既読にする
        if mail.get("unread", 0):
            self.viewmodel.mark_as_read(mail_id)
            self.logger.debug("PreviewContent: メールを既読に設定", mail_id=mail_id)

            # メールリスト内の該当アイテムを更新
            self.mail_list_component.mark_mail_as_read(mail_id)

            # 未読フラグを更新
            mail["unread"] = 0

        # MailContentViewerコンポーネントにViewModelを設定
        self.mail_content_viewer.viewmodel = self.viewmodel

        # メール内容を表示
        self.mail_content_viewer.show_mail_content(mail, mail_id)

        # メールリスト内の該当アイテムの背景色を変更して選択状態を示す
        for item in self.mail_list_component.mail_list_view.controls:
            if hasattr(item, "data") and item.data == mail_id:
                item.bgcolor = Colors.SELECTED
            else:
                item.bgcolor = Colors.BACKGROUND
            item.update()

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
        self.mail_content_viewer._show_empty_content()
        self.mail_content_viewer.show_error_message(message)
        self.update()

    def show_no_data_message(self, message):
        """データがない場合のメッセージを表示"""
        self.logger.info("PreviewContent: データなしメッセージ表示", message=message)

        # メールリストをクリア
        self.mail_list_component.mail_list_view.controls.clear()
        self.mail_list_component.mail_list_view.controls.append(
            Styles.container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.WARNING_AMBER_ROUNDED,
                            size=40,
                            color=ft.colors.AMBER,
                        ),
                        Styles.subtitle(
                            "メールデータがありません",
                            color=Colors.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER,
                            weight=ft.FontWeight.BOLD,
                        ),
                        Styles.caption(
                            message,
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

    def _load_keywords(self) -> list[str]:
        """キーワードをファイルから読み込む"""
        keywords = []
        try:
            with open("config/keywords.txt", "r", encoding="utf-8") as file:
                for line in file:
                    keyword = line.strip()
                    if keyword:  # 空行を除外
                        keywords.append(keyword)
            self.logger.info(f"キーワード読み込み完了: {len(keywords)}件")
        except Exception as e:
            self.logger.error(f"キーワード読み込みエラー: {str(e)}")
        return keywords

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
                        color=Colors.TEXT_SECONDARY,
                    ),
                    Styles.caption(
                        f"{len(mail['attachments'])}個の添付ファイル",
                    ),
                ],
                spacing=2,
            )
            if mail.get("attachments")
            else ft.Container(width=0)
        )

        # メール本文
        content = mail["content"]
        content_lines = content.split("\n")
        is_truncated = len(content_lines) > 5

        # メール本文を表示するコンテナ
        content_container = Styles.card(
            content=self.styled_text.generate_styled_text(
                "\n".join(content_lines[:5]) + ("..." if is_truncated else ""),
                self.keywords,
                None,
                None,
            ),
            padding=10,
            border_radius=5,
            # データに表示状態を保存
            data={
                "expanded": False,
                "full_text": content,
                "preview_text": "\n".join(content_lines[:5])
                + ("..." if is_truncated else ""),
            },
        )

        # 続きを見るボタン
        expand_button = Styles.clickable_container(
            content=ft.Row(
                [
                    Styles.text(
                        "続きを見る",
                        color=Colors.ACTION,
                        size=12,
                    ),
                    ft.Icon(
                        name=ft.icons.EXPAND_MORE,
                        color=Colors.ACTION,
                        size=16,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5,
            ),
            padding=5,
            border_radius=15,
            alignment=ft.alignment.center,
            on_click=lambda e, container=content_container: self._toggle_mail_content_container(
                e, container
            ),
            visible=is_truncated,
            height=30,
            bgcolor=ft.colors.with_opacity(0.05, Colors.ACTION),
        )

        return Styles.container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            Styles.container(
                                content=Styles.text(
                                    f"#{index+1}",
                                    color=Colors.TEXT_ON_PRIMARY,
                                    text_align=ft.TextAlign.CENTER,
                                    size=12,
                                ),
                                bgcolor=(
                                    Colors.ACTION
                                    if mail.get("unread", 0)
                                    else Colors.TEXT_SECONDARY
                                ),
                                border_radius=15,
                                width=30,
                                height=20,
                                alignment=ft.alignment.center,
                            ),
                            Styles.caption(
                                mail["date"],
                            ),
                            Styles.subtitle(
                                f"送信者: {sender_name}",
                                size=12,
                                expand=True,
                            ),
                            attachments_icon,
                            # 新しいフラグボタンを使用
                            ft.Container(
                                content=self.create_flag_button(
                                    mail["id"], mail.get("flagged", False)
                                ),
                                alignment=ft.alignment.center_right,
                                expand=True,
                            ),
                        ],
                        spacing=5,
                        expand=True,
                    ),
                    content_container,
                    expand_button,
                ],
                spacing=5,
            ),
            padding=5,
            bgcolor=(
                Colors.SELECTED_LIGHT if mail.get("unread", 0) else Colors.BACKGROUND
            ),
            border_radius=5,
            border=ft.border.all(1, Colors.BORDER),
        )

    def _on_expand_button_hover(self, e):
        """展開ボタンのホバー効果"""
        # マウスが入ったとき
        if e.data == "true":
            e.control.bgcolor = ft.colors.with_opacity(0.1, Colors.ACTION)
        # マウスが出たとき
        else:
            e.control.bgcolor = ft.colors.with_opacity(0.05, Colors.ACTION)
        e.control.update()

    def _toggle_mail_content_container(self, e, content_container):
        """メール内容の全文表示/折りたたみを切り替える"""
        self.logger.info("PreviewContent: メール内容表示切り替え")

        # 現在の表示状態を確認
        container_data = content_container.data
        is_expanded = container_data.get("expanded", False)

        # ボタンを取得 (コンテナからアイコンを取得)
        button = e.control
        button_icon = button.content.controls[1]
        button_text = button.content.controls[0]

        if is_expanded:
            # 折りたたむ
            content_container.content = self.styled_text.generate_styled_text(
                container_data["preview_text"], self.keywords, None, None
            )
            content_container.data["expanded"] = False
            button_text.value = "続きを見る"
            button_icon.name = ft.icons.EXPAND_MORE
        else:
            # 展開する
            content_container.content = self.styled_text.generate_styled_text(
                container_data["full_text"], self.keywords, None, None
            )
            content_container.data["expanded"] = True
            button_text.value = "折りたたむ"
            button_icon.name = ft.icons.EXPAND_LESS

        # 高さを自動調整
        content_container.height = None

        # 更新
        content_container.update()
        button.update()

        self.logger.info(
            "PreviewContent: メール内容表示切り替え完了", expanded=not is_expanded
        )

    def _toggle_thread_sort_order(self, e):
        """会話表示の時系列ソート順を切り替える"""
        self.logger.info(
            "PreviewContent: 会話ソート順切り替え",
            current_order=("新しい順" if self.thread_sort_newest_first else "古い順"),
        )

        # ソート順を反転
        self.thread_sort_newest_first = not self.thread_sort_newest_first

        # ボタンのテキストとアイコンを更新
        button = e.control
        text_control = button.content.controls[0]
        icon_control = button.content.controls[1]

        text_control.value = "新しい順" if self.thread_sort_newest_first else "古い順"
        icon_control.name = (
            ft.icons.ARROW_DOWNWARD
            if self.thread_sort_newest_first
            else ft.icons.ARROW_UPWARD
        )

        # ホバー状態を保持
        is_hovered = button.data.get("is_hovered", False)
        button.bgcolor = Colors.ACTION_DARK if is_hovered else Colors.ACTION

        button.update()

        # 現在表示中の会話グループを再表示
        for group_id, mails in self.thread_containers.items():
            # 現在選択されているグループを特定
            for item in self.mail_list_component.mail_list_view.controls:
                if (
                    hasattr(item, "data")
                    and item.data == group_id
                    and item.bgcolor == Colors.SELECTED
                ):
                    self._show_thread(mails)
                    break

        self.logger.info(
            "PreviewContent: 会話ソート順切り替え完了",
            new_order="新しい順" if self.thread_sort_newest_first else "古い順",
        )

    def _on_ai_review_refresh(self, e):
        """AIレビューの再評価ボタンがクリックされたときの処理"""
        self.logger.info("PreviewContent: AIレビュー再評価リクエスト")

        # 再評価中の表示
        ai_review_section = e.control.parent.parent.parent

        # 読み込み中表示に切り替え
        ai_review_section.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            name=ft.icons.PSYCHOLOGY_ALT,
                            size=16,
                            color=Colors.ACTION,
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
                                color=Colors.ACTION,
                            ),
                            ft.Text("AIレビュー (更新済み)", weight="bold"),
                            Styles.action_icon_button(
                                icon=ft.icons.REFRESH,
                                tooltip="AIに再評価させる",
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
                                            opacity=1.0,
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
                                        self._create_animated_point(
                                            "重要な期限が近づいています", 100
                                        ),
                                        self._create_animated_point(
                                            "複数の関係者への連絡が必要です", 300
                                        ),
                                        self._create_animated_point(
                                            "添付ファイルに重要な情報が含まれています",
                                            500,
                                            is_important=True,
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

    def _create_animated_point(self, text, delay_ms, is_important=False):
        """アニメーション付きのポイントを作成"""
        return Styles.container(
            content=Styles.text(
                f"• {text}",
                size=14,
                color=Colors.ERROR if is_important else None,
                weight="bold" if is_important else None,
            ),
            opacity=1.0,
            data={"delay": delay_ms, "text": text},
        )

    def _on_refresh_button_hover(self, e):
        """更新ボタンのホバー効果"""
        # マウスが入ったとき
        if e.data == "true":
            e.control.bgcolor = ft.colors.with_opacity(0.1, Colors.ACTION)
        # マウスが出たとき
        else:
            e.control.bgcolor = None
        e.control.update()

    def _toggle_flag(self, mail_id, is_flagged):
        """メールのフラグ状態を切り替える"""
        self.logger.info("PreviewContent: メールフラグ切り替え", mail_id=mail_id)

        # フラグ状態をViewModelに保存
        if self.viewmodel:
            self.viewmodel.set_mail_flag(mail_id, is_flagged)

            # メールリスト全体を更新する代わりに、現在のメールリストアイテムのみを更新
            for item in self.mail_list_component.mail_list_view.controls:
                if hasattr(item, "data") and item.data == mail_id:
                    # このメールアイテムにフラグ表示があれば更新
                    for row in item.content.controls:
                        if (
                            isinstance(row, ft.Row) and len(row.controls) > 3
                        ):  # フラグアイコンがある行
                            for control in row.controls:
                                # フラグアイコンを探す
                                if (
                                    hasattr(control, "content")
                                    and isinstance(control.content, ft.Icon)
                                    and control.content.name
                                    in [ft.icons.FLAG, ft.icons.FLAG_OUTLINED]
                                ):
                                    # フラグを更新
                                    control.content.name = (
                                        ft.icons.FLAG
                                        if is_flagged
                                        else ft.icons.FLAG_OUTLINED
                                    )
                                    control.content.color = (
                                        ft.colors.RED if is_flagged else ft.colors.GREY
                                    )
                                    control.visible = True
                                    control.width = 42
                    item.update()
                    break

        self.logger.info(
            "PreviewContent: メールフラグ切り替え完了",
            mail_id=mail_id,
            flagged=is_flagged,
        )

    def on_group_by_thread_changed(self, e):
        """会話ごとに集約するフラグを切り替える"""
        self.logger.info(
            "PreviewContent: 会話ごとに集約フラグ切り替え開始",
            value=e.control.value if hasattr(e, "control") else e,
            current_group_by_thread=self.group_by_thread,
        )

        # フラグを切り替え
        if hasattr(e, "control"):
            # イベントオブジェクトの場合
            self.group_by_thread = e.control.value
            self.logger.debug("PreviewContent: イベントオブジェクトから値を取得")
        else:
            # 直接値が渡された場合
            self.group_by_thread = e
            self.logger.debug("PreviewContent: 直接値が渡された")

        self.logger.debug(
            "PreviewContent: group_by_threadフラグを更新",
            new_value=self.group_by_thread,
        )

        # メール一覧コンポーネントのフラグも更新
        self.mail_list_component.group_by_thread = self.group_by_thread
        self.logger.debug(
            "PreviewContent: mail_list_componentのフラグを更新",
            component_value=self.mail_list_component.group_by_thread,
        )

        # メール一覧を再読み込み
        self.logger.debug("PreviewContent: load_all_mailsを呼び出し")
        self.load_all_mails()

        self.logger.info(
            "PreviewContent: 会話ごとに集約フラグ切り替え完了",
            group_by_thread=self.group_by_thread,
        )

    def _display_grouped_mails(self, mails):
        """会話ごとにグループ化されたメールを表示"""
        self.logger.info("PreviewContent: 会話ごとにグループ化されたメール表示開始")

        # 会話コンテナを初期化
        self.thread_containers = {}

        # 現在のコンテナの状態をログ出力
        self.logger.debug(
            "PreviewContent: 会話コンテナを初期化しました",
            previous_count=len(self.thread_containers),
        )

        # thread_idでグループ化
        threads = {}
        for mail in mails:
            # thread_idがない場合は単独のメールとして扱う
            if not mail.get("thread_id"):
                # メールIDをキーとして使用
                thread_key = f"single_{mail['id']}"
                if thread_key not in threads:
                    threads[thread_key] = []
                threads[thread_key].append(mail)
                continue

            # thread_id全体をそのまま使用
            thread_id = mail["thread_id"]

            if thread_id not in threads:
                threads[thread_id] = []
            threads[thread_id].append(mail)

        # グループ化されたメールのログ
        self.logger.debug(
            "PreviewContent: 会話グループ化結果",
            thread_count=len(threads),
            thread_keys=list(threads.keys())[:5] if threads else [],
        )

        # グループごとにリストに追加
        for thread_key, mails_in_thread in threads.items():
            # 会話内のメールを日付順にソート
            sorted_mails = sorted(
                mails_in_thread,
                key=lambda x: x["date"],
                reverse=self.thread_sort_newest_first,
            )

            # 会話グループ用の識別子を作成（conv_プレフィックスを付与）
            # プレフィックスが既にある場合は追加しない
            if thread_key.startswith("conv_"):
                thread_id = thread_key
            else:
                thread_id = f"conv_{thread_key}"

            self.logger.debug(
                "PreviewContent: 会話グループ作成",
                original_key=thread_key,
                thread_id=thread_id,
                mail_count=len(sorted_mails),
                first_mail_id=(
                    sorted_mails[0].get("id", "不明") if sorted_mails else "なし"
                ),
            )

            # キャッシュに保存
            self.thread_containers[thread_id] = sorted_mails

            # メールリストが空でないことを確認
            if not sorted_mails:
                self.logger.warning(
                    "PreviewContent: 会話グループのメールリストが空です",
                    thread_id=thread_id,
                )
                continue

            # 会話の代表的な件名を取得（最新のメールの件名を使用）
            subject = sorted_mails[0].get("subject") or "(件名なし)"

            # 件名が文字列でない場合は修正
            if not isinstance(subject, str):
                subject = "(件名なし)"
                self.logger.warning(
                    "PreviewContent: 会話の件名が文字列ではありません",
                    thread_id=thread_id,
                    subject_type=type(subject).__name__,
                )

            # グループのヘッダーアイテムを作成
            unread_count = sum(1 for mail in sorted_mails if mail.get("unread", 0))
            attachment_count = sum(
                1 for mail in sorted_mails if mail.get("attachments", [])
            )

            # AIレビュースコアを取得
            ai_score = 0
            risk_color = ft.colors.GREEN  # デフォルトは緑（安全）

            # メールからAIレビュー情報を取得
            for mail in sorted_mails:
                if mail.get("ai_review"):
                    ai_review = mail.get("ai_review", {})
                    if isinstance(ai_review, dict):
                        # スコア情報を取得（0～10の範囲）
                        score = ai_review.get("score", 0)
                        if isinstance(score, int) or isinstance(score, float):
                            ai_score = score
                            # スコアに応じた色分け
                            if ai_score >= 4:
                                risk_color = ft.colors.RED
                            elif ai_score >= 1:
                                risk_color = ft.colors.YELLOW
                            else:
                                risk_color = ft.colors.GREEN
                            break  # AIレビュー情報が見つかったらループを抜ける

            try:
                thread_header = ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Text(
                                            f"{ai_score}",  # メール数の代わりにAIスコアを表示
                                            color=ft.colors.WHITE,
                                            text_align=ft.TextAlign.CENTER,
                                            size=12,
                                        ),
                                        bgcolor=risk_color,  # AIスコアに基づく色設定
                                        border_radius=15,
                                        width=25,
                                        height=20,
                                        alignment=ft.alignment.center,
                                        tooltip=f"AIリスクスコア: {ai_score}",
                                    ),
                                    ft.Text(
                                        subject,
                                        weight="bold" if unread_count else "normal",
                                        expand=True,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    (
                                        ft.Text(
                                            f"{unread_count}件の未読",
                                            size=12,
                                            color=ft.colors.BLUE,
                                        )
                                        if unread_count
                                        else ft.Container(width=0)
                                    ),
                                    (
                                        ft.Icon(
                                            name=ft.icons.ATTACH_FILE,
                                            size=14,
                                            color=ft.colors.GREY,
                                        )
                                        if attachment_count
                                        else ft.Container(width=0)
                                    ),
                                ],
                                spacing=5,
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        f"最新: {sorted_mails[0].get('date', '不明な日時')}",
                                        size=12,
                                        color=ft.colors.GREY,
                                        expand=True,
                                    ),
                                    ft.Text(
                                        f"メール数: {len(sorted_mails)}",
                                        size=12,
                                        color=ft.colors.GREY,
                                    ),
                                ],
                                spacing=5,
                            ),
                        ],
                        spacing=2,
                    ),
                    padding=10,
                    border_radius=5,
                    on_click=lambda e, cid=thread_id: self._show_thread(
                        self.thread_containers[cid], cid
                    ),
                    data=thread_id,
                    ink=True,
                    bgcolor=ft.colors.WHITE,
                    border=ft.border.all(1, ft.colors.BLACK12),
                    margin=ft.margin.only(bottom=5),
                )

                self.mail_list_component.mail_list_view.controls.append(thread_header)
            except Exception as e:
                self.logger.error(
                    "PreviewContent: 会話ヘッダー作成中にエラーが発生",
                    error=str(e),
                    thread_id=thread_id,
                )

        # 会話コンテナの内容をログ出力
        self.logger.debug(
            "PreviewContent: 会話コンテナ作成完了",
            container_count=len(self.thread_containers),
            container_keys=(
                list(self.thread_containers.keys())[:5]
                if self.thread_containers
                else []
            ),
        )

        self.logger.info(
            "PreviewContent: 会話ごとにグループ化されたメール表示完了",
            thread_count=len(threads),
        )

    def _show_thread(self, mails=None, thread_id=None):
        """会話内容を表示"""
        self.logger.info(
            "PreviewContent: 会話内容表示",
            mail_count=len(mails) if isinstance(mails, list) else 0,
            thread_id=thread_id,
        )

        # 詳細なデバッグ情報
        self.logger.debug(
            "PreviewContent: _show_thread引数詳細",
            mails_type=type(mails).__name__,
            mails_is_list=isinstance(mails, list),
            thread_id_type=(type(thread_id).__name__ if thread_id else "None"),
            thread_id=thread_id,
        )

        if isinstance(mails, str):
            # mailsが文字列の場合、それは会話IDとして扱い、本来のmailsとthread_idを入れ替える
            self.logger.warning(
                "PreviewContent: mails引数が文字列です。会話IDとして処理します",
                mails_as_string=mails,
                original_thread_id=thread_id,
            )
            thread_id = mails  # 文字列をthread_idとして設定
            mails = []  # mailsを空リストにリセット

            # 会話コンテナから会話IDに対応するメールリストを取得
            if thread_id in self.thread_containers:
                mails = self.thread_containers[thread_id]
                self.logger.debug(
                    "PreviewContent: 会話IDからメールを取得",
                    thread_id=thread_id,
                    mail_count=len(mails),
                )
        elif mails is None:
            # mailsがNoneの場合は空リストに変換
            self.logger.warning(
                "PreviewContent: mails引数がNoneです", thread_id=thread_id
            )
            mails = []
        elif not isinstance(mails, list):
            self.logger.warning(
                "PreviewContent: メールデータがリスト型ではありません",
                type=type(mails).__name__ if mails is not None else "None",
            )
            mails = []

        # mails引数の内容検証
        if isinstance(mails, list) and mails:
            if not all(isinstance(mail, dict) for mail in mails):
                self.logger.warning(
                    "PreviewContent: メールリストに辞書型でない要素が含まれています",
                    mail_types=[type(mail).__name__ for mail in mails[:5]],
                )
                # 辞書型でない要素をフィルタリング
                mails = [mail for mail in mails if isinstance(mail, dict)]

            # 残ったメールが有効かを確認
            for i, mail in enumerate(mails[:5]):  # 最初の5件だけログ出力
                self.logger.debug(
                    "PreviewContent: メールデータ検証",
                    idx=i,
                    mail_id=mail.get("id", "不明"),
                    has_content="content" in mail,
                    has_subject="subject" in mail,
                    has_sender="sender" in mail,
                    has_date="date" in mail,
                )

            # 必須フィールドを持たないメールをフィルタリング
            mails = [mail for mail in mails if "id" in mail and "date" in mail]

        # mailsデータが空の場合のエラーハンドリング
        if not mails:
            self.logger.warning(
                "PreviewContent: メールデータが空です", thread_id=thread_id
            )

        # mailsが空でthread_idが指定されている場合、会話コンテナから取得を試みる
        if (not mails or len(mails) == 0) and thread_id:
            # まず完全一致で検索
            if thread_id in self.thread_containers:
                mails = self.thread_containers[thread_id]
                self.logger.debug(
                    "PreviewContent: 会話コンテナからメールを取得 (完全一致)",
                    thread_id=thread_id,
                    mail_count=len(mails),
                )
            # conv_プレフィックスがない場合は追加して検索
            elif (
                not thread_id.startswith("conv_")
                and f"conv_{thread_id}" in self.thread_containers
            ):
                mails = self.thread_containers[f"conv_{thread_id}"]
                self.logger.debug(
                    "PreviewContent: 会話コンテナからメールを取得 (プレフィックス追加)",
                    original_id=thread_id,
                    modified_id=f"conv_{thread_id}",
                    mail_count=len(mails),
                )
            # conv_プレフィックスがある場合は削除して検索
            elif (
                thread_id.startswith("conv_")
                and thread_id[5:] in self.thread_containers
            ):
                mails = self.thread_containers[thread_id[5:]]
                self.logger.debug(
                    "PreviewContent: 会話コンテナからメールを取得 (プレフィックス削除)",
                    original_id=thread_id,
                    modified_id=thread_id[5:],
                    mail_count=len(mails),
                )
            else:
                self.logger.warning(
                    "PreviewContent: 指定された会話IDのメールが見つかりません",
                    thread_id=thread_id,
                )

                # 会話コンテナの内容をデバッグ出力
                container_keys = list(self.thread_containers.keys())
                self.logger.debug(
                    "PreviewContent: 利用可能な会話コンテナ一覧",
                    container_count=len(container_keys),
                    sample_keys=(
                        container_keys[:5]
                        if len(container_keys) > 5
                        else container_keys
                    ),
                )

        # メールリスト内の全アイテムの選択状態をリセット
        for item in self.mail_list_component.mail_list_view.controls:
            # 選択されたアイテムだけ色を変更
            if thread_id and hasattr(item, "data") and item.data == thread_id:
                item.bgcolor = Colors.SELECTED
                self.logger.debug(
                    "PreviewContent: 選択アイテムの背景色を変更",
                    item_id=item.data,
                    thread_id=thread_id,
                )
            else:
                item.bgcolor = Colors.BACKGROUND
            item.update()

        # メール内容表示をクリア
        self.mail_content_viewer._show_empty_content()

        if not mails or len(mails) == 0:
            self.logger.warning("PreviewContent: 表示するメールデータがありません")
            self._show_empty_mail_content()
            return

        # 会話内のメールを時系列順に並べ替え
        sorted_mails = sorted(
            mails,
            key=lambda x: x["date"],
            reverse=self.thread_sort_newest_first,
        )

        # メールを既読にする
        for mail in sorted_mails:
            if mail.get("unread", 0):
                self.viewmodel.mark_as_read(mail["id"])
                mail["unread"] = 0

        # メールデータの整合性チェックと対応
        cleaned_mails = []
        for mail in sorted_mails:
            # 辞書のキーを確認して初期化
            mail_copy = mail.copy()  # 元のオブジェクトを保護するためにコピー

            # 最低限必要な項目の確認と初期化
            if "id" not in mail_copy:
                self.logger.warning("PreviewContent: メールにIDがありません")
                continue  # IDがない場合はスキップ

            # 必須項目の設定
            required_fields = {
                "sender": "不明 <unknown@example.com>",
                "recipient": "不明 <unknown@example.com>",
                "subject": "(件名なし)",
                "content": "",
                "date": "不明な日時",
                "unread": 0,
                "flagged": False,
                "attachments": [],
            }

            for field, default_value in required_fields.items():
                if field not in mail_copy or mail_copy[field] is None:
                    mail_copy[field] = default_value
                    self.logger.debug(
                        f"PreviewContent: メールの{field}フィールドを初期化しました",
                        mail_id=mail_copy["id"],
                    )

            # 型チェックと修正
            if not isinstance(mail_copy["content"], str):
                mail_copy["content"] = (
                    str(mail_copy["content"])
                    if mail_copy["content"] is not None
                    else ""
                )

            if not isinstance(mail_copy["attachments"], list):
                mail_copy["attachments"] = []

            cleaned_mails.append(mail_copy)

        if not cleaned_mails:
            self.logger.warning(
                "PreviewContent: クリーニング後にメールデータがありません"
            )
            self._show_empty_mail_content()
            return

        # クリーンアップしたメールに切り替え
        sorted_mails = cleaned_mails

        # ソート順切り替えボタン
        sort_button = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "新しい順" if self.thread_sort_newest_first else "古い順",
                        color=Colors.TEXT_ON_ACTION,
                        size=14,
                    ),
                    ft.Icon(
                        name=(
                            ft.icons.ARROW_DOWNWARD
                            if self.thread_sort_newest_first
                            else ft.icons.ARROW_UPWARD
                        ),
                        color=Colors.TEXT_ON_ACTION,
                        size=18,
                    ),
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=Colors.ACTION,
            padding=ft.padding.only(left=12, right=12, top=8, bottom=8),
            border_radius=4,
            on_click=self._toggle_thread_sort_order,
            # ホバー効果の追加
            data={"is_hovered": False},
            on_hover=self._on_sort_button_hover,
        )

        # メール内容表示
        try:
            self.mail_content_viewer.show_thread_content(sorted_mails)

            # AIレビューセクションの後にソートボタンを配置
            if len(self.mail_content_viewer.content_column.controls) >= 3:
                # AIレビューセクションとメール一覧の間にソートボタンを追加
                self.mail_content_viewer.content_column.controls.insert(
                    2,  # AIレビューセクションが1番目(0-indexed)、メール一覧が2番目の位置
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("メール表示順:", size=14),
                                sort_button,
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            spacing=10,
                        ),
                        padding=ft.padding.only(right=10, top=10),
                    ),
                )
                self.mail_content_viewer.update()
        except Exception as e:
            self.logger.error(
                "PreviewContent: メール内容表示中にエラーが発生", error=str(e)
            )
            self.mail_content_viewer._show_empty_content()
            self.mail_content_viewer.show_error_message(
                f"メール内容の表示中にエラーが発生しました: {str(e)}"
            )

        self.update()
        self.logger.info(
            "PreviewContent: 会話内容表示完了",
            mail_count=len(sorted_mails),
            thread_id=thread_id,
        )

    def _on_hover_effect(self, e):
        """フラグボタンのホバー効果"""
        # マウスが入ったとき
        if e.data == "true":
            e.control.bgcolor = ft.colors.with_opacity(0.1, Colors.TEXT_SECONDARY)
        # マウスが出たとき
        else:
            e.control.bgcolor = None
        e.control.update()

    def _on_sort_button_hover(self, e):
        """ソートボタンのホバー効果"""
        # マウスが入ったとき
        if e.data == "true":
            e.control.bgcolor = Colors.ACTION_DARK
            e.control.data["is_hovered"] = True
        # マウスが出たとき
        else:
            e.control.bgcolor = Colors.ACTION
            e.control.data["is_hovered"] = False
        e.control.update()

    def create_flag_button(self, mail_id, is_flagged):
        """フラグボタンを作成"""
        return Styles.clickable_container(
            content=ft.Icon(
                name=ft.icons.FLAG if is_flagged else ft.icons.FLAG_OUTLINED,
                size=32,
                color=Colors.ERROR if is_flagged else Colors.TEXT_SECONDARY,
            ),
            tooltip=(
                "フラグを解除する"
                if is_flagged
                else "問題のあるメールとしてフラグを立てる"
            ),
            width=42,
            height=42,
            border_radius=21,
            on_click=lambda e, mid=mail_id: self._toggle_flag(mid, not is_flagged),
            alignment=ft.alignment.center,
            data={"flagged": is_flagged},
            padding=0,
        )
