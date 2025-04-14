"""
メール内容表示コンポーネント
選択されたメールの詳細情報を表示するためのコンポーネント
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import flet as ft

from src.core.logger import get_logger
from src.util.object_util import get_safe


class MailContentViewer(ft.Container):
    """
    メール内容表示コンポーネント
    選択されたメールの詳細な内容を表示する
    """

    def __init__(
        self,
        on_flag_click: Optional[Callable] = None,
        on_download_attachment: Optional[Callable] = None,
        **kwargs,
    ):
        """
        MailContentViewerの初期化

        Args:
            on_flag_click: フラグボタンクリック時のコールバック関数
            on_download_attachment: 添付ファイルダウンロード時のコールバック関数
            **kwargs: その他のキーワード引数
        """
        super().__init__()
        self.logger = get_logger()
        self.logger.info("MailContentViewer: 初期化開始")

        # コールバック関数
        self.on_flag_click = on_flag_click
        self.on_download_attachment = on_download_attachment

        # 現在表示中のメールID
        self.current_mail_id = None

        # viewmodel参照用変数（外部から設定される）
        self.viewmodel = None

        # メイン表示領域
        self.content_column = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        # 初期表示を設定
        self._show_empty_content()

        # コンテナの設定
        self.content = self.content_column
        self.expand = True
        self.border = ft.border.all(1, ft.colors.BLACK12)
        self.border_radius = 10
        self.padding = 10

        self.logger.info("MailContentViewer: 初期化完了")

    def _show_empty_content(self):
        """空のメール内容表示"""
        self.content_column.controls.clear()
        self.content_column.controls.append(
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
        self._safe_update()

    def _safe_update(self):
        """安全にコンポーネントを更新するメソッド"""
        try:
            if hasattr(self, "page") and self.page:
                self.update()
        except Exception as e:
            self.logger.debug(f"MailContentViewer: 更新を延期します - {str(e)}")

    def show_error_message(self, message):
        """エラーメッセージを表示"""
        self.logger.error("MailContentViewer: エラーメッセージ表示", message=message)
        self.content_column.controls.clear()
        self.content_column.controls.append(
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
        self._safe_update()

    def _get_file_icon(self, filename):
        """ファイル種類に応じたアイコンを取得"""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext in ["pdf"]:
            return ft.Icon(name=ft.icons.PICTURE_AS_PDF, size=16, color=ft.colors.RED)
        elif ext in ["jpg", "jpeg", "png", "gif", "bmp"]:
            return ft.Icon(name=ft.icons.IMAGE, size=16, color=ft.colors.BLUE)
        elif ext in ["doc", "docx"]:
            return ft.Icon(name=ft.icons.DESCRIPTION, size=16, color=ft.colors.BLUE)
        elif ext in ["xls", "xlsx"]:
            return ft.Icon(name=ft.icons.TABLE_CHART, size=16, color=ft.colors.GREEN)
        elif ext in ["ppt", "pptx"]:
            return ft.Icon(
                name=ft.icons.PRESENT_TO_ALL, size=16, color=ft.colors.ORANGE
            )
        elif ext in ["zip", "rar", "7z", "tar", "gz"]:
            return ft.Icon(name=ft.icons.FOLDER_ZIP, size=16, color=ft.colors.BROWN)
        elif ext in ["mp3", "wav", "ogg"]:
            return ft.Icon(name=ft.icons.AUDIO_FILE, size=16, color=ft.colors.PURPLE)
        elif ext in ["mp4", "avi", "mov"]:
            return ft.Icon(name=ft.icons.VIDEO_FILE, size=16, color=ft.colors.RED_700)
        else:
            return ft.Icon(
                name=ft.icons.INSERT_DRIVE_FILE, size=16, color=ft.colors.GREY
            )

    def _get_file_type(self, filename):
        """ファイル種類に応じた説明を取得"""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext in ["pdf"]:
            return "PDF文書"
        elif ext in ["jpg", "jpeg", "png", "gif", "bmp"]:
            return f"{ext.upper()}画像"
        elif ext in ["doc", "docx"]:
            return "Word文書"
        elif ext in ["xls", "xlsx"]:
            return "Excel表計算"
        elif ext in ["ppt", "pptx"]:
            return "PowerPointプレゼン"
        elif ext in ["zip", "rar", "7z", "tar", "gz"]:
            return f"{ext.upper()}圧縮ファイル"
        elif ext in ["mp3", "wav", "ogg"]:
            return f"{ext.upper()}音声ファイル"
        elif ext in ["mp4", "avi", "mov"]:
            return f"{ext.upper()}動画ファイル"
        elif ext in ["txt"]:
            return "テキストファイル"
        elif ext in ["html", "htm"]:
            return "HTMLファイル"
        elif ext:
            return f"{ext}ファイル"
        else:
            return "不明なファイル"

    def create_flag_button(self, mail_id, is_flagged):
        """フラグボタンを作成"""
        return ft.Container(
            content=ft.Icon(
                name=ft.icons.FLAG if is_flagged else ft.icons.FLAG_OUTLINED,
                size=16,
                color=ft.colors.RED if is_flagged else ft.colors.GREY,
            ),
            tooltip=(
                "フラグを解除する"
                if is_flagged
                else "問題のあるメールとしてフラグを立てる"
            ),
            width=32,
            height=32,
            border_radius=16,
            on_click=lambda e, mid=mail_id: self._toggle_flag(e, mid),
            on_hover=self._on_hover_effect,
            alignment=ft.alignment.center,
            data={"flagged": is_flagged},
        )

    def _on_hover_effect(self, e):
        """ホバー効果"""
        # マウスが入ったとき
        if e.data == "true":
            e.control.bgcolor = ft.colors.with_opacity(0.1, ft.colors.BLUE)
        # マウスが出たとき
        else:
            e.control.bgcolor = None

        try:
            e.control.update()
        except Exception as ex:
            self.logger.debug(
                f"MailContentViewer: コントロール更新を延期します - {str(ex)}"
            )

    def _toggle_flag(self, e, mail_id):
        """メールのフラグ状態を切り替える"""
        self.logger.info("MailContentViewer: メールフラグ切り替え", mail_id=mail_id)

        # ボタンの状態を取得
        button = e.control
        is_flagged = button.data.get("flagged", False)

        # フラグ状態を切り替え
        is_flagged = not is_flagged
        button.data["flagged"] = is_flagged

        # アイコンと色を更新
        if is_flagged:
            button.content.name = ft.icons.FLAG
            button.content.color = ft.colors.RED
            button.tooltip = "フラグを解除する"
        else:
            button.content.name = ft.icons.FLAG_OUTLINED
            button.content.color = ft.colors.GREY
            button.tooltip = "問題のあるメールとしてフラグを立てる"

        # 外部コールバック関数に通知
        if self.on_flag_click:
            self.on_flag_click(mail_id, is_flagged)

        try:
            button.update()
        except Exception as ex:
            self.logger.debug(
                f"MailContentViewer: フラグボタン更新を延期します - {str(ex)}"
            )

        self.logger.info(
            "MailContentViewer: メールフラグ切り替え完了",
            mail_id=mail_id,
            flagged=is_flagged,
        )

    def _download_attachment(self, e, file_id):
        """添付ファイルのダウンロード処理"""
        self.logger.info("MailContentViewer: 添付ファイルダウンロード", file_id=file_id)
        if self.on_download_attachment:
            self.on_download_attachment(file_id)

    def show_mail_content(self, mail: Dict[str, Any], mail_id: str = None):
        """メール内容を表示"""
        if mail_id:
            self.current_mail_id = mail_id
        else:
            self.current_mail_id = mail.get("id", None)

        self.logger.info(
            "MailContentViewer: メール内容表示", mail_id=self.current_mail_id
        )

        if not mail:
            self.show_error_message("メール内容の取得に失敗しました")
            return

        # メール内容表示をクリア
        self.content_column.controls.clear()

        # メールデータのチェックと安全な取得
        # 送信者情報を解析
        sender = mail.get("sender", "不明 <unknown@example.com>")
        sender_name = sender.split("<")[0].strip() if "<" in sender else sender
        sender_email = (
            sender.split("<")[1].replace(">", "") if "<" in sender else sender
        )

        # 受信者情報を解析
        recipient = mail.get("recipient", "不明 <unknown@example.com>")
        recipient_name = (
            recipient.split("<")[0].strip() if "<" in recipient else recipient
        )
        recipient_email = (
            recipient.split("<")[1].replace(">", "") if "<" in recipient else recipient
        )

        # 添付ファイルがあれば表示用のリストを作成
        attachments_section = []
        attachments = mail.get("attachments", [])
        if attachments:
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
                                            self._get_file_icon(
                                                attachment.get("name", "不明なファイル")
                                            ),
                                            ft.Text(
                                                attachment.get("name", "不明なファイル")
                                            ),
                                            ft.Text(
                                                self._get_file_type(
                                                    attachment.get(
                                                        "name", "不明なファイル"
                                                    )
                                                ),
                                                size=12,
                                                color=ft.colors.GREY,
                                            ),
                                            ft.IconButton(
                                                icon=ft.icons.DOWNLOAD,
                                                tooltip="ダウンロード",
                                                icon_size=16,
                                                on_click=lambda e, fid=attachment.get(
                                                    "id", ""
                                                ): self._download_attachment(e, fid),
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
        self.content_column.controls.extend(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        mail.get("subject", "(件名なし)"),
                                        size=18,
                                        weight="bold",
                                        expand=True,
                                    ),
                                    # フラグボタン
                                    self.create_flag_button(
                                        self.current_mail_id, mail.get("flagged", False)
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
                                            # CC参加者を表示（存在する場合）
                                            self._create_participants_row(
                                                "CC",
                                                mail.get("participants", {}).get(
                                                    "cc", []
                                                ),
                                            ),
                                            # BCC参加者を表示（存在する場合）
                                            self._create_participants_row(
                                                "BCC",
                                                mail.get("participants", {}).get(
                                                    "bcc", []
                                                ),
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        "日時:", weight="bold", width=80
                                                    ),
                                                    ft.Text(
                                                        mail.get("date", "不明な日時")
                                                    ),
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
                            # Markdownフォーマットされたテキストの場合はft.Markdownを使用
                            ft.Container(
                                content=(
                                    ft.Markdown(
                                        mail.get("content", ""),
                                        selectable=True,
                                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                    )
                                    if mail.get("is_markdown", False)
                                    else ft.Text(mail.get("content", ""))
                                ),
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

        self._safe_update()
        self.logger.info(
            "MailContentViewer: メール内容表示完了", mail_id=self.current_mail_id
        )

    def show_conversation_content(
        self, mails: List[Dict[str, Any]], sort_button: ft.Control = None
    ):
        """会話内容を表示"""
        self.logger.info(
            "MailContentViewer: 会話内容表示", mail_count=len(mails) if mails else 0
        )

        # 詳細なデバッグ情報
        self.logger.debug(
            "MailContentViewer: show_conversation_content引数詳細",
            mails_type=type(mails).__name__,
            mails_is_list=isinstance(mails, list),
            sort_button_type=type(sort_button).__name__ if sort_button else "None",
        )

        # Noneチェック
        if mails is None:
            self.logger.error("MailContentViewer: メールリストがNoneです")
            self._show_empty_content()
            self.show_error_message("メールデータがありません")
            return

        # 型チェック
        if not isinstance(mails, list):
            self.logger.error(
                "MailContentViewer: メールリストがリスト型ではありません",
                actual_type=type(mails).__name__,
            )
            self._show_empty_content()
            self.show_error_message(
                f"無効なメールデータ形式です: {type(mails).__name__}"
            )
            return

        # 空リストチェック
        if not mails:
            self.logger.warning("MailContentViewer: メールリストが空です")
            self._show_empty_content()
            return

        # 各メールが辞書型か確認
        if not all(isinstance(mail, dict) for mail in mails):
            self.logger.error(
                "MailContentViewer: メールリストに辞書型でない要素が含まれています",
                mail_types=[type(mail).__name__ for mail in mails[:5]],
            )
            # 辞書型のメールだけを抽出
            valid_mails = [mail for mail in mails if isinstance(mail, dict)]
            if not valid_mails:
                self._show_empty_content()
                self.show_error_message("有効なメールデータがありません")
                return
            mails = valid_mails
            self.logger.debug(
                "MailContentViewer: 有効なメールだけを抽出しました",
                original_count=len(mails),
                valid_count=len(valid_mails),
            )

        if isinstance(mails, list) and len(mails) > 0:
            self.logger.debug(
                "MailContentViewer: メールリスト最初の要素",
                first_mail_keys=(
                    list(mails[0].keys())
                    if isinstance(mails[0], dict)
                    else "not a dict"
                ),
                first_mail_type=type(mails[0]).__name__,
                first_mail_id=(
                    mails[0].get("id", "不明") if isinstance(mails[0], dict) else "不明"
                ),
                first_mail_content_type=(
                    type(mails[0].get("content", "")).__name__
                    if isinstance(mails[0], dict)
                    else "不明"
                ),
            )

        # メール内容表示をクリア
        self.content_column.controls.clear()

        # 会話内の最初のメールから件名を取得（空の場合はデフォルト値）
        first_mail = mails[0] if mails else {}
        subject = first_mail.get("subject", "(件名なし)")
        if not isinstance(subject, str):
            subject = "(件名なし)"

        # メールのデータを事前に整備
        for mail in mails:
            # 必須フィールドを確保（プリミティブ型をチェック）
            for field, default in [
                ("content", ""),
                ("sender", "不明 <unknown@example.com>"),
                ("subject", "(件名なし)"),
                ("date", "不明な日時"),
            ]:
                if field not in mail or not isinstance(mail.get(field), str):
                    mail[field] = default

            # 添付ファイルリストの確保
            if "attachments" not in mail or not isinstance(
                mail.get("attachments"), list
            ):
                mail["attachments"] = []

            # ID確保
            if "id" not in mail:
                mail["id"] = f"unknown_{id(mail)}"

        # AIレビュー情報を取得
        ai_review_info = None
        # まずメールからAIレビュー情報を取得
        for mail in mails:
            if mail.get("ai_review"):
                ai_review_info = mail["ai_review"]
                self.logger.debug(
                    "MailContentViewer: メールからAIレビュー情報を取得",
                    ai_review=ai_review_info,
                )
                break

        # ViewModelからリスクスコア情報を取得
        risk_score = None
        if self.viewmodel:
            risk_score = self.viewmodel.get_conversation_risk_score(mails)
            self.logger.debug(
                "MailContentViewer: ViewModelからリスクスコア情報を取得",
                risk_score=risk_score,
            )

        # メール内容表示
        self.content_column.controls.extend(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        subject,
                                        size=18,
                                        weight="bold",
                                        expand=True,
                                    ),
                                    sort_button if sort_button else ft.Container(),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Text(
                                f"{len(mails)}件のメール",
                                size=12,
                                color=ft.colors.GREY,
                            ),
                            ft.Divider(height=1, color=ft.colors.BLACK12),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                    bgcolor=ft.colors.WHITE,
                    border_radius=5,
                    border=ft.border.all(1, ft.colors.BLACK12),
                ),
                # AIレビュー - リスクスコア情報があれば表示
                self._create_ai_review_section(ai_review_info, risk_score),
                # 会話内の各メールを表示
                ft.Container(
                    content=ft.Column(
                        [],
                        spacing=10,
                    ),
                    padding=10,
                    margin=ft.margin.only(top=10),
                    expand=True,
                ),
            ]
        )

        # 会話内の各メールを表示
        mail_container = self.content_column.controls[-1]

        # 各メールをループ処理
        mail_items = []
        for idx, mail in enumerate(mails):
            try:
                self.logger.debug(
                    "MailContentViewer: メールアイテム作成",
                    mail_id=mail.get("id", "不明"),
                    mail_idx=idx,
                    mail_keys=(
                        list(mail.keys()) if isinstance(mail, dict) else "not a dict"
                    ),
                    mail_has_content=(
                        "content" in mail if isinstance(mail, dict) else False
                    ),
                    mail_content_type=(
                        type(mail.get("content", "")).__name__
                        if isinstance(mail, dict)
                        else "None"
                    ),
                )

                # メールの基本検証
                if not isinstance(mail, dict):
                    raise ValueError(
                        f"メールデータが辞書型ではありません: {type(mail).__name__}"
                    )

                if "id" not in mail:
                    mail["id"] = f"unknown_{idx}"
                    self.logger.warning(
                        f"メールにIDがないため一時IDを生成: {mail['id']}"
                    )

                # 必須フィールドの再確認
                for field, default in [
                    ("content", ""),
                    ("sender", "不明 <unknown@example.com>"),
                    ("subject", "(件名なし)"),
                    ("date", "不明な日時"),
                ]:
                    if (
                        field not in mail
                        or mail[field] is None
                        or not isinstance(mail[field], str)
                    ):
                        old_value = str(mail.get(field, "None"))
                        mail[field] = default
                        self.logger.warning(
                            f"メールの{field}フィールドを修正",
                            mail_id=mail["id"],
                            old_value=old_value,
                            new_value=default,
                        )

                # メールアイテム作成
                mail_item = self._create_mail_content_item(mail, idx)
                mail_items.append(mail_item)
            except Exception as e:
                self.logger.error(
                    "MailContentViewer: メールアイテム作成エラー",
                    error=str(e),
                    mail_id=(
                        mail.get("id", "不明") if isinstance(mail, dict) else "不明"
                    ),
                    mail_idx=idx,
                )
                # エラーが発生した場合はエラー表示を追加
                mail_items.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "メール表示エラー",
                                    color=ft.colors.RED,
                                    weight="bold",
                                ),
                                ft.Text(f"エラー内容: {str(e)}", size=12),
                                ft.Text(
                                    (
                                        f"メールID: {mail.get('id', '不明')}"
                                        if isinstance(mail, dict)
                                        else "無効なメールデータ"
                                    ),
                                    size=12,
                                ),
                            ]
                        ),
                        padding=10,
                        bgcolor=ft.colors.RED_50,
                        border=ft.border.all(1, ft.colors.RED_400),
                        border_radius=5,
                    )
                )

        # 処理結果の確認
        if not mail_items:
            self.logger.error("MailContentViewer: 表示可能なメールアイテムがありません")
            self._show_empty_content()
            self.show_error_message("有効なメールデータがありません")
            return

        # メールアイテムの表示
        try:
            mail_container.content.controls = mail_items
        except Exception as e:
            self.logger.error(
                "MailContentViewer: メールアイテム表示中にエラーが発生", error=str(e)
            )
            self._show_empty_content()
            self.show_error_message(f"メール表示中にエラーが発生しました: {str(e)}")
            return

        self._safe_update()
        self.logger.info("MailContentViewer: 会話内容表示完了", mail_count=len(mails))

    def _create_ai_review_section(self, ai_review_info=None, risk_score=None):
        """AIレビュー情報セクションを作成"""
        # デフォルトのリスクスコア
        if not risk_score:
            risk_score = {
                "label": "不明",
                "color": ft.colors.GREY,
                "score": 0,
                "tooltip": "リスク評価が利用できません",
            }

        # AI情報の安全な取得
        summary = get_safe(
            ai_review_info, "summary", "AIによる会話の要約情報はありません。"
        )
        attention_points = get_safe(ai_review_info, "attention_points", [])
        organizations = get_safe(ai_review_info, "organizations", [])
        review = get_safe(ai_review_info, "review", "詳細な評価情報はありません。")
        score = get_safe(ai_review_info, "score", 0)

        # スコアに基づくリスクレベルの設定
        if score > 3:
            risk_level = {
                "label": "高",
                "color": ft.colors.RED,
                "tooltip": "複数の注意点があります。内容を慎重に確認してください。",
            }
        elif score > 1:
            risk_level = {
                "label": "中",
                "color": ft.colors.ORANGE,
                "tooltip": "いくつかの注意点があります。確認を推奨します。",
            }
        elif score > 0:
            risk_level = {
                "label": "低",
                "color": ft.colors.YELLOW,
                "tooltip": "軽微な注意点があります。",
            }
        else:
            risk_level = {
                "label": "なし",
                "color": ft.colors.GREEN,
                "tooltip": "特に問題は見つかりませんでした。",
            }

        # 注目ポイントのコントロールを作成
        attention_controls = []
        for i, point in enumerate(attention_points):
            is_important = i < 2  # 最初の2つは重要なポイントとして扱う
            attention_controls.append(
                self._create_animated_point(point, i * 200, is_important)
            )

        # 組織情報が存在する場合は表示用のコンポーネントを作成
        organizations_section = None
        if organizations:
            org_chips = []
            for org in organizations:
                org_chips.append(
                    ft.Chip(
                        label=ft.Text(org),
                        bgcolor=ft.colors.BLUE_50,
                        label_style=ft.TextStyle(size=12),
                    )
                )

            organizations_section = ft.Column(
                [
                    ft.Text("関連組織:", weight="bold"),
                    ft.Wrap(
                        spacing=5,
                        run_spacing=5,
                        children=org_chips,
                    ),
                ]
            )

        # AIレビューセクションの作成
        return ft.Container(
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
                            ft.Container(
                                content=ft.Icon(
                                    name=ft.icons.REFRESH,
                                    size=16,
                                    color=ft.colors.BLUE,
                                ),
                                tooltip="AIに再評価させる",
                                width=32,
                                height=32,
                                border_radius=16,
                                on_hover=self._on_hover_effect,
                                on_click=self._on_ai_review_refresh,
                                alignment=ft.alignment.center,
                            ),
                        ],
                        spacing=5,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                # 要約セクション
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text("要約:", weight="bold"),
                                            ft.Text(summary, size=14),
                                        ]
                                    ),
                                    margin=ft.margin.only(bottom=10),
                                ),
                                # リスクスコアセクション
                                ft.Row(
                                    [
                                        ft.Text("リスクスコア:", weight="bold"),
                                        ft.Container(
                                            content=ft.Text(
                                                risk_level["label"],
                                                color=ft.colors.WHITE,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            bgcolor=risk_level["color"],
                                            border_radius=5,
                                            padding=5,
                                            width=50,
                                            alignment=ft.alignment.center,
                                            tooltip=risk_level["tooltip"],
                                        ),
                                        ft.Text(
                                            f"({score}点)",
                                            size=12,
                                            color=ft.colors.GREY,
                                        ),
                                    ],
                                    spacing=10,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                # 注目ポイントセクション
                                ft.Column(
                                    [
                                        ft.Text("注目ポイント:", weight="bold"),
                                        (
                                            ft.Column(
                                                attention_controls,
                                                spacing=2,
                                            )
                                            if attention_controls
                                            else ft.Text(
                                                "特に注目すべきポイントはありません",
                                                size=12,
                                                italic=True,
                                            )
                                        ),
                                    ],
                                    spacing=5,
                                ),
                                # 組織情報セクション（存在する場合のみ）
                                (
                                    organizations_section
                                    if organizations_section
                                    else ft.Container()
                                ),
                                # レビュー詳細セクション
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text("詳細評価:", weight="bold"),
                                            ft.Container(
                                                content=ft.Text(review, size=12),
                                                bgcolor=ft.colors.GREY_50,
                                                border_radius=5,
                                                padding=10,
                                                width=float("inf"),
                                            ),
                                        ]
                                    ),
                                    margin=ft.margin.only(top=10),
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
            margin=ft.margin.only(top=10),
            border=ft.border.all(1, ft.colors.BLACK12),
            border_radius=5,
        )

    def _create_mail_content_item(self, mail, index):
        """会話内の個別メールアイテムを作成"""
        # データの安全な取得
        mail_id = mail.get("id", "")

        self.logger.debug(
            "MailContentViewer: _create_mail_content_item詳細",
            mail_id=mail_id,
            mail_idx=index,
            mail_type=type(mail).__name__,
        )

        if not isinstance(mail, dict):
            self.logger.error(
                "MailContentViewer: メールデータが辞書型ではありません",
                mail_type=type(mail).__name__,
                mail_idx=index,
            )
            return ft.Container(
                content=ft.Text(f"無効なメールデータ (ID: {mail_id})"),
                padding=10,
                bgcolor=ft.colors.RED_50,
                border=ft.border.all(1, ft.colors.RED_400),
                border_radius=5,
            )

        # 送信者情報を解析
        sender = mail.get("sender", "不明 <unknown@example.com>")
        if not isinstance(sender, str):
            self.logger.warning(
                "MailContentViewer: 送信者情報が文字列ではありません",
                sender_type=type(sender).__name__,
                mail_id=mail_id,
            )
            sender = "不明 <unknown@example.com>"

        sender_name = sender.split("<")[0].strip() if "<" in sender else sender
        sender_email = (
            sender.split("<")[1].replace(">", "") if "<" in sender else sender
        )

        # 受信者情報を解析
        recipient = mail.get("recipient", "不明 <unknown@example.com>")
        if not isinstance(recipient, str):
            self.logger.warning(
                "MailContentViewer: 受信者情報が文字列ではありません",
                recipient_type=type(recipient).__name__,
                mail_id=mail_id,
            )
            recipient = "不明 <unknown@example.com>"

        recipient_name = (
            recipient.split("<")[0].strip() if "<" in recipient else recipient
        )
        recipient_email = (
            recipient.split("<")[1].replace(">", "") if "<" in recipient else recipient
        )

        # 添付ファイルアイコン
        attachments = mail.get("attachments", [])
        if not isinstance(attachments, list):
            self.logger.warning(
                "MailContentViewer: 添付ファイル情報がリスト型ではありません",
                attachments_type=type(attachments).__name__,
                mail_id=mail_id,
            )
            attachments = []

        attachments_icon = (
            ft.Row(
                [
                    ft.Icon(
                        name=ft.icons.ATTACH_FILE,
                        size=14,
                        color=ft.colors.GREY,
                    ),
                    ft.Text(
                        f"{len(attachments)}個の添付ファイル",
                        size=12,
                        color=ft.colors.GREY,
                    ),
                ],
                spacing=2,
            )
            if attachments
            else ft.Container(width=0)
        )

        # メール本文
        content = mail.get("content", "")
        if not isinstance(content, str):
            self.logger.warning(
                "MailContentViewer: メール本文が文字列ではありません",
                content_type=type(content).__name__,
                mail_id=mail_id,
            )
            content = str(content) if content is not None else ""

        content_lines = content.split("\n") if content else []
        is_truncated = len(content_lines) > 5
        is_markdown = mail.get("is_markdown", False)

        # プレビュー用テキストとフルテキストを準備
        preview_text = "\n".join(content_lines[:5]) + ("..." if is_truncated else "")
        full_text = content

        try:
            # メール本文を表示するコンテナ
            content_container = ft.Container(
                content=(
                    ft.Markdown(
                        preview_text,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    )
                    if is_markdown
                    else ft.Text(preview_text)
                ),
                padding=10,
                border_radius=5,
                bgcolor=ft.colors.WHITE,
                border=ft.border.all(1, ft.colors.BLACK12),
                # データに表示状態を保存
                data={
                    "expanded": False,
                    "full_text": full_text,
                    "preview_text": preview_text,
                    "is_markdown": is_markdown,
                },
            )

            # 続きを見るボタン
            expand_button = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            "続きを見る",
                            color=ft.colors.BLUE,
                            size=12,
                        ),
                        ft.Icon(
                            name=ft.icons.EXPAND_MORE,
                            color=ft.colors.BLUE,
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
                on_hover=self._on_hover_effect,
                visible=is_truncated,
                height=30,
                bgcolor=ft.colors.with_opacity(0.05, ft.colors.BLUE),
            )

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
                                    mail.get("date", "不明な日時"),
                                    size=12,
                                    color=ft.colors.GREY,
                                ),
                                ft.Text(
                                    f"送信者: {sender_name}",
                                    size=12,
                                    weight="bold",
                                    expand=True,
                                ),
                                # フラグボタン
                                self.create_flag_button(
                                    mail_id, mail.get("flagged", False)
                                ),
                                attachments_icon,
                            ],
                            spacing=5,
                        ),
                        content_container,
                        expand_button,
                    ],
                    spacing=5,
                ),
                padding=5,
                bgcolor=ft.colors.BLUE_50 if mail.get("unread", 0) else ft.colors.WHITE,
                border_radius=5,
                border=ft.border.all(1, ft.colors.BLACK12),
            )
        except Exception as e:
            self.logger.error(
                "MailContentViewer: メールアイテム作成中にエラーが発生",
                error=str(e),
                mail_id=mail_id,
                mail_keys=list(mail.keys()),
            )
            return ft.Container(
                content=ft.Text(f"メール表示エラー: {str(e)}"),
                padding=10,
                bgcolor=ft.colors.RED_50,
                border=ft.border.all(1, ft.colors.RED_400),
                border_radius=5,
            )

    def _toggle_mail_content_container(self, e, content_container):
        """メール内容の全文表示/折りたたみを切り替える"""
        self.logger.info("MailContentViewer: メール内容表示切り替え")

        # 現在の表示状態を確認
        container_data = content_container.data
        is_expanded = container_data.get("expanded", False)
        is_markdown = container_data.get("is_markdown", False)

        # ボタンを取得 (コンテナからアイコンを取得)
        button = e.control
        button_icon = button.content.controls[1]
        button_text = button.content.controls[0]

        if is_expanded:
            # 折りたたむ
            if is_markdown:
                content_container.content = ft.Markdown(
                    container_data["preview_text"],
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                )
            else:
                content_container.content = ft.Text(container_data["preview_text"])
            content_container.data["expanded"] = False
            button_text.value = "続きを見る"
            button_icon.name = ft.icons.EXPAND_MORE
        else:
            # 展開する
            if is_markdown:
                content_container.content = ft.Markdown(
                    container_data["full_text"],
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                )
            else:
                content_container.content = ft.Text(container_data["full_text"])
            content_container.data["expanded"] = True
            button_text.value = "折りたたむ"
            button_icon.name = ft.icons.EXPAND_LESS

        # 高さを自動調整
        content_container.height = None

        # 更新
        try:
            content_container.update()
            button.update()
        except Exception as ex:
            self.logger.debug(
                f"MailContentViewer: コンテンツ更新を延期します - {str(ex)}"
            )

        self.logger.info(
            "MailContentViewer: メール内容表示切り替え完了", expanded=not is_expanded
        )

    def _create_animated_point(self, text, delay_ms, is_important=False):
        """アニメーション付きのポイントを作成"""
        return ft.Container(
            content=ft.Text(
                f"• {text}",
                size=14,
                color=ft.colors.RED if is_important else None,
                weight="bold" if is_important else None,
            ),
            opacity=1.0,
            data={"delay": delay_ms, "text": text},
        )

    def _on_ai_review_refresh(self, e):
        """AIレビューの再評価ボタンがクリックされたときの処理"""
        self.logger.info("MailContentViewer: AIレビュー再評価リクエスト")

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
        self._safe_update()

        # ViewModelが設定されていない場合はモック処理を行う
        if not self.viewmodel:

            async def simulate_ai_review():
                # 処理時間をシミュレート
                await asyncio.sleep(2)
                # モックのAIレビュー結果（新しい形式）
                mock_review = {
                    "summary": "この会話はプロジェクトの納期に関する相談と予算の確認について述べています。",
                    "attention_points": [
                        "来週金曜日までに納品が必要です",
                        "予算超過の可能性があります",
                        "関係者全員への確認が必要です",
                    ],
                    "organizations": ["株式会社テクノ", "ABCコンサルティング"],
                    "review": "この会話は納期と予算に関する重要な情報を含んでいます。特に期限が迫っているため早急な対応が必要です。",
                    "score": 2,
                }

                # レビュー結果表示を更新
                self._update_ai_review_section(ai_review_section, mock_review, None)

            # 非同期処理を開始
            asyncio.create_task(simulate_ai_review())
            return

        # 会話IDを取得
        conversation_id = None
        # 現在表示中のメールがあれば、そのメールから会話IDを取得
        if hasattr(self, "current_mail_id") and self.current_mail_id:
            mail = self.viewmodel.get_mail_content(self.current_mail_id)
            if mail and mail.get("conversation_id"):
                conversation_id = mail["conversation_id"]
                self.logger.debug(
                    "MailContentViewer: 現在のメールから会話IDを取得",
                    mail_id=self.current_mail_id,
                    conversation_id=conversation_id,
                )

        # 会話IDが取得できなかった場合は、モック処理を行う
        if not conversation_id:
            self.logger.warning("MailContentViewer: 会話IDが取得できません")

            async def fallback_ai_review():
                await asyncio.sleep(1)
                # 会話IDがないことを示すエラー表示
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
                                ft.Container(
                                    content=ft.Icon(
                                        name=ft.icons.REFRESH,
                                        size=16,
                                        color=ft.colors.BLUE,
                                    ),
                                    tooltip="AIに再評価させる",
                                    width=32,
                                    height=32,
                                    border_radius=16,
                                    on_hover=self._on_hover_effect,
                                    on_click=self._on_ai_review_refresh,
                                    alignment=ft.alignment.center,
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
                                                    "不明",
                                                    color=ft.colors.WHITE,
                                                    text_align=ft.TextAlign.CENTER,
                                                ),
                                                bgcolor=ft.colors.GREY,
                                                border_radius=5,
                                                padding=5,
                                                width=50,
                                                alignment=ft.alignment.center,
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                    ft.Text(
                                        "会話IDが特定できないため、AIレビューを実行できません。",
                                        size=14,
                                        color=ft.colors.RED_400,
                                    ),
                                ],
                                spacing=10,
                            ),
                            padding=10,
                        ),
                    ],
                    spacing=5,
                )
                self._safe_update()

            # 非同期処理を開始
            asyncio.create_task(fallback_ai_review())
            return

        # AIレビューを実行する非同期処理
        async def run_ai_review():
            try:
                # 実際のAIレビュー結果を取得（本来はAPI呼び出しなど）
                await asyncio.sleep(2)  # APIレスポンスを待つ時間を模倣

                # ViewModelからAIレビュー結果を再取得
                ai_review = self.viewmodel.model.get_ai_review_for_conversation(
                    conversation_id
                )

                # AIレビュー結果がない場合はモックデータを使用
                if not ai_review:
                    self.logger.warning(
                        "MailContentViewer: AIレビュー結果がないためモックデータを使用",
                        conversation_id=conversation_id,
                    )
                    # 新しい形式のモックデータ
                    ai_review = {
                        "summary": "この会話はプロジェクトの納期に関する相談と予算の確認について述べています。",
                        "attention_points": [
                            "来週金曜日までに納品が必要です",
                            "予算超過の可能性があります",
                            "関係者全員への確認が必要です",
                        ],
                        "organizations": ["株式会社テクノ", "ABCコンサルティング"],
                        "review": "この会話は納期と予算に関する重要な情報を含んでいます。特に期限が迫っているため早急な対応が必要です。",
                        "score": 2,
                    }

                # リスクスコア情報を取得
                risk_score = self._get_risk_score_from_ai_review(ai_review)

                # レビュー結果表示を更新
                self._update_ai_review_section(ai_review_section, ai_review, risk_score)

            except Exception as e:
                self.logger.error(f"AIレビュー実行中にエラーが発生: {str(e)}")
                # エラー表示
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
                                ft.Container(
                                    content=ft.Icon(
                                        name=ft.icons.REFRESH,
                                        size=16,
                                        color=ft.colors.BLUE,
                                    ),
                                    tooltip="AIに再評価させる",
                                    width=32,
                                    height=32,
                                    border_radius=16,
                                    on_hover=self._on_hover_effect,
                                    on_click=self._on_ai_review_refresh,
                                    alignment=ft.alignment.center,
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
                                                    "エラー",
                                                    color=ft.colors.WHITE,
                                                    text_align=ft.TextAlign.CENTER,
                                                ),
                                                bgcolor=ft.colors.RED_400,
                                                border_radius=5,
                                                padding=5,
                                                width=50,
                                                alignment=ft.alignment.center,
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                    ft.Text(
                                        f"AIレビューの実行中にエラーが発生しました: {str(e)}",
                                        size=14,
                                        color=ft.colors.RED_400,
                                    ),
                                ],
                                spacing=10,
                            ),
                            padding=10,
                        ),
                    ],
                    spacing=5,
                )
                self._safe_update()

        # 非同期処理を開始
        asyncio.create_task(run_ai_review())

    def _get_risk_score_from_ai_review(self, ai_review):
        """AIレビュー結果からリスクスコア情報を取得"""
        # AIレビュー結果がない場合はデフォルト値を返す
        if not ai_review:
            return {
                "label": "不明",
                "color": ft.colors.GREY,
                "score": 0,
                "tooltip": "リスク評価が利用できません",
            }

        # 新しいAIレビュー形式からスコアを取得
        score = get_safe(ai_review, "score", 0)

        # スコアに応じてリスクレベルを設定
        if score > 3:
            return {
                "label": "高",
                "color": ft.colors.RED,
                "score": 3,
                "tooltip": "複数の注意点があります。内容を慎重に確認してください。",
            }
        elif score > 1:
            return {
                "label": "中",
                "color": ft.colors.ORANGE,
                "score": 2,
                "tooltip": "いくつかの注意点があります。確認を推奨します。",
            }
        elif score > 0:
            return {
                "label": "低",
                "color": ft.colors.YELLOW,
                "score": 1,
                "tooltip": "軽微な注意点があります。",
            }
        else:
            return {
                "label": "なし",
                "color": ft.colors.GREEN,
                "score": 0,
                "tooltip": "特に問題は見つかりませんでした。",
            }

    def _update_ai_review_section(self, section, ai_review, risk_score):
        """AIレビューセクションの表示を更新"""
        # 安全にAI情報を取得
        summary = get_safe(ai_review, "summary", "AIによる会話の要約情報はありません。")
        attention_points = get_safe(ai_review, "attention_points", [])
        organizations = get_safe(ai_review, "organizations", [])
        review = get_safe(ai_review, "review", "詳細な評価情報はありません。")
        score = get_safe(ai_review, "score", 0)

        # スコアに基づくリスクレベルの設定
        if score > 3:
            risk_level = {
                "label": "高",
                "color": ft.colors.RED,
                "tooltip": "複数の注意点があります。内容を慎重に確認してください。",
            }
        elif score > 1:
            risk_level = {
                "label": "中",
                "color": ft.colors.ORANGE,
                "tooltip": "いくつかの注意点があります。確認を推奨します。",
            }
        elif score > 0:
            risk_level = {
                "label": "低",
                "color": ft.colors.YELLOW,
                "tooltip": "軽微な注意点があります。",
            }
        else:
            risk_level = {
                "label": "なし",
                "color": ft.colors.GREEN,
                "tooltip": "特に問題は見つかりませんでした。",
            }

        # 注目ポイントのコントロールを作成
        attention_controls = []
        for i, point in enumerate(attention_points):
            is_important = i < 2  # 最初の2つは重要なポイントとして扱う
            attention_controls.append(
                self._create_animated_point(point, i * 200, is_important)
            )

        # 組織情報が存在する場合は表示用のコンポーネントを作成
        organizations_ui = None
        if organizations:
            org_chips = []
            for org in organizations:
                org_chips.append(
                    ft.Chip(
                        label=ft.Text(org),
                        bgcolor=ft.colors.BLUE_50,
                        label_style=ft.TextStyle(size=12),
                    )
                )

            organizations_ui = ft.Column(
                [
                    ft.Text("関連組織:", weight="bold"),
                    ft.Wrap(
                        spacing=5,
                        run_spacing=5,
                        children=org_chips,
                    ),
                ]
            )

        # セクションの内容を更新
        section.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            name=ft.icons.PSYCHOLOGY_ALT,
                            size=16,
                            color=ft.colors.BLUE,
                        ),
                        ft.Text("AIレビュー (更新済み)", weight="bold"),
                        ft.Container(
                            content=ft.Icon(
                                name=ft.icons.REFRESH,
                                size=16,
                                color=ft.colors.BLUE,
                            ),
                            tooltip="AIに再評価させる",
                            width=32,
                            height=32,
                            border_radius=16,
                            on_hover=self._on_hover_effect,
                            on_click=self._on_ai_review_refresh,
                            alignment=ft.alignment.center,
                        ),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            # 要約セクション
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("要約:", weight="bold"),
                                        ft.Text(summary, size=14),
                                    ]
                                ),
                                margin=ft.margin.only(bottom=10),
                            ),
                            # リスクスコアセクション
                            ft.Row(
                                [
                                    ft.Text("リスクスコア:", weight="bold"),
                                    ft.Container(
                                        content=ft.Text(
                                            risk_level["label"],
                                            color=ft.colors.WHITE,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        bgcolor=risk_level["color"],
                                        border_radius=5,
                                        padding=5,
                                        width=50,
                                        alignment=ft.alignment.center,
                                        tooltip=risk_level["tooltip"],
                                    ),
                                    ft.Text(
                                        f"({score}点)", size=12, color=ft.colors.GREY
                                    ),
                                ],
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            # 注目ポイントセクション
                            ft.Column(
                                [
                                    ft.Text("注目ポイント:", weight="bold"),
                                    (
                                        ft.Column(
                                            attention_controls,
                                            spacing=2,
                                        )
                                        if attention_controls
                                        else ft.Text(
                                            "特に注目すべきポイントはありません",
                                            size=12,
                                            italic=True,
                                        )
                                    ),
                                ],
                                spacing=5,
                            ),
                            # 組織情報セクション（存在する場合のみ）
                            organizations_ui if organizations_ui else ft.Container(),
                            # レビュー詳細セクション
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("詳細評価:", weight="bold"),
                                        ft.Container(
                                            content=ft.Text(review, size=12),
                                            bgcolor=ft.colors.GREY_50,
                                            border_radius=5,
                                            padding=10,
                                            width=float("inf"),
                                        ),
                                    ]
                                ),
                                margin=ft.margin.only(top=10),
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=10,
                ),
            ],
            spacing=5,
        )

        self._safe_update()

    def _create_participants_row(self, role, participants):
        """参加者情報を表示する行を作成"""
        if not participants:
            return ft.Container(width=0)

        # 参加者が辞書形式のリストの場合
        if participants and isinstance(participants[0], dict):
            participant_names = []
            for p in participants:
                display_name = p.get("display_name") or p.get("name") or ""
                email = p.get("email") or ""
                if display_name and email:
                    participant_names.append(f"{display_name} <{email}>")
                elif email:
                    participant_names.append(email)
                elif display_name:
                    participant_names.append(display_name)

            if not participant_names:
                return ft.Container(width=0)

            return ft.Row(
                [
                    ft.Text(
                        f"{role}:",
                        weight="bold",
                        width=80,
                    ),
                    ft.Text(
                        ", ".join(participant_names),
                        size=12,
                    ),
                ],
                spacing=5,
            )

        # 従来の文字列形式の場合（後方互換性のため）
        return ft.Row(
            [
                ft.Text(
                    f"{role}:",
                    weight="bold",
                    width=80,
                ),
                ft.Text(
                    ", ".join(
                        [
                            p.split("<")[0].strip() if "<" in p else p
                            for p in participants
                        ]
                    ),
                    size=12,
                ),
            ],
            spacing=5,
        )

    def get_formatted_date(self, date_str):
        """日付を整形する"""
        try:
            # 日付文字列のフォーマットが異なる場合に対応するよう複数のパターンを試す
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
            ]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    # 日本語の曜日を取得
                    weekday = ["月", "火", "水", "木", "金", "土", "日"][dt.weekday()]
                    # 日本語形式で日付を整形
                    return f"{dt.year}年{dt.month}月{dt.day}日({weekday}) {dt.hour:02d}:{dt.minute:02d}"
                except ValueError:
                    continue

            # すべてのパターンが失敗した場合はそのまま返す
            return date_str
        except Exception:
            return date_str

    def reset(self):
        """コンポーネントの状態をリセット"""
        # コンテンツをクリア
        if hasattr(self, "header_container") and self.header_container:
            # 件名をクリア
            if hasattr(self, "subject_text") and self.subject_text:
                self.subject_text.value = ""

            # 送信者情報をクリア
            if hasattr(self, "sender_text") and self.sender_text:
                self.sender_text.value = ""

            # 日付をクリア
            if hasattr(self, "date_text") and self.date_text:
                self.date_text.value = ""

        # 本文コンテナをクリア
        if hasattr(self, "content_container") and self.content_container:
            self.content_container.content = None

        # 添付ファイルコンテナをクリア
        if hasattr(self, "attachments_container") and self.attachments_container:
            self.attachments_container.content = None

        # 現在表示中のメールIDをクリア
        self.current_mail_id = None

        # 表示中のメールデータをクリア
        self.current_mail = None
