"""
メールリストコンポーネント
メール一覧を表示するためのコンポーネント
"""

from typing import Callable, Dict, List, Optional

import flet as ft

from src.core.logger import get_logger
from src.views.components.mail_list_item import MailListItem
from src.views.styles.style import AppTheme


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
            on_refresh: 更新ボタンクリック時のコールバック関数
            **kwargs: その他のキーワード引数
        """
        self.logger = get_logger()
        self.logger.info("MailList: 初期化開始")

        # コールバック関数
        self.on_mail_selected = on_mail_selected
        self.on_refresh = on_refresh

        # 会話ごとに集約するフラグ
        self.group_by_conversation = False

        # 会話表示の時系列ソート順（True: 新しい順、False: 古い順）
        self.conversation_sort_newest_first = True

        # 会話グループのコンテナを保存する辞書
        self.conversation_containers = {}

        # 現在選択されているメールID
        self.selected_mail_id = None

        # メールリストアイテムの辞書（mail_id: MailListItem）
        self.mail_items = {}

        # 検索フィールド
        self.search_field = ft.TextField(
            hint_text="メールを検索...",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_submit=self._on_search,
            border_radius=20,
            height=40,
        )

        # メールリスト
        self.mail_list_view = ft.ListView(
            expand=True,
            spacing=2,
            padding=5,
        )

        # メインコンテンツ
        content = ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("メール一覧", weight="bold", size=16),
                            ft.IconButton(
                                icon=ft.icons.REFRESH,
                                tooltip="更新",
                                on_click=self._on_refresh_clicked,
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
                                on_change=self._on_group_by_conversation_changed,
                                scale=0.8,
                            ),
                            ft.IconButton(
                                icon=ft.icons.HELP_OUTLINE,
                                tooltip="同じ会話IDを持つメールをまとめて表示します",
                                icon_size=16,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    padding=ft.padding.only(left=10, right=10, bottom=5),
                ),
                ft.Container(
                    content=self.mail_list_view,
                    expand=True,
                    border=ft.border.all(1, ft.colors.BLACK12),
                    border_radius=AppTheme.CONTAINER_BORDER_RADIUS,
                    padding=5,
                ),
            ],
            spacing=0,
            expand=True,
        )

        # Containerの初期化
        super().__init__(
            content=content,
            expand=True,
            **kwargs,
        )

        self.logger.info("MailList: 初期化完了")

    def _on_refresh_clicked(self, e):
        """更新ボタンがクリックされたときの処理"""
        self.logger.info("MailList: 更新ボタンクリック")
        if self.on_refresh:
            self.on_refresh()

    def _on_search(self, e):
        """検索実行時の処理"""
        search_term = self.search_field.value
        self.logger.info("MailList: 検索実行", search_term=search_term)
        # 検索イベントを上位コンポーネントに通知
        if hasattr(self, "on_search") and self.on_search:
            self.on_search(search_term)

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

    def _on_group_by_conversation_changed(self, e):
        """会話ごとに集約するフラグを切り替える"""
        self.logger.info(
            "MailList: 会話ごとに集約フラグ切り替え",
            value=e.control.value,
            group_by_conversation_before=self.group_by_conversation,
        )
        self.group_by_conversation = e.control.value
        # 表示を更新（既存のデータで）
        if hasattr(self, "on_group_changed") and self.on_group_changed:
            self.logger.debug("MailList: on_group_changedコールバック呼び出し")
            self.on_group_changed(e)
        else:
            self.logger.warning(
                "MailList: on_group_changedコールバックが設定されていません"
            )

        self.logger.info(
            "MailList: 会話ごとに集約フラグ切り替え完了",
            group_by_conversation_after=self.group_by_conversation,
        )

    def _show_conversation(self, conversation_id):
        """会話内容表示のトリガー"""
        self.logger.info(
            "MailList: 会話表示リクエスト", conversation_id=conversation_id
        )

        # 会話コンテナの状態ログ
        self.logger.debug(
            "MailList: 会話コンテナの状態",
            conversation_containers_count=len(self.conversation_containers),
            conversation_containers_keys=(
                list(self.conversation_containers.keys())[:5]
                if self.conversation_containers
                else []
            ),
            requested_id=conversation_id,
            id_exists=conversation_id in self.conversation_containers,
        )

        # 会話に属するメールを取得
        conversation_mails = []
        if conversation_id in self.conversation_containers:
            conversation_mails = self.conversation_containers[conversation_id]
            self.logger.debug(
                "MailList: 会話コンテナからメールを取得",
                conversation_id=conversation_id,
                mail_count=len(conversation_mails),
                first_mail_id=(
                    conversation_mails[0].get("id", "不明")
                    if conversation_mails
                    else "なし"
                ),
                all_mail_ids=(
                    [m.get("id", "不明") for m in conversation_mails[:5]]
                    if conversation_mails
                    else []
                ),
            )
        else:
            self.logger.warning(
                "MailList: 指定された会話IDのメールが見つかりません",
                conversation_id=conversation_id,
            )

            # 追加の検索を試みる
            if conversation_id.startswith("conv_"):
                stripped_id = conversation_id[5:]
                if stripped_id in self.conversation_containers:
                    self.logger.debug(
                        "MailList: プレフィックスを除いたIDでメールを発見",
                        original_id=conversation_id,
                        stripped_id=stripped_id,
                    )
                    conversation_mails = self.conversation_containers[stripped_id]
            elif f"conv_{conversation_id}" in self.conversation_containers:
                prefixed_id = f"conv_{conversation_id}"
                self.logger.debug(
                    "MailList: プレフィックスを追加したIDでメールを発見",
                    original_id=conversation_id,
                    prefixed_id=prefixed_id,
                )
                conversation_mails = self.conversation_containers[prefixed_id]

        # 選択状態を更新
        for item in self.mail_list_view.controls:
            if hasattr(item, "data") and item.data == conversation_id:
                item.bgcolor = ft.colors.BLUE_50
            else:
                item.bgcolor = ft.colors.WHITE
            item.update()

        # 会話表示イベントを上位コンポーネントに通知
        # conversation_mailsとconversation_idの両方を個別の引数として渡す（順序を修正）
        if self.on_conversation_selected:
            # 詳細なデバッグ情報
            self.logger.debug(
                "MailList: 会話選択イベント引数詳細",
                conversation_id_type=type(conversation_id).__name__,
                conversation_id=conversation_id,
                mails_type=type(conversation_mails).__name__,
                mails_is_list=isinstance(conversation_mails, list),
                mail_count=len(conversation_mails) if conversation_mails else 0,
                handler_type=type(self.on_conversation_selected).__name__,
                has_handler=self.on_conversation_selected is not None,
            )

            if isinstance(conversation_mails, list) and len(conversation_mails) > 0:
                self.logger.debug(
                    "MailList: 会話メールリスト最初の要素",
                    first_mail_keys=(
                        list(conversation_mails[0].keys())
                        if isinstance(conversation_mails[0], dict)
                        else "not a dict"
                    ),
                    mail_id=(
                        conversation_mails[0].get("id", "不明")
                        if isinstance(conversation_mails[0], dict)
                        else "不明"
                    ),
                )

            self.logger.debug(
                "MailList: 会話選択イベント発火",
                handler=str(self.on_conversation_selected),
                conversation_id=conversation_id,
                mail_count=len(conversation_mails),
            )

            try:
                # 明示的に引数の順序を示して呼び出す
                self.on_conversation_selected(
                    mails=conversation_mails, conversation_id=conversation_id
                )
                self.logger.debug("MailList: 会話選択イベント発火完了")
            except Exception as e:
                self.logger.error("MailList: 会話選択イベント発火エラー", error=str(e))
        else:
            self.logger.error("MailList: 会話選択イベントハンドラが設定されていません")

    def display_mails(self, mails: List[Dict]):
        """メール一覧を表示"""
        self.logger.info(
            "MailList: メール一覧表示",
            mail_count=len(mails) if mails else 0,
            group_by_conversation=self.group_by_conversation,
        )

        # メールリストをクリア
        self.mail_list_view.controls.clear()
        self.mail_items = {}
        self.selected_mail_id = None

        # メールが存在しない場合のメッセージ
        if not mails:
            self.logger.debug("MailList: メールデータなし")
            self.mail_list_view.controls.append(
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
            self.update()
            return

        # 会話ごとに集約するかどうかの判定
        use_grouped_view = self.group_by_conversation
        self.logger.debug(f"MailList: グループ表示モード: {use_grouped_view}")

        if use_grouped_view:
            self.logger.debug("MailList: 会話グループ表示モードでメール表示")
            self._display_grouped_mails(mails)
        else:
            self.logger.debug("MailList: 通常表示モードでメール表示")
            # 通常表示
            for mail in mails:
                mail_item = MailListItem(
                    mail_data=mail,
                    on_click=self._on_mail_item_click,
                )
                self.mail_items[mail["id"]] = mail_item
                self.mail_list_view.controls.append(mail_item)

        self.update()
        self.logger.info(
            "MailList: メール一覧表示完了",
            display_mode="グループ表示" if use_grouped_view else "通常表示",
        )

    def _display_grouped_mails(self, mails):
        """会話ごとにグループ化されたメールを表示"""
        self.logger.info("MailList: 会話ごとにグループ化されたメール表示開始")

        # 会話コンテナを初期化
        self.conversation_containers = {}

        # conversation_idでグループ化
        conversations = {}
        for mail in mails:
            # conversation_idがない場合は単独のメールとして扱う
            if not mail.get("conversation_id"):
                # メールIDをキーとして使用
                conversation_key = f"single_{mail['id']}"
                if conversation_key not in conversations:
                    conversations[conversation_key] = []
                conversations[conversation_key].append(mail)
                continue

            # conversation_id全体をそのまま使用
            conversation_id = mail["conversation_id"]

            if conversation_id not in conversations:
                conversations[conversation_id] = []
            conversations[conversation_id].append(mail)

        # グループごとにリストに追加
        for conversation_key, mails_in_conversation in conversations.items():
            # 会話内のメールを日付順にソート
            sorted_mails = sorted(
                mails_in_conversation,
                key=lambda x: x["date"],
                reverse=self.conversation_sort_newest_first,
            )

            # 会話グループ用の識別子を作成（conv_プレフィックスを付与）
            conversation_id = f"conv_{conversation_key}"

            self.logger.debug(
                "MailList: 会話グループ作成",
                original_key=conversation_key,
                conversation_id=conversation_id,
                mail_count=len(sorted_mails),
            )

            # キャッシュに保存
            self.conversation_containers[conversation_id] = sorted_mails

            # 会話の代表的な件名を取得（最新のメールの件名を使用）
            subject = sorted_mails[0]["subject"] or "(件名なし)"

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
                        ai_score = ai_review.get("score", 0)
                        if isinstance(ai_score, int) or isinstance(ai_score, float):
                            # スコアに応じた色分け
                            if ai_score >= 4:
                                risk_color = ft.colors.RED
                            elif ai_score >= 1:
                                risk_color = ft.colors.YELLOW
                            else:
                                risk_color = ft.colors.GREEN
                            break  # AIレビュー情報が見つかったらループを抜ける

            conversation_header = ft.Container(
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
                                    f"最新: {sorted_mails[0]['date']}",
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
                on_click=lambda e, cid=conversation_id: self._show_conversation(cid),
                data=conversation_id,
                ink=True,
                bgcolor=ft.colors.WHITE,
                border=ft.border.all(1, ft.colors.BLACK12),
                margin=ft.margin.only(bottom=5),
            )

            self.mail_list_view.controls.append(conversation_header)

        self.logger.info(
            "MailList: 会話ごとにグループ化されたメール表示完了",
            conversation_count=len(conversations),
        )

    def display_search_results(self, mails: List[Dict], search_term: str):
        """検索結果を表示"""
        self.logger.info(
            "MailList: 検索結果表示", result_count=len(mails) if mails else 0
        )

        # メールリストをクリア
        self.mail_list_view.controls.clear()
        self.mail_items = {}
        self.selected_mail_id = None

        # 検索結果がない場合
        if not mails:
            self.mail_list_view.controls.append(
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
                                on_click=lambda _: self._on_refresh_clicked(None),
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
        else:
            # 検索結果を表示
            for mail in mails:
                mail_item = MailListItem(
                    mail_data=mail,
                    on_click=self._on_mail_item_click,
                )
                self.mail_items[mail["id"]] = mail_item
                self.mail_list_view.controls.append(mail_item)

        self.update()
        self.logger.info("MailList: 検索結果表示完了", search_term=search_term)

    def mark_mail_as_read(self, mail_id):
        """メールを既読としてマーク"""
        if mail_id in self.mail_items:
            self.mail_items[mail_id].mark_as_read()
            self.logger.info("MailList: メールを既読に設定", mail_id=mail_id)

    def update_flag_status(self, mail_id, is_flagged):
        """メールのフラグ状態を更新"""
        if mail_id in self.mail_items:
            self.mail_items[mail_id].update_flag_status(is_flagged)
            self.logger.info(
                "MailList: メールのフラグ状態を更新",
                mail_id=mail_id,
                flagged=is_flagged,
            )

    def get_conversation_mails(self, conversation_id):
        """会話に含まれるメール一覧を取得"""
        return self.conversation_containers.get(conversation_id, [])
