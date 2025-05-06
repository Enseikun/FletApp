"""
メールリストコンポーネント
メール一覧を表示するためのコンポーネント
"""

from typing import Callable, Dict, List, Optional

import flet as ft

from src.core.logger import get_logger
from src.views.components.mail_list_item import MailListItem
from src.views.styles.color import Colors, ComponentColors
from src.views.styles.style import AppTheme, ComponentState, Styles


class MailList(ft.Container):
    """
    メール一覧を表示するコンポーネント
    検索機能、会話ごとの集約表示などの機能を提供
    """

    def __init__(
        self,
        on_mail_selected: Optional[Callable] = None,
        on_refresh: Optional[Callable] = None,
        **kwargs,
    ):
        """
        MailListの初期化

        Args:
            on_mail_selected: メール選択時のコールバック関数
            on_refresh: 更新時のコールバック関数
            **kwargs: その他のキーワード引数
        """
        self.logger = get_logger()
        self.logger.info("MailList: 初期化開始")

        # コールバック関数
        self.on_mail_selected = on_mail_selected
        self.on_refresh = on_refresh
        self.on_sort_order_changed = None
        self.on_group_changed = None

        # 状態変数を初期化
        self.mail_items = {}  # メールIDをキーにしたアイテムのディクショナリ
        self.thread_containers = {}  # 会話IDをキーにしたメールリストのディクショナリ
        self.selected_mail_id = None  # 選択中のメールID（通常モード用）
        self.selected_thread_id = None  # 選択中の会話ID（会話集約モード用）
        self.enable_grouping = False  # 会話ごとに集約するかどうか
        self.grouping_mode = "none"  # グループ化モード（"none", "conversation", "participants", "subject"）
        self.thread_sort_newest_first = True  # 会話内のメールソート順：trueなら新しい順
        self.sort_order = "date_desc"  # メールのソート順（デフォルトは新しい順）

        # 検索結果を保持する変数
        self.last_search_results = []
        self.last_search_term = None
        self.is_search_result_view = False

        # ドロップダウン共通スタイル
        dropdown_width = 180
        dropdown_padding = ft.padding.only(left=10, right=10, bottom=5)
        dropdown_radius = 8
        dropdown_text_size = 12
        dropdown_bgcolor = ft.colors.WHITE
        dropdown_height = 32

        # 検索フィールド
        self.search_field = ft.TextField(
            hint_text="メールを検索...",
            border=ft.InputBorder.NONE,
            expand=True,
            height=40,
            text_size=14,
            content_padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            on_submit=self._on_search,
            on_change=self._on_search_field_change,
        )

        # 検索ボタン
        self.search_button = ft.IconButton(
            icon=ft.icons.SEARCH,
            tooltip="検索",
            icon_color=Colors.PRIMARY,
            on_click=self._on_search,
        )

        # クリアボタン（検索フィールドに値がある場合のみ表示）
        self.clear_button = ft.IconButton(
            icon=ft.icons.CLOSE,
            tooltip="検索をクリア",
            icon_size=18,
            visible=False,
            on_click=self._clear_search,
        )

        # 検索バー
        self.search_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.SEARCH, size=18, color=ft.colors.BLACK54),
                    self.search_field,
                    self.clear_button,
                    self.search_button,
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            border_radius=20,
            bgcolor=ft.colors.with_opacity(0.08, ft.colors.BLACK),
            padding=ft.padding.only(left=8, right=5),
            expand=True,
            height=42,
        )

        # グループ化メニュー
        self.grouping_menu = ft.PopupMenuButton(
            icon=ft.icons.GROUP_WORK,
            tooltip="グループ化の設定",
            items=[
                ft.PopupMenuItem(
                    text="グループ化なし",
                    on_click=lambda e: self._on_group_mode_changed("none"),
                    checked=self.grouping_mode == "none",
                ),
                ft.PopupMenuItem(
                    text="会話IDでグループ化",
                    on_click=lambda e: self._on_group_mode_changed("conversation"),
                    checked=self.grouping_mode == "conversation",
                ),
                ft.PopupMenuItem(
                    text="参加者でグループ化",
                    on_click=lambda e: self._on_group_mode_changed("participants"),
                    checked=self.grouping_mode == "participants",
                ),
                ft.PopupMenuItem(
                    text="件名でグループ化",
                    on_click=lambda e: self._on_group_mode_changed("subject"),
                    checked=self.grouping_mode == "subject",
                ),
            ],
        )

        # 更新ボタン
        self.refresh_button = ft.IconButton(
            icon=ft.icons.REFRESH,
            tooltip="メール一覧を更新",
            on_click=self._on_refresh_clicked,
        )

        # ソートメニュー
        self.sort_menu = ft.PopupMenuButton(
            icon=ft.icons.SORT,
            tooltip="並び替え",
            items=[
                ft.PopupMenuItem(
                    text="日付 (新しい順)",
                    on_click=lambda e: self._on_sort_order_changed("date_desc"),
                    checked=self.sort_order == "date_desc",
                ),
                ft.PopupMenuItem(
                    text="日付 (古い順)",
                    on_click=lambda e: self._on_sort_order_changed("date_asc"),
                    checked=self.sort_order == "date_asc",
                ),
                ft.PopupMenuItem(
                    text="送信者 (昇順)",
                    on_click=lambda e: self._on_sort_order_changed("sender_asc"),
                    checked=self.sort_order == "sender_asc",
                ),
                ft.PopupMenuItem(
                    text="送信者 (降順)",
                    on_click=lambda e: self._on_sort_order_changed("sender_desc"),
                    checked=self.sort_order == "sender_desc",
                ),
                ft.PopupMenuItem(
                    text="リスクスコア (低→高)",
                    on_click=lambda e: self._on_sort_order_changed("risk_score_asc"),
                    checked=self.sort_order == "risk_score_asc",
                ),
                ft.PopupMenuItem(
                    text="リスクスコア (高→低)",
                    on_click=lambda e: self._on_sort_order_changed("risk_score_desc"),
                    checked=self.sort_order == "risk_score_desc",
                ),
            ],
        )

        # 上部ツールバー
        self.top_toolbar = ft.Row(
            [
                ft.Text("メール一覧", weight="bold", size=16),
                ft.Row(
                    [
                        self.refresh_button,
                        self.grouping_menu,
                        self.sort_menu,
                    ],
                    spacing=0,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # メールリスト
        self.mail_list_view = ft.ListView(
            expand=True,
            spacing=AppTheme.SPACING_XS,
            padding=AppTheme.SPACING_XS,
        )

        # メインコンテンツ
        self._init_layout()

        # Containerの初期化
        super().__init__(
            content=self.content,
            expand=True,
            **kwargs,
        )

        self.logger.info("MailList: 初期化完了")

    def _init_layout(self):
        """全体レイアウトを初期化"""
        self.content = ft.Column(
            [
                # ヘッダーセクション
                ft.Container(
                    content=ft.Column(
                        [
                            # 上部ツールバー
                            self.top_toolbar,
                            # 検索バー
                            self.search_bar,
                        ],
                        spacing=10,
                    ),
                    padding=10,
                    bgcolor=Colors.BACKGROUND,
                ),
                # メールリスト
                self.mail_list_view,
            ],
            spacing=0,
            expand=True,
        )

    def _on_refresh_clicked(self, e):
        """更新ボタンがクリックされたときの処理"""
        self.logger.info("MailList: 更新ボタンクリック")
        if self.on_refresh:
            self.on_refresh()

    def _on_search(self, e):
        """検索実行時の処理"""
        search_term = self.search_field.value
        self.logger.info("MailList: 検索実行", search_term=search_term)

        # クリアボタンの表示状態を更新
        self._update_clear_button_visibility()

        # 検索イベントを上位コンポーネントに通知
        if hasattr(self, "on_search") and self.on_search:
            self.on_search(search_term)

    def _clear_search(self, e):
        """検索フィールドをクリアする"""
        self.search_field.value = ""
        self.clear_button.visible = False
        self.clear_button.update()
        self.search_field.update()

        # 検索結果をクリアして全メールを表示
        if hasattr(self, "on_search") and self.on_search:
            self.on_search("")

    def _update_clear_button_visibility(self):
        """検索フィールドの値に基づいてクリアボタンの表示状態を更新"""
        has_value = self.search_field.value and len(self.search_field.value) > 0
        if self.clear_button.visible != has_value:
            self.clear_button.visible = has_value
            self.clear_button.update()

    def _on_mail_item_click(self, e):
        """メールアイテムがクリックされたときの処理"""
        mail_id = e.control.data
        self.logger.info("MailList: メールアイテムクリック", mail_id=mail_id)

        # 選択状態を更新
        self._update_selection(mail_id)

        # コールバックを呼び出し
        if self.on_mail_selected:
            self.on_mail_selected(mail_id)

    def _update_selection(self, mail_id):
        """選択状態を更新"""
        # 前回の選択をリセット
        if self.selected_mail_id and self.selected_mail_id in self.mail_items:
            self.mail_items[self.selected_mail_id].set_selected(False)

        # 新しい選択を設定
        self.selected_mail_id = mail_id
        if mail_id in self.mail_items:
            self.mail_items[mail_id].set_selected(True)

    def _on_group_mode_changed(self, mode):
        """グループ化モードが変更されたときの処理"""
        self.logger.info("MailList: グループ化モード変更", mode=mode)
        self.grouping_mode = mode

        # グループ化状態を更新
        self.enable_grouping = mode != "none"

        # UI表示を更新
        self._update_grouping_ui()

        # 親コンポーネントに通知
        if self.on_group_changed:
            self.on_group_changed(mode)

        self.logger.debug("MailList: グループ化モード変更完了", mode=self.grouping_mode)

    def _update_grouping_ui(self):
        """グループ化設定に応じてUIを更新"""
        # グループ化設定表示を更新
        if hasattr(self, "grouping_menu"):
            # メニュー項目のチェック状態を更新
            for item in self.grouping_menu.items:
                if hasattr(item, "text"):
                    if item.text == "グループ化なし":
                        item.checked = self.grouping_mode == "none"
                    elif item.text == "会話IDでグループ化":
                        item.checked = self.grouping_mode == "conversation"
                    elif item.text == "参加者でグループ化":
                        item.checked = self.grouping_mode == "participants"
                    elif item.text == "件名でグループ化":
                        item.checked = self.grouping_mode == "subject"

            # メニューの更新
            self.grouping_menu.update()

    def _show_thread(self, thread_id):
        """会話内容表示のトリガー"""
        thread_mails = None
        self.logger.debug("MailList: 会話内容表示", thread_id=thread_id)

        # 会話IDが渡されていることを確認
        if not thread_id:
            self.logger.error("MailList: 会話IDが指定されていません")
            return

        # 会話ID毎のメールリストを取得
        if thread_id in self.thread_containers:
            thread_mails = self.thread_containers[thread_id]
            self.logger.debug(
                "MailList: 会話メール取得成功",
                thread_id=thread_id,
                mail_count=len(thread_mails),
            )
        else:
            self.logger.warning(
                "MailList: 指定された会話IDのメールが見つかりません",
                thread_id=thread_id,
            )

            # 追加の検索を試みる
            if thread_id.startswith("conv_"):
                stripped_id = thread_id[5:]
                if stripped_id in self.thread_containers:
                    self.logger.debug(
                        "MailList: プレフィックスを除いたIDでメールを発見",
                        original_id=thread_id,
                        stripped_id=stripped_id,
                    )
                    thread_mails = self.thread_containers[stripped_id]
            elif f"conv_{thread_id}" in self.thread_containers:
                prefixed_id = f"conv_{thread_id}"
                self.logger.debug(
                    "MailList: プレフィックスを追加したIDでメールを発見",
                    original_id=thread_id,
                    prefixed_id=prefixed_id,
                )
                thread_mails = self.thread_containers[prefixed_id]

        # 選択中のスレッドIDを更新
        self.selected_thread_id = thread_id
        self.logger.debug(
            "MailList: 選択中のスレッドIDを更新", selected_thread_id=thread_id
        )

        # 選択状態を更新
        for item in self.mail_list_view.controls:
            if hasattr(item, "data") and item.data == thread_id:
                item.bgcolor = Colors.SELECTED
                self.logger.debug(
                    "MailList: スレッドアイテムの選択状態を更新",
                    item_id=item.data,
                    selected=True,
                )
            else:
                item.bgcolor = Colors.BACKGROUND
            item.update()

        # 会話選択イベントを発火（存在する場合）
        if (
            thread_mails
            and hasattr(self, "on_thread_selected")
            and self.on_thread_selected
        ):
            self.logger.debug(
                "MailList: 会話選択イベント発火",
                thread_id=thread_id,
                mail_count=len(thread_mails),
            )

            try:
                # 明示的に引数の順序を示して呼び出す
                self.on_thread_selected(mails=thread_mails, thread_id=thread_id)
                self.logger.debug("MailList: 会話選択イベント発火完了")
            except Exception as e:
                self.logger.error("MailList: 会話選択イベント発火エラー", error=str(e))
        else:
            self.logger.error(
                "MailList: 会話選択イベントハンドラが設定されていないか、メールが見つかりません"
            )

    def display_mails(self, mails: List[Dict]):
        """
        メールリストを表示する

        Args:
            mails: 表示するメールのリスト
        """
        self.logger.info(
            "MailList: メール一覧表示",
            mail_count=len(mails) if mails else 0,
            grouping_mode=self.grouping_mode,
        )

        # 表示するメールがない場合
        if not mails or len(mails) == 0:
            self.mail_list_view.controls.clear()
            self._show_no_results_message("表示可能なメールがありません")
            self.mail_list_view.update()
            self.update()
            return

        # キャッシュを更新
        self.current_mails = mails

        # リストをクリア
        self.mail_list_view.controls.clear()

        # 検索状態をリセット
        self.is_search_result = False
        self.current_search_term = ""

        # グループ化モードに応じて表示
        if self.grouping_mode == "none":
            # グループ化なし - 個別メール表示
            self._display_individual_mails(mails)
        elif self.grouping_mode == "conversation":
            # 会話IDでグループ化
            self.enable_grouping = True
            self._display_grouped_mails(mails)
        elif self.grouping_mode == "participants":
            # 参加者でグループ化（実装予定）
            self.logger.info("参加者によるグループ化は未実装です - 個別表示に戻します")
            self._display_individual_mails(mails)
        elif self.grouping_mode == "subject":
            # 件名でグループ化（実装予定）
            self.logger.info("件名によるグループ化は未実装です - 個別表示に戻します")
            self._display_individual_mails(mails)
        else:
            # 不明なモード - デフォルトで個別表示
            self.logger.warning(
                f"不明なグループ化モード: {self.grouping_mode} - 個別表示に戻します"
            )
            self._display_individual_mails(mails)

        # 強制更新（見た目を確実に反映）
        self.mail_list_view.update()
        self.update()

        self.logger.info(
            "MailList: メール一覧表示完了",
            mail_count=len(mails),
            displayed_items=len(self.mail_list_view.controls),
            grouping_mode=self.grouping_mode,
        )

    def _display_individual_mails(self, mails: List[Dict]):
        """個別メールを表示する"""
        self.logger.info("MailList: 個別メール表示開始", mail_count=len(mails))

        # グループコンテナをクリア
        self.group_containers = {}

        # メールをソート（すでにソートされている前提）
        for mail in mails:
            # メールアイテムを作成
            mail_item = self._create_mail_item(mail)

            # メールリストに追加
            self.mail_list_view.controls.append(mail_item)

        self.logger.info("MailList: 個別メール表示完了", mail_count=len(mails))

    def _display_grouped_mails(self, mails: List[Dict]):
        """グループ化されたメールを表示する"""
        self.logger.info("MailList: グループ化メール表示", mail_count=len(mails))

        # グループコンテナをクリア
        self.group_containers = {}

        # メールをグループ化
        groups = {}
        for mail in mails:
            group_key = self._get_group_key(mail)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(mail)

        # 各グループをリストに追加
        for group_key, group_mails in groups.items():
            # グループIDを生成
            group_id = (
                f"group_{group_key}"
                if not group_key.startswith("group_")
                else group_key
            )

            # グループコンテナに保存
            self.group_containers[group_id] = group_mails

            # グループヘッダーを作成
            group_header = self._create_group_header(group_id, group_mails)
            self.mail_list_view.controls.append(group_header)

        self.logger.info(
            "MailList: グループ化メール表示完了",
            group_count=len(groups),
            mail_count=len(mails),
        )

    def _on_mail_item_click(self, e):
        """メールアイテムクリック時の処理"""
        # データがない場合は何もしない
        if not hasattr(e, "control") or not hasattr(e.control, "data"):
            self.logger.warning("MailList: クリックされたアイテムにデータがありません")
            return

        # クリックされたデータを取得
        item_data = e.control.data

        self.logger.info(
            "MailList: アイテムクリック",
            item_data=item_data,
            data_type=type(item_data).__name__,
        )

        # グループクリックかメールクリックかを判断
        is_group = False
        if isinstance(item_data, str) and item_data.startswith("group_"):
            is_group = True

        # グループの場合はグループ表示
        if is_group:
            self.logger.debug("MailList: グループヘッダークリック", group_id=item_data)

            # 選択状態を更新
            self.selected_thread_id = item_data
            self.selected_mail_id = None

            # コントロールの選択状態を更新
            self._update_selection_ui(item_data)

            # グループの内容を親コンポーネントに通知
            if self.on_thread_selected:
                # グループに含まれるメールを取得
                group_mails = self.group_containers.get(item_data, [])
                self.on_thread_selected(group_mails, item_data)

        # 個別メールの場合はメール表示
        else:
            self.logger.debug("MailList: メールアイテムクリック", mail_id=item_data)

            # 選択状態を更新
            self.selected_mail_id = item_data
            self.selected_thread_id = None

            # コントロールの選択状態を更新
            self._update_selection_ui(item_data)

            # メール内容を親コンポーネントに通知
            if self.on_mail_selected:
                self.on_mail_selected(e)

    def _update_selection_ui(self, selected_id):
        """UIの選択状態を更新"""
        # 全てのアイテムの背景色をリセット
        for item in self.mail_list_view.controls:
            if hasattr(item, "data"):
                # 選択されたアイテムは強調表示
                if item.data == selected_id:
                    item.bgcolor = Colors.SELECTED
                else:
                    item.bgcolor = Colors.BACKGROUND
                item.update()

    def _create_mail_item(self, mail):
        """メールアイテムを作成"""
        mail_id = mail.get("id", "")
        subject = mail.get("subject", "(件名なし)")
        sender = mail.get("sender", "不明")
        date = mail.get("date", "")
        unread = mail.get("unread", 0)
        flagged = mail.get("flagged", False)
        attachments = mail.get("attachments", [])

        # 送信者名を取得（<>の前の部分）
        sender_name = sender.split("<")[0].strip() if "<" in sender else sender

        # フラグアイコン
        flag_icon = self._create_flag_icon(mail_id, flagged)

        # 添付ファイルアイコン
        attachment_icon = (
            ft.Icon(ft.icons.ATTACH_FILE, size=16, color=Colors.TEXT_SECONDARY)
            if attachments and len(attachments) > 0
            else ft.Container(width=0)
        )

        # メールアイテムを作成
        return ft.Container(
            content=ft.Column(
                [
                    # 1行目：件名、日付
                    ft.Row(
                        [
                            ft.Text(
                                subject,
                                weight="bold" if unread else "normal",
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                            ft.Text(
                                date,
                                size=12,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=5,
                    ),
                    # 2行目：送信者、フラグ、添付ファイル
                    ft.Row(
                        [
                            ft.Text(
                                f"差出人: {sender_name}",
                                size=12,
                                color=Colors.TEXT_SECONDARY,
                                expand=True,
                            ),
                            attachment_icon,
                            flag_icon,
                        ],
                        spacing=5,
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border_radius=5,
            ink=True,
            bgcolor=Colors.BACKGROUND_LIGHT if unread else Colors.BACKGROUND,
            border=ft.border.all(1, Colors.BORDER),
            data=mail_id,
            on_click=self._on_mail_item_click,
        )

    def _create_flag_icon(self, mail_id, is_flagged):
        """フラグアイコンを作成"""
        return ft.Container(
            content=ft.Icon(
                ft.icons.FLAG if is_flagged else ft.icons.FLAG_OUTLINED,
                size=16,
                color=Colors.ERROR if is_flagged else Colors.TEXT_SECONDARY,
            ),
            data={"mail_id": mail_id, "is_flagged": is_flagged},
            width=24,
            height=24,
            border_radius=12,
            tooltip="問題ありとしてマーク" if not is_flagged else "マークを解除",
        )

    def _get_group_key(self, mail):
        """
        メールのグループキーを取得する

        Args:
            mail: 対象のメール情報

        Returns:
            str: グループキー
        """
        # グループ化モードに応じてキーを選択
        if self.grouping_mode == "conversation":
            # 会話IDによるグループ化（従来のもの）
            thread_id = (
                mail.get("thread_id")
                or mail.get("conversation_id")
                or mail.get("mail_id")
            )
            return f"thread_{thread_id}"
        elif self.grouping_mode == "participants":
            # 参加者によるグループ化
            sender = mail.get("sender", "").split("<")[0].strip()
            return f"sender_{sender}"
        elif self.grouping_mode == "subject":
            # 件名によるグループ化
            subject = self._clean_subject(mail.get("subject", ""))
            return f"subject_{subject}"
        else:
            # デフォルト（会話ID）でのグループ化
            thread_id = (
                mail.get("thread_id")
                or mail.get("conversation_id")
                or mail.get("mail_id")
            )
            return f"thread_{thread_id}"

    def _clean_subject(self, subject):
        """件名から返信プレフィックスなどを除去"""
        if not subject:
            return ""

        # 一般的な返信プレフィックス
        prefixes = ["re:", "fw:", "fwd:", "re : ", "fw : ", "fwd : "]

        # 小文字化して比較
        lower_subject = subject.lower()

        # プレフィックスを除去
        for prefix in prefixes:
            if lower_subject.startswith(prefix):
                return subject[len(prefix) :].strip()

        return subject

    def _create_group_header(self, group_id, mails):
        """グループヘッダーを作成"""
        # 最初のメールから情報を取得
        first_mail = mails[0] if mails else {}

        # 件名
        subject = first_mail.get("subject", "(件名なし)")
        if subject.startswith("subject_"):
            subject = subject[8:]  # プレフィックスを除去

        # 未読カウント
        unread_count = sum(1 for mail in mails if mail.get("unread", 0))

        # 添付ファイルの有無
        has_attachments = any(len(mail.get("attachments", [])) > 0 for mail in mails)

        # 最新日時
        latest_date = max((mail.get("date", "") for mail in mails), default="")

        # フラグあり
        has_flags = any(mail.get("flagged", False) for mail in mails)

        # グループヘッダーを作成
        return ft.Container(
            content=ft.Column(
                [
                    # 1行目：件名、未読数
                    ft.Row(
                        [
                            ft.Text(
                                subject,
                                weight="bold" if unread_count else "normal",
                                expand=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            (
                                ft.Container(
                                    content=ft.Text(
                                        f"{unread_count}",
                                        color=Colors.TEXT_ON_PRIMARY,
                                        text_align=ft.TextAlign.CENTER,
                                        size=12,
                                    ),
                                    bgcolor=Colors.PRIMARY,
                                    border_radius=10,
                                    width=24,
                                    height=20,
                                    alignment=ft.alignment.center,
                                )
                                if unread_count
                                else ft.Container(width=0)
                            ),
                        ],
                        spacing=5,
                    ),
                    # 2行目：メール数、日付、アイコン
                    ft.Row(
                        [
                            ft.Text(
                                f"メール：{len(mails)}件",
                                size=12,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            ft.Text(
                                f"最新：{latest_date}",
                                size=12,
                                color=Colors.TEXT_SECONDARY,
                                expand=True,
                            ),
                            (
                                ft.Icon(
                                    ft.icons.ATTACH_FILE,
                                    size=14,
                                    color=Colors.TEXT_SECONDARY,
                                )
                                if has_attachments
                                else ft.Container(width=0)
                            ),
                            (
                                ft.Icon(
                                    ft.icons.FLAG,
                                    size=14,
                                    color=Colors.ERROR,
                                )
                                if has_flags
                                else ft.Container(width=0)
                            ),
                        ],
                        spacing=5,
                    ),
                ],
                spacing=2,
            ),
            padding=10,
            border_radius=5,
            ink=True,
            bgcolor=Colors.BACKGROUND_LIGHT if unread_count else Colors.BACKGROUND,
            border=ft.border.all(1, Colors.BORDER),
            data=group_id,
            on_click=self._on_mail_item_click,
        )

    def display_search_results(self, mails: List[Dict], search_term: str):
        """検索結果を表示"""
        self.logger.info(
            "MailList: 検索結果表示", result_count=len(mails) if mails else 0
        )

        # 検索結果とその情報を保持
        self.last_search_results = mails
        self.last_search_term = search_term
        self.is_search_result_view = True

        # メールリストをクリア
        self.mail_list_view.controls.clear()
        self.mail_items = {}
        self.selected_mail_id = None

        # 検索結果がない場合
        if not mails:
            self._show_no_results_message(search_term)
        else:
            # 検索結果を表示（会話グループ表示モードも考慮）
            if self.enable_grouping:
                self._display_grouped_mails(mails)
            else:
                # 通常表示
                for mail in mails:
                    mail_item = MailListItem(
                        mail_data=mail,
                        on_click=self._on_mail_item_click,
                    )
                    self.mail_items[mail["id"]] = mail_item
                    self.mail_list_view.controls.append(mail_item)

        self.update()
        self.logger.info("MailList: 検索結果表示完了", search_term=search_term)

    def _show_no_results_message(self, search_term: str):
        """検索結果がない場合のメッセージを表示"""
        self.mail_list_view.controls.append(
            Styles.container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.SEARCH_OFF,
                            size=40,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        Styles.subtitle(
                            f"「{search_term}」に一致するメールはありません",
                            color=Colors.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.TextButton(
                            text="すべてのメールを表示",
                            on_click=lambda _: self._on_refresh_clicked(None),
                            style=ft.ButtonStyle(
                                color=Colors.PRIMARY,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=AppTheme.SPACING_SM,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )

    def mark_mail_as_read(self, mail_id):
        """メールを既読としてマーク"""
        if mail_id in self.mail_items:
            self.mail_items[mail_id].mark_as_read()
            self.logger.info("MailList: メールを既読に設定", mail_id=mail_id)

    def _update_flag_icon_in_container(self, container, is_flagged):
        """コンテナ内のフラグアイコンを更新"""
        # コンテナからフラグアイコンを探す
        if hasattr(container, "content") and container.content:
            # Rowを探す
            for control in self._get_all_controls(container):
                if isinstance(control, ft.Container) and hasattr(control, "content"):
                    # アイコンを含むコンテナを探す
                    if isinstance(
                        control.content, ft.Icon
                    ) and control.content.name in [
                        ft.icons.FLAG,
                        ft.icons.FLAG_OUTLINED,
                    ]:
                        # フラグアイコンが見つかった
                        control.content.name = (
                            ft.icons.FLAG if is_flagged else ft.icons.FLAG_OUTLINED
                        )
                        control.content.color = (
                            Colors.ERROR if is_flagged else Colors.TEXT_SECONDARY
                        )
                        if hasattr(control, "data"):
                            control.data["flagged"] = is_flagged
                        if hasattr(control, "tooltip"):
                            control.tooltip = (
                                "フラグを解除する"
                                if is_flagged
                                else "問題のあるメールとしてフラグを立てる"
                            )

                        # 即時更新
                        try:
                            control.update()

                            # 親階層も更新
                            parent = getattr(control, "parent", None)
                            if parent:
                                parent.update()

                                # さらに親も更新
                                grandparent = getattr(parent, "parent", None)
                                if grandparent:
                                    grandparent.update()
                        except Exception as e:
                            self.logger.warning(f"フラグアイコン更新エラー: {str(e)}")

                        return True
        return False

    def _get_all_controls(self, container):
        """コンテナから再帰的にすべてのコントロールを取得"""
        controls = []

        if not container:
            return controls

        # コンテナ自体を追加
        controls.append(container)

        # コンテナの中身を探索
        if hasattr(container, "content"):
            content = container.content
            if content:
                # contentがRow/Columnの場合
                if hasattr(content, "controls"):
                    controls.append(content)
                    for child in content.controls:
                        controls.extend(self._get_all_controls(child))
                else:
                    controls.append(content)

        # controlsプロパティがある場合
        elif hasattr(container, "controls"):
            for child in container.controls:
                controls.extend(self._get_all_controls(child))

        return controls

    def _update_flag_in_cached_mail(self, mail_id, is_flagged):
        """キャッシュされたメールデータのフラグ状態を更新"""
        # キャッシュされたメールリストを更新
        if hasattr(self, "cached_mail_list"):
            for mail in self.cached_mail_list:
                if mail.get("id") == mail_id:
                    mail["flagged"] = is_flagged
                    break

        # スレッドコンテナを更新
        if hasattr(self, "thread_mails"):
            for thread_id, mails in self.thread_mails.items():
                for mail in mails:
                    if mail.get("id") == mail_id:
                        mail["flagged"] = is_flagged
                        break

    def get_thread_mails(self, thread_id: str) -> List[Dict]:
        """スレッドに関連するメールの一覧を取得する"""
        self.logger.debug("MailList: スレッドメール取得開始", thread_id=thread_id)

        # スレッドコンテナから直接取得
        if thread_id in self.thread_containers:
            return self.thread_containers[thread_id]

        # conv_プレフィックスがない場合は追加して検索
        if (
            not thread_id.startswith("conv_")
            and f"conv_{thread_id}" in self.thread_containers
        ):
            return self.thread_containers[f"conv_{thread_id}"]

        # conv_プレフィックスがある場合は削除して検索
        if thread_id.startswith("conv_") and thread_id[5:] in self.thread_containers:
            return self.thread_containers[thread_id[5:]]

        # 前回の検索結果から探す
        if self.last_search_results:
            thread_mails = []
            for mail in self.last_search_results:
                if (
                    mail.get("thread_id") == thread_id
                    or mail.get("thread_id") == thread_id[5:]
                ):
                    thread_mails.append(mail)

            if thread_mails:
                return thread_mails

        self.logger.warning(
            "指定された会話IDのメールが見つかりません", thread_id=thread_id
        )
        return []

    def do_scroll_top(self):
        """リストをトップにスクロール"""
        if hasattr(self, "scroll_container") and self.scroll_container:
            self.scroll_container.scroll_to(offset=0, duration=300)

    def reset(self):
        """リストの状態をリセット"""
        self.logger.info("MailList: リセット")

        # 内部状態のリセット
        self.mail_items = {}
        self.thread_containers = {}
        self.selected_mail_id = None
        self.selected_thread_id = None

        # 検索結果をリセット
        self.last_search_results = []
        self.last_search_term = None
        self.is_search_result_view = False

        # UIのリセット
        if hasattr(self, "mail_list_view"):
            self.mail_list_view.controls.clear()

        # 検索フィールドのリセット
        if hasattr(self, "search_field"):
            self.search_field.value = ""

        # ページに接続されている場合のみ更新を実行
        if hasattr(self, "page") and self.page:
            try:
                self.update()
                self.logger.debug("MailList: リセット完了 - UIを更新しました")
            except Exception as e:
                self.logger.warning(f"MailList: リセット中のUI更新でエラー - {str(e)}")
        else:
            self.logger.debug(
                "MailList: リセット完了 - ページに接続されていないためUI更新をスキップしました"
            )

    def update_flag_status(self, mail_id: str, is_flagged: bool) -> None:
        """
        メールリスト内のフラグ状態を更新する

        Args:
            mail_id: メールID
            is_flagged: 新しいフラグ状態
        """
        self.logger.debug(
            "MailList: フラグ状態更新",
            mail_id=mail_id,
            is_flagged=is_flagged,
        )

        # メールリスト内のアイテムを探す
        for item in self.mail_list_view.controls:
            if not hasattr(item, "data"):
                continue

            # 会話モードの場合と個別メールモードの場合で処理を分ける
            if self.enable_grouping:
                # 会話モード: 会話内のメールを更新
                if isinstance(item.data, str) and item.data.startswith("conv_"):
                    thread_id = item.data
                    # 会話内のメールを取得
                    thread_mails = self.get_thread_mails(thread_id)
                    if thread_mails:
                        for mail in thread_mails:
                            if mail.get("id") == mail_id:
                                # 見つかった場合はUIを更新
                                mail["flagged"] = is_flagged
                                # コンテナのフラグアイコンを更新する処理が必要
                                self._update_container_flag_if_visible(
                                    item, mail_id, is_flagged
                                )
                                item.update()
                                break
            else:
                # 個別メールモード: メールIDが一致するアイテムを更新
                if item.data == mail_id:
                    # MailListItemコンポーネントの場合
                    if hasattr(item, "update_flag_status"):
                        item.update_flag_status(is_flagged)
                    # 通常のコンテナの場合はデータを更新
                    else:
                        self._update_flag_icon_in_container(item, is_flagged)
                        item.update()

    def _update_container_flag_if_visible(self, container, mail_id, is_flagged):
        """表示されているコンテナ内のフラグアイコンを更新する（会話モード用）"""
        try:
            # コンテナ内のコントロールにアクセス
            if hasattr(container, "content") and container.content:
                if isinstance(container.content, ft.Column):
                    # 会話アイテム内のフラグアイコンを探す
                    for row in container.content.controls:
                        if isinstance(row, ft.Row):
                            # 行の中の各コントロールを確認
                            for control in row.controls:
                                # フラグアイコンまたはそのコンテナを探す
                                if self._is_flag_icon_or_container(control):
                                    # フラグアイコンを更新
                                    self._update_flag_control(control, is_flagged)
                                    return True

                        # コンテナの場合は中を探索
                        elif isinstance(row, ft.Container):
                            if self._update_flag_in_container(row, is_flagged):
                                return True

            self.logger.debug(
                "会話コンテナ内でフラグアイコンが見つかりませんでした", mail_id=mail_id
            )
            return False

        except Exception as e:
            self.logger.error(f"会話コンテナ内のフラグ更新エラー: {e}")
            return False

    def _is_flag_icon_or_container(self, control):
        """フラグアイコンまたはそのコンテナかどうかを判定"""
        # アイコン自体の場合
        if isinstance(control, ft.Icon) and control.name in [
            ft.icons.FLAG,
            ft.icons.FLAG_OUTLINED,
        ]:
            return True

        # アイコンを含むコンテナの場合
        if isinstance(control, ft.Container) and hasattr(control, "content"):
            if isinstance(control.content, ft.Icon) and control.content.name in [
                ft.icons.FLAG,
                ft.icons.FLAG_OUTLINED,
            ]:
                return True

        return False

    def _update_flag_control(self, control, is_flagged):
        """フラグコントロールを更新"""
        # アイコン自体の場合
        if isinstance(control, ft.Icon):
            control.name = ft.icons.FLAG if is_flagged else ft.icons.FLAG_OUTLINED
            control.color = Colors.ERROR if is_flagged else Colors.TEXT_SECONDARY

        # アイコンを含むコンテナの場合
        elif isinstance(control, ft.Container) and hasattr(control, "content"):
            if isinstance(control.content, ft.Icon):
                control.content.name = (
                    ft.icons.FLAG if is_flagged else ft.icons.FLAG_OUTLINED
                )
                control.content.color = (
                    Colors.ERROR if is_flagged else Colors.TEXT_SECONDARY
                )

                # データも更新
                if hasattr(control, "data"):
                    control.data["flagged"] = is_flagged

                # ツールチップも更新
                if hasattr(control, "tooltip"):
                    control.tooltip = (
                        "フラグを解除する"
                        if is_flagged
                        else "問題のあるメールとしてフラグを立てる"
                    )

        return True

    def _update_flag_in_container(self, container, is_flagged):
        """コンテナ内のフラグアイコンを更新"""
        if hasattr(container, "content"):
            # コンテナ内に行がある場合
            if isinstance(container.content, ft.Row):
                for control in container.content.controls:
                    if self._is_flag_icon_or_container(control):
                        return self._update_flag_control(control, is_flagged)

            # コンテナ内に列がある場合
            elif isinstance(container.content, ft.Column):
                for row in container.content.controls:
                    if isinstance(row, ft.Row):
                        for control in row.controls:
                            if self._is_flag_icon_or_container(control):
                                return self._update_flag_control(control, is_flagged)

        return False

    def _on_sort_order_changed(self, e):
        """ソート順が変更されたときの処理"""
        # 選択されたソート順を保存
        self.sort_order = e

        # コールバック関数が設定されていれば呼び出す
        if self.on_sort_order_changed:
            self.on_sort_order_changed(e)

    def _on_search_field_change(self, e):
        """検索フィールドの値が変更されたときの処理"""
        self._update_clear_button_visibility()
