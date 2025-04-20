"""
プレビューコンテンツ
メールプレビュー画面のコンテンツを提供するクラス
"""

import asyncio
from typing import Any, Dict, List, Optional

import flet as ft

from src.core.logger import get_logger
from src.models.mail.styled_text import StyledText
from src.viewmodels.preview_content_viewmodel import PreviewContentViewModel
from src.views.components.mail_content_viewer import MailContentViewer
from src.views.components.mail_list import MailList
from src.views.components.progress_dialog import ProgressDialog
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
        self.contents_viewmodel = contents_viewmodel
        self.logger = get_logger()
        self.logger.info("PreviewContent: 初期化開始")
        self.progress_dialog = ProgressDialog()
        self.floating_action_button = None
        self.task_id = None

        # ダイアログ管理用変数
        self._current_dialog = None
        self._is_dialog_open = False

        # コンポーネント初期化
        self._init_parameters()
        self._init_components()
        self._init_styles()
        self._init_floating_action_button()

        # UIを構築（重要：this was missing）
        self._build()

        # サイズ設定
        self.expand = True

        self.logger.info("PreviewContent: 初期化完了")

    def _reset_click_states(self):
        """クリックポイント状態をリセット（空の実装）"""
        # この関数は空の実装としておく（必要に応じて後で実装）
        pass

    def _init_parameters(self):
        """パラメータの初期化"""
        # ViewModelの初期化（遅延）
        self.viewmodel = None

        # 設定パラメータ
        self.group_by_thread = False
        self.thread_sort_newest_first = True
        self.mail_sort_order = "date_desc"

        # データストア
        self.thread_containers = {}

        # サンプルデータフラグ
        self.use_sample_data = False

    def _init_components(self):
        """コンポーネントの初期化"""
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

        # StyledTextインスタンス
        self.styled_text = StyledText()

        # キーワードリスト
        self.keywords = self._load_keywords()

    def _init_styles(self):
        """スタイルの初期化"""
        # Fletコンテナの設定
        self.padding = AppTheme.CONTENT_PADDING
        self.bgcolor = Colors.BACKGROUND

    def _init_floating_action_button(self):
        """フローティングアクションボタンの初期化"""
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
            on_click=self.on_review_complete,
        )

    def _build(self):
        """UIを構築"""
        self.logger.debug("PreviewContent: UI構築開始")

        # メインコンテンツを設定
        self._build_main_content()

        # コンテナのスタイルを設定
        self.bgcolor = Colors.BACKGROUND

        self.logger.debug("PreviewContent: UI構築完了")

    def _build_main_content(self):
        """メインコンテンツを構築"""
        # 左側のペイン（メールリスト）
        left_pane = self._build_left_pane()

        # 右側のペイン（メール内容表示）
        right_pane = self._build_right_pane()

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

    def _build_left_pane(self):
        """左側のペイン（メールリスト）を構築"""
        return Styles.container(
            content=self.mail_list_component,
            expand=1,
            padding=0,
        )

    def _build_right_pane(self):
        """右側のペイン（メール内容表示）を構築"""
        return Styles.container(
            content=ft.Column(
                [
                    Styles.container(
                        content=Styles.title("メールプレビュー", size=16),
                        padding=10,
                        border=None,
                    ),
                    Styles.styled_container(
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

    def did_mount(self):
        """コンポーネントがマウントされた時の処理"""
        self.logger.info("PreviewContent: マウント処理開始")

        # タスクIDを取得
        self.task_id = self._get_task_id()
        self.logger.debug("PreviewContent: タスクID取得", task_id=self.task_id)

        # ViewModelを初期化
        self._init_viewmodel()

        # ProgressDialogを初期化
        self.progress_dialog.initialize(self.page)

        # FloatingActionButton
        self.page.floating_action_button = self.floating_action_button
        self.logger.info("PreviewContent: FloatingActionButton を設定しました")
        self.page.update()

        # データを読み込む
        self.load_data()

        self.logger.info("PreviewContent: マウント処理完了")

    def _init_viewmodel(self):
        """ViewModelを初期化"""
        self.viewmodel = PreviewContentViewModel(self.task_id)

        # サンプルデータを使用するフラグをViewModelから取得
        self.use_sample_data = self.viewmodel.use_sample_data
        self.logger.debug(
            "PreviewContent: サンプルデータ使用フラグ設定",
            use_sample=self.use_sample_data,
        )

    def will_unmount(self):
        """コンポーネントがアンマウントされる前の処理"""
        self.logger.info("PreviewContent: アンマウント処理開始")

        try:
            # 保留中のフラグ変更をコミット
            if (
                hasattr(self, "viewmodel")
                and self.viewmodel
                and hasattr(self.viewmodel, "commit_flag_changes")
            ):
                self.logger.info("PreviewContent: 保留中のフラグ変更をコミット")
                self.viewmodel.commit_flag_changes()

            self._release_resources()
            self.logger.info("PreviewContent: アンマウント処理完了")
        except Exception as e:
            self.logger.error(f"PreviewContent: アンマウント処理中にエラー - {str(e)}")

    def _release_resources(self):
        """リソースを解放"""
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
            self.logger.debug("PreviewContent: メールコンテンツビューアーをリセット")

        # タスクIDをクリア
        self.task_id = None

        # FloatingActionButtonをクリア
        self.page.floating_action_button = None
        self.page.update()

    def on_dispose(self):
        """リソース解放時の処理"""
        self.logger.info("PreviewContent: リソース解放")
        if self.viewmodel:
            self.viewmodel.close()

    def on_close_button_click(self, e):
        """終了ボタンがクリックされたときの処理"""
        self.logger.info("PreviewContent: 終了ボタンクリック")

        # 保留中のフラグ変更をコミット
        if (
            hasattr(self, "viewmodel")
            and self.viewmodel
            and hasattr(self.viewmodel, "commit_flag_changes")
        ):
            self.logger.info("PreviewContent: 終了前に保留中のフラグ変更をコミット")
            self.viewmodel.commit_flag_changes()

        # コンテンツビューモデルに戻る処理を委譲
        if hasattr(self.contents_viewmodel, "show_home"):
            self.contents_viewmodel.show_home()
        elif hasattr(self.contents_viewmodel, "main_viewmodel") and hasattr(
            self.contents_viewmodel.main_viewmodel, "show_home"
        ):
            self.contents_viewmodel.main_viewmodel.show_home()
        else:
            self.logger.error("PreviewContent: ホーム画面に戻る処理が見つかりません")

    def load_data(self):
        """データを読み込む"""
        self.logger.info("PreviewContent: データ読み込み開始")

        if self.task_id:
            self.logger.debug("PreviewContent: タスクID有効", task_id=self.task_id)
            # ViewModelを初期化
            self.viewmodel = PreviewContentViewModel(self.task_id)

            try:
                # タスク情報を取得して表示を更新
                self._fetch_task_info()

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

    def _fetch_task_info(self):
        """タスク情報を取得"""
        task_info = self.viewmodel.get_task_info()
        if task_info:
            task_name = task_info.get("name", "不明なタスク")
            self.logger.debug("PreviewContent: タスク情報取得", task_name=task_name)

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
        # メールIDの抽出
        mail_id = self._extract_mail_id(e, mail_id)
        self.logger.info(f"PreviewContent: メール内容表示 - mail_id: {mail_id}")

        if not self.viewmodel:
            self.logger.error("PreviewContent: ViewModelが初期化されていません")
            return

        # メール内容を取得（ViewModelで整合性チェック済み）
        mail = self.viewmodel.get_mail_content(mail_id)
        if not mail:
            self.logger.error(
                f"PreviewContent: メール内容取得失敗 - mail_id: {mail_id}"
            )
            return

        # メールを既読に設定
        self._mark_mail_as_read(mail, mail_id)

        # メール内容を表示
        self._display_mail_content(mail, mail_id)

        # メールリスト内の選択状態を更新
        self._update_mail_selection_in_list(mail_id)

        self.logger.info("PreviewContent: メール内容表示完了", mail_id=mail_id)

    def _extract_mail_id(self, e, mail_id):
        """イベントまたはパラメータからメールIDを抽出"""
        if e and not mail_id:
            if hasattr(e, "control") and hasattr(e.control, "data"):
                return e.control.data
            elif hasattr(e, "data"):
                # e自体がmailIdの場合（MailListコンポーネントから直接渡された場合）
                return e.data
            else:
                # メールIDそのものが渡された場合
                return e
        return mail_id

    def _mark_mail_as_read(self, mail, mail_id):
        """メールを既読に設定"""
        if mail.get("unread", 0):
            self.viewmodel.mark_as_read(mail_id)
            self.logger.debug("PreviewContent: メールを既読に設定", mail_id=mail_id)

            # メールリスト内の該当アイテムを更新
            self.mail_list_component.mark_mail_as_read(mail_id)

            # 未読フラグを更新
            mail["unread"] = 0

    def _display_mail_content(self, mail, mail_id):
        """メール内容を表示コンポーネントに設定"""
        # MailContentViewerコンポーネントにViewModelを設定
        self.mail_content_viewer.viewmodel = self.viewmodel

        # メール内容を表示
        self.mail_content_viewer.show_mail_content(mail, mail_id)

    def _update_mail_selection_in_list(self, mail_id):
        """メールリスト内の選択状態を更新"""
        # メールリストコンポーネントの選択状態を更新
        if hasattr(self.mail_list_component, "selected_thread_id"):
            self.mail_list_component.selected_thread_id = mail_id
            self.logger.debug(
                "PreviewContent: メールリストコンポーネントの選択状態を更新",
                thread_id=mail_id,
            )

        # 各アイテムの背景色を更新
        for item in self.mail_list_component.mail_list_view.controls:
            # 選択されたアイテムだけ色を変更
            if mail_id and hasattr(item, "data") and item.data == mail_id:
                item.bgcolor = Colors.SELECTED
                self.logger.debug(
                    "PreviewContent: 選択アイテムの背景色を変更",
                    item_id=item.data,
                    thread_id=mail_id,
                )
            else:
                item.bgcolor = Colors.BACKGROUND
            item.update()

    def download_attachment(self, file_id):
        """添付ファイルをダウンロード"""
        self.logger.info("PreviewContent: 添付ファイルダウンロード", file_id=file_id)

        if not self.viewmodel:
            return

        # ViewModelに処理を委譲
        success = self.viewmodel.download_attachment(file_id)

        # 結果に応じた通知を表示
        self._show_download_notification(success)

    def _show_download_notification(self, success):
        """ダウンロード結果の通知を表示"""
        if success:
            # ダウンロード成功時の通知
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("ファイルをダウンロードしました"),
                action="閉じる",
            )
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
        # ログ出力を修正: messageキーワード引数を重複させない
        self.logger.error(f"PreviewContent: エラーメッセージ表示 - {message}")

        # メール内容表示をクリア
        self.mail_content_viewer._show_empty_content()
        self.mail_content_viewer.show_error_message(message)
        self.update()

    def show_no_data_message(self, message):
        """データがない場合のメッセージを表示"""
        # ログ出力を修正: messageキーワード引数を重複させない
        self.logger.info(f"PreviewContent: データなしメッセージ表示 - {message}")

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
        # 送信者情報
        sender_name, sender_email = self.viewmodel.parse_sender_info(mail["sender"])

        # 添付ファイル情報
        attachments_icon = self._create_attachments_icon(mail)

        # メール本文表示用コンテナ
        content = mail["content"]
        content_container, is_truncated = self._create_content_container(content)

        # 続きを見るボタン
        expand_button = self._create_expand_button(content_container, is_truncated)

        # 全体のコンテナを返す
        return self._create_mail_item_container(
            mail, index, sender_name, attachments_icon, content_container, expand_button
        )

    def _create_attachments_icon(self, mail):
        """添付ファイルアイコンを作成"""
        return (
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

    def _create_content_container(self, content):
        """メール本文表示用コンテナを作成"""
        content_lines = content.split("\n")
        is_truncated = len(content_lines) > 5

        preview_text = "\n".join(content_lines[:5]) + ("..." if is_truncated else "")

        content_container = Styles.styled_container(
            content=self.styled_text.generate_styled_text(
                preview_text,
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
                "preview_text": preview_text,
            },
        )

        return content_container, is_truncated

    def _create_expand_button(self, content_container, is_truncated):
        """続きを見るボタンを作成"""
        return Styles.clickable_container(
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

    def _create_mail_item_container(
        self,
        mail,
        index,
        sender_name,
        attachments_icon,
        content_container,
        expand_button,
    ):
        """メールアイテムのコンテナを作成"""
        return Styles.container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            self._create_item_number_container(mail, index),
                            Styles.caption(mail["date"]),
                            Styles.subtitle(
                                f"送信者: {sender_name}",
                                size=12,
                                expand=True,
                            ),
                            attachments_icon,
                            # フラグボタン
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

    def _create_item_number_container(self, mail, index):
        """アイテム番号コンテナを作成"""
        return Styles.container(
            content=Styles.text(
                f"#{index+1}",
                color=Colors.TEXT_ON_PRIMARY,
                text_align=ft.TextAlign.CENTER,
                size=12,
            ),
            bgcolor=(Colors.ACTION if mail.get("unread", 0) else Colors.TEXT_SECONDARY),
            border_radius=15,
            width=30,
            height=20,
            alignment=ft.alignment.center,
        )

    def _toggle_mail_content_container(self, e, content_container):
        """メール内容の全文表示/折りたたみを切り替える"""
        self.logger.info("PreviewContent: メール内容表示切り替え")

        # 現在の表示状態を確認
        container_data = content_container.data
        is_expanded = container_data.get("expanded", False)

        # ボタンを取得
        button = e.control
        button_icon = button.content.controls[1]
        button_text = button.content.controls[0]

        if is_expanded:
            # 折りたたむ
            self._collapse_mail_content(
                content_container, container_data, button_text, button_icon
            )
        else:
            # 展開する
            self._expand_mail_content(
                content_container, container_data, button_text, button_icon
            )

        # 高さを自動調整
        content_container.height = None

        # 更新
        content_container.update()
        button.update()

        self.logger.info(
            "PreviewContent: メール内容表示切り替え完了", expanded=not is_expanded
        )

    def _collapse_mail_content(
        self, content_container, container_data, button_text, button_icon
    ):
        """メール内容を折りたたむ"""
        content_container.content = self.styled_text.generate_styled_text(
            container_data["preview_text"], self.keywords, None, None
        )
        content_container.data["expanded"] = False
        button_text.value = "続きを見る"
        button_icon.name = ft.icons.EXPAND_MORE

    def _expand_mail_content(
        self, content_container, container_data, button_text, button_icon
    ):
        """メール内容を展開する"""
        content_container.content = self.styled_text.generate_styled_text(
            container_data["full_text"], self.keywords, None, None
        )
        content_container.data["expanded"] = True
        button_text.value = "折りたたむ"
        button_icon.name = ft.icons.EXPAND_LESS

    def _on_expand_button_hover(self, e):
        """展開ボタンのホバー効果"""
        # マウスが入ったとき
        if e.data == "true":
            e.control.bgcolor = ft.colors.with_opacity(0.1, Colors.ACTION)
        # マウスが出たとき
        else:
            e.control.bgcolor = ft.colors.with_opacity(0.05, Colors.ACTION)
        e.control.update()

    def _toggle_thread_sort_order(self, e):
        """会話表示の時系列ソート順を切り替える"""
        self.logger.info(
            "PreviewContent: 会話ソート順切り替え",
            current_order=("新しい順" if self.thread_sort_newest_first else "古い順"),
        )

        # ソート順を反転
        self.thread_sort_newest_first = not self.thread_sort_newest_first

        # UI要素の更新
        self._update_sort_button_ui(e.control)

        # 現在の会話を再表示
        self._reapply_sort_to_current_thread()

        self.logger.info(
            "PreviewContent: 会話ソート順切り替え完了",
            new_order="新しい順" if self.thread_sort_newest_first else "古い順",
        )

    def _update_sort_button_ui(self, button):
        """ソートボタンのUIを更新"""
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

    def _reapply_sort_to_current_thread(self):
        """現在表示中の会話に新しいソート順を適用"""
        for thread_id, mails in self.thread_containers.items():
            # 現在選択されているグループを特定
            for item in self.mail_list_component.mail_list_view.controls:
                if (
                    hasattr(item, "data")
                    and item.data == thread_id
                    and item.bgcolor == Colors.SELECTED
                ):
                    # ソート順を指定して再表示
                    sort_order = (
                        "date_desc" if self.thread_sort_newest_first else "date_asc"
                    )
                    sorted_mails = self.viewmodel.sort_mails(mails, sort_order)
                    self._show_thread(sorted_mails, thread_id)
                    break

    def _on_ai_review_refresh(self, e):
        """AIレビューの再評価ボタンがクリックされたときの処理"""
        self.logger.info("PreviewContent: AIレビュー再評価リクエスト")

        # AIレビューセクションを取得
        ai_review_section = e.control.parent.parent.parent

        # 読み込み中表示に切り替え
        self._show_ai_review_loading(ai_review_section)

        # シミュレーション処理を非同期で開始
        asyncio.create_task(self._simulate_ai_review(ai_review_section))

    def _show_ai_review_loading(self, ai_review_section):
        """AIレビューの読み込み中表示"""
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

    async def _simulate_ai_review(self, ai_review_section):
        """AIレビューのシミュレーション処理"""
        # 処理時間をシミュレート
        await asyncio.sleep(2)

        # 新しい評価結果を表示
        self._update_ai_review_result(ai_review_section)
        self.update()

    def _update_ai_review_result(self, ai_review_section):
        """新しいAIレビュー結果を表示"""
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
                            self._create_risk_score_row(),
                            ft.Text(
                                "この会話には注意が必要な項目があります。期限や重要な決定事項について確認してください。",
                                size=14,
                            ),
                            ft.Row(
                                [
                                    ft.Text("キーポイント:", weight="bold"),
                                ],
                            ),
                            self._create_key_points_column(),
                        ],
                        spacing=10,
                    ),
                    padding=10,
                ),
            ],
            spacing=5,
        )

    def _create_risk_score_row(self):
        """リスクスコア行を作成"""
        return ft.Row(
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
        )

    def _create_key_points_column(self):
        """キーポイント列を作成"""
        return ft.Column(
            [
                self._create_animated_point("重要な期限が近づいています", 100),
                self._create_animated_point("複数の関係者への連絡が必要です", 300),
                self._create_animated_point(
                    "添付ファイルに重要な情報が含まれています",
                    500,
                    is_important=True,
                ),
            ],
            spacing=2,
        )

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

        # フラグ状態をViewModelに保存（UI更新のみ）
        if self.viewmodel:
            success, message = self.viewmodel.set_mail_flag(mail_id, is_flagged)
            if success:
                # メールリスト内のフラグ表示を更新
                self._update_flag_in_mail_list(mail_id, is_flagged)
                # メール詳細表示のフラグも更新
                self._update_flag_in_content_viewer(mail_id, is_flagged)

                # 会話モードがオンの場合、関連する会話内の他のメールも更新
                if self.group_by_thread:
                    self._update_related_thread_flags(mail_id, is_flagged)

                self.logger.info(
                    "PreviewContent: メールフラグ切り替え完了",
                    mail_id=mail_id,
                    flagged=is_flagged,
                    message=str(message),
                )
            else:
                self.logger.error(
                    "PreviewContent: メールフラグ切り替え失敗",
                    mail_id=mail_id,
                    message=str(message),
                )
                # エラーメッセージを表示
                self.show_error_message(str(message))

    def _update_related_thread_flags(self, mail_id, is_flagged):
        """関連する会話内の他のメールのフラグも更新"""
        try:
            # フラグを切り替えたメールを取得
            flagged_mail = self.viewmodel.get_mail_content(mail_id)
            if not flagged_mail or not flagged_mail.get("thread_id"):
                return

            thread_id = flagged_mail.get("thread_id")
            self.logger.debug(
                "PreviewContent: 関連会話内のフラグ更新",
                mail_id=mail_id,
                thread_id=thread_id,
            )

            # スレッド内の他のメールを取得
            thread_mails = self.mail_list_component.get_thread_mails(thread_id)
            if not thread_mails:
                return

            # 関連メールも更新
            for thread_mail in thread_mails:
                related_mail_id = thread_mail.get("id")
                if related_mail_id and related_mail_id != mail_id:
                    # UIの更新のみ行う（ViewModelのキャッシュも更新）
                    self.viewmodel.set_mail_flag(related_mail_id, is_flagged)
                    # メールリストの表示を更新
                    self.mail_list_component.update_flag_status(
                        related_mail_id, is_flagged
                    )
                    self.logger.debug(
                        "PreviewContent: 関連メールのフラグ更新",
                        mail_id=related_mail_id,
                        is_flagged=is_flagged,
                    )
        except Exception as e:
            self.logger.error(
                f"PreviewContent: 関連会話更新エラー - {str(e)}", mail_id=mail_id
            )

    def _update_flag_in_content_viewer(self, mail_id, is_flagged):
        """メール詳細表示のフラグを更新"""
        # MailContentViewerコンポーネントのAPIを使用
        self.mail_content_viewer.update_flag_status(mail_id, is_flagged)
        self.logger.debug(
            "PreviewContent: メール詳細表示内のフラグ更新完了",
            mail_id=mail_id,
            is_flagged=is_flagged,
        )

    def _update_flag_in_mail_list(self, mail_id, is_flagged):
        """メールリスト内のフラグ表示を更新"""
        # メールリストコンポーネントのAPI経由で更新
        self.mail_list_component.update_flag_status(mail_id, is_flagged)
        self.logger.debug(
            "PreviewContent: メールリスト内のフラグ更新完了",
            mail_id=mail_id,
            is_flagged=is_flagged,
        )

    def create_flag_button(self, mail_id, is_flagged):
        """フラグボタンを作成"""
        return ft.IconButton(
            icon=ft.icons.FLAG if is_flagged else ft.icons.FLAG_OUTLINED,
            icon_color=Colors.ERROR if is_flagged else Colors.TEXT_SECONDARY,
            icon_size=32,
            tooltip=(
                "フラグを解除する"
                if is_flagged
                else "問題のあるメールとしてフラグを立てる"
            ),
            on_click=lambda e, mid=mail_id: self._toggle_flag(mid, not is_flagged),
            data={"flagged": is_flagged, "mail_id": mail_id},
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

    def on_group_by_thread_changed(self, e):
        """会話ごとに集約するフラグを切り替える"""
        self.logger.info(
            "PreviewContent: 会話ごとに集約フラグ切り替え開始",
            value=e.control.value if hasattr(e, "control") else e,
            current_group_by_thread=self.group_by_thread,
        )

        # フラグを切り替え
        self._update_group_by_thread_flag(e)

        # メール一覧を再読み込み
        self.logger.debug("PreviewContent: load_all_mailsを呼び出し")
        self.load_all_mails()

        self.logger.info(
            "PreviewContent: 会話ごとに集約フラグ切り替え完了",
            group_by_thread=self.group_by_thread,
        )

    def _update_group_by_thread_flag(self, e):
        """会話ごとに集約するフラグを更新"""
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

    def _show_thread(self, mails=None, thread_id=None):
        """会話内容を表示"""
        self.logger.info(
            "PreviewContent: 会話内容表示",
            mail_count=len(mails) if isinstance(mails, list) else 0,
            thread_id=thread_id,
        )

        # パラメータの検証とメールリストの取得
        mails = self._get_mails_for_thread_display(mails, thread_id)

        # メールリスト内の選択状態を更新
        self._update_thread_selection_in_list(thread_id)

        # メール内容表示をクリア
        self.mail_content_viewer._show_empty_content()

        # メールがない場合は早期リターン
        if not mails or len(mails) == 0:
            self.logger.warning("PreviewContent: 表示するメールデータがありません")
            self._show_empty_mail_content()
            return

        # メールを時系列順にソート
        sorted_mails = self._sort_thread_mails(mails)

        # メールを既読に設定
        self._mark_thread_mails_as_read(sorted_mails)

        # 会話内容を表示
        self._display_thread_content(sorted_mails)

        self.update()
        self.logger.info(
            "PreviewContent: 会話内容表示完了",
            mail_count=len(sorted_mails),
            thread_id=thread_id,
        )

    def _get_mails_for_thread_display(self, mails, thread_id):
        """会話表示用のメールリストを取得"""
        self.logger.debug(
            "PreviewContent: _show_thread引数詳細",
            mails_type=type(mails).__name__,
            mails_is_list=isinstance(mails, list),
            thread_id_type=(type(thread_id).__name__ if thread_id else "None"),
            thread_id=thread_id,
        )

        # mailsが文字列の場合（会話ID）
        if isinstance(mails, str):
            self.logger.warning(
                "PreviewContent: mails引数が文字列です。会話IDとして処理します",
                mails_as_string=mails,
                original_thread_id=thread_id,
            )
            thread_id = mails
            mails = []

            # 会話コンテナからメールリストを取得
            if thread_id in self.thread_containers:
                mails = self.thread_containers[thread_id]

        # mailsがNoneの場合
        elif mails is None:
            self.logger.warning(
                "PreviewContent: mails引数がNoneです", thread_id=thread_id
            )
            mails = []

        # mailsが空でthread_idがある場合
        if (not mails or len(mails) == 0) and thread_id:
            mails = self._find_mails_for_thread_id(thread_id)

        return mails

    def _find_mails_for_thread_id(self, thread_id):
        """指定されたthread_idに対応するメールリストを見つける"""
        # 完全一致で検索
        if thread_id in self.thread_containers:
            mails = self.thread_containers[thread_id]
            self.logger.debug(
                "PreviewContent: 会話コンテナからメールを取得 (完全一致)",
                thread_id=thread_id,
                mail_count=len(mails),
            )
            return mails

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
            return mails

        # conv_プレフィックスがある場合は削除して検索
        elif thread_id.startswith("conv_") and thread_id[5:] in self.thread_containers:
            mails = self.thread_containers[thread_id[5:]]
            self.logger.debug(
                "PreviewContent: 会話コンテナからメールを取得 (プレフィックス削除)",
                original_id=thread_id,
                modified_id=thread_id[5:],
                mail_count=len(mails),
            )
            return mails

        # 見つからない場合
        else:
            self.logger.warning(
                "PreviewContent: 指定された会話IDのメールが見つかりません",
                thread_id=thread_id,
            )
            self._log_available_thread_containers()
            return []

    def _log_available_thread_containers(self):
        """利用可能な会話コンテナ一覧をログ出力"""
        container_keys = list(self.thread_containers.keys())
        self.logger.debug(
            "PreviewContent: 利用可能な会話コンテナ一覧",
            container_count=len(container_keys),
            sample_keys=(
                container_keys[:5] if len(container_keys) > 5 else container_keys
            ),
        )

    def _update_thread_selection_in_list(self, thread_id):
        """メールリスト内の選択状態を更新"""
        # メールリストコンポーネントの選択状態を更新
        if hasattr(self.mail_list_component, "selected_thread_id"):
            self.mail_list_component.selected_thread_id = thread_id
            self.logger.debug(
                "PreviewContent: メールリストコンポーネントの選択状態を更新",
                thread_id=thread_id,
            )

        # 各アイテムの背景色を更新
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

    def _sort_thread_mails(self, mails):
        """会話内のメールを時系列順に並べ替える"""
        sort_order = "date_desc" if self.thread_sort_newest_first else "date_asc"
        return self.viewmodel.sort_mails(mails, sort_order)

    def _mark_thread_mails_as_read(self, mails):
        """会話内のメールを既読に設定"""
        for mail in mails:
            if mail.get("unread", 0):
                self.viewmodel.mark_as_read(mail["id"])
                mail["unread"] = 0

    def _display_thread_content(self, sorted_mails):
        """会話内容をメール内容表示コンポーネントに表示"""
        try:
            # メール内容を表示
            self.mail_content_viewer.show_thread_content(sorted_mails)

            # ソートボタンを追加
            self._add_sort_button_to_content_viewer()
        except Exception as e:
            self.logger.error(
                "PreviewContent: メール内容表示中にエラーが発生", error=str(e)
            )
            self.mail_content_viewer._show_empty_content()
            self.mail_content_viewer.show_error_message(
                f"メール内容の表示中にエラーが発生しました: {str(e)}"
            )

    def _add_sort_button_to_content_viewer(self):
        """メール内容表示コンポーネントにソートボタンを追加"""
        # ソート順切り替えボタン
        sort_button = self._create_sort_button()

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

    def _create_sort_button(self):
        """ソート順切り替えボタンを作成"""
        return ft.Container(
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
            self._log_task_id_error()

        return task_id

    def _log_task_id_error(self):
        """タスクID取得失敗時のログ出力"""
        self.logger.error("PreviewContent: タスクIDの取得に失敗しました")
        # contents_viewmodelの状態を確認
        if hasattr(self.contents_viewmodel, "current_task_id"):
            current_task_id = getattr(self.contents_viewmodel, "current_task_id", None)
            self.logger.debug(
                f"PreviewContent: contents_viewmodel.current_task_id = {current_task_id}"
            )
        # main_viewmodelの状態も確認
        if (
            hasattr(self.contents_viewmodel, "main_viewmodel")
            and self.contents_viewmodel.main_viewmodel
            and hasattr(self.contents_viewmodel.main_viewmodel, "get_current_task_id")
        ):
            main_task_id = self.contents_viewmodel.main_viewmodel.get_current_task_id()
            self.logger.debug(
                f"PreviewContent: main_viewmodel.get_current_task_id()の直接呼び出し結果 = {main_task_id}"
            )

    #
    # 会話グループ表示関連メソッド
    #

    def _display_grouped_mails(self, mails):
        """会話ごとにグループ化されたメールを表示"""
        self.logger.info("PreviewContent: 会話ごとにグループ化されたメール表示開始")

        # 会話コンテナを初期化
        self.thread_containers = {}

        # ViewModelを使用してメールをグループ化
        threads = self.viewmodel.group_mails_by_thread(mails)

        # グループ化されたメールのログ
        self.logger.debug(
            "PreviewContent: 会話グループ化結果",
            thread_count=len(threads),
            thread_keys=list(threads.keys())[:5] if threads else [],
        )

        # グループごとにリストに追加
        for thread_key, mails_in_thread in threads.items():
            # 会話グループを作成
            self._create_thread_group(thread_key, mails_in_thread)

        # 会話コンテナの内容をログ出力
        self._log_thread_containers()

        self.logger.info(
            "PreviewContent: 会話ごとにグループ化されたメール表示完了",
            thread_count=len(threads),
        )

    def _create_thread_group(self, thread_key, mails_in_thread):
        """会話グループを作成"""
        # 会話内のメールを日付順にソート
        sorted_mails = mails_in_thread

        # 会話グループ用の識別子を作成
        thread_id = self._create_thread_id(thread_key)

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
            return

        # 会話ヘッダーを作成してリストに追加
        self._create_and_add_thread_header(thread_id, sorted_mails)

    def _create_thread_id(self, thread_key):
        """会話グループ用の識別子を作成"""
        # プレフィックスが既にある場合は追加しない
        if thread_key.startswith("conv_"):
            return thread_key
        else:
            return f"conv_{thread_key}"

    def _create_and_add_thread_header(self, thread_id, sorted_mails):
        """会話ヘッダーを作成してリストに追加"""
        try:
            # ViewModelから会話の概要情報を取得
            thread_summary = self.viewmodel.get_thread_summary(sorted_mails)

            # ヘッダー情報を抽出
            subject, unread_count, attachment_count, risk_score = (
                self._extract_thread_summary_info(thread_summary)
            )

            # スレッドヘッダーを作成
            thread_header = self._create_thread_header(
                thread_id,
                subject,
                unread_count,
                attachment_count,
                risk_score,
                thread_summary,
            )

            # リストに追加
            self.mail_list_component.mail_list_view.controls.append(thread_header)
        except Exception as e:
            self.logger.error(
                "PreviewContent: 会話ヘッダー作成中にエラーが発生",
                error=str(e),
                thread_id=thread_id,
            )

    def _extract_thread_summary_info(self, thread_summary):
        """会話サマリー情報を抽出"""
        subject = thread_summary["subject"]
        unread_count = thread_summary["unread_count"]
        attachment_count = 1 if thread_summary["has_attachments"] else 0

        # AIスコア情報
        risk_score = thread_summary["risk_score"]

        return subject, unread_count, attachment_count, risk_score

    def _create_thread_header(
        self,
        thread_id,
        subject,
        unread_count,
        attachment_count,
        risk_score,
        thread_summary,
    ):
        """会話ヘッダーを作成"""
        ai_score = risk_score.get("score", 0)
        risk_color = risk_score.get("color", ft.colors.GREEN)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    f"{ai_score}",  # AIスコアを表示
                                    color=ft.colors.WHITE,
                                    text_align=ft.TextAlign.CENTER,
                                    size=12,
                                ),
                                bgcolor=risk_color,  # AIスコアに基づく色設定
                                border_radius=15,
                                width=25,
                                height=20,
                                alignment=ft.alignment.center,
                                tooltip=risk_score.get(
                                    "tooltip", f"AIリスクスコア: {ai_score}"
                                ),
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
                                f"最新: {thread_summary['latest_date']}",
                                size=12,
                                color=ft.colors.GREY,
                                expand=True,
                            ),
                            ft.Text(
                                f"メール数: {thread_summary['mail_count']}",
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
            on_click=lambda e, tid=thread_id: self._show_thread(thread_id=tid),
            data=thread_id,
            ink=True,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.BLACK12),
            margin=ft.margin.only(bottom=5),
        )

    def _log_thread_containers(self):
        """会話コンテナの内容をログ出力"""
        self.logger.debug(
            "PreviewContent: 会話コンテナ作成完了",
            container_count=len(self.thread_containers),
            container_keys=(
                list(self.thread_containers.keys())[:5]
                if self.thread_containers
                else []
            ),
        )

    def on_review_complete(self, e):
        """査閲終了処理"""
        self.logger.info("PreviewContent: 査閲終了ボタンがクリックされました")
        print("査閲終了ボタンがクリックされました")  # 直接コンソール出力

        # 確認ダイアログを表示
        self._show_confirmation_dialog()

    def _show_confirmation_dialog(self):
        """査閲終了確認ダイアログを表示"""
        dialog = ft.AlertDialog(
            modal=True,  # モーダルダイアログとして表示
            title=ft.Text("査閲終了の確認"),
            content=ft.Text(
                "査閲を終了してよろしいですか？\n\n"
                "フラグありメールはOutlookにフラグが設定され、\n"
                "フラグなしメールは別フォルダに移動されます。"
            ),
            actions=[
                ft.TextButton(
                    text="いいえ",
                    on_click=lambda e: self._close_dialog(e, dialog),
                    style=ft.ButtonStyle(
                        color=Colors.TEXT,
                    ),
                ),
                ft.ElevatedButton(
                    text="はい",
                    on_click=lambda e: self._on_confirmation_confirmed(e, dialog),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=4),
                        color=Colors.TEXT_ON_ACTION,
                        bgcolor=Colors.ACTION,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.logger.debug("PreviewContent: 確認ダイアログを作成しました")
        self._show_dialog(dialog)

    def _on_confirmation_confirmed(self, e, dialog):
        """確認ダイアログでYesが選択された場合の処理"""
        # 確認ダイアログを閉じる
        self._close_dialog(e, dialog)

        # ここから本来の査閲終了処理を実行
        self.logger.info("PreviewContent: 査閲終了処理開始")

        try:
            # 処理中表示（ProgressDialogのIndeterminateモードを使用）
            self.progress_dialog.show(
                title="査閲終了",
                content="査閲終了処理中です。しばらくお待ちください...",
                current_value=0,
                max_value=0,  # Indeterminateモード
            )

            # 保留中の変更をDBに確実に保存
            self._commit_pending_changes()

            # フラグが立っていないメールを移動フォルダに移動
            self._move_unflagged_mails_to_destination()

            # ProgressDialogを閉じる
            if self.progress_dialog.is_open:
                self.page.close(self.progress_dialog._dialog)
                self.page.update()

            # 完了メッセージをAlertDialogで表示
            moved_count = getattr(self, "_last_moved_count", 0)
            self._show_completion_dialog(moved_count)

            self.logger.info("PreviewContent: 査閲終了処理完了")
        except Exception as e:
            self.logger.error(f"PreviewContent: 査閲終了処理中にエラー - {str(e)}")

            # ProgressDialogを閉じる
            if hasattr(self, "progress_dialog") and self.progress_dialog.is_open:
                self.page.close(self.progress_dialog._dialog)
                self.page.update()

            # エラーメッセージをAlertDialogで表示
            self._show_error_dialog(str(e))

    def _show_completion_dialog(self, moved_count):
        """完了ダイアログを表示"""
        flag_set_count = getattr(self, "_last_flag_set_count", 0)

        dialog = ft.AlertDialog(
            modal=True,  # モーダルダイアログとして表示
            title=ft.Text("査閲終了"),
            content=ft.Text(
                f"査閲終了処理が完了しました。\n\n"
                f"・フラグなしメール {moved_count} 件を移動しました。\n"
                f"・フラグありメール {flag_set_count} 件にフラグを設定しました。"
            ),
            actions=[
                ft.ElevatedButton(
                    text="OK",
                    on_click=lambda e: self._close_dialog(e, dialog),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.logger.debug("PreviewContent: 完了ダイアログを作成しました")
        self._show_dialog(dialog)

    def _show_error_dialog(self, error_message):
        """エラーダイアログを表示"""
        dialog = ft.AlertDialog(
            modal=True,  # モーダルダイアログとして表示
            title=ft.Text("エラー"),
            content=ft.Text(
                f"査閲終了処理中にエラーが発生しました:\n\n{error_message}"
            ),
            actions=[
                ft.ElevatedButton(
                    text="OK",
                    on_click=lambda e: self._close_dialog(e, dialog),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.logger.debug("PreviewContent: エラーダイアログを作成しました")
        self._show_dialog(dialog)

    def _close_dialog(self, e, dialog):
        """ダイアログを閉じる"""
        self.page.close(dialog)
        self._current_dialog = None
        self._is_dialog_open = False
        self.logger.debug("PreviewContent: ダイアログを閉じます")

    def _commit_pending_changes(self):
        """保留中の変更をDBに確実に保存"""
        self.logger.debug("PreviewContent: 保留中の変更をDBに保存")

        # ViewModelの確認
        if not hasattr(self, "viewmodel") or not self.viewmodel:
            self.logger.warning("PreviewContent: ViewModelが初期化されていません")
            return

        # 保留中のフラグ変更をコミット
        if hasattr(self.viewmodel, "commit_flag_changes"):
            self.logger.info("PreviewContent: 保留中のフラグ変更をコミット")
            self.viewmodel.commit_flag_changes()

        # 保留中の既読変更をコミット
        if hasattr(self.viewmodel, "commit_read_changes"):
            self.logger.info("PreviewContent: 保留中の既読変更をコミット")
            self.viewmodel.commit_read_changes()

    def _move_unflagged_mails_to_destination(self):
        """フラグが立っていないメールを移動フォルダに移動"""
        self.logger.info("PreviewContent: フラグなしメールの移動処理開始")

        # ViewModelの確認
        if not hasattr(self, "viewmodel") or not self.viewmodel:
            self.logger.warning("PreviewContent: ViewModelが初期化されていません")
            return

        # モデルの取得
        model = self.viewmodel.model

        try:
            # 抽出条件からto_folder_idを取得
            to_folder_id = self._get_destination_folder_id(model)

            if not to_folder_id:
                self.logger.warning(
                    "PreviewContent: 移動先フォルダIDが取得できませんでした"
                )
                return

            # Outlookサービスを初期化
            from src.models.outlook.outlook_service import OutlookService

            outlook_service = OutlookService()

            # フラグなしメールを取得して移動
            unflagged_mails = self._get_unflagged_mails(model)
            if not unflagged_mails:
                self.logger.info("PreviewContent: 移動対象のメールはありません")
                self._last_moved_count = 0
            else:
                # メールをOutlook内で移動
                moved_count = 0
                for mail in unflagged_mails:
                    mail_id = mail.get("entry_id")
                    if mail_id:
                        success = outlook_service.move_item(mail_id, to_folder_id)
                        if success:
                            moved_count += 1
                            self.logger.debug(f"メールを移動しました: {mail_id}")
                        else:
                            self.logger.warning(
                                f"メールの移動に失敗しました: {mail_id}"
                            )

                # 移動数を保存（完了ダイアログ用）
                self._last_moved_count = moved_count
                self.logger.info(
                    f"PreviewContent: {moved_count}件のメールを移動しました"
                )

            # フラグありメールのフラグを設定
            flagged_mails = self._get_flagged_mails(model)
            flag_set_count = 0

            if flagged_mails:
                self.logger.info(
                    f"フラグありメール: {len(flagged_mails)}件にフラグを設定します"
                )

                # 定数定義
                FLAG_COMPLETE = 1  # 完了フラグ

                # Outlookアイテムにフラグを設定
                for mail in flagged_mails:
                    mail_id = mail.get("entry_id")
                    if mail_id:
                        try:
                            success = outlook_service.set_flag(
                                mail_id, FLAG_COMPLETE, 2
                            )  # FlagStatus=2は標準フラグ
                            if success:
                                flag_set_count += 1
                                self.logger.debug(
                                    f"メールにフラグを設定しました: {mail_id}"
                                )
                            else:
                                self.logger.warning(
                                    f"メールのフラグ設定に失敗しました: {mail_id}"
                                )
                        except Exception as flag_error:
                            self.logger.warning(
                                f"メールのフラグ設定中にエラー: {mail_id} - {str(flag_error)}"
                            )

                self.logger.info(
                    f"PreviewContent: {flag_set_count}件のメールにフラグを設定しました"
                )
            else:
                self.logger.info("PreviewContent: フラグ設定対象のメールはありません")

            # フラグ設定数も保存（完了ダイアログ用）
            self._last_flag_set_count = flag_set_count

        except Exception as e:
            self.logger.error(f"PreviewContent: メール処理中にエラー - {str(e)}")
            raise

    def _get_destination_folder_id(self, model):
        """移動先フォルダIDを取得"""
        try:
            query = """
                SELECT to_folder_id
                FROM extraction_conditions
                WHERE task_id = ?
                LIMIT 1
            """

            if not hasattr(model, "db_manager") or not model.db_manager:
                self.logger.warning(
                    "PreviewContent: DBマネージャーが初期化されていません"
                )
                return None

            results = model.db_manager.execute_query(query, (self.task_id,))

            if results and len(results) > 0:
                return results[0].get("to_folder_id")
            else:
                self.logger.warning(f"抽出条件が見つかりません: {self.task_id}")
                return None
        except Exception as e:
            self.logger.error(f"移動先フォルダID取得エラー: {str(e)}")
            return None

    def _get_unflagged_mails(self, model):
        """フラグが立っていないメールを取得"""
        try:
            query = """
                SELECT entry_id
                FROM mail_items
                WHERE (flagged = 0 OR flagged IS NULL)
                AND task_id = ?
            """

            if not hasattr(model, "db_manager") or not model.db_manager:
                self.logger.warning(
                    "PreviewContent: DBマネージャーが初期化されていません"
                )
                return []

            results = model.db_manager.execute_query(query, (self.task_id,))

            self.logger.info(f"フラグなしメール: {len(results)}件")
            return results
        except Exception as e:
            self.logger.error(f"フラグなしメール取得エラー: {str(e)}")
            return []

    def _get_flagged_mails(self, model):
        """フラグが立っているメールを取得"""
        try:
            query = """
                SELECT entry_id
                FROM mail_items
                WHERE flagged = 1
                AND task_id = ?
            """

            if not hasattr(model, "db_manager") or not model.db_manager:
                self.logger.warning(
                    "PreviewContent: DBマネージャーが初期化されていません"
                )
                return []

            results = model.db_manager.execute_query(query, (self.task_id,))

            self.logger.info(f"フラグありメール: {len(results)}件")
            return results
        except Exception as e:
            self.logger.error(f"フラグありメール取得エラー: {str(e)}")
            return []

    def _show_dialog(self, dialog):
        """ダイアログを表示する共通メソッド"""
        if hasattr(self, "page") and self.page:
            # 前のダイアログが開いていれば閉じる
            self._close_current_dialog()
            # 新しいダイアログを表示
            self._current_dialog = dialog
            self._is_dialog_open = True
            self.page.open(dialog)
            self.page.update()
            self.logger.debug("PreviewContent: ダイアログを表示しました")

    def _close_current_dialog(self):
        """現在開いているダイアログを閉じる"""
        if self._current_dialog is not None and self._is_dialog_open:
            self.page.close(self._current_dialog)
            self._current_dialog = None
            self._is_dialog_open = False
            self.logger.debug("PreviewContent: ダイアログを閉じました")
