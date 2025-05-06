"""
メール内容表示コンポーネント
選択されたメールの詳細情報を表示するためのコンポーネント
"""

import asyncio
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import flet as ft
from flet import ControlEvent

from src.core.logger import get_logger
from src.models.mail.styled_text import StyledText
from src.util.object_util import get_safe
from src.views.components.ai_review_component import AIReviewComponent
from src.views.styles.style import AppTheme, Colors, Styles


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

        # 初期化パラメータ
        self._init_parameters(on_flag_click, on_download_attachment)

        # コンポーネントの初期化
        self._init_components()

        # スタイル設定
        self._init_styles()

        # 初期表示を設定
        self._show_empty_content()

        self.logger.info("MailContentViewer: 初期化完了")

    def _init_parameters(self, on_flag_click, on_download_attachment):
        """パラメータの初期化"""
        # コールバック関数
        self.on_flag_click = on_flag_click
        self.on_download_attachment = on_download_attachment

        # 現在表示中のメールID
        self.current_mail_id = None

        # viewmodel参照用変数（外部から設定される）
        self.viewmodel = None

        # キーワードリスト
        self.keywords = self._load_keywords()

    def _init_components(self):
        """コンポーネントの初期化"""
        # StyledTextインスタンス
        self.styled_text = StyledText()

        # スクロール可能なコンテンツ列
        self.content_column = ft.Column(
            [],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # フラグボタン
        self.flag_button = ft.IconButton(
            icon=ft.icons.FLAG_OUTLINED,
            icon_color=Colors.TEXT_SECONDARY,
            icon_size=32,
            tooltip="問題のあるメールとしてフラグを立てる",
            on_click=self._toggle_flag,
        )

        # AIレビューコンポーネント
        self.ai_review_component = AIReviewComponent(
            on_refresh=self._handle_ai_review_refresh,
            viewmodel=None,  # ViewModelは後で設定
        )

        # コンテナの設定
        self.content = self.content_column

    def _init_styles(self):
        """スタイルの初期化"""
        self.expand = True
        self.bgcolor = Colors.BACKGROUND
        self.border = ft.border.all(1, Colors.BORDER)
        self.border_radius = AppTheme.CONTAINER_BORDER_RADIUS
        self.padding = AppTheme.DEFAULT_PADDING

    def _load_keywords(self) -> List[str]:
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

    def _show_empty_content(self):
        """空のメール内容表示"""
        self.content_column.controls.clear()
        self.content_column.controls.append(
            Styles.container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.EMAIL_OUTLINED,
                            size=40,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        Styles.subtitle(
                            "メールを選択してください",
                            color=Colors.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True,
                border=None,
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
        # ログ出力を修正: messageキーワード引数を重複させない
        # self.logger.error(f"MailContentViewer: エラーメッセージ表示 - {str(message)}")

        self.content_column.controls.clear()
        self.content_column.controls.append(
            Styles.container(
                content=ft.Column(
                    [
                        ft.Icon(
                            name=ft.icons.ERROR_OUTLINE,
                            size=40,
                            color=Colors.ERROR,
                        ),
                        Styles.subtitle(
                            "エラーが発生しました",
                            color=Colors.ERROR,
                            text_align=ft.TextAlign.CENTER,
                            weight=ft.FontWeight.BOLD,
                        ),
                        self.styled_text.generate_styled_text(
                            message,
                            self.keywords,
                            None,
                            {
                                "color": Colors.ERROR,
                                "text_align": ft.TextAlign.CENTER,
                            },
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True,
                border=None,
            )
        )
        self._safe_update()

    def _get_file_icon(self, filename):
        """ファイル種類に応じたアイコンを取得"""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext in ["pdf"]:
            return ft.Icon(name=ft.icons.PICTURE_AS_PDF, size=16, color=Colors.ERROR)
        elif ext in ["jpg", "jpeg", "png", "gif", "bmp"]:
            return ft.Icon(name=ft.icons.IMAGE, size=16, color=Colors.PRIMARY)
        elif ext in ["doc", "docx"]:
            return ft.Icon(name=ft.icons.DESCRIPTION, size=16, color=Colors.PRIMARY)
        elif ext in ["xls", "xlsx"]:
            return ft.Icon(name=ft.icons.TABLE_CHART, size=16, color=Colors.ACTION)
        elif ext in ["ppt", "pptx"]:
            return ft.Icon(
                name=ft.icons.PRESENT_TO_ALL, size=16, color=ft.colors.ORANGE
            )
        elif ext in ["zip", "rar", "7z", "tar", "gz"]:
            return ft.Icon(name=ft.icons.FOLDER_ZIP, size=16, color=ft.colors.BROWN)
        elif ext in ["mp3", "wav", "ogg"]:
            return ft.Icon(name=ft.icons.AUDIO_FILE, size=16, color=ft.colors.PURPLE)
        elif ext in ["mp4", "avi", "mov"]:
            return ft.Icon(name=ft.icons.VIDEO_FILE, size=16, color=Colors.ERROR)
        else:
            return ft.Icon(
                name=ft.icons.INSERT_DRIVE_FILE, size=16, color=Colors.TEXT_SECONDARY
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
        self.flag_button = ft.IconButton(
            icon=ft.icons.FLAG if is_flagged else ft.icons.FLAG_OUTLINED,
            icon_color=Colors.ERROR if is_flagged else Colors.TEXT_SECONDARY,
            tooltip=(
                "フラグを解除する"
                if is_flagged
                else "問題のあるメールとしてフラグを立てる"
            ),
            on_click=lambda e, mid=mail_id: self._toggle_flag(e, mid),
            icon_size=AppTheme.ICON_SIZE_MD,
        )

        return Styles.container(
            content=self.flag_button,
            tooltip=self.flag_button.tooltip,
            border=None,
            width=AppTheme.ICON_SIZE_LG,
            height=AppTheme.ICON_SIZE_LG,
            border_radius=AppTheme.ICON_SIZE_LG,
            on_hover=self._on_hover_effect,
            alignment=ft.alignment.center,
            data={"flagged": is_flagged},
            padding=0,
        )

    def _on_hover_effect(self, e):
        """ホバー効果"""
        # マウスが入ったとき
        if e.data == "true":
            e.control.bgcolor = ft.colors.with_opacity(0.1, Colors.PRIMARY)
        # マウスが出たとき
        else:
            e.control.bgcolor = None

        try:
            e.control.update()
        except Exception as ex:
            self.logger.debug(
                f"MailContentViewer: コントロール更新を延期します - {str(ex)}"
            )

    def _toggle_flag(self, e: ControlEvent, mail_id: str):
        """
        フラグ状態を切り替える
        即座にUIを更新し、親コンポーネントに通知する
        """
        try:
            # 現在のメール情報が取得できない場合は何もしない
            if not self.viewmodel or not mail_id:
                self.logger.warning("フラグ操作: 現在のメール情報がありません")
                return

            # 現在のフラグ状態を取得
            current_flag_state = self.viewmodel.get_mail_flag(mail_id)

            # フラグ状態を反転
            new_flag_state = not current_flag_state

            # ViewModelに変更を通知 (バックグラウンドでの処理)
            self.viewmodel.set_mail_flag(mail_id, new_flag_state)

            # まず即座にUIを更新
            self._update_flag_button_ui(new_flag_state)

            # 親コンポーネントのコールバックを呼び出す
            if self.on_flag_click:
                self.on_flag_click(mail_id, new_flag_state)
                self.logger.debug(
                    f"フラグ状態変更を通知: {mail_id}, 状態: {new_flag_state}"
                )

        except Exception as e:
            # エラーメッセージの修正 - messageキーワード引数の重複を修正
            # self.logger.error(f"フラグ切替処理でエラー: {str(e)}")
            self.show_error_message(f"フラグ操作に失敗しました: {str(e)}")

    def _update_flag_button_ui(self, is_flagged=None):
        """
        フラグボタンのUI状態を更新する
        """
        try:
            # フラグボタンが存在しない場合は何もしない
            if not hasattr(self, "flag_button") or not self.flag_button:
                return

            # 現在のメール情報が取得できない場合はボタンを無効化
            if not self.current_mail_id:
                self.flag_button.disabled = True
                self.flag_button.icon_color = ft.colors.GREY_400
                self.flag_button.tooltip = "メール未選択"
                self.flag_button.update()
                return

            # is_flaggedが指定されていない場合は、ViewModelから取得
            if is_flagged is None and self.viewmodel:
                is_flagged = self.viewmodel.get_mail_flag(self.current_mail_id)

            # ボタンをアクティブ化
            self.flag_button.disabled = False

            # アニメーション効果を追加
            self.flag_button.animate_opacity = 300  # ミリ秒

            if is_flagged:
                # フラグが立っている場合の表示
                self.flag_button.icon = ft.icons.FLAG
                self.flag_button.icon_color = Colors.ERROR
                self.flag_button.tooltip = "フラグを解除する"
            else:
                # フラグが立っていない場合の表示
                self.flag_button.icon = ft.icons.FLAG_OUTLINED
                self.flag_button.icon_color = Colors.TEXT_SECONDARY
                self.flag_button.tooltip = "問題のあるメールとしてフラグを立てる"

            # UIを更新
            self.flag_button.update()

        except Exception as e:
            self.logger.error(f"フラグボタンUI更新中にエラー: {e}")
            # UI更新失敗してもクラッシュさせない

    def _download_attachment(self, e, file_id):
        """添付ファイルのダウンロード処理"""
        self.logger.info(f"MailContentViewer: 添付ファイルダウンロード {file_id}")
        if self.on_download_attachment:
            self.on_download_attachment(file_id)

    def show_mail_content(self, mail: Dict[str, Any], mail_id: str = None):
        """メール内容を表示"""
        if mail_id:
            self.current_mail_id = mail_id
        else:
            self.current_mail_id = mail.get("id", None)

        self.logger.info(
            f"MailContentViewer: メール内容表示 mail_id={self.current_mail_id}"
        )

        if not mail:
            self.show_error_message("メール内容の取得に失敗しました")
            return

        # メール内容表示をクリア
        self.content_column.controls.clear()

        # ViewModelを設定
        self.ai_review_component.viewmodel = self.viewmodel

        # メールデータのチェックと安全な取得
        # 送信者情報を解析
        sender = mail.get("sender", "不明 <unknown@example.com>")
        sender_name = sender.split("<")[0].strip() if "<" in sender else sender
        sender_email = (
            sender.split("<")[1].replace(">", "") if "<" in sender else sender
        )

        # 受信者情報を解析
        recipient = mail.get("recipient", "不明 <unknown@example.com>")
        if not isinstance(recipient, str):
            self.logger.warning(
                f"MailContentViewer: 受信者情報が文字列ではありません recipient_type={type(recipient).__name__} mail_id={mail_id}"
            )
            recipient = "不明 <unknown@example.com>"

        recipient_name = (
            recipient.split("<")[0].strip() if "<" in recipient else recipient
        )
        recipient_email = (
            recipient.split("<")[1].replace(">", "") if "<" in recipient else recipient
        )

        # 受信者が複数いる場合（カンマで区切られている場合）
        recipients = []
        if "," in recipient:
            # カンマで区切って複数の受信者を分割
            recipient_parts = recipient.split(",")
            for part in recipient_parts:
                part = part.strip()
                if not part:
                    continue
                r_name = part.split("<")[0].strip() if "<" in part else part
                r_email = part.split("<")[1].replace(">", "") if "<" in part else part
                recipients.append(f"{r_name} <{r_email}>")
        else:
            # 単一の受信者の場合
            recipients.append(f"{recipient_name} <{recipient_email}>")

        # 添付ファイルがあれば表示用のリストを作成
        attachments_section = []
        attachments = mail.get("attachments", [])

        # 添付ファイルアイコン
        attachments_icon = (
            ft.Row(
                [
                    ft.Icon(
                        name=ft.icons.ATTACH_FILE,
                        size=14,
                        color=ft.colors.GREY,
                    ),
                    self.styled_text.generate_styled_text(
                        f"{len(attachments)}個の添付ファイル",
                        self.keywords,
                        None,
                        {"size": 12, "color": ft.colors.GREY},
                    ),
                ],
                spacing=2,
            )
            if attachments
            else ft.Container(width=0)
        )

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
                                            self.styled_text.generate_styled_text(
                                                attachment.get(
                                                    "name", "不明なファイル"
                                                ),
                                                self.keywords,
                                                None,
                                                None,
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
                                    ft.Container(
                                        content=self.styled_text.generate_styled_text(
                                            mail.get("subject", "(件名なし)"),
                                            self.keywords,
                                            None,
                                            {
                                                "size": 18,
                                                "weight": ft.FontWeight.BOLD,
                                            },
                                        ),
                                        expand=True,
                                    ),
                                    # フラグボタン
                                    ft.Container(
                                        content=self.create_flag_button(
                                            self.current_mail_id,
                                            mail.get("flagged", False),
                                        ),
                                        border=None,
                                        alignment=ft.alignment.center_right,
                                        width=50,
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
                                                    self.styled_text.generate_styled_text(
                                                        f"{sender_name} <{sender_email}>",
                                                        self.keywords,
                                                        None,
                                                        {
                                                            "size": 12,
                                                            "weight": ft.FontWeight.BOLD,
                                                        },
                                                    ),
                                                ],
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        "宛先:", weight="bold", width=80
                                                    ),
                                                    ft.Column(
                                                        [
                                                            self.styled_text.generate_styled_text(
                                                                recipient_text,
                                                                self.keywords,
                                                                None,
                                                                None,
                                                            )
                                                            for recipient_text in recipients
                                                        ],
                                                        spacing=2,
                                                    ),
                                                ],
                                                vertical_alignment=ft.CrossAxisAlignment.START,
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
                                                    self.styled_text.generate_styled_text(
                                                        mail.get("date", "不明な日時"),
                                                        self.keywords,
                                                        None,
                                                        None,
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
                # AIレビュー表示（メールにAIレビュー情報がある場合）
                self.ai_review_component,
                # コンテンツボディ
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
                                    else self.styled_text.generate_styled_text(
                                        mail.get("content", ""),
                                        self.keywords,
                                        None,
                                        None,
                                    )
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
                # 添付ファイル表示
                *attachments_section,
            ]
        )

        # AIレビュー情報があれば表示
        if mail.get("ai_review") or (mail.get("thread_id") and self.viewmodel):
            self.ai_review_component.show_review_for_mail(
                self.current_mail_id, mail.get("ai_review")
            )
        else:
            # AIレビュー情報がない場合は非表示
            self.ai_review_component.reset()

        self._safe_update()
        self.logger.info("MailContentViewer: メール内容表示完了")

    def show_thread_content(
        self, mails: List[Dict[str, Any]], sort_button: ft.Control = None
    ):
        """会話内容を表示"""
        self.logger.info(
            "MailContentViewer: 会話内容表示", mail_count=len(mails) if mails else 0
        )

        # 詳細なデバッグ情報
        self.logger.debug(
            "MailContentViewer: show_thread_content引数詳細",
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

        # ViewModelを設定
        self.ai_review_component.viewmodel = self.viewmodel

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
            risk_score = self.viewmodel.get_thread_risk_score(mails)
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
                # AIレビュー表示
                self.ai_review_component,
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

        # AIレビュー情報があれば表示
        thread_id = mails[0].get("thread_id") if mails else None
        if thread_id:
            self.ai_review_component.show_review_for_thread(
                thread_id, mails, ai_review_info, risk_score
            )
        else:
            # AIレビュー情報がない場合は非表示
            self.ai_review_component.reset()

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
        self.logger.info(f"MailContentViewer: 会話内容表示完了 mail_count={len(mails)}")

    def _create_mail_content_item(self, mail, index):
        """会話内の個別メールアイテムを作成"""
        # データの安全な取得
        mail_id = mail.get("id", "")

        self.logger.debug(
            f"MailContentViewer: _create_mail_content_item詳細 mail_id={mail_id} mail_idx={index} mail_type={type(mail).__name__}"
        )

        if not isinstance(mail, dict):
            self.logger.error(
                f"MailContentViewer: メールデータが辞書型ではありません mail_type={type(mail).__name__} mail_idx={index}"
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
                f"MailContentViewer: 送信者情報が文字列ではありません sender_type={type(sender).__name__} mail_id={mail_id}"
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
                f"MailContentViewer: 受信者情報が文字列ではありません recipient_type={type(recipient).__name__} mail_id={mail_id}"
            )
            recipient = "不明 <unknown@example.com>"

        recipient_name = (
            recipient.split("<")[0].strip() if "<" in recipient else recipient
        )
        recipient_email = (
            recipient.split("<")[1].replace(">", "") if "<" in recipient else recipient
        )

        # 受信者が複数いる場合（カンマで区切られている場合）
        recipients = []
        if "," in recipient:
            # カンマで区切って複数の受信者を分割
            recipient_parts = recipient.split(",")
            for part in recipient_parts:
                part = part.strip()
                if not part:
                    continue
                r_name = part.split("<")[0].strip() if "<" in part else part
                r_email = part.split("<")[1].replace(">", "") if "<" in part else part
                recipients.append(f"{r_name} <{r_email}>")
        else:
            # 単一の受信者の場合
            recipients.append(f"{recipient_name} <{recipient_email}>")

        # 添付ファイルアイコン
        attachments = mail.get("attachments", [])
        if not isinstance(attachments, list):
            self.logger.warning(
                f"MailContentViewer: 添付ファイル情報がリスト型ではありません attachments_type={type(attachments).__name__} mail_id={mail_id}"
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
                    self.styled_text.generate_styled_text(
                        f"{len(attachments)}個の添付ファイル",
                        self.keywords,
                        None,
                        {"size": 12, "color": ft.colors.GREY},
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
                f"MailContentViewer: メール本文が文字列ではありません content_type={type(content).__name__} mail_id={mail_id}"
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
                    else self.styled_text.generate_styled_text(
                        preview_text, self.keywords, None, None
                    )
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
                                self.styled_text.generate_styled_text(
                                    mail.get("date", "不明な日時"),
                                    self.keywords,
                                    None,
                                    {"size": 12, "color": ft.colors.GREY},
                                ),
                                self.styled_text.generate_styled_text(
                                    f"送信者: {sender_name}",
                                    self.keywords,
                                    None,
                                    {
                                        "size": 12,
                                        "weight": ft.FontWeight.BOLD,
                                    },
                                ),
                                # フラグボタン
                                ft.Container(
                                    content=self.create_flag_button(
                                        self.current_mail_id,
                                        mail.get("flagged", False),
                                    ),
                                    border=None,
                                    alignment=ft.alignment.center_right,
                                    width=50,
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
        self.logger.debug("MailContentViewer: メール内容表示切り替え")

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
            content_container.content = (
                ft.Markdown(
                    container_data["preview_text"],
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                )
                if is_markdown
                else self.styled_text.generate_styled_text(
                    container_data["preview_text"], self.keywords, None, None
                )
            )
            container_data["expanded"] = False
            button_text.value = "続きを見る"
            button_icon.name = ft.icons.EXPAND_MORE
        else:
            # 展開する
            content_container.content = (
                ft.Markdown(
                    container_data["full_text"],
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                )
                if is_markdown
                else self.styled_text.generate_styled_text(
                    container_data["full_text"], self.keywords, None, None
                )
            )
            container_data["expanded"] = True
            button_text.value = "折りたたむ"
            button_icon.name = ft.icons.EXPAND_LESS

        # 高さを自動調整
        content_container.height = None

        # データを更新
        content_container.data = container_data

        # 更新
        content_container.update()
        button.update()

        self.logger.debug(
            "MailContentViewer: メール内容表示切り替え完了", expanded=not is_expanded
        )

    def _create_participants_row(self, role, participants):
        """参加者情報を表示する行を作成"""
        if not participants:
            return ft.Container(height=0)  # 空のコンテナを返す

        # 参加者情報を整形
        participant_texts = []
        for p in participants:
            name = p.get("display_name") or p.get("name") or ""
            email = p.get("email") or ""
            if name and email:
                participant_texts.append(f"{name} <{email}>")
            elif email:
                participant_texts.append(email)
            elif name:
                participant_texts.append(name)

        if not participant_texts:
            return ft.Container(height=0)  # 参加者情報がなければ空のコンテナを返す

        # 参加者情報を結合
        participant_text = ", ".join(participant_texts)

        return ft.Row(
            [
                Styles.text(f"{role}:", weight=ft.FontWeight.BOLD, width=80),
                self.styled_text.generate_styled_text(
                    participant_text, self.keywords, None, None
                ),
            ],
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
        """コンポーネントのリセット"""
        self.content_column.controls.clear()
        self.current_mail_id = None
        self.flag_button = None

        # ViewModel参照をクリア
        self.viewmodel = None

        # AIレビューコンポーネントのリセット
        if hasattr(self, "ai_review_component"):
            self.ai_review_component.reset()

        self._safe_update()
        self.logger.debug("MailContentViewer: リセット完了")

    def update_flag_status(self, mail_id: str, is_flagged: bool) -> None:
        """
        外部からフラグ状態を更新する

        Args:
            mail_id: メールID
            is_flagged: 新しいフラグ状態
        """
        self.logger.debug(
            "MailContentViewer: フラグ状態を外部から更新",
            mail_id=mail_id,
            is_flagged=is_flagged,
        )

        # 表示中のメールIDと一致する場合のみUIを更新
        if mail_id == self.current_mail_id:
            self._update_flag_button_ui(is_flagged)

    def _handle_ai_review_refresh(self, id_value, is_thread):
        """AIレビューリフレッシュハンドラ"""
        self.logger.info(
            "MailContentViewer: AIレビュー再評価リクエスト",
            id_value=id_value,
            is_thread=is_thread,
        )

        try:
            # スレッドの場合
            if (
                is_thread
                and hasattr(self.viewmodel, "model")
                and hasattr(self.viewmodel.model, "get_ai_review_for_thread")
            ):
                # AIレビュー結果を再取得（実際には通常APIを呼ぶ）
                thread_id = id_value

                # 会話のメールリストを取得
                mails = []
                if hasattr(self.viewmodel, "get_thread_mails"):
                    mails = self.viewmodel.get_thread_mails(thread_id)

                # 非同期処理を模倣（実際のアプリでは適切な非同期処理を実装）
                def delayed_update():
                    time.sleep(2)  # 処理時間を模倣
                    ai_review = self.viewmodel.model.get_ai_review_for_thread(thread_id)
                    risk_score = (
                        self.viewmodel.get_thread_risk_score(mails) if mails else None
                    )

                    # 結果を表示
                    def update_ui():
                        self.ai_review_component.show_review_for_thread(
                            thread_id, mails, ai_review, risk_score
                        )

                    # UIスレッドで更新
                    if hasattr(self, "page") and self.page:
                        self.page.run_task(update_ui)

                # バックグラウンドスレッドで実行
                threading.Thread(target=delayed_update, daemon=True).start()

            # メール単体の場合
            elif not is_thread and hasattr(self.viewmodel, "get_mail_content"):
                mail_id = id_value

                # 非同期処理を模倣
                def delayed_update():
                    time.sleep(2)  # 処理時間を模倣
                    mail = self.viewmodel.get_mail_content(mail_id)

                    # 結果を表示
                    def update_ui():
                        if mail:
                            self.ai_review_component.show_review_for_mail(
                                mail_id, mail.get("ai_review")
                            )

                    # UIスレッドで更新
                    if hasattr(self, "page") and self.page:
                        self.page.run_task(update_ui)

                # バックグラウンドスレッドで実行
                threading.Thread(target=delayed_update, daemon=True).start()

            else:
                self.logger.warning(
                    "MailContentViewer: AIレビュー再評価に必要なメソッドが見つかりません"
                )

        except Exception as e:
            self.logger.error(
                f"MailContentViewer: AIレビュー再評価中にエラー - {str(e)}"
            )
